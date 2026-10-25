"""Session orchestration; no HTTP or browser dependency."""
import base64
import json
import secrets
import tempfile
import threading
from pathlib import Path
from ..android.adb import Adb
from ..android.catalog import AppCatalog
from ..collectors.render import Capture
from ..config import data_dir
from ..repositories.reports import ReportRepository


class Service:
    def __init__(self, reports=None, adb=None):
        self.repository = ReportRepository(reports or data_dir() / "reports")
        self.reports = self.repository.root
        self.adb = adb
        self.lock = threading.RLock()
        self.capture = None
        self.state = {"phase": "idle"}
        self.token = secrets.token_urlsafe(32)
        self.installing = False
        self.catalog = None

    def bridge(self):
        if self.adb is None:
            self.adb = Adb()
        return self.adb

    def applications(self, serial, refresh=False):
        if serial not in [d["serial"] for d in self.bridge().devices() if d["state"] == "device"]:
            raise ValueError("Thiết bị chưa được cấp quyền USB.")
        if self.catalog is None:
            self.catalog = AppCatalog(self.bridge())
        return self.catalog.read(serial, refresh)

    def start(self, data):
        with self.lock:
            if self.state["phase"] in ("recording", "finalizing") or self.installing:
                raise ValueError("Một tác vụ đang chạy. Hãy đợi hoàn tất.")
            serial = data["serial"]
            if serial not in [d["serial"] for d in self.bridge().devices() if d["state"] == "device"]:
                raise ValueError("Thiết bị chưa kết nối hoặc chưa cấp quyền USB.")
            package = self.bridge().package(data["package"])
            if package not in self.bridge().packages(serial):
                raise ValueError("App không còn trong danh sách ứng dụng trên thiết bị.")
            self.bridge().launch(serial, package)
            capture = Capture(self.bridge(), serial, package, data["seconds"], self.reports, self.progress)
            self.capture = capture
            self.state = {"phase": "recording", "session": capture.folder.name, "package": package,
                          "seconds": capture.seconds, "elapsed_s": 0, "summary": None, "trace": "not_started"}
        threading.Thread(target=self.run, args=(capture,), daemon=True).start()
        return self.snapshot()

    def progress(self, data):
        with self.lock:
            self.state.update(data)
            if data.get("finalizing"):
                self.state["phase"] = "finalizing"

    def run(self, capture):
        try:
            report = capture.run()
            with self.lock:
                self.state.update(phase="complete", report=report, summary=report["summary"])
        except Exception as exc:
            with self.lock:
                self.state.update(phase="error", error=str(exc))

    def snapshot(self):
        with self.lock:
            return json.loads(json.dumps(self.state))

    def history(self):
        return self.repository.list()

    def report_path(self, session, filename="report.json"):
        return self.repository.path(session, filename)

    def install(self, data):
        with self.lock:
            if self.installing or self.state["phase"] in ("recording", "finalizing"):
                raise ValueError("Hãy đợi tác vụ hiện tại hoàn tất.")
            self.installing = True
        try:
            serial = data["serial"]
            if serial not in [d["serial"] for d in self.bridge().devices() if d["state"] == "device"]:
                raise ValueError("Thiết bị chưa được cấp quyền USB.")
            content = base64.b64decode(data["apk"], validate=True)
            if len(content) > 140 * 1024 * 1024 or not content.startswith(b"PK"):
                raise ValueError("File APK không hợp lệ hoặc vượt 140 MB.")
            with tempfile.TemporaryDirectory(prefix="framelab-") as folder:
                path = Path(folder) / "upload.apk"
                path.write_bytes(content)
                return {"message": self.bridge().install(serial, path)}
        finally:
            with self.lock:
                self.installing = False

    def stop(self):
        with self.lock:
            if self.capture and self.state["phase"] in ("recording", "finalizing"):
                self.capture.stop.set()
        return self.snapshot()
