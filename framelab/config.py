"""Filesystem locations shared by source and standalone builds."""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"


def data_dir():
    override = os.environ.get("FRAMELAB_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support/Frame Lab"
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Frame Lab"
    return Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / "frame-lab"


def bundled_adb():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "tools" / ("adb.exe" if sys.platform == "win32" else "adb")
    return PROJECT_ROOT / "vendor/platform-tools" / ("adb.exe" if sys.platform == "win32" else "adb")
