@echo off
REM ============================================================
REM  build.bat — ValveMasterTool PyInstaller build script
REM  Run from the project root directory.
REM  Output: dist\ValveMasterTool\ValveMasterTool.exe
REM  Upload: ValveMasterTool.zip (exe only) to GitHub Release
REM ============================================================

echo Cleaning previous build...
if exist dist  rmdir /s /q dist
if exist build rmdir /s /q build
if exist ValveMasterTool.spec del ValveMasterTool.spec

echo Building with PyInstaller...
pyinstaller ^
    --onedir ^
    --windowed ^
    --icon=valve_master.ico ^
    --name=ValveMasterTool ^
    --add-data="valve_master.ico;." ^
    --add-data="vmt_logo_transparent.png;." ^
    --hidden-import=PySide6.QtCore ^
    --hidden-import=PySide6.QtGui ^
    --hidden-import=PySide6.QtWidgets ^
    --collect-all=PySide6 ^
    valve_master_pyside6.py

if errorlevel 1 (
    echo.
    echo BUILD FAILED. Check errors above.
    pause
    exit /b 1
)

echo.
echo Build succeeded. Zipping exe only for GitHub release...

REM Zip ONLY the exe (~5 MB), not the whole dist folder (~255 MB)
powershell -ExecutionPolicy Bypass -Command ^
"Add-Type -AssemblyName System.IO.Compression.FileSystem; ^
[System.IO.Compression.ZipFile]::CreateFromDirectory('placeholder', 'placeholder') 2>$null; ^
$zip = [System.IO.Compression.ZipFile]::Open('ValveMasterTool.zip', 'Create'); ^
[System.IO.Compression.ZipFileExtensions]::CreateEntryFromFile($zip, 'dist\ValveMasterTool\ValveMasterTool.exe', 'ValveMasterTool.exe'); ^
$zip.Dispose()" 2>NUL

REM Simpler approach — use Compress-Archive just on the exe
if exist ValveMasterTool.zip del ValveMasterTool.zip
powershell -ExecutionPolicy Bypass -Command ^
"Compress-Archive -Path 'dist\ValveMasterTool\ValveMasterTool.exe' -DestinationPath 'ValveMasterTool.zip' -Force"

if errorlevel 1 (
    echo.
    echo ZIP FAILED. Exe is still at dist\ValveMasterTool\ValveMasterTool.exe
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  DONE!
echo  Exe  : dist\ValveMasterTool\ValveMasterTool.exe
echo  Zip  : ValveMasterTool.zip  (upload this to GitHub Release)
echo ============================================================
echo.
echo Next steps:
echo   1. Bump version.py
echo   2. git add . ^&^& git commit -m "vX.X.X - description" ^&^& git push
echo   3. GitHub ^> Releases ^> Draft new release
echo   4. Tag: vX.X.X  ^|  Upload: ValveMasterTool.zip
echo.
pause
