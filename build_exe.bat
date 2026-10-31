@echo off
setlocal
cd /d "%~dp0"
set "ROOT=%~dp0"

echo ========================================
echo  WarOfChronos Windows x64 build
echo ========================================

python -c "import struct; assert struct.calcsize('P') * 8 == 64" >nul 2>&1
if errorlevel 1 (
    echo ERROR: 64-bit Python is required for the x64 build.
    goto error
)

python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [1/4] Installing PyInstaller...
    python -m pip install pyinstaller
    if errorlevel 1 goto error
) else (
    echo [1/4] PyInstaller is installed
)

echo [2/4] Cleaning old output...
if exist "build\win-x64" rmdir /S /Q "build\win-x64"
if exist "dist\win-x64" rmdir /S /Q "dist\win-x64"
mkdir "build\win-x64"
mkdir "dist\win-x64"

echo [3/4] Building...
python -m PyInstaller --noconfirm --clean --onefile --console --name "WarOfChronos" --distpath "dist\win-x64" --workpath "build\win-x64" --specpath "build\win-x64" --add-data "%ROOT%frontend;frontend" --add-data "%ROOT%assets;assets" --add-data "%ROOT%game\Constants.json;game" --collect-all uvicorn --collect-all websockets "%ROOT%run_game.py"

if errorlevel 1 goto error

echo [4/4] Copying external Constants.json...
copy /Y "game\Constants.json" "dist\win-x64\Constants.json" >nul
if errorlevel 1 goto error

echo.
echo Build complete:
echo   dist\win-x64\WarOfChronos.exe
echo   dist\win-x64\Constants.json
echo.
start "" "dist\win-x64"
goto :eof

:error
echo.
echo Build failed. Check the messages above.
exit /b 1
