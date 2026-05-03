using System.Runtime.InteropServices;
using System.Diagnostics;
using FSAE_PLM.Forms;
using FSAE_PLM.Models;
using FSAE_PLM.Services;

namespace FSAE_PLM;

/// <summary>
/// COM-visible bridge between CATIA VBS macros and the PLM backend.
/// VBS macros create this object via CreateObject("FSAE_PLM.PlmBridge").
///
/// All dialog methods spawn a dedicated STA thread so the CATIA main thread
/// is never blocked by WinForms message loops.
/// </summary>
[ComVisible(true)]
[ClassInterface(ClassInterfaceType.AutoDual)]
[Guid("A4D6D90B-E56E-4E96-A035-407E4EC7A0BD")]
public class PlmBridge
{
    private readonly PlmApiService _api = new();

    // -----------------------------------------------------------------------
    //  Properties
    // -----------------------------------------------------------------------

    /// <summary>Last error message from the most recent operation.</summary>
    public string LastError { get; private set; } = string.Empty;

    /// <summary>Local path of the file downloaded during the last CheckoutAndDownload call.</summary>
    public string LastCheckoutPath { get; private set; } = string.Empty;

    /// <summary>
    /// Direct access to the underlying API service for advanced scenarios
    /// not covered by the bridge methods.
    /// </summary>
    public PlmApiService Api => _api;

    // -----------------------------------------------------------------------
    //  CATIA Connection
    // -----------------------------------------------------------------------

    /// <summary>Whether CATIA V5 process is detected as running.</summary>
    public bool IsCatiaRunning => Process.GetProcessesByName("CNEXT").Length > 0
                                   || Process.GetProcessesByName("CATIA").Length > 0
                                   || Process.GetProcessesByName("cnext").Length > 0;

    /// <summary>
    /// Checks CATIA connection via COM automation.
    /// Returns true if CATIA COM object can be obtained.
    /// </summary>
    public bool CheckCatiaConnection()
    {
        try
        {
            var type = Type.GetTypeFromProgID("CATIA.Application");
            if (type == null) return false;
            dynamic catia = Activator.CreateInstance(type);
            if (catia == null) return false;
            // Try to access a basic property to verify COM works
            string name = catia.Name;
            return !string.IsNullOrEmpty(name);
        }
        catch
        {
            return false;
        }
    }

    /// <summary>Returns CATIA version string, or empty if not connected.</summary>
    public string GetCatiaVersion()
    {
        try
        {
            var type = Type.GetTypeFromProgID("CATIA.Application");
            if (type == null) return "";
            dynamic catia = Activator.CreateInstance(type);
            return catia?.Name?.ToString() ?? "";
        }
        catch { return ""; }
    }

    /// <summary>
    /// Full startup check: verifies CATIA is running, COM connection works,
    /// and macros directory exists. Returns a status summary string.
    /// </summary>
    public string StartupCheck()
    {
        var results = new List<string>();

        // Check CATIA process
        if (IsCatiaRunning)
            results.Add("[OK] CATIA V5 is running");
        else
            results.Add("[FAIL] CATIA V5 is not running");

        // Check COM connection
        if (CheckCatiaConnection())
        {
            var version = GetCatiaVersion();
            results.Add($"[OK] COM connection active: {version}");
        }
        else
        {
            results.Add("[WARN] COM connection not available (macros may not work)");
        }

        // Check macros installed
        var macroDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                                     "Dassault Systemes", "CATSettings", "Macros");
        if (!Directory.Exists(macroDir))
            macroDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                                     "Dassault Systemes", "CATIA", "Macros");

        if (Directory.Exists(macroDir))
        {
            var macroFiles = Directory.GetFiles(macroDir, "*.catvbs");
            if (macroFiles.Length > 0)
                results.Add($"[OK] {macroFiles.Length} PLM macros installed");
            else
                results.Add("[WARN] No PLM macros found in CATIA macros directory");
        }
        else
        {
            results.Add("[WARN] CATIA macros directory not found");
        }

        // Check API connectivity
        if (_api.IsAuthenticated)
            results.Add("[OK] PLM API authenticated");
        else
            results.Add("[INFO] PLM API not logged in yet");

        return string.Join("\n", results);
    }

    // -----------------------------------------------------------------------
    //  Authentication
    // -----------------------------------------------------------------------

    /// <summary>
    /// Authenticates against the PLM server. On success the session token is
    /// cached internally and <see cref="IsAuthenticated"/> becomes true.
    /// </summary>
    /// <param name="serverUrl">Base URL of the PLM API (e.g. http://localhost/api).</param>
    /// <param name="username">Login username.</param>
    /// <param name="password">Login password.</param>
    /// <returns>True when authentication succeeds.</returns>
    public bool Login(string serverUrl, string username, string password)
    {
        try
        {
            LastError = string.Empty;
            var success = _api.Login(serverUrl, username, password);
            if (!success)
            {
                LastError = _api.LastError;
            }
            return success;
        }
        catch (Exception ex)
        {
            LastError = $"Login error: {ex.Message}";
            return false;
        }
    }

    /// <summary>Clears the cached session token.</summary>
    public void Logout()
    {
        try
        {
            _api.Logout();
            LastError = string.Empty;
        }
        catch (Exception ex)
        {
            LastError = $"Logout error: {ex.Message}";
        }
    }

    /// <summary>True when a valid session token is cached.</summary>
    public bool IsAuthenticated => _api.IsAuthenticated;

    // -----------------------------------------------------------------------
    //  Dialog methods
    // -----------------------------------------------------------------------

    /// <summary>
    /// Opens the Login dialog. Blocks until the user closes it.
    /// After closing, check IsAuthenticated to see if login succeeded.
    /// </summary>
    public void ShowLoginDialog()
    {
        try
        {
            LastError = string.Empty;
            ShowDialog<LoginForm>(
                () => new LoginForm(_api),
                _ => { });
        }
        catch (Exception ex)
        {
            LastError = $"ShowLoginDialog error: {ex.Message}";
        }
    }

    /// <summary>
    /// Opens the Parts List dialog.  The user can browse / search parts and
    /// double-click one to select it.
    /// </summary>
    /// <returns>The selected part's ID as a string, or empty if the dialog was cancelled.</returns>
    public string ShowPartsList()
    {
        try
        {
            LastError = string.Empty;
            string? selectedId = null;

            ShowDialog<PartsListForm>(
                () => new PartsListForm(_api),
                form =>
                {
                    if (!string.IsNullOrEmpty(form.SelectedPartId))
                    {
                        selectedId = form.SelectedPartId;
                    }
                });

            return selectedId ?? string.Empty;
        }
        catch (Exception ex)
        {
            LastError = $"ShowPartsList error: {ex.Message}";
            return string.Empty;
        }
    }

    /// <summary>
    /// Opens the Part Detail dialog for the given part.  The user can
    /// check-out, check-in, or publish the part from within the dialog.
    /// </summary>
    /// <param name="partId">The ID of the part to display (GUID string).</param>
    /// <returns>
    /// A string describing the action the user performed:
    ///   "checkout:&lt;filepath&gt;"  — user checked out the part and downloaded a file
    ///   "checkin:ok"               — user checked in a new version
    ///   "publish:ok"               — user published the part
    ///   ""                         — dialog was closed without action
    /// </returns>
    public string ShowPartDetail(string partId)
    {
        try
        {
            LastError = string.Empty;
            if (!Guid.TryParse(partId, out _))
            {
                LastError = "Invalid part ID format.";
                return string.Empty;
            }

            string result = "";

            ShowDialog<PartDetailForm>(
                () => new PartDetailForm(_api, partId),
                form =>
                {
                    if (form.WasCheckedIn)
                        result = "checkin:ok";
                    else if (form.WasPublished)
                        result = "publish:ok";
                    else if (!string.IsNullOrEmpty(form.CheckoutFilePath))
                        result = $"checkout:{form.CheckoutFilePath}";
                });

            return result;
        }
        catch (Exception ex)
        {
            LastError = $"ShowPartDetail error: {ex.Message}";
            return string.Empty;
        }
    }

    /// <summary>
    /// Opens the Create Part dialog.  The user fills in part metadata and
    /// picks a numbering template; on confirm the part is created on the server.
    /// </summary>
    /// <returns>The newly-created part's ID as a string, or empty if cancelled.</returns>
    public string ShowCreatePart()
    {
        try
        {
            LastError = string.Empty;
            string? newPartId = null;

            ShowDialog<CreatePartForm>(
                () => new CreatePartForm(_api),
                form =>
                {
                    if (!string.IsNullOrEmpty(form.CreatedPartId))
                    {
                        newPartId = form.CreatedPartId;
                    }
                });

            return newPartId ?? string.Empty;
        }
        catch (Exception ex)
        {
            LastError = $"ShowCreatePart error: {ex.Message}";
            return string.Empty;
        }
    }

    // -----------------------------------------------------------------------
    //  Headless operations (no UI)
    // -----------------------------------------------------------------------

    /// <summary>
    /// Checks out a part and downloads its latest file to a local temp directory.
    /// The downloaded file path is stored in <see cref="LastCheckoutPath"/>.
    /// </summary>
    /// <param name="partId">The part to check out.</param>
    /// <returns>True on success.</returns>
    public bool CheckoutAndDownload(Guid partId)
    {
        try
        {
            LastError = string.Empty;
            LastCheckoutPath = string.Empty;

            var part = _api.Checkout(partId);
            if (part == null)
            {
                LastError = "Checkout failed. The part may already be checked out by another user.";
                return false;
            }

            // Determine latest version to download
            var versions = _api.GetVersions(partId);
            if (versions.Length == 0)
            {
                LastError = "No versions available for download.";
                return false;
            }

            var latest = versions[0]; // versions are ordered newest-first
            var downloadDir = Path.Combine(Path.GetTempPath(), "FSAE_PLM");
            Directory.CreateDirectory(downloadDir);

            var fileName = $"{part.PartNumber}_{latest.VersionNumber}{(latest.FileType != null ? "." + latest.FileType : "")}";
            var savePath = Path.Combine(downloadDir, fileName);

            var ok = _api.DownloadVersion(partId, latest.Id, savePath);
            if (!ok)
            {
                LastError = "File download failed.";
                return false;
            }

            LastCheckoutPath = savePath;
            return true;
        }
        catch (Exception ex)
        {
            LastError = $"CheckoutAndDownload error: {ex.Message}";
            return false;
        }
    }

    /// <summary>
    /// Uploads a local file as a new version of the specified part and
    /// releases the checkout lock.
    /// </summary>
    /// <param name="partId">The part to check in.</param>
    /// <param name="filePath">Absolute path to the local file to upload.</param>
    /// <returns>True on success.</returns>
    public bool CheckinFile(Guid partId, string filePath)
    {
        try
        {
            LastError = string.Empty;

            if (string.IsNullOrWhiteSpace(filePath) || !File.Exists(filePath))
            {
                LastError = $"File not found: {filePath}";
                return false;
            }

            var part = _api.Checkin(partId, filePath, "");
            if (part == null)
            {
                LastError = string.IsNullOrEmpty(_api.LastError) ? "Check-in failed." : _api.LastError;
                return false;
            }

            return true;
        }
        catch (Exception ex)
        {
            LastError = $"CheckinFile error: {ex.Message}";
            return false;
        }
    }

    /// <summary>
    /// Publishes a part, advancing its lifecycle state to "Published".
    /// The part must be in "checked-in" state before publishing.
    /// </summary>
    /// <param name="partId">The part to publish.</param>
    /// <returns>True on success.</returns>
    public bool PublishPart(Guid partId)
    {
        try
        {
            LastError = string.Empty;

            var result = _api.Publish(partId);
            if (result == null)
            {
                LastError = "Publish failed. Ensure the part is in checked-in state.";
                return false;
            }

            return true;
        }
        catch (Exception ex)
        {
            LastError = $"PublishPart error: {ex.Message}";
            return false;
        }
    }

    // -----------------------------------------------------------------------
    //  Private helpers
    // -----------------------------------------------------------------------

    /// <summary>
    /// Opens a WinForms dialog on a dedicated STA thread so that CATIA's
    /// main thread is never blocked.  After the form closes the optional
    /// <paramref name="resultExtractor"/> callback reads the form's output
    /// properties while the form object is still alive.
    /// </summary>
    private void ShowDialog<T>(Func<T> formFactory, Action<T>? resultExtractor = null) where T : Form
    {
        Exception? error = null;
        T? formInstance = null;

        var thread = new Thread(() =>
        {
            try
            {
                formInstance = formFactory();
                formInstance.StartPosition = FormStartPosition.CenterScreen;
                Application.Run(formInstance);
            }
            catch (Exception ex)
            {
                error = ex;
            }
            finally
            {
                // Extract results while the form is still in memory,
                // before the STA thread exits.
                if (formInstance != null && error == null)
                {
                    try { resultExtractor?.Invoke(formInstance); }
                    catch { /* swallow extraction errors */ }
                }
            }
        });

        thread.SetApartmentState(ApartmentState.STA);
        thread.Start();
        thread.Join();

        if (error != null)
        {
            throw error;
        }
    }
}
