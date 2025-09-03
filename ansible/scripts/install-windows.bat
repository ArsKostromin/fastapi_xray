@echo off
echo 🚀 FastAPI Xray VPN Service - Windows Setup
echo =============================================

REM Check if Python is installed
py --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [INFO] Python is installed ✓

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not installed. Please install pip first.
    pause
    exit /b 1
)

echo [INFO] pip is available ✓

REM Create virtual environment
echo [INFO] Creating Python virtual environment...
py -m venv venv

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip...
py -m pip install --upgrade pip

REM Install Python requirements
echo [INFO] Installing Python requirements...
pip install -r requirements.txt

REM Skip Ansible part on Windows
echo [INFO] Skipping Ansible installation (please install manually in WSL or via pipx)
echo [HINT] Run this in WSL/Ubuntu:
echo         sudo apt update && sudo apt install ansible -y
echo         ansible-galaxy install -r requirements.yml

REM Create backup directory
echo [INFO] Creating backup directory...
if not exist backups mkdir backups

echo [INFO] Setup completed successfully! 🎉
echo.
echo Next steps:
echo 1. Run: scripts\manage-servers.bat -a check   (only works if Ansible installed in WSL)
echo 2. Run: scripts\manage-servers.bat -a deploy  (same)
echo.
echo To activate the virtual environment in the future:
echo call venv\Scripts\activate.bat
echo.
pause
