#!/bin/zsh
set -eu
cd -- "${0:A:h:h}"
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  print -u2 'This build recipe targets macOS Apple Silicon.'
  exit 1
fi
python3 -m venv .venv-build
.venv-build/bin/python -m pip install -r packaging/requirements-build.txt
export FRAMELAB_ADB_DIR="${FRAMELAB_ADB_DIR:-$HOME/Library/Android/sdk/platform-tools}"
export PYINSTALLER_CONFIG_DIR="$PWD/build/pyinstaller-cache"
.venv-build/bin/python -m PyInstaller --noconfirm --clean --distpath release --workpath build packaging/FrameLab.spec
cp docs/QUICK_START_VI.md release/HUONG_DAN.md
mkdir -p 'build/share/Frame Lab'
ditto 'release/Frame Lab.app' 'build/share/Frame Lab/Frame Lab.app'
cp docs/QUICK_START_VI.md 'build/share/Frame Lab/HUONG_DAN.md'
ditto -c -k --sequesterRsrc --keepParent 'build/share/Frame Lab' release/Frame-Lab-0.2.0-macOS-Apple-Silicon.zip
shasum -a 256 release/Frame-Lab-0.2.0-macOS-Apple-Silicon.zip > release/SHA256SUMS.txt
