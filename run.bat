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