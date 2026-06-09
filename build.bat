@echo off
setlocal EnableDelayedExpansion

cd /d "%~dp0"

echo === DevCommandCenter Local Build ===

:: Find Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: python not found in PATH.
    exit /b 1
)

for /f "tokens=*" %%a in ('python --version') do set PYVER=%%a
echo Found %PYVER%

:: Install / upgrade pyinstaller
pip install -q --upgrade pyinstaller
if %errorlevel% neq 0 (
    echo ERROR: failed to install PyInstaller.
    exit /b 1
)

echo PyInstaller ready.

:: Clean previous build
echo Cleaning old builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

:: Build
echo Building executable...
pyinstaller ^
    --name "DevCommandCenter" ^
    --windowed ^
    --onefile ^
    --icon "NONE" ^
    --add-data "devcommandcenter\assets;devcommandcenter\assets" ^
    --hidden-import PySide6.QtSvg ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtGui ^
    --hidden-import PySide6.QtWidgets ^
    --hidden-import sqlalchemy.ext.baked ^
    --hidden-import sqlalchemy.sql.default_comparator ^
    devcommandcenter/cli.py

if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed.
    exit /b 1
)

echo.
echo === Build complete ===
echo Output: dist\DevCommandCenter.exe
echo.

endlocal
