@echo off
REM ============================================================
REM  build.bat — ValveMasterTool build script
REM
REM  Steps:
REM    1. PyInstaller  → dist\ValveMasterTool\ValveMasterTool.exe
REM    2. Inno Setup   → dist\ValveMasterToolSetup.exe
REM    3. Zip (exe)    → dist\ValveMasterTool.zip       (auto-updater)
REM    4. Zip (full)   → dist\ValveMasterTool_FullInstall.zip (manual)
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
echo Cleaning previous build...
if exist dist  rmdir /s /q dist
if exist build rmdir /s /q build

REM ── Step 1: PyInstaller ─────────────────────────────────────
echo.
echo [1/4] Running PyInstaller...
pyinstaller ^
    --onedir ^
    --windowed ^
    --icon=valve_master.ico ^
    --name=ValveMasterTool ^
    --add-data="valve_master.ico;." ^
    --add-data="vmt_logo_transparent.png;." ^
    --add-data="version.py;." ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=PySide6.QtWidgets ^
    --collect-all=PySide6 ^
    valve_master_pyside6.py

if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller failed. Check errors above.
    pause
    exit /b 1
)

REM ── Step 2: Inno Setup ──────────────────────────────────────
echo.
echo [2/4] Compiling installer with Inno Setup...
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% (
    echo ERROR: Inno Setup not found at %ISCC%
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

REM ── Step 3: Zip (exe only — for auto-updater) ───────────────
echo.
echo [3/4] Creating ValveMasterTool.zip (exe only)...
if exist dist\ValveMasterTool.zip del dist\ValveMasterTool.zip
powershell -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path 'dist\ValveMasterTool\ValveMasterTool.exe' -DestinationPath 'dist\ValveMasterTool.zip' -Force"

if errorlevel 1 (
    echo ERROR: Zip (exe only) failed.
    pause
    exit /b 1
)

REM ── Step 4: Zip (full folder — for manual installs) ─────────
echo.
echo [4/4] Creating ValveMasterTool_FullInstall.zip (full folder)...
if exist dist\ValveMasterTool_FullInstall.zip del dist\ValveMasterTool_FullInstall.zip
powershell -ExecutionPolicy Bypass -Command ^
    "Compress-Archive -Path 'dist\ValveMasterTool' -DestinationPath 'dist\ValveMasterTool_FullInstall.zip' -Force"

if errorlevel 1 (
    echo ERROR: Zip (full install) failed.
    pause
    exit /b 1
)

REM ── Done ────────────────────────────────────────────────────
echo.
echo ============================================================
echo  DONE  —  v%APP_VERSION%
echo.
echo  Installer : dist\ValveMasterToolSetup.exe   (new users)
echo  Zip       : dist\ValveMasterTool.zip         (auto-updater)
echo  Full zip  : dist\ValveMasterTool_FullInstall.zip (manual)
echo ============================================================
echo.
echo Release checklist:
echo   1. Bump version.py
echo   2. git add . ^&^& git commit -m "vX.X.X - description" ^&^& git push
echo   3. GitHub ^> Releases ^> Draft new release
echo   4. Tag: vX.X.X
echo   5. Upload: ValveMasterToolSetup.exe  +  ValveMasterTool.zip
echo.
pause
