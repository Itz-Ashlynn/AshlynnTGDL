@echo off
echo.
echo  =========================================
echo   AshlynnTGDL - Build EXE
echo  =========================================
echo.

:: Install runtime dependencies
echo  [1/3] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo  ERROR: Failed to install dependencies.
    pause & exit /b 1
)

:: Install PyInstaller
echo  [2/3] Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo  ERROR: Failed to install PyInstaller.
    pause & exit /b 1
)

:: Build the executable
echo  [3/3] Building AshlynnTGDL.exe...
python -m PyInstaller ^
  --noconfirm ^
  --onefile ^
  --console ^
  --name AshlynnTGDL ^
  --hidden-import pyrogram ^
  --hidden-import pyrogram.raw ^
  --hidden-import pyrogram.raw.all ^
  --hidden-import pyrogram.raw.types ^
  --hidden-import pyrogram.raw.functions ^
  --hidden-import pyrogram.crypto ^
  --hidden-import TgCrypto ^
  --collect-all pyrogram ^
  ashlynntgdl.py

:: Move output and clean up
if exist dist\AshlynnTGDL.exe (
    move /Y dist\AshlynnTGDL.exe AshlynnTGDL.exe
    rmdir /s /q build dist 2>nul
    del /q AshlynnTGDL.spec 2>nul
    echo.
    echo  =========================================
    echo   SUCCESS: AshlynnTGDL.exe is ready!
    echo  =========================================
) else (
    echo.
    echo  ERROR: Build failed. Check the output above.
)

echo.
pause
