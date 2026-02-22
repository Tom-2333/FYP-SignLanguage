@echo off
setlocal

echo ========================================
echo Run app.py with System Python 3.10
echo ========================================

set "PY310=C:\Users\lam10\AppData\Local\Programs\Python\Python310\python.exe"

if not exist "%PY310%" (
  echo ERROR: Python 3.10 not found at:
  echo %PY310%
  pause
  exit /b 1
)

cd /d "%~dp0cv_hands"
"%PY310%" app.py
