"""Real application labels/icons via a read-only shell helper, with explicit fallback."""
import json
import logging
import threading
import time
import uuid
from pathlib import Path

HELPER = Path(__file__).resolve().parent.parent / "assets/app-catalog.dex"


class AppCatalog:
    def __init__(self, adb):
        self.adb = adb
        self.cache = {}
        self.lock = threading.Lock()

    def read(self, serial, refresh=False):
        with self.lock:
            cached = self.cache.get(serial)
            if cached and not refresh and time.monotonic() - cached[0] < 300:
                return cached[1]
            packages = self.adb.packages(serial)
            fallback = [{"package": package, "label": package, "icon": None,
                         "label_available": False} for package in packages]
            remote = "/data/local/tmp/framelab-catalog-" + uuid.uuid4().hex + ".dex"
            try:
                if not HELPER.is_file():
                    raise RuntimeError("Thiếu bộ đọc tên/icon ứng dụng.")
                self.adb.run("push", str(HELPER), remote, serial=serial)
                raw = self.adb.run("shell", "env", "CLASSPATH=" + remote,
                                   "app_process", "/system/bin", "com.framelab.AppCatalog",
                                   serial=serial, timeout=120)
                parsed = None
                for line in reversed(raw.splitlines()):
                    try:
                        parsed = json.loads(line)
                        if isinstance(parsed, dict) and isinstance(parsed.get("apps"), list):
                            break
                    except ValueError:
                        pass
                if not isinstance(parsed, dict) or not isinstance(parsed.get("apps"), list):
                    raise RuntimeError("Thiết bị không trả về tên/icon ứng dụng hợp lệ.")
                by_package = {app["package"]: app for app in parsed["apps"] if "package" in app}
                apps = [by_package.get(row["package"], row) for row in fallback]
                result = {"apps": apps, "warning": None}
            except Exception as exc:
                logging.warning("App catalog failed for %s: %s", serial, exc)
                result = {"apps": fallback,
                          "warning": "Không lấy được tên/icon trên thiết bị này; dùng package ID. " + str(exc).splitlines()[0][:180]}
            finally:
                try:
                    self.adb.run("shell", "rm", "-f", remote, serial=serial)
                except Exception:
                    pass
            self.cache[serial] = (time.monotonic(), result)
            return result
