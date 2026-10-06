#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=== DevCommandCenter Local Build ==="

# Find Python
if ! command -v python3 >/dev/null 2>&1; then
    echo "ERROR: python3 not found in PATH."
    exit 1
fi

echo "Found $(python3 --version)"

# Install / upgrade pyinstaller
python3 -m pip install -q --upgrade pyinstaller || {
    echo "ERROR: failed to install PyInstaller."
    exit 1
}

echo "PyInstaller ready."

# Clean previous build
echo "Cleaning old builds..."
rm -rf build dist

# Build
# --add-data keeps the package layout (devcommandcenter/assets) so
# config.resource_path() finds bundled files under sys._MEIPASS
echo "Building executable..."
python3 -m PyInstaller \
    --name "DevCommandCenter" \
    --windowed \
    --onefile \
    --icon "NONE" \
    --add-data "devcommandcenter/assets:devcommandcenter/assets" \
    --hidden-import PySide6.QtSvg \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtGui \
    --hidden-import PySide6.QtWidgets \
    --hidden-import sqlalchemy.ext.baked \
    --hidden-import sqlalchemy.sql.default_comparator \
    main.py

echo ""
echo "=== Build complete ==="
echo "Output: dist/DevCommandCenter"
echo ""
