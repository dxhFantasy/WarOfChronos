@echo off
setlocal
cd /d "%~dp0"
set "ROOT=%~dp0"
set "PYTHON=py -3.12-32"

echo ========================================
echo  WarOfChronos Windows x86 build
echo ========================================

%PYTHON% -c "import struct, sys; assert struct.calcsize('P') * 8 == 32" >nul 2>&1
if errorlevel 1 (
    echo ERROR: 32-bit Python 3.12 not found.
    echo Install Python 3.12 x86 and make sure "py -3.12-32" works.
    goto error
)

%PYTHON% -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [1/4] Installing 32-bit build dependencies...
    %PYTHON% -m pip install fastapi uvicorn websockets pyinstaller
    if errorlevel 1 goto error
) else (
    echo [1/4] 32-bit PyInstaller is installed
)

%PYTHON% -c "import fastapi, uvicorn, websockets" >nul 2>&1
if errorlevel 1 (
    echo Installing missing runtime dependencies...
    %PYTHON% -m pip install fastapi uvicorn websockets
    if errorlevel 1 goto error
)

echo [2/4] Cleaning old output...
if exist "build\win-x86" rmdir /S /Q "build\win-x86"
if exist "dist\win-x86" rmdir /S /Q "dist\win-x86"
mkdir "build\win-x86"
mkdir "dist\win-x86"

echo [3/4] Building...
%PYTHON% -m PyInstaller --noconfirm --clean --onefile --console --name "WarOfChronos" --distpath "dist\win-x86" --workpath "build\win-x86" --specpath "build\win-x86" --add-data "%ROOT%frontend;frontend" --add-data "%ROOT%assets;assets" --add-data "%ROOT%game\Constants.json;game" --collect-all uvicorn --collect-all websockets "%ROOT%run_game.py"

if errorlevel 1 goto error

echo [4/4] Copying external Constants.json...
copy /Y "game\Constants.json" "dist\win-x86\Constants.json" >nul
if errorlevel 1 goto error

echo.
echo Build complete:
echo   dist\win-x86\WarOfChronos.exe
echo   dist\win-x86\Constants.json
echo.
start "" "dist\win-x86"
goto :eof

:error
echo.
echo Build failed. Check the messages above.
exit /b 1
