Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
strPath = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = strPath

' Localiza o interpretador pythonw para execução 100% oculta sem janela de console
pythonPath = "C:\Users\Gabriel\AppData\Local\Programs\Python\Python313\pythonw.exe"
If Not fso.FileExists(pythonPath) Then
    pythonPath = "pythonw.exe"
End If

' Executa com estilo de janela 0 (oculto) e sem bloqueio
WshShell.Run """" & pythonPath & """ -m bot_99freelas dashboard", 0, False
