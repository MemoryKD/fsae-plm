# Manual COM registration for FSAE_PLM .NET 8 comhost.dll (x64)
$clsid = "{A4D6D90B-E56E-4E96-A035-407E4EC7A0BD}"
$dllPath = "D:\AI\test2\fsae-plm\catia_addin\bin\Release\net8.0-windows\FSAE_PLM.comhost.dll"
$progId = "FSAE_PLM.PlmBridge"

Write-Host "=== COM Registration (x64) ==="

# CLSID entry
$clsidPath = "HKLM:\SOFTWARE\Classes\CLSID\$clsid"
New-Item -Path $clsidPath -Force | Out-Null
Set-ItemProperty -Path $clsidPath -Name "(Default)" -Value $progId

$inprocPath = "$clsidPath\InProcServer32"
New-Item -Path $inprocPath -Force | Out-Null
Set-ItemProperty -Path $inprocPath -Name "(Default)" -Value $dllPath
Set-ItemProperty -Path $inprocPath -Name "ThreadingModel" -Value "Both"

# ProgID
$progIdPath = "HKLM:\SOFTWARE\Classes\$progId"
New-Item -Path $progIdPath -Force | Out-Null
Set-ItemProperty -Path $progIdPath -Name "(Default)" -Value $progId

$progClsidPath = "$progIdPath\CLSID"
New-Item -Path $progClsidPath -Force | Out-Null
Set-ItemProperty -Path $progClsidPath -Name "(Default)" -Value $clsid

Write-Host "Registered OK" -ForegroundColor Green

# Test
$vbs = @'
Dim obj
Set obj = CreateObject("FSAE_PLM.PlmBridge")
If Err.Number <> 0 Then
    WScript.Echo "FAIL: " & Err.Description
    WScript.Quit 1
End If
WScript.Echo "COM OK"
WScript.Echo obj.StartupCheck()
'@
$vbsFile = "$env:TEMP\fsae_test.vbs"
$vbs | Out-File $vbsFile -Encoding ASCII
$result = & cscript //nologo $vbsFile 2>&1
Write-Host $result
Remove-Item $vbsFile -ErrorAction SilentlyContinue
