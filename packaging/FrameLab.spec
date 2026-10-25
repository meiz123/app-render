# Build on macOS Apple Silicon; no machine-specific paths are stored here.
from pathlib import Path
import os

root = Path(SPECPATH).parent
adb_dir = Path(os.environ.get("FRAMELAB_ADB_DIR", str(root / "vendor/platform-tools")))
if not (adb_dir / "adb").is_file() or not (adb_dir / "NOTICE.txt").is_file():
    raise SystemExit("Set FRAMELAB_ADB_DIR to Android SDK platform-tools containing adb and NOTICE.txt")

a = Analysis(
    [str(root / "packaging/entrypoint.py")], pathex=[str(root)],
    binaries=[(str(adb_dir / "adb"), "tools")],
    datas=[(str(root / "framelab/static"), "framelab/static"),
           (str(root / "framelab/assets"), "framelab/assets"),
           (str(adb_dir / "NOTICE.txt"), "tools")],
    hiddenimports=[], hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=["tkinter", "unittest"], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Frame Lab",
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, argv_emulation=False, target_arch="arm64",
          codesign_identity=None, entitlements_file=None)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Frame Lab")
app = BUNDLE(coll, name="Frame Lab.app", icon=None,
             bundle_identifier="local.framelab.desktop",
             info_plist={"CFBundleShortVersionString":"0.2.0", "CFBundleVersion":"2",
                         "LSUIElement":True, "NSHighResolutionCapable":True})
