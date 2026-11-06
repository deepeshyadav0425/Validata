@echo off
title Validata - Authenticity Engine Server
color 0A

echo =======================================================
echo        Validata - Authenticity Engine Server
echo =======================================================
echo.

set PYTHON_CMD=python
where python >nul 2>nul
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
        set PYTHON_CMD="%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    ) else (
        echo [ERROR] Python 3.12 was not found. Please ensure Python is installed.
        pause
        exit /b 1
    )
)

echo [*] Using Python: %PYTHON_CMD%
echo [*] Checking dependencies...
%PYTHON_CMD% -c "import flask, sklearn, bs4, requests, numpy" >nul 2>nul
if %errorlevel% neq 0 (
    echo [*] Installing missing Python libraries...
    %PYTHON_CMD% -m pip install -r requirements.txt
)

echo [*] Starting web application at http://127.0.0.1:5000...
start "" "http://127.0.0.1:5000"

%PYTHON_CMD% -m backend.app
pause
