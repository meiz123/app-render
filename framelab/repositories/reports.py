"""Report storage and path confinement, independent of HTTP and devices."""
import json
from pathlib import Path


class ReportRepository:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(exist_ok=True, parents=True)

    def path(self, session, filename="report.json"):
        # Only a single session directory and a single file basename are accepted.
        if Path(session).name != session or Path(filename).name != filename:
            raise ValueError("Đường dẫn báo cáo không hợp lệ.")
        path = (self.root / session / filename).resolve()
        if path.parent.parent != self.root or not path.is_file():
            raise ValueError("Không tìm thấy dữ liệu phiên đo.")
        return path

    def list(self):
        reports = []
        for path in sorted(self.root.glob("*/report.json"), reverse=True):
            try:
                report = json.loads(self.path(path.parent.name).read_text())
                reports.append({"id": path.parent.name, "package": report["package"],
                                "started_utc": report["started_utc"], "summary": report["summary"],
                                "errors": report["errors"]})
            except (ValueError, KeyError, OSError):
                continue
        return reports

    def load(self, session):
        report_path = self.path(session)
        return {"report": json.loads(report_path.read_text()),
                "files": sorted(p.name for p in report_path.parent.iterdir() if p.is_file() and not p.is_symlink()),
                "frames": json.loads(self.path(session, "frames.json").read_text())}
