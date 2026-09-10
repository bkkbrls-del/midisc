#!/usr/bin/env bash
# Download official Octatrack OS 1.40C (your own copy). Do not commit it.
set -euo pipefail
cd "$(dirname "$0")/.."

OS_VER="1.40C"
ZIP_URL="https://www.elektron.se/wp-content/uploads/2025/03/OCTATRACK_OS${OS_VER}_dist.zip"
DL=downloads
ZIP="$DL/OCTATRACK_OS${OS_VER}_dist.zip"

mkdir -p "$DL"

echo "[fetch] downloading OS $OS_VER ..."
curl -fL --retry 3 --max-time 120 -o "$ZIP" "$ZIP_URL"

echo "[fetch] ZIP sha256:"
shasum -a 256 "$ZIP" || sha256sum "$ZIP"

echo "[fetch] extracting ..."
unzip -o "$ZIP" -d "$DL/extracted"

echo "[fetch] firmware files:"
find "$DL/extracted" -type f \( -iname '*.bin' -o -iname '*.syx' \) -exec ls -la {} \;

echo
echo "[fetch] done. Next:  python tools/build_midisc40.py"
