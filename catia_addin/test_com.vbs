Dim bridge
Set bridge = CreateObject("FSAE_PLM.PlmBridge")
If Err.Number <> 0 Then
    WScript.Echo "FAIL: " & Err.Description
    WScript.Quit 1
End If

WScript.Echo bridge.StartupCheck()
WScript.Echo ""
WScript.Echo "COM OK"
