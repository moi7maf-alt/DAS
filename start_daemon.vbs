' بدء خادم نظام التخطيط التنموي بصمت (بدون ظهور نافذة)
Dim shell
Set shell = CreateObject("WScript.Shell")
shell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
shell.Run "python ai_server.py", 0, False
Set shell = Nothing
