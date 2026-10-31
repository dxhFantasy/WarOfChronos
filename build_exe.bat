@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo  WarOfChronos PyInstaller build
echo ========================================

python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [1/4] Installing PyInstaller...
    python -m pip install pyinstaller
    if errorlevel 1 goto error
) else (
    echo [1/4] PyInstaller is installed
)

echo [2/4] Cleaning old output...
if exist build rmdir /S /Q build
if exist "dist\WarOfChronos.exe" del /Q "dist\WarOfChronos.exe"

echo [3/4] Building...
python -m PyInstaller --noconfirm --clean --onefile --console --name "WarOfChronos" --add-data "frontend;frontend" --add-data "assets;assets" --add-data "game\Constants.json;game" --collect-all uvicorn --collect-all websockets run_game.py

if errorlevel 1 goto error

echo [4/4] Copying external Constants.json...
copy /Y "game\Constants.json" "dist\Constants.json" >nul
if errorlevel 1 goto error

echo.
echo Build complete:
echo   dist\WarOfChronos.exe
echo   dist\Constants.json
echo.
echo Edit dist\Constants.json to change DEBUG.
echo Local URL: http://127.0.0.1:8000/
echo LAN URL:   http://YOUR-IP:8000/
echo.
start "" "dist"
goto :eof

:error
echo.
echo Build failed. Check the messages above.
exit /b 1
