@echo off
REM ============================================
REM   FSAE-PLM CATIA Add-in Deployment
REM   C# COM DLL + VBS Macro approach
REM ============================================
REM
REM  Usage: Run as Administrator
REM
REM  This script:
REM    1. Builds the C# COM DLL
REM    2. Registers it for COM interop
REM    3. Copies VBS macros to CATIA startup folder

echo.
echo ============================================
echo   FSAE-PLM CATIA Add-in Deployment
echo ============================================
echo.

cd /d "%~dp0"

REM Step 1: Build
echo [1/3] Building FSAE_PLM.dll...
dotnet build -c Release -p:PlatformTarget=x86 2>nul
if errorlevel 1 (
    echo ERROR: Build failed. Make sure .NET 8 SDK is installed.
    echo Download: https://dotnet.microsoft.com/download/dotnet/8.0
    pause
    exit /b 1
)
echo     Build OK: bin\Release\net8.0-windows\FSAE_PLM.dll
echo.

REM Step 2: Register COM server
echo [2/3] Registering COM server...
REM For .NET 8, use regsvr32 on the comhost.dll
if exist "bin\Release\net8.0-windows\FSAE_PLM.comhost.dll" (
    regsvr32 /s "bin\Release\net8.0-windows\FSAE_PLM.comhost.dll"
    if errorlevel 1 (
        echo ERROR: COM registration failed. Run as Administrator.
        pause
        exit /b 1
    )
    echo     COM server registered (comhost.dll)
) else (
    echo WARNING: comhost.dll not found, trying regasm...
    set REGASM="%WINDIR%\Microsoft.NET\Framework\v4.0.30319\regasm.exe"
    if exist %REGASM% (
        %REGASM% /codebase "bin\Release\net8.0-windows\FSAE_PLM.dll"
    ) else (
        echo ERROR: regasm not found. Install .NET Framework 4.8.
        pause
        exit /b 1
    )
)
echo.

REM Step 3: Copy macros to CATIA startup
echo [3/3] Installing VBS macros...
set STARTUP_DIR=%APPDATA%\Dassault Systemes\CATSettings\Macros
if not exist "%STARTUP_DIR%" (
    set STARTUP_DIR=%APPDATA%\Dassault Systemes\CATIA\Macros
)
if not exist "%STARTUP_DIR%" (
    mkdir "%STARTUP_DIR%"
)
copy /Y macros\*.catvbs "%STARTUP_DIR%\" >nul
if errorlevel 1 (
    echo WARNING: Failed to copy macros. Copy manually from macros\ folder.
) else (
    echo     Macros installed to: %STARTUP_DIR%
echo.
echo     00_Startup        - Auto-load on CATIA startup
echo     01_Login          - Login to PLM
)

echo.
echo ============================================
echo   Deployment complete!
echo.
echo   Next steps:
echo   1. Restart CATIA V5
echo   2. Tools > Macro > Macros
echo   3. Select each macro > drag to toolbar
echo.
echo   Macros installed:
echo     01_Login          - Login to PLM
echo     02_SearchParts    - Search parts
echo     03_Checkout       - Checkout part
echo     04_Checkin        - Checkin document
echo     05_Publish        - Publish part
echo     06_SyncProps      - Sync PLM properties
echo     07_CreatePart     - Create new part
echo ============================================
pause
