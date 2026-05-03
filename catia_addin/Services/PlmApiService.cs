using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Runtime.InteropServices;
using System.Text.Json;
using Microsoft.Win32;
using FSAE_PLM.Models;

namespace FSAE_PLM.Services;

/// <summary>
/// Synchronous PLM API service for VBS/CATIA consumption.
/// Wraps HttpClient calls with .GetAwaiter().GetResult() so VBS can invoke directly.
/// Stores the JWT token in the Windows registry for session persistence.
/// </summary>
[ComVisible(true)]
[ClassInterface(ClassInterfaceType.AutoDual)]
[Guid("B7E3A2F1-5C4D-4E8A-9F6B-1D2E3F4A5B6C")]
public class PlmApiService
{
    private const string RegistryKeyPath = @"SOFTWARE\FSAE_PLM";
    private const string RegistryTokenValueName = "JwtToken";
    private const string RegistryUrlValueName = "ServerUrl";

    private HttpClient? _http;
    private string? _token;

    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
    };

    public PlmApiService() { }

    /// <summary>Whether the service has a valid JWT token.</summary>
    public bool IsAuthenticated => !string.IsNullOrEmpty(_token);

    /// <summary>Last error message, set when any method fails. Empty string on success.</summary>
    public string LastError { get; private set; } = "";

    // ─── Public Sync Methods ───────────────────────────────────────────

    /// <summary>
    /// Log in to the PLM server. Creates the HttpClient, authenticates, and
    /// persists the JWT token to the registry.
    /// </summary>
    public bool Login(string serverUrl, string username, string password)
    {
        try
        {
            LastError = "";

            // Dispose previous HttpClient if switching servers
            _http?.Dispose();
            var baseAddress = serverUrl.TrimEnd('/') + "/";
            _http = new HttpClient { BaseAddress = new Uri(baseAddress) };

            var json = JsonSerializer.Serialize(new { username, password });
            var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");
            var response = _http.PostAsync("auth/login", content).GetAwaiter().GetResult();
            var body = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();

            if (!response.IsSuccessStatusCode)
            {
                LastError = $"Login failed: {response.StatusCode}";
                return false;
            }

            var result = JsonSerializer.Deserialize<JsonElement>(body);
            _token = result.GetProperty("access_token").GetString()!;
            _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", _token);

            SaveTokenToRegistry(serverUrl, _token);
            return true;
        }
        catch (Exception ex)
        {
            LastError = $"Login error: {ex.Message}";
            return false;
        }
    }

    /// <summary>
    /// Log out: clear the token from memory and the registry.
    /// </summary>
    public void Logout()
    {
        try
        {
            _token = null;
            if (_http != null)
                _http.DefaultRequestHeaders.Authorization = null;
            ClearTokenFromRegistry();
        }
        catch (Exception ex)
        {
            LastError = $"Logout error: {ex.Message}";
        }
    }

    /// <summary>
    /// Try to restore a session from the saved registry token.
    /// Returns true if the token was loaded (does not verify expiry).
    /// </summary>
    public bool TryRestoreSession()
    {
        try
        {
            LastError = "";
            var (serverUrl, token) = LoadTokenFromRegistry();
            if (string.IsNullOrEmpty(serverUrl) || string.IsNullOrEmpty(token))
            {
                LastError = "No saved session found";
                return false;
            }

            _http?.Dispose();
            var baseAddress = serverUrl.TrimEnd('/') + "/";
            _http = new HttpClient { BaseAddress = new Uri(baseAddress) };

            _token = token;
            _http.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", _token);
            return true;
        }
        catch (Exception ex)
        {
            LastError = $"Restore session error: {ex.Message}";
            return false;
        }
    }

    /// <summary>Get a list of parts, optionally filtered by search keyword.</summary>
    public PartInfo[] GetParts(string search)
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();

            var url = "parts/";
            if (!string.IsNullOrEmpty(search))
                url += $"?search={Uri.EscapeDataString(search)}";

            var list = _http!.GetFromJsonAsync<List<PartInfo>>(url, JsonOptions).GetAwaiter().GetResult();
            return list?.ToArray() ?? Array.Empty<PartInfo>();
        }
        catch (Exception ex)
        {
            LastError = $"GetParts error: {ex.Message}";
            return Array.Empty<PartInfo>();
        }
    }

    /// <summary>Get a single part by ID.</summary>
    public PartInfo? GetPart(Guid partId)
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();
            return _http!.GetFromJsonAsync<PartInfo>($"parts/{partId}", JsonOptions).GetAwaiter().GetResult();
        }
        catch (Exception ex)
        {
            LastError = $"GetPart error: {ex.Message}";
            return null;
        }
    }

    /// <summary>Check out a part (lock for editing).</summary>
    public PartInfo? Checkout(Guid partId)
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();

            var response = _http!.PostAsync($"parts/{partId}/checkout", null).GetAwaiter().GetResult();
            if (!response.IsSuccessStatusCode)
            {
                LastError = $"Checkout failed: {response.StatusCode}";
                return null;
            }
            return response.Content.ReadFromJsonAsync<PartInfo>(JsonOptions).GetAwaiter().GetResult();
        }
        catch (Exception ex)
        {
            LastError = $"Checkout error: {ex.Message}";
            return null;
        }
    }

    /// <summary>
    /// Check in a part: upload a CATIA file and create a new version.
    /// Uses multipart/form-data encoding.
    /// </summary>
    public PartInfo? Checkin(Guid partId, string filePath, string comment)
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();

            using var content = new MultipartFormDataContent();
            var fileBytes = File.ReadAllBytes(filePath);
            content.Add(new ByteArrayContent(fileBytes), "file", Path.GetFileName(filePath));
            content.Add(new StringContent(comment ?? ""), "comment");

            var response = _http!.PostAsync($"parts/{partId}/checkin", content).GetAwaiter().GetResult();
            if (response.IsSuccessStatusCode)
            {
                return response.Content.ReadFromJsonAsync<PartInfo>(JsonOptions).GetAwaiter().GetResult();
            }

            var body = response.Content.ReadAsStringAsync().GetAwaiter().GetResult();
            try
            {
                var result = JsonSerializer.Deserialize<JsonElement>(body);
                LastError = result.GetProperty("detail").GetString() ?? "Checkin failed";
            }
            catch
            {
                LastError = $"Checkin failed: {response.StatusCode}";
            }
            return null;
        }
        catch (Exception ex)
        {
            LastError = $"Checkin error: {ex.Message}";
            return null;
        }
    }

    /// <summary>Publish a part (change lifecycle state to published).</summary>
    public PartInfo? Publish(Guid partId)
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();

            var response = _http!.PostAsync($"parts/{partId}/publish", null).GetAwaiter().GetResult();
            if (!response.IsSuccessStatusCode)
            {
                LastError = $"Publish failed: {response.StatusCode}";
                return null;
            }
            return response.Content.ReadFromJsonAsync<PartInfo>(JsonOptions).GetAwaiter().GetResult();
        }
        catch (Exception ex)
        {
            LastError = $"Publish error: {ex.Message}";
            return null;
        }
    }

    /// <summary>Create a new part using a number template.</summary>
    public PartInfo? CreateWithTemplate(string name, string type, string subsystem, Guid templateId)
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();

            var json = JsonSerializer.Serialize(new
            {
                name,
                type,
                subsystem,
                template_id = templateId.ToString()
            });
            var content = new StringContent(json, System.Text.Encoding.UTF8, "application/json");

            var response = _http!.PostAsync("parts/create-with-template", content).GetAwaiter().GetResult();
            if (!response.IsSuccessStatusCode)
            {
                LastError = $"CreateWithTemplate failed: {response.StatusCode}";
                return null;
            }
            return response.Content.ReadFromJsonAsync<PartInfo>(JsonOptions).GetAwaiter().GetResult();
        }
        catch (Exception ex)
        {
            LastError = $"CreateWithTemplate error: {ex.Message}";
            return null;
        }
    }

    /// <summary>Get all versions for a part.</summary>
    public VersionInfo[] GetVersions(Guid partId)
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();

            var list = _http!.GetFromJsonAsync<List<VersionInfo>>(
                $"parts/{partId}/versions", JsonOptions).GetAwaiter().GetResult();
            return list?.ToArray() ?? Array.Empty<VersionInfo>();
        }
        catch (Exception ex)
        {
            LastError = $"GetVersions error: {ex.Message}";
            return Array.Empty<VersionInfo>();
        }
    }

    /// <summary>Download a specific version file to a local path.</summary>
    public bool DownloadVersion(Guid partId, Guid versionId, string savePath)
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();

            var response = _http!.GetAsync(
                $"parts/{partId}/versions/{versionId}/download").GetAwaiter().GetResult();
            if (!response.IsSuccessStatusCode)
            {
                LastError = $"Download failed: {response.StatusCode}";
                return false;
            }

            var bytes = response.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult();
            File.WriteAllBytes(savePath, bytes);
            return true;
        }
        catch (Exception ex)
        {
            LastError = $"DownloadVersion error: {ex.Message}";
            return false;
        }
    }

    /// <summary>Get all number templates.</summary>
    public TemplateInfo[] GetTemplates()
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();

            var list = _http!.GetFromJsonAsync<List<TemplateInfo>>(
                "templates", JsonOptions).GetAwaiter().GetResult();
            return list?.ToArray() ?? Array.Empty<TemplateInfo>();
        }
        catch (Exception ex)
        {
            LastError = $"GetTemplates error: {ex.Message}";
            return Array.Empty<TemplateInfo>();
        }
    }

    /// <summary>Preview the next available part number for a given template.</summary>
    public string GetNextPartNumber(Guid templateId, string subsystemCode, string partType)
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();

            var url = $"parts/next-number?template_id={templateId}" +
                      $"&subsystem_code={Uri.EscapeDataString(subsystemCode)}" +
                      $"&part_type={partType}";

            var result = _http!.GetFromJsonAsync<JsonElement>(url).GetAwaiter().GetResult();
            return result.GetProperty("part_number").GetString() ?? "";
        }
        catch (Exception ex)
        {
            LastError = $"GetNextPartNumber error: {ex.Message}";
            return "";
        }
    }

    /// <summary>Get the BOM (bill of materials) for an assembly part.</summary>
    public BomItemInfo[] GetBom(Guid partId)
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();

            var list = _http!.GetFromJsonAsync<List<BomItemInfo>>(
                $"parts/{partId}/bom", JsonOptions).GetAwaiter().GetResult();
            return list?.ToArray() ?? Array.Empty<BomItemInfo>();
        }
        catch (Exception ex)
        {
            LastError = $"GetBom error: {ex.Message}";
            return Array.Empty<BomItemInfo>();
        }
    }

    /// <summary>Create a branch from an existing part.</summary>
    public PartInfo? CreateBranch(Guid partId, string branchName)
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();

            var form = new Dictionary<string, string> { ["branch_name"] = branchName };
            var response = _http!.PostAsync(
                $"parts/{partId}/branch", new FormUrlEncodedContent(form)).GetAwaiter().GetResult();

            if (!response.IsSuccessStatusCode)
            {
                LastError = $"CreateBranch failed: {response.StatusCode}";
                return null;
            }
            return response.Content.ReadFromJsonAsync<PartInfo>(JsonOptions).GetAwaiter().GetResult();
        }
        catch (Exception ex)
        {
            LastError = $"CreateBranch error: {ex.Message}";
            return null;
        }
    }

    /// <summary>Get all branches for a part.</summary>
    public PartInfo[] GetBranches(Guid partId)
    {
        try
        {
            LastError = "";
            EnsureAuthenticated();

            var list = _http!.GetFromJsonAsync<List<PartInfo>>(
                $"parts/{partId}/branches", JsonOptions).GetAwaiter().GetResult();
            return list?.ToArray() ?? Array.Empty<PartInfo>();
        }
        catch (Exception ex)
        {
            LastError = $"GetBranches error: {ex.Message}";
            return Array.Empty<PartInfo>();
        }
    }

    // ─── Private Helpers ───────────────────────────────────────────────

    private void EnsureAuthenticated()
    {
        if (_http == null || string.IsNullOrEmpty(_token))
            throw new InvalidOperationException("Not logged in. Call Login() first.");
    }

    private void SaveTokenToRegistry(string serverUrl, string token)
    {
        try
        {
            using var key = Registry.CurrentUser.CreateSubKey(RegistryKeyPath);
            key.SetValue(RegistryUrlValueName, serverUrl);
            key.SetValue(RegistryTokenValueName, token);
        }
        catch
        {
            // Non-critical: registry save failure should not block login
        }
    }

    private (string? ServerUrl, string? Token) LoadTokenFromRegistry()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RegistryKeyPath);
            if (key == null) return (null, null);
            return (
                key.GetValue(RegistryUrlValueName) as string,
                key.GetValue(RegistryTokenValueName) as string
            );
        }
        catch
        {
            return (null, null);
        }
    }

    private void ClearTokenFromRegistry()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RegistryKeyPath, writable: true);
            if (key == null) return;
            key.DeleteValue(RegistryTokenValueName, throwOnMissingValue: false);
        }
        catch
        {
            // Non-critical
        }
    }
}
