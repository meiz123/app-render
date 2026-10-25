"""Capture recent-frame samples plus optional system trace; preserve raw evidence."""
import json
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from ..domain.frames import parse_frames, summarize, frame_identity, android_rendered_total


TRACE_CONFIG = '''buffers { size_kb: 32768 fill_policy: RING_BUFFER }
duration_ms: DURATION
write_into_file: true
file_write_period_ms: 1000
max_file_size_bytes: 268435456
data_sources { config { name: "android.surfaceflinger.frametimeline" } }
data_sources { config { name: "linux.process_stats" } }
'''


class Capture:
    def __init__(self, adb, serial, package, seconds, root, update=lambda data: None):
        self.adb, self.serial = adb, serial
        self.package = adb.package(package)
        self.seconds = int(seconds)
        if not 5 <= self.seconds <= 300:
            raise ValueError("Thời lượng phải trong khoảng 5–300 giây cho bản đầu.")
        self.folder = Path(root) / (datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6])
        self.folder.mkdir(parents=True)
        self.update = update
        self.stop = threading.Event()
        self.frames = {}
        self.trace_status = "not_started"
        self.count_audit = {"version": 2, "android_rendered_total": None, "revised_records_merged": 0,
                            "repeated_records_ignored": 0, "pre_session_records_ignored": 0}

    def run(self):
        errors, samples = [], []
        remote = "/data/misc/perfetto-traces/framelab-" + uuid.uuid4().hex + ".perfetto-trace"
        metadata = {"package": self.package, "serial": self.serial,
                    "started_utc": datetime.now(timezone.utc).isoformat(),
                    "requested_seconds": self.seconds, "source": "gfxinfo framestats",
                    "coverage": "recent_frame_samples_not_guaranteed_complete",
                    "bitmap": {"status": "unsupported", "bytes": None,
                               "reason": "No verified bitmap allocation source for this APK/device."}}
        began = time.monotonic()
        trace_thread = None
        try:
            metadata["android_sdk"] = self.adb.run("shell", "getprop", "ro.build.version.sdk", serial=self.serial).strip()
            metadata["model"] = self.adb.run("shell", "getprop", "ro.product.model", serial=self.serial).strip()
            reset_output = self.adb.run("shell", "dumpsys", "gfxinfo", self.package, "reset", serial=self.serial)
            (self.folder / "gfxinfo-reset.txt").write_text(reset_output)
            reset_time = re.search(r"Stats since:\s*(\d+)ns", reset_output)
            cutoff = int(reset_time.group(1)) if reset_time else None
            cutoff_refreshed = False
            metadata["frame_start_cutoff_ns"] = cutoff
            if int(metadata["android_sdk"]) >= 31:
                config = self.folder / "trace-config.pbtxt"
                config.write_text(TRACE_CONFIG.replace("DURATION", str(self.seconds * 1000)))
                def record():
                    try:
                        self.trace_status = "recording"
                        output = self.adb.run("shell", "perfetto", "--txt", "-c", "-",
                                              "-o", remote, serial=self.serial,
                                              input_text=config.read_text(), timeout=self.seconds + 30)
                        (self.folder / "perfetto.log").write_text(output)
                        self.adb.run("pull", remote, str(self.folder / "capture.perfetto-trace"),
                                     serial=self.serial, timeout=60)
                        trace_file = self.folder / "capture.perfetto-trace"
                        if not trace_file.is_file() or trace_file.stat().st_size == 0:
                            raise RuntimeError("File trace không tồn tại hoặc rỗng sau khi tải.")
                        self.trace_status = "saved_unvalidated"
                    except Exception as exc:
                        self.trace_status = "failed"
                        errors.append("Perfetto: " + str(exc))
                trace_thread = threading.Thread(target=record)
                trace_thread.start()
            else:
                self.trace_status = "requires_android_12"
            index = 0
            while time.monotonic() - began < self.seconds:
                raw = self.adb.run("shell", "dumpsys", "gfxinfo", self.package, "framestats", serial=self.serial)
                if not cutoff_refreshed:
                    current_reset = re.search(r"Stats since:\s*(\d+)ns", raw)
                    if current_reset:
                        cutoff = int(current_reset.group(1))
                        metadata["frame_start_cutoff_ns"] = cutoff
                    cutoff_refreshed = True
                (self.folder / f"frames-{index:04}.txt").write_text(raw)
                self.count_audit["android_rendered_total"] = android_rendered_total(raw)
                for frame in parse_frames(raw):
                    if cutoff is not None and frame["IntendedVsync"] < cutoff:
                        self.count_audit["pre_session_records_ignored"] += 1
                        continue
                    key = frame_identity(frame)
                    previous = self.frames.get(key)
                    if previous is not None:
                        field = ("revised_records_merged" if previous["FrameCompleted"] != frame["FrameCompleted"]
                                 else "repeated_records_ignored")
                        self.count_audit[field] += 1
                    self.frames[key] = frame
                if index % 4 == 0:
                    memory = self.adb.run("shell", "dumpsys", "meminfo", self.package, serial=self.serial)
                    (self.folder / f"memory-{index:04}.txt").write_text(memory)
                elapsed = round(time.monotonic() - began, 2)
                samples.append({"elapsed_s": elapsed, "unique_frames": len(self.frames)})
                diagnostic = None
                if not self.frames:
                    diagnostic = ("App chưa chạy hoặc đã thoát. Mở đúng app trên điện thoại."
                                  if "No process found" in raw else
                                  "Chưa có frame hợp lệ. Hãy cuộn hoặc chuyển màn hình trong app mục tiêu.")
                self.update({"elapsed_s": elapsed, "summary": summarize(list(self.frames.values())),
                             "trace": self.trace_status, "diagnostic": diagnostic, "frame_start_cutoff_ns": cutoff,
                             "count_audit": dict(self.count_audit),
                             "frames": [{"IntendedVsync": f["IntendedVsync"], "duration_ms": f["duration_ms"],
                                         "FrameCompleted": f["FrameCompleted"], "FrameDeadline": f.get("FrameDeadline"),
                                         "window": f.get("window"), "FrameTimelineVsyncId": f.get("FrameTimelineVsyncId")}
                                        for f in sorted(self.frames.values(), key=lambda f: f["IntendedVsync"])[-200:]]})
                index += 1
                if self.stop.wait(.5):
                    break
        except Exception as exc:
            errors.append(str(exc))
        finally:
            if trace_thread:
                # Perfetto has a bounded duration; do not kill unrelated recording processes.
                self.update({"finalizing": True, "trace": self.trace_status})
                trace_thread.join()
                try:
                    self.adb.run("shell", "rm", "-f", remote, serial=self.serial)
                except Exception as exc:
                    errors.append("Temporary trace cleanup: " + str(exc))
            metadata.update({"actual_wall_seconds": round(time.monotonic() - began, 2),
                             "stopped_early": self.stop.is_set(), "trace_status": self.trace_status,
                             "trace_coverage": "unvalidated_open_in_perfetto",
                             "errors": errors, "samples": samples,
                             "summary": summarize(list(self.frames.values()))})
            metadata["count_audit"] = dict(self.count_audit)
            metadata["diagnostic"] = ("Không thu được frame hợp lệ. Kiểm tra app có đang mở và thao tác đúng app. "
                                      "Mở các file frames-*.txt để xem phản hồi từ Android."
                                      if not self.frames else None)
            (self.folder / "frames.json").write_text(json.dumps(list(self.frames.values()), indent=2))
            (self.folder / "report.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
        return metadata
