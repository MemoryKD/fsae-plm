' Test script for FSAE-PLM COM DLL
' Run this to test the login dialog outside of CATIA

On Error Resume Next

Dim bridge
Set bridge = CreateObject("FSAE_PLM.PlmBridge")
If Err.Number <> 0 Then
    MsgBox "Cannot create PlmBridge. COM DLL not registered." & vbCrLf & _
           "Run deploy.bat as Administrator first." & vbCrLf & vbCrLf & _
           "Error: " & Err.Description, vbCritical, "FSAE-PLM Test"
    WScript.Quit
End If

' Show login dialog
bridge.ShowLoginDialog()

If bridge.IsAuthenticated Then
    MsgBox "Login successful! Token is cached." & vbCrLf & _
           "You can now run other macros.", vbInformation, "FSAE-PLM Test"

    ' Test: show parts list
    Dim partId
    partId = bridge.ShowPartsList()
    If partId <> "" Then
        MsgBox "Selected part ID: " & partId, vbInformation, "FSAE-PLM Test"
    End If
Else
    If bridge.LastError <> "" Then
        MsgBox "Login failed: " & bridge.LastError, vbExclamation, "FSAE-PLM Test"
    Else
        MsgBox "Login cancelled.", vbInformation, "FSAE-PLM Test"
    End If
End If
