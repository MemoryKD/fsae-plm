using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using CatiaClient.Models;

namespace CatiaClient.Services;

/// <summary>
/// PLM 系统 REST API 客户端，封装所有与后端的 HTTP 通信。
/// 使用 HttpClient 的 BaseAddress 机制，所有请求路径为相对路径。
/// JSON 序列化使用 snake_case 命名策略以匹配后端 API 规范。
/// </summary>
public class ApiClient
{
    private HttpClient _http;
    private readonly string _baseUrl;
    private string? _token;

    /// <summary>
    /// JSON 序列化选项，使用 snake_case 命名策略匹配后端 API。
    /// </summary>
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
    };

    /// <summary>
    /// 初始化 API 客户端。
    /// 注意：HttpClient.BaseAddress 要求以 "/" 结尾，否则相对路径拼接会出错。
    /// </summary>
    /// <param name="baseUrl">后端 API 基础地址，默认为 http://localhost/api</param>
    public ApiClient(string baseUrl = "http://localhost/api")
    {
        _baseUrl = baseUrl;
        _http = new HttpClient { BaseAddress = new Uri(baseUrl.TrimEnd('/') + "/") };
    }

    /// <summary>
    /// 动态切换 API 服务器地址。会销毁旧 HttpClient 并创建新实例。
    /// </summary>
    /// <param name="baseUrl">新的后端 API 基础地址</param>
    public void SetBaseUrl(string baseUrl)
    {
        _http.Dispose();
        _http = new HttpClient { BaseAddress = new Uri(baseUrl.TrimEnd('/') + "/") };
    }

    /// <summary>是否已通过认证（存在有效的 JWT token）</summary>
    public bool IsAuthenticated => !string.IsNullOrEmpty(_token);

    /// <summary>
    /// 设置 JWT token 并添加到 HttpClient 默认请求头。
    /// 后续所有请求都会自动携带 Authorization: Bearer {token}。
    /// </summary>
    /// <param name="token">JWT access token</param>
    private void SetToken(string token)
    {
        _token = token;
        _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);
    }

    /// <summary>
    /// 用户登录。成功后自动保存 JWT token 用于后续请求。
    /// </summary>
    /// <param name="username">用户名</param>
    /// <param name="password">密码</param>
    /// <returns>登录成功返回 true，失败返回 false</returns>
    public async Task<bool> LoginAsync(string username, string password)
    {
        var json = JsonSerializer.Serialize(new { username, password });
        var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");
        var response = await _http.PostAsync("auth/login", content);
        var body = await response.Content.ReadAsStringAsync();
        if (!response.IsSuccessStatusCode) return false;
        var result = JsonSerializer.Deserialize<JsonElement>(body);
        SetToken(result.GetProperty("access_token").GetString()!);
        return true;
    }

    /// <summary>
    /// 用户注册。注册后需等待管理员审批。
    /// </summary>
    /// <param name="username">用户名</param>
    /// <param name="password">密码</param>
    /// <param name="fullName">真实姓名</param>
    /// <param name="department">所属部门，可选</param>
    /// <param name="joinYear">入队年份，可选</param>
    /// <param name="phone">联系电话，可选</param>
    /// <returns>成功返回 (true, "")，失败返回 (false, 错误信息)</returns>
    public async Task<(bool Success, string Error)> RegisterAsync(string username, string password, string fullName, string? department, string? joinYear, string? phone)
    {
        var json = JsonSerializer.Serialize(new
        {
            username,
            password,
            full_name = fullName,
            department,
            join_year = joinYear,
            phone
        });
        var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");
        var response = await _http.PostAsync("auth/register", content);
        if (response.IsSuccessStatusCode) return (true, "");
        var body = await response.Content.ReadAsStringAsync();
        try
        {
            var result = JsonSerializer.Deserialize<JsonElement>(body);
            return (false, result.GetProperty("detail").GetString() ?? "注册失败");
        }
        catch { return (false, $"注册失败: {response.StatusCode}"); }
    }

    /// <summary>
    /// 获取零件列表，支持按关键词模糊搜索。
    /// </summary>
    /// <param name="search">搜索关键词（按名称或编号匹配），为 null 时返回全部</param>
    /// <returns>零件列表</returns>
    public async Task<List<Part>> GetPartsAsync(string? search = null)
    {
        var url = "parts/";
        if (!string.IsNullOrEmpty(search)) url += $"?search={Uri.EscapeDataString(search)}";
        return await _http.GetFromJsonAsync<List<Part>>(url, JsonOptions) ?? new();
    }

    /// <summary>
    /// 获取单个零件详情。
    /// </summary>
    /// <param name="partId">零件 ID</param>
    /// <returns>零件信息，失败返回 null</returns>
    public async Task<Part?> GetPartAsync(Guid partId)
    {
        try { return await _http.GetFromJsonAsync<Part>($"parts/{partId}", JsonOptions); }
        catch { return null; }
    }

    /// <summary>
    /// 基于模板创建新零件，服务器根据模板规则自动生成零件编号。
    /// </summary>
    /// <param name="name">零件名称</param>
    /// <param name="type">零件类型（part 或 assembly）</param>
    /// <param name="subsystem">所属子系统</param>
    /// <param name="templateId">编号模板 ID</param>
    /// <returns>创建的零件，失败返回 null</returns>
    public async Task<Part?> CreateWithTemplateAsync(string name, string type, string subsystem, Guid templateId)
    {
        var form = new Dictionary<string, string>
        {
            ["name"] = name,
            ["type"] = type,
            ["subsystem"] = subsystem,
            ["template_id"] = templateId.ToString()
        };
        var response = await _http.PostAsync("parts/create-with-template", new FormUrlEncodedContent(form));
        if (!response.IsSuccessStatusCode) return null;
        return await response.Content.ReadFromJsonAsync<Part>(JsonOptions);
    }

    /// <summary>
    /// 删除指定零件。
    /// </summary>
    /// <param name="partId">要删除的零件 ID</param>
    /// <returns>删除成功返回 true</returns>
    public async Task<bool> DeletePartAsync(Guid partId)
    {
        var response = await _http.DeleteAsync($"parts/{partId}");
        return response.IsSuccessStatusCode;
    }

    /// <summary>
    /// 检出零件。将零件状态锁定为"检出"，防止其他人同时编辑。
    /// </summary>
    /// <param name="partId">要检出的零件 ID</param>
    /// <returns>更新后的零件信息，失败返回 null</returns>
    public async Task<Part?> CheckoutAsync(Guid partId)
    {
        var response = await _http.PostAsync($"parts/{partId}/checkout", null);
        if (!response.IsSuccessStatusCode) return null;
        return await response.Content.ReadFromJsonAsync<Part>(JsonOptions);
    }

    /// <summary>
    /// 检入零件。上传 CATIA 文件并创建新版本，解除检出锁定。
    /// 使用 multipart/form-data 格式上传文件。
    /// </summary>
    /// <param name="partId">要检入的零件 ID</param>
    /// <param name="filePath">本地 CATIA 文件路径</param>
    /// <param name="comment">检入备注，可选</param>
    /// <returns>更新后的零件信息，失败返回 null</returns>
    public async Task<Part?> CheckinAsync(Guid partId, string filePath, string comment = "")
    {
        using var content = new MultipartFormDataContent();
        var fileBytes = await File.ReadAllBytesAsync(filePath);
        content.Add(new ByteArrayContent(fileBytes), "file", Path.GetFileName(filePath));
        content.Add(new StringContent(comment), "comment");
        var response = await _http.PostAsync($"parts/{partId}/checkin", content);
        if (!response.IsSuccessStatusCode) return null;
        return await response.Content.ReadFromJsonAsync<Part>(JsonOptions);
    }

    /// <summary>
    /// 发布零件，将生命周期状态变更为"已发布"。
    /// 仅已检入状态的零件可以发布。
    /// </summary>
    /// <param name="partId">要发布的零件 ID</param>
    /// <returns>更新后的零件信息，失败返回 null</returns>
    public async Task<Part?> PublishAsync(Guid partId)
    {
        var response = await _http.PostAsync($"parts/{partId}/publish", null);
        if (!response.IsSuccessStatusCode) return null;
        return await response.Content.ReadFromJsonAsync<Part>(JsonOptions);
    }

    /// <summary>
    /// 获取指定零件的版本历史列表。
    /// </summary>
    /// <param name="partId">零件 ID</param>
    /// <returns>版本列表，按版本号降序排列</returns>
    public async Task<List<PartVersion>> GetVersionsAsync(Guid partId)
    {
        return await _http.GetFromJsonAsync<List<PartVersion>>($"parts/{partId}/versions", JsonOptions) ?? new();
    }

    /// <summary>
    /// 下载指定版本的文件到本地。
    /// </summary>
    /// <param name="partId">零件 ID</param>
    /// <param name="versionId">版本 ID</param>
    /// <param name="savePath">本地保存路径</param>
    /// <returns>下载成功返回 true</returns>
    public async Task<bool> DownloadVersionAsync(Guid partId, Guid versionId, string savePath)
    {
        var response = await _http.GetAsync($"parts/{partId}/versions/{versionId}/download");
        if (!response.IsSuccessStatusCode) return false;
        var bytes = await response.Content.ReadAsByteArrayAsync();
        await File.WriteAllBytesAsync(savePath, bytes);
        return true;
    }

    /// <summary>
    /// 预览下一个可用的零件编号，用于创建零件前展示。
    /// </summary>
    /// <param name="templateId">编号模板 ID</param>
    /// <param name="subsystemCode">子系统代码</param>
    /// <param name="partType">零件类型</param>
    /// <returns>预览编号字符串，失败返回 null</returns>
    public async Task<string?> GetNextPartNumberAsync(Guid templateId, string subsystemCode, string partType)
    {
        try
        {
            var result = await _http.GetFromJsonAsync<JsonElement>(
                $"parts/next-number?template_id={templateId}&subsystem_code={Uri.EscapeDataString(subsystemCode)}&part_type={partType}");
            return result.GetProperty("part_number").GetString();
        }
        catch { return null; }
    }

    /// <summary>
    /// 获取所有可用的编号模板列表。
    /// </summary>
    /// <returns>模板列表</returns>
    public async Task<List<Template>> GetTemplatesAsync()
    {
        return await _http.GetFromJsonAsync<List<Template>>("templates", JsonOptions) ?? new();
    }

    /// <summary>
    /// 获取指定总成零件的 BOM（物料清单）。
    /// </summary>
    /// <param name="partId">总成零件 ID</param>
    /// <returns>BOM 条目列表</returns>
    public async Task<List<BomItem>> GetBomAsync(Guid partId)
    {
        return await _http.GetFromJsonAsync<List<BomItem>>($"parts/{partId}/bom", JsonOptions) ?? new();
    }

    /// <summary>
    /// 下载总成及其所有子零件的文件。下载为 ZIP 压缩包后自动解压到指定目录。
    /// </summary>
    /// <param name="partId">总成零件 ID</param>
    /// <param name="saveDir">本地保存目录</param>
    /// <returns>下载并解压成功返回 true</returns>
    public async Task<bool> DownloadAssemblyAsync(Guid partId, string saveDir)
    {
        var response = await _http.GetAsync($"parts/{partId}/download-all");
        if (!response.IsSuccessStatusCode) return false;
        var zipPath = Path.Combine(saveDir, $"assembly_{partId}.zip");
        var bytes = await response.Content.ReadAsByteArrayAsync();
        await File.WriteAllBytesAsync(zipPath, bytes);
        System.IO.Compression.ZipFile.ExtractToDirectory(zipPath, saveDir, true);
        File.Delete(zipPath);
        return true;
    }

    /// <summary>
    /// 为零件创建分支，用于并行设计方案。
    /// </summary>
    /// <param name="partId">源零件 ID</param>
    /// <param name="branchName">分支名称</param>
    /// <returns>新创建的分支零件，失败返回 null</returns>
    public async Task<Part?> CreateBranchAsync(Guid partId, string branchName)
    {
        var form = new Dictionary<string, string> { ["branch_name"] = branchName };
        var response = await _http.PostAsync($"parts/{partId}/branch", new FormUrlEncodedContent(form));
        if (!response.IsSuccessStatusCode) return null;
        return await response.Content.ReadFromJsonAsync<Part>(JsonOptions);
    }

    /// <summary>
    /// 获取指定零件的所有分支列表。
    /// </summary>
    /// <param name="partId">源零件 ID</param>
    /// <returns>分支零件列表</returns>
    public async Task<List<Part>> GetBranchesAsync(Guid partId)
    {
        return await _http.GetFromJsonAsync<List<Part>>($"parts/{partId}/branches", JsonOptions) ?? new();
    }
}
