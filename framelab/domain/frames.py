"""Explicit gfxinfo metrics. No inference of bitmap bytes from total RAM."""
import math
import re


def parse_frames(output):
    header = None
    window = None
    process_id = None
    records = []
    for line in output.splitlines():
        process = re.search(r"Graphics info for pid (\d+)", line)
        if process:
            process_id = int(process.group(1))
            window = None
            header = None
        if line.strip().startswith("Window:"):
            window = line.strip().removeprefix("Window:").strip()
        fields = [part.strip() for part in line.strip().rstrip(",").split(",")]
        if "Flags" in fields and "IntendedVsync" in fields and "FrameCompleted" in fields:
            header = fields
            continue
        if not header or len(fields) < len(header):
            continue
        try:
            row = dict(zip(header, map(int, fields[:len(header)])))
        except ValueError:
            continue
        start, end = row["IntendedVsync"], row["FrameCompleted"]
        # Flagged frames and sentinel / incomplete timestamps are not comparable.
        if row["Flags"] != 0 or start <= 0 or end <= start or end >= 2**63 - 1:
            continue
        row["duration_ms"] = (end - start) / 1_000_000
        row["window"] = window
        row["process_id"] = process_id
        records.append(row)
    return records


def frame_identity(frame):
    """A completion timestamp may be revised by Android; it is not an identity."""
    vsync_id = frame.get("FrameTimelineVsyncId")
    token = ("vsync", vsync_id) if isinstance(vsync_id, int) and vsync_id > 0 else ("start", frame["IntendedVsync"])
    return (frame.get("process_id"), frame.get("window"), *token)


def android_rendered_total(output):
    """Only the process-level counter, never add its per-window subtotals."""
    totals = []
    awaiting = False
    for line in output.splitlines():
        if "Graphics info for pid" in line:
            awaiting = True
        elif awaiting:
            match = re.match(r"\s*Total frames rendered:\s*(\d+)", line)
            if match:
                totals.append(int(match.group(1)))
                awaiting = False
    return sum(totals) if totals else None


def summarize(frames):
    values = sorted(f["duration_ms"] for f in frames)
    if not values:
        return {"count": 0, "frozen_count": 0, "frozen_pct": None,
                "p50_ms": None, "p90_ms": None, "p99_ms": None,
                "over_16_67_pct": None, "deadline_miss_pct": None}
    percentile = lambda p: values[max(0, math.ceil(p * len(values)) - 1)]
    eligible = [f for f in frames if f.get("FrameDeadline", 0) > f["IntendedVsync"]
                and f["FrameDeadline"] < 2**63 - 1]
    misses = sum(f["FrameCompleted"] > f["FrameDeadline"] for f in eligible)
    frozen = sum(v > 700 for v in values)
    return {"count": len(values), "frozen_count": frozen,
            "frozen_pct": frozen / len(values) * 100,
            "p50_ms": percentile(.5), "p90_ms": percentile(.9), "p99_ms": percentile(.99),
            "over_16_67_pct": sum(v > 1000/60 for v in values) / len(values) * 100,
            "deadline_sample_count": len(eligible),
            "deadline_miss_pct": misses / len(eligible) * 100 if eligible else None}
