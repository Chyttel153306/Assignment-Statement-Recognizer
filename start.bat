@echo off
cd /d "%~dp0"
where python >nul 2>nul
if not errorlevel 1 (
    python --version >nul 2>nul
    if not errorlevel 1 (
        python app.py
        pause
        exit /b
    )
)
where py >nul 2>nul
if not errorlevel 1 (
    py --version >nul 2>nul
    if not errorlevel 1 (
        py app.py
        pause
        exit /b
    )
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
    "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" app.py
    pause
    exit /b
)
echo Python 3.9 or newer is required. Install Python, then run this file again.
pause
