' Process Manager - Lanzador silencioso (sin consola)
' Doble clic y solo aparece la ventana GUI

Set WshShell = CreateObject("WScript.Shell")
scriptPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
pythonScript = scriptPath & "\process_manager.pyw"

' Ejecutar pythonw.exe (sin consola) con el script
' Run con WindowStyle=0 (hidden), WaitOnReturn=False (no espera)
WshShell.Run "pythonw.exe """ & pythonScript & """", 0, False

Set WshShell = Nothing
