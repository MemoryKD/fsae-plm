Attribute VB_Name = "Module1"
Option Explicit

Const PLM_SERVER As String = "http://localhost:8000"
Const API_PREFIX As String = "/api"

Sub SaveToPLM()
    On Error GoTo ErrorHandler

    Dim catia As Application
    Set catia = catia

    Dim doc As Document
    Set doc = catia.ActiveDocument

    Dim partNumber As String
    Dim partName As String
    Dim revision As String

    If TypeOf doc Is ProductDocument Then
        partNumber = doc.Product.Name
        partName = doc.Product.Name
        revision = "A"
    ElseIf TypeOf doc Is PartDocument Then
        partNumber = doc.Part.Name
        partName = doc.Part.Name
        revision = "A"
    End If

    If partNumber = "" Then
        MsgBox "请先设置零件编号！", vbExclamation
        Exit Sub
    End If

    Dim msg As String
    msg = "零件编号: " & partNumber & vbCrLf & _
          "零件名称: " & partName & vbCrLf & _
          "版本: " & revision & vbCrLf & vbCrLf & _
          "确认上传到 PLM？"

    If MsgBox(msg, vbYesNo + vbQuestion, "保存到 PLM") = vbNo Then
        Exit Sub
    End If

    Dim tempPath As String
    tempPath = Environ("TEMP") & "\" & partNumber & ".CATProduct"
    doc.SaveAs tempPath

    Dim result As String
    result = UploadFile(tempPath, partNumber, partName, revision)

    If result <> "" Then
        MsgBox "上传成功！", vbInformation
    Else
        MsgBox "上传失败，请检查网络连接。", vbCritical
    End If

    Exit Sub
ErrorHandler:
    MsgBox "错误: " & Err.Description, vbCritical
End Sub

Sub CheckNaming()
    Dim doc As Document
    Set doc = catia.ActiveDocument

    Dim partNumber As String
    If TypeOf doc Is ProductDocument Then
        partNumber = doc.Product.Name
    ElseIf TypeOf doc Is PartDocument Then
        partNumber = doc.Part.Name
    End If

    Dim url As String
    url = PLM_SERVER & API_PREFIX & "/parts/check-name?number=" & partNumber

    Dim response As String
    response = HttpGet(url)

    If response = "valid" Then
        MsgBox "命名规范检查通过！", vbInformation
    Else
        MsgBox "命名不符合规范: " & response, vbExclamation
    End If
End Sub

Private Function UploadFile(filePath As String, partNumber As String, partName As String, revision As String) As String
    On Error GoTo ErrHandler

    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")

    Dim url As String
    url = PLM_SERVER & API_PREFIX & "/parts/upload"

    Dim boundary As String
    boundary = "----FormBoundary" & Format(Timer * 1000, "0")

    Dim body As String
    body = "--" & boundary & vbCrLf & _
           "Content-Disposition: form-data; name=""part_number""" & vbCrLf & vbCrLf & _
           partNumber & vbCrLf & _
           "--" & boundary & vbCrLf & _
           "Content-Disposition: form-data; name=""name""" & vbCrLf & vbCrLf & _
           partName & vbCrLf & _
           "--" & boundary & vbCrLf & _
           "Content-Disposition: form-data; name=""version""" & vbCrLf & vbCrLf & _
           revision & vbCrLf & _
           "--" & boundary & "--"

    http.Open "POST", url, False
    http.setRequestHeader "Content-Type", "multipart/form-data; boundary=" & boundary
    http.Send body

    If http.Status = 200 Then
        UploadFile = http.responseText
    Else
        UploadFile = ""
    End If

    Exit Function
ErrHandler:
    UploadFile = ""
End Function

Private Function HttpGet(url As String) As String
    On Error GoTo ErrHandler

    Dim http As Object
    Set http = CreateObject("MSXML2.XMLHTTP")

    http.Open "GET", url, False
    http.Send

    If http.Status = 200 Then
        HttpGet = http.responseText
    Else
        HttpGet = ""
    End If

    Exit Function
ErrHandler:
    HttpGet = ""
End Function

