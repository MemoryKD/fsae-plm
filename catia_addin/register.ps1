# FSAE-PLM COM Registration Script
$dll = "D:\AI\test2\fsae-plm\catia_addin\bin\Release\net8.0-windows\FSAE_PLM.comhost.dll"
$clsid = "{A4D6D90B-E56E-4E96-A035-407E4EC7A0BD}"

Write-Host "=== FSAE-PLM COM Registration ==="
Write-Host ""

# Step 1: Register with regsvr32
Write-Host "[1] Registering comhost.dll..."
$result = Start-Process "regsvr32" -ArgumentList "/s", $dll -Wait -PassThru -Verb RunAs
if ($result.ExitCode -eq 0) {
    Write-Host "    OK: regsvr32 succeeded" -ForegroundColor Green
} else {
    Write-Host "    FAIL: regsvr32 exit code $($result.ExitCode)" -ForegroundColor Red
}

# Step 2: Check CLSID registration
Write-Host "[2] Checking CLSID..."
$clsidPath = "Registry::HKEY_CLASSES_ROOT\CLSID\$clsid"
if (Test-Path $clsidPath) {
    Write-Host "    OK: CLSID registered" -ForegroundColor Green
} else {
    Write-Host "    FAIL: CLSID not found" -ForegroundColor Red
}

# Step 3: Register ProgID manually if missing
$progIdPath = "Registry::HKEY_CLASSES_ROOT\FSAE_PLM.PlmBridge"
if (!(Test-Path $progIdPath)) {
    Write-Host "[3] Registering ProgID..."
    New-Item -Path $progIdPath -Force | Out-Null
    Set-ItemProperty -Path $progIdPath -Name "(Default)" -Value "FSAE_PLM.PlmBridge"
    New-Item -Path "$progIdPath\CLSID" -Force | Out-Null
    Set-ItemProperty -Path "$progIdPath\CLSID" -Name "(Default)" -Value $clsid
    Write-Host "    OK: ProgID registered" -ForegroundColor Green
} else {
    Write-Host "[3] ProgID already registered" -ForegroundColor Green
}

# Step 4: Verify
Write-Host "[4] Verifying..."
$verify = Test-Path $progIdPath
Write-Host "    ProgID exists: $verify"

# Test with VBScript
Write-Host ""
Write-Host "[5] Testing COM via VBScript..."
$vbs = @"
Set obj = CreateObject("FSAE_PLM.PlmBridge")
If Err.Number <> 0 Then
    WScript.Echo "FAIL: " & Err.Description
    WScript.Quit 1
End If
WScript.Echo "COM OK: " & obj.StartupCheck()
"@
$tempVbs = "$env:TEMP\test_com_reg.vbs"
$vbs | Out-File -FilePath $tempVbs -Encoding ASCII
$comResult = & cscript //nologo $tempVbs 2>&1
Write-Host $comResult
Remove-Item $tempVbs -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "=== Done ==="
