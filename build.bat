@echo off
REM ============================================================
REM  build.bat — PhoenixMasterTool build script
REM
REM  Steps:
REM    1. PyInstaller  → dist\PhoenixMasterTool\PhoenixMasterTool.exe
REM    2. Inno Setup   → dist\PhoenixMasterToolSetup.exe
REM    3. Zip (exe)    → dist\PhoenixMasterTool.zip       (auto-updater)
REM    4. Zip (full)   → dist\PhoenixMasterTool_FullInstall.zip (manual)
REM
REM  Requires:
REM    - PyInstaller  (pip install pyinstaller)
REM    - Inno Setup 6 (https://jrsoftware.org/isdl.php)
REM ============================================================

REM ── Read version from version.py ────────────────────────────
for /f "delims=" %%V in ('python -c "from version import __version__; print(__version__)"') do set APP_VERSION=%%V
if "%APP_VERSION%"=="" (
    echo ERROR: Could not read version from version.py
    pause
    exit /b 1
)
echo Building version %APP_VERSION%...

REM ── Clean previous build ────────────────────────────────────
echo.
echo Cleaning previous dist...
if exist dist  rmdir /s /q dist
REM NOTE: build\ is kept for PyInstaller's incremental cache.
REM       Run with "build.bat clean" to force a full rebuild.
if /i "%1"=="clean" (
    echo Forcing clean build - removing build cache...
    if exist build rmdir /s /q build
)

REM ── Step 1: PyInstaller ─────────────────────────────────────
echo.
echo [1/4] Running PyInstaller...
pyinstaller ^
    --onedir ^
    --windowed ^
    --icon=Normal_red.ico ^
    --name=PhoenixMasterTool ^
    --add-data="version.py;." ^
    --add-data="phoenix_style.qss;." ^
    --add-data="inventory.py;." ^
    --collect-submodules=PySide6.QtCore ^
    --collect-submodules=PySide6.QtGui ^
    --collect-submodules=PySide6.QtWidgets ^
    phoenix_master_pyside6.py

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed. Check errors above.
    pause
    exit /b 1
)

REM ── Optional code-signing (runs only if VMT_SIGNING_CERT is set) ──
REM Set these in your shell before invoking build.bat, e.g.:
REM   set VMT_SIGNING_CERT=C:\path\to\cert.pfx
REM   set VMT_SIGNING_PASSWORD=...
REM   set SIGNTOOL=C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe
REM See GIT_SETUP.md for cert procurement and full instructions.
REM
REM Signing is dispatched to a labeled subroutine via `call` so the
REM `(x86)` literal inside %ProgramFiles(x86)% doesn't break cmd's nested
REM IF-block paren counter.
if not "%VMT_SIGNING_CERT%"=="" (
    call :sign_exe
    if errorlevel 1 exit /b 1
) else (
    echo [skip] Code signing disabled ^(set VMT_SIGNING_CERT to enable - see GIT_SETUP.md^).
)

REM ── Step 2: Inno Setup ──────────────────────────────────────
echo.
echo [2/4] Compiling installer with Inno Setup...
set ISCC=""
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "C:\Program Files\Inno Setup 6\ISCC.exe"       set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if %ISCC%=="" (
    echo ERROR: Inno Setup 6 not found in any known location.
    echo        Download from https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

%ISCC% /DMyAppVersion=%APP_VERSION% installer.iss

if errorlevel 1 (
    echo.
    echo ERROR: Inno Setup compilation failed. Check errors above.
    pause
    exit /b 1
)

REM Sign the installer too if a cert is configured.
if not "%VMT_SIGNING_CERT%"=="" (
    call :sign_installer
    if errorlevel 1 exit /b 1
)

REM ── Step 3: Zip (exe only — for auto-updater) ───────────────
echo.
echo [3/4] Creating PhoenixMasterTool.zip (exe only)...
if exist dist\PhoenixMasterTool.zip del dist\PhoenixMasterTool.zip
powershell -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path 'dist\PhoenixMasterTool\PhoenixMasterTool.exe' -DestinationPath 'dist\PhoenixMasterTool.zip' -Force"

if errorlevel 1 (
    echo ERROR: Zip ^(exe only^) failed.
    pause
    exit /b 1
)

REM ── Step 4: Zip (full folder — for manual installs) ─────────
echo.
echo [4/4] Creating PhoenixMasterTool_FullInstall.zip (full folder)...
if exist dist\PhoenixMasterTool_FullInstall.zip del dist\PhoenixMasterTool_FullInstall.zip
powershell -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path 'dist\PhoenixMasterTool' -DestinationPath 'dist\PhoenixMasterTool_FullInstall.zip' -Force"

if errorlevel 1 (
    echo ERROR: Zip ^(full install^) failed.
    pause
    exit /b 1
)

REM ── Done ────────────────────────────────────────────────────
echo.
echo ============================================================
echo  DONE  —  v%APP_VERSION%
echo.
echo  Installer : dist\PhoenixMasterToolSetup.exe   (new users)
echo  Zip       : dist\PhoenixMasterTool.zip         (auto-updater)
echo  Full zip  : dist\PhoenixMasterTool_FullInstall.zip (manual)
echo ============================================================
echo.
echo Release checklist:
echo   1. Bump version.py
echo   2. git add . ^&^& git commit -m "vX.X.X - description" ^&^& git push
echo   3. GitHub ^> Releases ^> Draft new release
echo   4. Tag: vX.X.X
echo   5. Upload: PhoenixMasterToolSetup.exe  +  PhoenixMasterTool.zip
echo.
pause
exit /b 0

REM ============================================================
REM  Subroutines (called from the signing checks above)
REM ============================================================

:sign_exe
if "%SIGNTOOL%"=="" (
    if exist "%ProgramFiles(x86)%\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe" set SIGNTOOL=%ProgramFiles(x86)%\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe
)
if "%SIGNTOOL%"=="" (
    echo WARNING: VMT_SIGNING_CERT is set but signtool.exe was not found.
    echo          Install the Windows 10/11 SDK, or set %%SIGNTOOL%% explicitly.
    echo          Skipping signing.
    exit /b 0
)
echo Signing dist\PhoenixMasterTool\PhoenixMasterTool.exe...
"%SIGNTOOL%" sign /f "%VMT_SIGNING_CERT%" /p "%VMT_SIGNING_PASSWORD%" /tr http://timestamp.digicert.com /td sha256 /fd sha256 "dist\PhoenixMasterTool\PhoenixMasterTool.exe"
if errorlevel 1 (
    echo ERROR: Code signing failed.
    pause
    exit /b 1
)
exit /b 0

:sign_installer
if "%SIGNTOOL%"=="" exit /b 0
echo Signing dist\PhoenixMasterToolSetup.exe...
"%SIGNTOOL%" sign /f "%VMT_SIGNING_CERT%" /p "%VMT_SIGNING_PASSWORD%" /tr http://timestamp.digicert.com /td sha256 /fd sha256 "dist\PhoenixMasterToolSetup.exe"
if errorlevel 1 (
    echo ERROR: Installer signing failed.
    pause
    exit /b 1
)
exit /b 0
