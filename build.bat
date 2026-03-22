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
if exist *.spec del *.spec

echo Building with PyInstaller...
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
    echo BUILD FAILED. Check errors above.
    pause
    exit /b 1
)

echo.
echo Build succeeded. Zipping exe only for GitHub release...

if exist dist\ValveMasterTool.zip del dist\ValveMasterTool.zip
powershell -ExecutionPolicy Bypass -Command ^
"Compress-Archive -Path 'dist\ValveMasterTool\ValveMasterTool.exe' -DestinationPath 'dist\ValveMasterTool.zip' -Force"

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
echo  Zip  : dist\ValveMasterTool.zip  (upload this to GitHub Release)
echo ============================================================
echo.
echo Next steps:
echo   1. Bump version.py
echo   2. git add . ^&^& git commit -m "vX.X.X - description" ^&^& git push
echo   3. GitHub ^> Releases ^> Draft new release
echo   4. Tag: vX.X.X  ^|  Upload: ValveMasterTool.zip
echo.
pause
