@echo off
REM FSAE-PLM CAA V5 Add-in Deployment Script
REM ==========================================
REM
REM Prerequisites:
REM   1. CAA RADE installed and configured (cnext.exe)
REM   2. Visual Studio (matching CAA version)
REM   3. CATIA V5 installed
REM
REM Usage: Run as Administrator from this directory

echo ============================================
echo   FSAE-PLM CAA V5 Add-in Deployment
echo ============================================
echo.

REM Step 1: Set up CAA environment
echo [1/4] Setting up CAA environment...
if exist "%CATNextPath%\cnext.exe" (
    call "%CATNextPath%\cnext.exe" -run "mkCreateRuntimeView -workspace %CD%"
) else (
    echo WARNING: CATNextPath not set. Please configure CAA environment first.
    echo Run cnext.exe and set your CATIA V5 installation path.
    echo.
)

REM Step 2: Build
echo [2/4] Building CAA project...
if exist "%VS140COMNTOOLS%\..\IDE\devenv.com" (
    "%VS140COMNTOOLS%\..\IDE\devenv.com" FSAE_PLM_CAA.sln /Build "Release|Win32"
) else if exist "%VS150COMNTOOLS%\..\IDE\devenv.com" (
    "%VS150COMNTOOLS%\..\IDE\devenv.com" FSAE_PLM_CAA.sln /Build "Release|Win32"
) else (
    echo WARNING: Visual Studio not found. Build manually from VS IDE.
    echo.
)

REM Step 3: Copy to CATIA startup
echo [3/4] Installing to CATIA startup directory...
set STARTUP_DIR=%APPDATA%\Dassault Systemes\CATSettings\startup
if not exist "%STARTUP_DIR%" mkdir "%STARTUP_DIR%"

REM Copy compiled DLL
if exist "Win32\Release\*.dll" (
    copy /Y "Win32\Release\*.dll" "%STARTUP_DIR%\"
    echo DLL installed to: %STARTUP_DIR%
) else (
    echo WARNING: No compiled DLL found. Build first.
)

REM Step 4: Register
echo [4/4] Registration complete.
echo.
echo ============================================
echo   Next steps:
echo   1. Restart CATIA V5
echo   2. Go to Tools > Options > General > Macros
echo   3. Enable "Load CAA libraries at startup"
echo   4. The FSAE-PLM toolbar should appear automatically
echo ============================================
pause
