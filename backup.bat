@echo off
setlocal

set "ROOT=%~dp0"
set "VENV=%ROOT%.venv-app310"
set "PY_EXE=%VENV%\Scripts\python.exe"
set "PY_BOOTSTRAP="
set "REQ_FILE=%ROOT%cv_hands\requirements.txt"

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

py -3.10 -V >nul 2>&1
if not errorlevel 1 (
    set "PY_BOOTSTRAP=py -3.10"
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python 3.10 not found.
        echo Install Python 3.10 and enable PATH or py launcher.
        pause
        exit /b 1
    )
    set "PY_BOOTSTRAP=python"
)

where node >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found in PATH.
    pause
    exit /b 1
)

if not exist "%PY_EXE%" (
    echo Creating virtual environment: %VENV%
    call %PY_BOOTSTRAP% -m venv "%VENV%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

if not exist "%VENV%\.deps_installed" (
    echo Installing Python dependencies from cv_hands\requirements.txt...
    call "%PY_EXE%" -m pip install --upgrade pip
    if errorlevel 1 (
        echo ERROR: Failed to upgrade pip.
        pause
        exit /b 1
    )

    call "%PY_EXE%" -m pip install -r "%REQ_FILE%"
    if errorlevel 1 (
        echo ERROR: Failed to install Python dependencies.
        pause
        exit /b 1
    )

    type nul > "%VENV%\.deps_installed"
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
start "FYP Python Backend" cmd /k "cd /d ""%ROOT%cv_hands"" && ""%PY_EXE%"" app_simple.py"

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