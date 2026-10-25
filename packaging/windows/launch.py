"""Portable Windows entrypoint; app logic stays in framelab."""
import ctypes
import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.environ["ADB_PATH"] = str(ROOT / "tools/adb.exe")


def main():
    try:
        from framelab.app import main as start
        start()
    except Exception:
        folder = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Frame Lab"
        folder.mkdir(exist_ok=True, parents=True)
        error_file = folder / "startup-error.log"
        error_file.write_text(traceback.format_exc(), encoding="utf-8")
        message = "Khong the mo Frame Lab. Xem chi tiet tai:\n" + str(error_file)
        if sys.stderr:
            print(message, file=sys.stderr)
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(None, message, "Frame Lab", 0x10)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
