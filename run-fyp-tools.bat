@echo off
setlocal

set "ROOT=%~dp0"
set "REQ_FILE=%ROOT%cv_hands\requirements.txt"
set "PY_MARKER=%ROOT%.python_deps_installed"

echo ========================================
echo FYP Sign Language - One Click Runner
echo ========================================
echo This launcher starts:
echo 1) Python backend: cv_hands\app_simple.py
echo 2) React frontend:  my-app
echo It will auto-install required Python/Node packages.
echo ========================================

cd /d "%ROOT%"

if not exist "%REQ_FILE%" (
    echo ERROR: Python requirements file not found.
    echo %REQ_FILE%
    pause
    exit /b 1
)

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH.
    echo Install Python and enable PATH first.
    pause
    exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found in PATH.
    pause
    exit /b 1
)

if not exist "%PY_MARKER%" (
    echo Installing Python dependencies from cv_hands\requirements.txt...
    call python -m pip install --upgrade pip
    if errorlevel 1 (
        echo ERROR: Failed to upgrade pip.
        pause
        exit /b 1
    )

    call python -m pip install -r "%REQ_FILE%"
    if errorlevel 1 (
        echo ERROR: Failed to install Python dependencies.
        pause
        exit /b 1
    )

    type nul > "%PY_MARKER%"
)

if not exist "%ROOT%node_modules" (
    echo Installing root Node.js dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install root Node.js dependencies.
        pause
        exit /b 1
    )
)

if not exist "%ROOT%my-app\node_modules" (
    echo Installing React dependencies for first run...
    call npm --prefix "%ROOT%my-app" install
    if errorlevel 1 (
        echo ERROR: Failed to install React dependencies.
        pause
        exit /b 1
    )
)

echo.
echo Starting Python backend window...
start "FYP Python Backend" cmd /k "cd /d ""%ROOT%cv_hands"" && python app_simple.py"

echo Waiting 4 seconds before starting React...
timeout /t 4 /nobreak >nul

echo Starting React frontend window...
start "FYP React Frontend" cmd /k "cd /d ""%ROOT%my-app"" && npm start"

echo.
echo Started successfully.
echo Backend:  http://localhost:5001
echo Frontend: http://localhost:3000
echo.
echo You can close this launcher now.
endlocal
exit /b 0
