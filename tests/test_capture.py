import tempfile
import unittest
from pathlib import Path
from framelab.collectors.render import Capture


class CaptureAdb:
    def __init__(self):
        self.calls = []

    def package(self, value):
        return value

    def run(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if "ro.build.version.sdk" in args:
            return "31"
        if "reset" in args:
            return "Stats since: 2000000ns"
        if "framestats" in args:
            return "Flags,IntendedVsync,FrameCompleted,FrameDeadline,\n0,1000000,4000000,3000000,\n0,3000000,8000000,7000000,\n"
        if args[0] == "pull":
            Path(args[-1]).write_bytes(b"trace")
        return ""


class CaptureTests(unittest.TestCase):
    def test_trace_stdin_and_filter_pre_reset_frames(self):
        with tempfile.TemporaryDirectory() as folder:
            adb = CaptureAdb()
            capture = Capture(adb, "device", "com.example.app", 5, folder)
            capture.update = lambda _: capture.stop.set()
            report = capture.run()
            self.assertEqual(report["summary"]["count"], 1)
            self.assertEqual(report["trace_status"], "saved_unvalidated")
            perfetto = next(call for call in adb.calls if "perfetto" in call[0])
            self.assertIn("input_text", perfetto[1])
            self.assertEqual(perfetto[0][perfetto[0].index("-c") + 1], "-")
            self.assertFalse(any(call[0][0] == "push" for call in adb.calls))


if __name__ == "__main__":
    unittest.main()
