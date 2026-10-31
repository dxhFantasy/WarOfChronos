#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
ROOT="$(pwd)"
PYTHON="${PYTHON:-python3}"
ARCH="$(uname -m)"
OUT="dist/uos-${ARCH}"
VENV="build/uos-venv"

echo "========================================"
echo " WarOfChronos UOS/Linux build (${ARCH})"
echo "========================================"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "ERROR: $PYTHON not found."
    exit 1
fi

if ! "$PYTHON" -c 'import sys; assert sys.version_info >= (3, 10)' >/dev/null 2>&1; then
    echo "ERROR: Python 3.10 or newer is required."
    echo "Current: $("$PYTHON" --version 2>&1)"
    exit 1
fi

if [ ! -d "$VENV" ]; then
    echo "[1/4] Creating build venv..."
    "$PYTHON" -m venv "$VENV"
else
    echo "[1/4] Using existing build venv..."
fi

# shellcheck disable=SC1091
. "$VENV/bin/activate"

echo "[2/4] Installing build dependencies..."
python -m pip install --upgrade pip
python -m pip install fastapi uvicorn websockets pyinstaller

echo "[3/4] Building..."
rm -rf "$ROOT/build/uos" "$ROOT/$OUT"
mkdir -p "$ROOT/build/uos" "$ROOT/$OUT"
python -m PyInstaller \
    --noconfirm \
    --clean \
    --onefile \
    --console \
    --name "WarOfChronos" \
    --distpath "$ROOT/$OUT" \
    --workpath "$ROOT/build/uos" \
    --specpath "$ROOT/build/uos" \
    --add-data "$ROOT/frontend:frontend" \
    --add-data "$ROOT/assets:assets" \
    --add-data "$ROOT/game/Constants.json:game" \
    --collect-all uvicorn \
    --collect-all websockets \
    "$ROOT/run_game.py"

echo "[4/4] Copying external Constants.json..."
cp "$ROOT/game/Constants.json" "$ROOT/$OUT/Constants.json"
chmod +x "$ROOT/$OUT/WarOfChronos"

echo
echo "Build complete:"
echo "  $ROOT/$OUT/WarOfChronos"
echo "  $ROOT/$OUT/Constants.json"
echo
echo "Run on UOS:"
echo "  cd $ROOT/$OUT && ./WarOfChronos"
echo
echo "NOTE: Run this script on the UOS machine (or a compatible Linux"
echo "with an older/equal glibc) for best compatibility. PyInstaller"
echo "does not cross-compile from Windows to Linux."
