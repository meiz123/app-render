"""Bounded, argument-based ADB calls; never execute a host shell."""
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from ..config import bundled_adb


class Adb:
    def __init__(self):
        sdk_adb = (Path(os.environ.get("LOCALAPPDATA", Path.home())) / "Android/sdk/platform-tools/adb.exe"
                   if sys.platform == "win32" else Path.home() / "Library/Android/sdk/platform-tools/adb")
        candidates = [os.environ.get("ADB_PATH"), str(bundled_adb()), shutil.which("adb"),
                      str(sdk_adb)]
        self.path = next((p for p in candidates if p and Path(p).is_file()), None)
        if not self.path:
            raise RuntimeError("Không tìm thấy ADB. Cài Android SDK Platform Tools hoặc đặt ADB_PATH.")

    def run(self, *args, serial=None, timeout=20, input_text=None):
        command = [self.path] + (["-s", serial] if serial else []) + list(args)
        options = {"creationflags": subprocess.CREATE_NO_WINDOW} if sys.platform == "win32" else {}
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=timeout, input=input_text, **options)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "ADB thất bại")
        return result.stdout

    def devices(self):
        rows = []
        for line in self.run("devices", "-l").splitlines()[1:]:
            fields = line.split()
            if len(fields) >= 2:
                rows.append({"serial": fields[0], "state": fields[1], "detail": " ".join(fields[2:])})
        return rows

    @staticmethod
    def package(value):
        if not re.fullmatch(r"[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+", value):
            raise ValueError("Package ID không hợp lệ, ví dụ: com.example.app")
        return value

    def packages(self, serial):
        output = self.run("shell", "pm", "list", "packages", serial=serial)
        return sorted(line.removeprefix("package:").strip() for line in output.splitlines()
                      if line.startswith("package:"))

    def launch(self, serial, package):
        package = self.package(package)
        resolved = self.run("shell", "cmd", "package", "resolve-activity", "--brief",
                            "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LAUNCHER",
                            package, serial=serial)
        components = [line.strip() for line in resolved.splitlines()
                      if re.fullmatch(re.escape(package) + r"/[A-Za-z0-9_.$]+", line.strip())]
        if not components:
            raise ValueError("App này không có màn hình mở trực tiếp. Hãy mở app thủ công trước khi đo.")
        output = self.run("shell", "am", "start", "-W", "-n", components[-1], serial=serial, timeout=45)
        if "Error:" in output or "Exception" in output:
            raise RuntimeError("Không mở được app: " + output.strip())
        return output

    def install(self, serial, apk):
        path = Path(apk).resolve(strict=True)
        if path.suffix.lower() != ".apk":
            raise ValueError("Vui lòng chọn file .apk")
        output = self.run("install", "-r", str(path), serial=serial, timeout=180)
        if "Success" not in output:
            raise RuntimeError(output)
        return output
