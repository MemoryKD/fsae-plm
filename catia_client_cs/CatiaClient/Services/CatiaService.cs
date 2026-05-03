using System.Runtime.InteropServices;
using CatiaClient.Models;

namespace CatiaClient.Services;

/// <summary>
/// CATIA COM 自动化服务，通过 P/Invoke 和动态 COM 互操作与正在运行的 CATIA 进程通信。
/// 提供文档操作、自定义属性读写、缩略图捕获等功能。
/// </summary>
public class CatiaService
{
    /// <summary>CATIA Application COM 对象，通过 dynamic 类型实现后期绑定调用</summary>
    private dynamic? _catia;

    /// <summary>
    /// P/Invoke 声明：获取已运行的 COM 对象实例。
    /// oleaut32.dll 中的 GetActiveObject 根据 CLSID 查找已注册的运行中 COM 对象。
    /// PreserveSig = false 表示失败时抛出异常而非返回 HRESULT。
    /// </summary>
    [DllImport("oleaut32.dll", PreserveSig = false)]
    private static extern void GetActiveObject(
        [MarshalAs(UnmanagedType.LPStruct)] Guid rclsid,
        IntPtr pvReserved,
        [MarshalAs(UnmanagedType.IUnknown)] out object ppunk);

    /// <summary>
    /// P/Invoke 声明：将 ProgID（如 "CATIA.Application"）转换为 CLSID。
    /// ole32.dll 中的 CLSIDFromProgID 是 COM 基础设施函数。
    /// </summary>
    [DllImport("ole32.dll")]
    private static extern int CLSIDFromProgID(
        [MarshalAs(UnmanagedType.LPWStr)] string progId,
        out Guid clsid);

    /// <summary>
    /// 尝试获取已运行的 COM 对象实例，支持多个 ProgID。
    /// CATIA 不同版本/安装方式可能使用不同的 ProgID。
    /// </summary>
    private static object? GetActiveComObject(string progId)
    {
        try
        {
            CLSIDFromProgID(progId, out var clsid);
            GetActiveObject(clsid, IntPtr.Zero, out var obj);
            return obj;
        }
        catch
        {
            return null;
        }
    }

    /// <summary>是否已连接到 CATIA 进程</summary>
    public bool IsConnected => _catia != null;

    /// <summary>最近一次操作的错误信息</summary>
    public string? LastError { get; private set; }

    /// <summary>
    /// 连接到已运行的 CATIA 进程。尝试多个 ProgID 以兼容不同 CATIA 版本。
    /// </summary>
    /// <returns>连接成功返回 true</returns>
    public bool Connect()
    {
        _catia = null;
        LastError = null;

        // 尝试多个 ProgID，覆盖不同 CATIA 版本
        var progIds = new[]
        {
            "CATIA.Application",
            "CATIA.Application.1",
        };

        var errors = new List<string>();

        foreach (var progId in progIds)
        {
            try
            {
                var obj = GetActiveComObject(progId);
                if (obj != null)
                {
                    _catia = obj;
                    return true;
                }
                errors.Add($"ProgID '{progId}': 未找到运行中的实例");
            }
            catch (Exception ex)
            {
                errors.Add($"ProgID '{progId}': {ex.Message}");
            }
        }

        // 所有 ProgID 都失败，尝试直接用 Type.GetTypeFromProgID 创建新实例
        try
        {
            var type = Type.GetTypeFromProgID("CATIA.Application");
            if (type != null)
            {
                _catia = Activator.CreateInstance(type);
                if (_catia != null) return true;
            }
        }
        catch (Exception ex)
        {
            errors.Add($"CreateInstance: {ex.Message}");
        }

        LastError = string.Join("; ", errors);
        return false;
    }

    /// <summary>
    /// 获取 CATIA 当前活动文档的名称（不含路径）。
    /// </summary>
    /// <returns>文档名称，无活动文档返回 null</returns>
    public string? GetActiveDocumentName()
    {
        try { return _catia?.ActiveDocument?.Name; }
        catch { return null; }
    }

    /// <summary>
    /// 获取 CATIA 当前活动文档的完整文件路径。
    /// </summary>
    /// <returns>文件完整路径，无活动文档返回 null</returns>
    public string? GetActiveDocumentPath()
    {
        try { return _catia?.ActiveDocument?.FullName; }
        catch { return null; }
    }

    /// <summary>
    /// 读取 CATIA 当前活动文档的所有自定义属性（UserRefProperties）。
    /// CATIA 的 UserRefProperties 集合索引从 1 开始（非 0）。
    /// </summary>
    /// <returns>属性名-值字典，无文档时返回空字典</returns>
    public Dictionary<string, string> GetCustomProperties()
    {
        var props = new Dictionary<string, string>();
        try
        {
            if (_catia?.ActiveDocument == null) return props;
            var userRefs = _catia.ActiveDocument.UserRefProperties;
            // CATIA COM 集合索引从 1 开始
            for (int i = 1; i <= userRefs.Count; i++)
            {
                var prop = userRefs.Item(i);
                props[prop.Name] = prop.Value?.ToString() ?? "";
            }
        }
        catch { }
        return props;
    }

    /// <summary>
    /// 设置 CATIA 当前活动文档的指定自定义属性值。
    /// 如果属性不存在，CATIA 会抛出异常（静默忽略）。
    /// </summary>
    /// <param name="name">属性名称</param>
    /// <param name="value">属性值</param>
    public void SetCustomProperty(string name, string value)
    {
        try
        {
            if (_catia?.ActiveDocument == null) return;
            _catia.ActiveDocument.UserRefProperties.Item(name).Value = value;
        }
        catch { }
    }

    /// <summary>
    /// 将 PLM 零件属性同步到 CATIA 文档的自定义属性中。
    /// 写入 PLM_PartNumber、PLM_Name、PLM_Version、PLM_State 四个属性。
    /// </summary>
    /// <param name="part">PLM 零件数据</param>
    public void SyncPlmProperties(Part part)
    {
        SetCustomProperty("PLM_PartNumber", part.PartNumber);
        SetCustomProperty("PLM_Name", part.Name);
        SetCustomProperty("PLM_Version", part.CurrentVersion ?? "");
        SetCustomProperty("PLM_State", part.LifecycleState);
    }

    /// <summary>
    /// 捕获 CATIA 当前活动文档的缩略图。通过 ExportData 导出为 BMP 格式。
    /// width 和 height 参数当前未使用，ExportData 按 CATIA 默认分辨率导出。
    /// </summary>
    /// <param name="savePath">缩略图保存路径</param>
    /// <param name="width">期望宽度（当前未生效）</param>
    /// <param name="height">期望高度（当前未生效）</param>
    /// <returns>保存路径，失败返回 null</returns>
    public string? CaptureThumbnail(string savePath, int width = 800, int height = 600)
    {
        try
        {
            if (_catia?.ActiveDocument == null) return null;
            _catia.ActiveDocument.ExportData(savePath, "bmp");
            return savePath;
        }
        catch { return null; }
    }

    /// <summary>
    /// 保存 CATIA 当前活动文档。
    /// </summary>
    /// <returns>成功返回 true，失败返回 false</returns>
    public bool SaveDocument()
    {
        try
        {
            if (_catia?.ActiveDocument == null) return false;
            _catia.ActiveDocument.Save();
            return true;
        }
        catch (Exception ex)
        {
            LastError = $"保存文档失败: {ex.Message}";
            return false;
        }
    }

    /// <summary>
    /// 在 CATIA 中打开指定路径的文档。
    /// </summary>
    /// <param name="filePath">文档文件的完整路径</param>
    /// <returns>成功返回 true，失败返回 false 并设置 LastError</returns>
    public bool OpenDocument(string filePath)
    {
        try
        {
            if (_catia == null)
            {
                LastError = "CATIA 未连接";
                return false;
            }
            _catia.Documents.Open(filePath);
            return true;
        }
        catch (Exception ex)
        {
            LastError = $"打开文件失败: {ex.Message}";
            return false;
        }
    }
}
