@echo off
echo ========================================
echo FYP Sign Language Project - CLEAN SETUP (Windows)
echo ========================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10+ and add to PATH
    pause
    exit /b 1
)

REM Check Node.js installation
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found! Please install Node.js 18.x LTS
    pause
    exit /b 1
)

echo.
echo ========================================
echo STEP 1: UNINSTALLING ALL DEPENDENCIES
echo ========================================

echo.
echo [1.1] Uninstalling Python packages...
pip uninstall -y opencv-python mediapipe numpy pillow tensorflow
pip uninstall -y opencv-python-headless opencv-contrib-python opencv-contrib-python-headless

echo.
echo [1.2] Cleaning root node_modules...
if exist node_modules (
    echo Removing root node_modules...
    rmdir /s /q node_modules
)
if exist package-lock.json (
    echo Removing root package-lock.json...
    del /f /q package-lock.json
)

echo.
echo [1.3] Cleaning my-app node_modules...
cd my-app
if exist node_modules (
    echo Removing my-app node_modules...
    rmdir /s /q node_modules
)
if exist package-lock.json (
    echo Removing my-app package-lock.json...
    del /f /q package-lock.json
)
cd ..

echo.
echo [1.4] Cleaning Python cache...
cd cv_hands
if exist __pycache__ rmdir /s /q __pycache__
if exist model\__pycache__ rmdir /s /q model\__pycache__
if exist model\keypoint_classifier\__pycache__ rmdir /s /q model\keypoint_classifier\__pycache__
if exist utils\__pycache__ rmdir /s /q utils\__pycache__
cd ..

echo.
echo ========================================
echo STEP 2: REINSTALLING ALL DEPENDENCIES
echo ========================================

echo.
echo [2.1] Installing root-level MediaPipe dependencies...
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install root dependencies!
    pause
    exit /b 1
)

echo.
echo [2.2] Installing Python dependencies for cv_hands...
cd cv_hands
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies!
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo [2.3] Installing React app dependencies...
cd my-app
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install React dependencies!
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo ========================================
echo STEP 3: STARTING PROJECT
echo ========================================

echo.
echo [3.1] Starting Python Flask server (cv_hands)...
start "Python Flask Server" cmd /k "cd /d %CD%\cv_hands && python app_simple.py"

echo.
echo [3.2] Waiting 5 seconds before starting React...
timeout /t 5 /nobreak

echo.
echo [3.3] Starting React development server...
start "React Dev Server" cmd /k "cd /d %CD%\my-app && npm start"

echo.
echo ========================================
echo CLEAN SETUP COMPLETE!
echo ========================================
echo Python Flask server: http://localhost:5000
echo React app: http://localhost:3000
echo ========================================
echo Press any key to close this window...
pause