"""Assemble official Windows runtimes on any host; does not cross-compile.

Downloads are supplied as arguments. Python archive is verified against the
SHA-256 published on the official Python 3.14.9 release page.
"""
import argparse
import hashlib
import json
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON_VERSION = "3.14.9"
PYTHON_SHA256 = "3c01d7cfc666f746a6f064f60fb2156ab0ec464d3d738ab796371a46a9bb24a2"


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def extract(archive, destination):
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as source:
        for info in source.infolist():
            target = (destination / info.filename).resolve()
            if not target.is_relative_to(destination.resolve()):
                raise ValueError("Unsafe archive member: " + info.filename)
        source.extractall(destination)


def windows_machine(path):
    data = Path(path).read_bytes()
    if data[:2] != b"MZ" or len(data) < 64:
        return None
    offset = struct.unpack_from("<I", data, 0x3C)[0]
    if offset + 6 > len(data) or data[offset:offset+4] != b"PE\0\0":
        return None
    return struct.unpack_from("<H", data, offset+4)[0]


def assemble(python_zip, adb_zip, output):
    if sha256(python_zip) != PYTHON_SHA256:
        raise ValueError("Python archive does not match the official SHA-256.")
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    # A unique fresh directory avoids merging stale app files into releases.
    import tempfile
    work = Path(tempfile.mkdtemp(prefix="windows-portable-", dir=ROOT / "build"))
    stage = work / "Frame Lab Windows"
    runtime = stage / "runtime"
    extract(python_zip, runtime)
    extract(adb_zip, work / "adb-source")
    tools = stage / "tools"
    tools.mkdir()
    adb_source = work / "adb-source/platform-tools"
    required = ["adb.exe", "AdbWinApi.dll", "AdbWinUsbApi.dll", "NOTICE.txt", "source.properties"]
    for name in required:
        shutil.copy2(adb_source / name, tools / name)
    # Include any additional runtime DLLs shipped with the downloaded ADB.
    for path in adb_source.glob("*.dll"):
        shutil.copy2(path, tools / path.name)
    for path in [runtime / "python.exe", runtime / "pythonw.exe"]:
        if windows_machine(path) != 0x8664:
            raise ValueError("Expected Windows x64 executable: " + str(path))
    # Google's Windows ADB can be x86; Windows x64 runs it via WOW64.
    if windows_machine(tools / "adb.exe") not in (0x14C, 0x8664):
        raise ValueError("Expected official Windows x86/x64 ADB executable")
    source = stage / "app/framelab"
    shutil.copytree(ROOT / "framelab", source,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "presentation"))
    # Embedded Python ignores PYTHONPATH. Add the sibling app directory explicitly.
    (runtime / "python314._pth").write_text("python314.zip\n.\n../app\n", encoding="utf-8")
    shutil.copy2(ROOT / "packaging/windows/launch.py", stage / "launch.py")
    for src, dest in [("start.cmd", "Mo Frame Lab.cmd"), ("diagnose.cmd", "Kiem tra loi.cmd")]:
        content = (ROOT / "packaging/windows" / src).read_text()
        (stage / dest).write_bytes(content.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"))
    shutil.copy2(ROOT / "docs/QUICK_START_WINDOWS_VI.md", stage / "HUONG_DAN.md")
    manifest = {
        "app_version": "0.2.0", "target": "Windows x64 portable", "native_windows_tested": False,
        "python": {"version": PYTHON_VERSION, "sha256": sha256(python_zip),
                   "source": "https://www.python.org/ftp/python/3.14.9/python-3.14.9-embed-amd64.zip"},
        "adb": {"sha256": sha256(adb_zip),
                "source": "https://dl.google.com/android/repository/platform-tools-latest-windows.zip",
                "properties": (tools / "source.properties").read_text()},
    }
    (stage / "BUILD_INFO.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    archive = output / "Frame-Lab-0.2.0-Windows-x64-Portable.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for path in sorted(stage.rglob("*")):
            if path.is_file():
                zipped.write(path, path.relative_to(work))
    (output / "WINDOWS-SHA256SUMS.txt").write_text(sha256(archive) + "  " + archive.name + "\n")
    return archive


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-zip", type=Path, required=True)
    parser.add_argument("--adb-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "release")
    args = parser.parse_args()
    (ROOT / "build").mkdir(exist_ok=True)
    print(assemble(args.python_zip, args.adb_zip, args.output))


if __name__ == "__main__":
    main()
