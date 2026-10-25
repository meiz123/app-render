import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from framelab.services.session import Service
from framelab.api.http import handler


class FakeAdb:
    def devices(self):
        return [{"serial": "test-device", "state": "device", "detail": "model:Test"}]

    def packages(self, serial):
        return ["com.example.test"]


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.service = Service(cls.temp.name, FakeAdb())
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), handler(cls.service))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, method, path, data=None, headers=None):
        conn = HTTPConnection("127.0.0.1", self.server.server_port)
        conn.request(method, path, json.dumps(data) if data else None, headers or {})
        response = conn.getresponse()
        status, body = response.status, response.read()
        conn.close()
        return status, body

    def test_devices_and_static_page(self):
        status, body = self.request("GET", "/api/devices")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["devices"][0]["serial"], "test-device")
        status, body = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn(b"Frame Lab", body)

    def test_cross_origin_and_missing_token_rejected(self):
        self.assertEqual(self.request("POST", "/api/stop", {"stop": True})[0], 403)
        self.assertEqual(self.request("GET", "/api/status", headers={"Origin": "https://other.example"})[0], 403)
        self.assertEqual(self.request("GET", "/api/status", headers={"Host": "other.example"})[0], 403)

    def test_authorized_stop_and_traversal_rejection(self):
        status, _ = self.request("POST", "/api/stop", {"stop": True}, {"X-FrameLab-Token": self.service.token})
        self.assertEqual(status, 200)
        status, _ = self.request("GET", "/api/download?id=..&file=README.md")
        self.assertEqual(status, 400)

    def test_report_download_and_frames(self):
        folder = Path(self.temp.name) / "sample"
        folder.mkdir(exist_ok=True)
        (folder / "report.json").write_text(json.dumps({"package":"com.example.test"}))
        (folder / "frames.json").write_text("[]")
        status, body = self.request("GET", "/api/report?id=sample")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["frames"], [])
        status, body = self.request("GET", "/api/download?id=sample&file=frames.json")
        self.assertEqual((status, body), (200,b"[]"))


if __name__ == "__main__":
    unittest.main()
