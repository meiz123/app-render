"""HTTP transport: origin validation, JSON and file responses."""
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from ..config import STATIC_DIR


def handler(service):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def allowed(self):
            expected = f"127.0.0.1:{self.server.server_port}"
            if self.headers.get("Host") != expected:
                return False
            origin = self.headers.get("Origin")
            return origin is None or origin == "http://" + expected

        def send(self, data, status=200, content_type="application/json; charset=utf-8", download=None):
            body = data if isinstance(data, bytes) else json.dumps(data, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'")
            if download:
                self.send_header("Content-Disposition", 'attachment; filename="' + download + '"')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if not self.allowed():
                return self.send({"error": "Local origin required"}, 403)
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            try:
                if parsed.path == "/api/health":
                    return self.send({"app": "frame-lab", "version": "0.2.0"})
                if parsed.path == "/api/bootstrap":
                    return self.send({"token": service.token})
                if parsed.path == "/api/devices":
                    return self.send({"devices": service.bridge().devices()})
                if parsed.path == "/api/packages":
                    serial = query["serial"][0]
                    if serial not in [d["serial"] for d in service.bridge().devices() if d["state"] == "device"]:
                        raise ValueError("Thiết bị chưa được cấp quyền.")
                    return self.send({"packages": service.bridge().packages(serial)})
                if parsed.path == "/api/apps":
                    return self.send(service.applications(query["serial"][0], query.get("refresh", ["0"])[0] == "1"))
                if parsed.path == "/api/status":
                    return self.send(service.snapshot())
                if parsed.path == "/api/reports":
                    return self.send({"reports": service.history()})
                if parsed.path == "/api/report":
                    return self.send(service.repository.load(query["id"][0]))
                if parsed.path == "/api/download":
                    path = service.report_path(query["id"][0], query["file"][0])
                    return self.send(path.read_bytes(), content_type="application/octet-stream", download=path.name)
                relative = "index.html" if parsed.path == "/" else parsed.path.lstrip("/")
                asset = (STATIC_DIR / relative).resolve()
                if not asset.is_relative_to(STATIC_DIR.resolve()) or not asset.is_file() or asset.suffix not in {".html", ".css", ".js"}:
                    return self.send({"error": "Not found"}, 404)
                mime = {".html": "text/html", ".css": "text/css", ".js": "text/javascript"}[asset.suffix]
                self.send(asset.read_bytes(), content_type=mime + "; charset=utf-8")
            except Exception as exc:
                self.send({"error": str(exc)}, 400)

        def do_POST(self):
            if not self.allowed() or not secrets.compare_digest(self.headers.get("X-FrameLab-Token", ""), service.token):
                return self.send({"error": "Local session required"}, 403)
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 200 * 1024 * 1024:
                    raise ValueError("Nội dung quá lớn; APK tối đa 140 MB trong bản đầu.")
                data = json.loads(self.rfile.read(length))
                if self.path == "/api/start":
                    return self.send(service.start(data))
                if self.path == "/api/shutdown":
                    with service.lock:
                        if service.installing or service.state["phase"] in ("recording", "finalizing"):
                            raise ValueError("Hãy đợi phiên đo hoặc cài APK hoàn tất trước khi thoát.")
                    self.send({"message": "Frame Lab đã đóng."})
                    threading.Thread(target=self.server.shutdown, daemon=True).start()
                    return
                if self.path == "/api/stop":
                    return self.send(service.stop())
                if self.path == "/api/install":
                    return self.send(service.install(data))
                self.send({"error": "Not found"}, 404)
            except Exception as exc:
                self.send({"error": str(exc)}, 400)
    return Handler

