Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Lấy đường dẫn thư mục TweetBot (parent của scripts\)
strScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
strBotDir = fso.GetParentFolderName(strScriptDir)

' Kiểm tra xem bot đã chạy chưa (chống chạy nhiều instance)
Set objWMI = GetObject("winmgmts:\\.\root\cimv2")
Set colProcesses = objWMI.ExecQuery("SELECT * FROM Win32_Process WHERE CommandLine LIKE '%tweet_forward_bot.py%' AND Name LIKE '%python%'")
If colProcesses.Count > 0 Then
    WScript.Quit
End If

' Chuyển working directory về thư mục TweetBot
WshShell.CurrentDirectory = strBotDir

' Chạy bot ẩn bằng pythonw từ venv (không hiện cửa sổ console)
WshShell.Run "pythonw """ & strBotDir & "\tweet_forward_bot.py""", 0, False

Set objWMI = Nothing
Set WshShell = Nothing
Set fso = Nothing
