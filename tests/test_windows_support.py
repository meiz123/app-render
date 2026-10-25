import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from framelab.android.adb import Adb
from framelab.config import data_dir


class WindowsSupportTests(unittest.TestCase):
    def test_localappdata_storage(self):
        with patch("sys.platform", "win32"), patch.dict(os.environ, {"LOCALAPPDATA": "C:/Users/Test/AppData/Local"}):
            with patch.dict(os.environ, clear=False):
                os.environ.pop("FRAMELAB_DATA_DIR", None)
                self.assertEqual(data_dir(), Path("C:/Users/Test/AppData/Local/Frame Lab"))

    def test_adb_runs_without_console_and_decodes_unicode(self):
        with tempfile.TemporaryDirectory() as folder:
            adb = Path(folder) / "adb.exe"
            adb.touch()
            with patch.dict(os.environ, {"ADB_PATH": str(adb)}), patch("sys.platform", "win32"), patch("shutil.which", return_value=None):
                bridge = Adb()
                with patch.object(subprocess, "CREATE_NO_WINDOW", 0x08000000, create=True):
                    with patch("subprocess.run") as run:
                        run.return_value.returncode = 0
                        run.return_value.stdout = "Success\n"
                        self.assertEqual(bridge.run("version"), "Success\n")
                        kwargs = run.call_args.kwargs
                        self.assertEqual(kwargs["creationflags"], 0x08000000)
                        self.assertEqual(kwargs["encoding"], "utf-8")
                        self.assertEqual(kwargs["errors"], "replace")


if __name__ == "__main__":
    unittest.main()
