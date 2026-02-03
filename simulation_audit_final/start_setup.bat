@echo off
echo 🐿️ FlashSquirrel (閃電松鼠) - Windows Launcher
echo.
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python from https://www.python.org/
    pause
    exit /b
)
echo 🚀 Starting Setup Wizard...
python setup_wizard.py
pause
