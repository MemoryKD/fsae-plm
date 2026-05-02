@echo off
chcp 65001 >nul
echo ========================================
echo   FSAE-PLM CATIA Client Installer
echo ========================================
echo.

echo [1/2] Installing Python dependencies...
pip install ttkbootstrap requests Pillow pywin32
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/2] Creating config template...
if not exist config.json (
    echo {"server_url": "http://localhost:8000", "username": "", "remember_me": true} > config.json
)

echo.
echo ========================================
echo   Installation complete!
echo   Run: python main.py
echo ========================================
pause
