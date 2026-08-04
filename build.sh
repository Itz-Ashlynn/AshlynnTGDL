#!/usr/bin/env bash
set -e

echo ""
echo " ========================================="
echo "  AshlynnTGDL - Build Binary"
echo " ========================================="
echo ""

echo " [1/3] Installing dependencies..."
pip3 install -r requirements.txt

echo " [2/3] Installing PyInstaller..."
pip3 install pyinstaller

echo " [3/3] Building AshlynnTGDL binary..."
pyinstaller \
  --noconfirm \
  --onefile \
  --console \
  --name AshlynnTGDL \
  --collect-all kurigram \
  --collect-all pyrogram \
  --collect-all PyroTgCrypto \
  --collect-all alive_progress \
  ashlynntgdl.py

if [ -f dist/AshlynnTGDL ]; then
    mv dist/AshlynnTGDL AshlynnTGDL
    chmod +x AshlynnTGDL
    rm -rf build/ dist/ AshlynnTGDL.spec
    echo ""
    echo " ========================================="
    echo "  SUCCESS: ./AshlynnTGDL is ready!"
    echo " ========================================="
else
    echo ""
    echo " ERROR: Build failed. Check the output above."
    exit 1
fi
