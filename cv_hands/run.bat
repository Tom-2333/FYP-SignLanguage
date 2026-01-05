@echo off
REM 手勢識別程序啟動腳本
REM 使用系統 Python 3.10 環境運行

echo ========================================
echo   Hand Gesture Recognition Program
echo ========================================
echo.
echo Starting application...
echo Press ESC in the window to exit
echo.

C:\Users\PC\AppData\Local\Programs\Python\Python310\python.exe app.py

if errorlevel 1 (
    echo.
    echo Program exited with an error!
    pause
)

