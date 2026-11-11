@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE=.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    echo [INFO] Creating virtual environment...
    where uv >nul 2>nul
    if not errorlevel 1 (
        uv venv --python 3.12 .venv
        if errorlevel 1 goto :setup_failed
        uv pip install --python "%PYTHON_EXE%" -r requirements.txt
    ) else (
        py -3.12 -m venv .venv
        if errorlevel 1 goto :setup_failed
        "%PYTHON_EXE%" -m pip install -r requirements.txt
    )
    if errorlevel 1 goto :setup_failed
)

"%PYTHON_EXE%" main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Application exited with code %errorlevel%.
    pause
)
exit /b %errorlevel%

:setup_failed
echo.
echo [ERROR] Environment setup failed. Please install Python 3.12 and try again.
pause
exit /b 1
