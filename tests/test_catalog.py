import json
import unittest
from framelab.android.catalog import AppCatalog


class CatalogAdb:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def packages(self, serial):
        return ["com.example.gallery", "com.example.other"]

    def run(self, *args, **kwargs):
        self.calls.append(args)
        if "app_process" in args:
            if self.fail:
                raise RuntimeError("Permission denied\ninternal stack")
            return 'runtime notice\n' + json.dumps({"apps": [
                {"package": "com.example.gallery", "label": "Thư viện ảnh", "label_available": True,
                 "icon": "data:image/png;base64,test"}]})
        return ""


class CatalogTests(unittest.TestCase):
    def test_real_metadata_merged_with_package_fallback_and_cached(self):
        adb = CatalogAdb()
        catalog = AppCatalog(adb)
        result = catalog.read("device")
        self.assertEqual(result["apps"][0]["label"], "Thư viện ảnh")
        self.assertFalse(result["apps"][1]["label_available"])
        self.assertIsNone(result["warning"])
        count = len(adb.calls)
        catalog.read("device")
        self.assertEqual(len(adb.calls), count)
        catalog.read("device", refresh=True)
        self.assertGreater(len(adb.calls), count)
        self.assertTrue(any(call[:3] == ("shell", "rm", "-f") for call in adb.calls))

    def test_restricted_device_falls_back_without_inventing_labels(self):
        result = AppCatalog(CatalogAdb(fail=True)).read("device")
        self.assertEqual(result["apps"][0]["label"], "com.example.gallery")
        self.assertIsNone(result["apps"][0]["icon"])
        self.assertNotIn("internal stack", result["warning"])


if __name__ == "__main__":
    unittest.main()
