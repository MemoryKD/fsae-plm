using FSAE_PLM;
using FSAE_PLM.Forms;
using FSAE_PLM.Services;
using System.Windows.Forms;

Application.EnableVisualStyles();
Application.SetCompatibleTextRenderingDefault(false);

Console.WriteLine("=== FSAE-PLM CATIA Client Test ===");
Console.WriteLine();

// Step 1: CATIA connection check
var bridge = new PlmBridge();
Console.WriteLine("--- Startup Check ---");
Console.WriteLine(bridge.StartupCheck());
Console.WriteLine();

bool catiaOk = bridge.IsCatiaRunning;
if (!catiaOk)
{
    Console.ForegroundColor = ConsoleColor.Yellow;
    Console.WriteLine("WARNING: CATIA V5 is not running.");
    Console.WriteLine("PLM functions that require CATIA (checkout, checkin, sync) will not work.");
    Console.WriteLine("Please start CATIA V5 first, then restart this client.");
    Console.ResetColor();
    Console.WriteLine();
    Console.WriteLine("Press any key to continue anyway, or close to exit...");
    Console.ReadKey();
    Console.WriteLine();
}

// Step 2: PLM API authentication
var api = new PlmApiService();

if (api.TryRestoreSession())
{
    Console.ForegroundColor = ConsoleColor.Green;
    Console.WriteLine("[OK] Session restored from registry.");
    Console.ResetColor();
}
else
{
    Console.WriteLine("No saved session. Please login.");
    Console.WriteLine();

    // Show login form
    Application.Run(new LoginForm(api));
}

if (!api.IsAuthenticated)
{
    Console.ForegroundColor = ConsoleColor.Red;
    Console.WriteLine("Not logged in. Exiting.");
    Console.ResetColor();
    Console.ReadKey();
    return;
}

Console.ForegroundColor = ConsoleColor.Green;
Console.WriteLine("[OK] Logged in successfully!");
Console.ResetColor();
Console.WriteLine();

// Step 3: CATIA macro verification
if (catiaOk)
{
    Console.WriteLine("--- CATIA Status ---");
    if (bridge.CheckCatiaConnection())
    {
        Console.ForegroundColor = ConsoleColor.Green;
        Console.WriteLine($"[OK] CATIA COM connected: {bridge.GetCatiaVersion()}");
        Console.ResetColor();
    }
    else
    {
        Console.ForegroundColor = ConsoleColor.Yellow;
        Console.WriteLine("[WARN] CATIA COM not available - macros may not work");
        Console.ResetColor();
    }
}
Console.WriteLine();

// Step 4: Open parts list
Console.WriteLine("Opening parts list...");
var partsForm = new PartsListForm(api);
Application.Run(partsForm);

if (!string.IsNullOrEmpty(partsForm.SelectedPartId))
{
    Console.WriteLine($"Selected part: {partsForm.SelectedPartId}");

    var detailForm = new PartDetailForm(api, partsForm.SelectedPartId);
    Application.Run(detailForm);

    if (!string.IsNullOrEmpty(detailForm.CheckoutFilePath))
        Console.WriteLine($"Checkout file: {detailForm.CheckoutFilePath}");
    if (detailForm.WasCheckedIn)
        Console.WriteLine("Part was checked in.");
    if (detailForm.WasPublished)
        Console.WriteLine("Part was published.");
}

Console.WriteLine();
Console.WriteLine("Test complete. Press any key to exit.");
Console.ReadKey();
