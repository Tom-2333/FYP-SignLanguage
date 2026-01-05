# 手勢識別程序啟動腳本 (PowerShell)
# 使用系統 Python 3.10 環境運行

Write-Host "Starting Hand Gesture Recognition..." -ForegroundColor Green
Write-Host ""

C:\Users\PC\AppData\Local\Programs\Python\Python310\python.exe app.py

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
