@echo off
setlocal

echo ========================================
echo FYP Training Shell (CUDA 11.5)
echo ========================================

set "ROOT=%~dp0"
set "VENV=%ROOT%cv_hands\.venv-train310"
set "CUDA115=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.5"
set "LOCAL_CUDNN=%ROOT%cv_hands\third_party\cudnn-8.9.7-cuda11"

if not exist "%VENV%\Scripts\python.exe" (
    echo ERROR: Training venv not found: %VENV%
    echo Please create it first.
    pause
    exit /b 1
)

if not exist "%CUDA115%\bin\cudart64_110.dll" (
    echo ERROR: CUDA 11.5 runtime not found at:
    echo %CUDA115%\bin\cudart64_110.dll
    echo Finish CUDA 11.5 installation first.
    pause
    exit /b 1
)

if exist "%CUDA115%\bin\cudnn64_8.dll" (
    set "CUDNN_BIN=%CUDA115%\bin"
) else (
    if exist "%LOCAL_CUDNN%\bin\cudnn64_8.dll" (
        set "CUDNN_BIN=%LOCAL_CUDNN%\bin"
    ) else (
        echo ERROR: cudnn64_8.dll not found.
        echo Place cuDNN in either:
        echo - %CUDA115%\bin
        echo - %LOCAL_CUDNN%\bin
        pause
        exit /b 1
    )
)

set "PATH=%CUDNN_BIN%;%CUDA115%\bin;%CUDA115%\libnvvp;%PATH%"
set "CUDA_PATH=%CUDA115%"

call "%VENV%\Scripts\activate.bat"

echo.
echo Python:
python --version
echo.
echo CUDA_PATH=%CUDA_PATH%
echo.
echo Running TensorFlow GPU verification...
python "%ROOT%cv_hands\tools\verify_tf_gpu.py"

echo.
echo If GPU is detected, you can start notebook in this shell:
echo jupyter notebook
echo.
echo Press any key to close...
pause >nul
