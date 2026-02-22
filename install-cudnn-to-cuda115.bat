@echo off
setlocal

set "CUDA115=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.5"

echo ========================================
echo Install cuDNN into CUDA 11.5
echo ========================================

if "%~1"=="" (
    echo Usage:
    echo   install-cudnn-to-cuda115.bat "C:\path\to\cudnn-windows-x86_64-8.x.x.x_cuda11-archive"
    echo.
    echo Example:
    echo   install-cudnn-to-cuda115.bat "%%USERPROFILE%%\Downloads\cudnn-windows-x86_64-8.1.1.33_cuda11-archive"
    exit /b 1
)

set "CUDNN_SRC=%~1"

if not exist "%CUDA115%\bin" (
    echo ERROR: CUDA 11.5 not found at %CUDA115%
    exit /b 1
)

if not exist "%CUDNN_SRC%\bin\cudnn64_8.dll" (
    echo ERROR: cuDNN dll not found in "%CUDNN_SRC%\bin"
    exit /b 1
)

if not exist "%CUDNN_SRC%\include\cudnn.h" (
    echo ERROR: cuDNN headers not found in "%CUDNN_SRC%\include"
    exit /b 1
)

echo Copying cuDNN files to CUDA 11.5...
xcopy /Y /I "%CUDNN_SRC%\bin\*" "%CUDA115%\bin\" >nul
xcopy /Y /I "%CUDNN_SRC%\include\*" "%CUDA115%\include\" >nul
xcopy /Y /I "%CUDNN_SRC%\lib\x64\*" "%CUDA115%\lib\x64\" >nul

if not exist "%CUDA115%\bin\cudnn64_8.dll" (
    echo ERROR: Copy finished but cudnn64_8.dll not found in CUDA bin.
    exit /b 1
)

echo SUCCESS: cuDNN installed into CUDA 11.5
echo You can now run: start-train-cuda115.bat
exit /b 0
