"""Native desktop UI. Workers communicate through a queue; no Tk calls off-thread."""
import json
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from ..android.adb import Adb
from ..collectors.render import Capture

BG, PANEL, INK, MUTED, ACCENT = "#F5F7FA", "#FFFFFF", "#142039", "#66748A", "#2563EB"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Frame Lab · Android performance")
        self.root.geometry("1180x820")
        self.root.minsize(1000, 760)
        self.root.configure(bg=BG)
        self.events = queue.Queue()
        self.capture = None
        self.busy = False
        from ..config import data_dir
        self.reports = data_dir() / "reports"
        self.adb = Adb()
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", padding=9, fieldbackground=PANEL)
        style.configure("TButton", padding=(14, 9), font=("Helvetica Neue", 12))
        style.configure("Accent.TButton", background=ACCENT, foreground="white")
        style.map("Accent.TButton", background=[("active", "#1D4ED8"), ("disabled", "#CBD5E1")])
        self.device = tk.StringVar()
        self.package = tk.StringVar()
        self.duration = tk.StringVar(value="30")
        self.status = tk.StringVar(value="Kết nối điện thoại để bắt đầu")
        self.build()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self.drain)
        self.refresh()

    def label(self, parent, text, size=12, color=INK, bold=False, **kw):
        return tk.Label(parent, text=text, bg=parent.cget("bg"), fg=color,
                        font=("Helvetica Neue", size, "bold" if bold else "normal"), **kw)

    def card(self, parent):
        return tk.Frame(parent, bg=PANEL, padx=24, pady=20, highlightbackground="#E3E8EF", highlightthickness=1)

    def build(self):
        sidebar = tk.Frame(self.root, bg=INK, width=190, padx=22, pady=30)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        self.label(sidebar, "FRAME LAB", 17, "white", True).pack(anchor="w")
        self.label(sidebar, "Android performance", 10, "#A6B2C6").pack(anchor="w", pady=(6, 40))
        self.label(sidebar, "●   Phiên đo mới", 12, "#ADC8FF", True).pack(anchor="w")
        ttk.Button(sidebar, text="Lịch sử báo cáo", command=self.history).pack(anchor="w", pady=20)
        self.label(sidebar, "USB · Dữ liệu cục bộ\nKhông cần Play Console", 10, "#A6B2C6", justify="left").pack(side="bottom", anchor="w")
        main = tk.Frame(self.root, bg=BG, padx=30, pady=26)
        main.pack(side="left", fill="both", expand=True)
        self.label(main, "Đo hiệu năng Android", 26, bold=True).pack(anchor="w")
        self.label(main, "Chọn app. Ghi thao tác. Kiểm tra bằng dữ liệu gốc.", 12, MUTED).pack(anchor="w", pady=(6, 20))
        setup = self.card(main)
        setup.pack(fill="x")
        self.label(setup, "01   Thiết lập phiên đo", 14, bold=True).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 16))
        self.device_box = ttk.Combobox(setup, textvariable=self.device, state="readonly", width=38)
        self.device_box.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.device_box.bind("<<ComboboxSelected>>", lambda e: self.load_packages())
        self.refresh_button = ttk.Button(setup, text="Quét thiết bị", command=self.refresh)
        self.refresh_button.grid(row=1, column=1, sticky="w")
        self.install_button = ttk.Button(setup, text="Cài APK…", command=self.install)
        self.install_button.grid(row=1, column=2, sticky="e")
        self.package_box = ttk.Combobox(setup, textvariable=self.package, width=38, state="readonly")
        self.package_box.grid(row=2, column=0, sticky="ew", pady=(12, 0), padx=(0, 10))
        ttk.Combobox(setup, textvariable=self.duration, values=["15", "30", "60", "120", "300"],
                     width=7, state="readonly").grid(row=2, column=1, sticky="w", pady=(12, 0))
        self.label(setup, "giây · bản đầu tối đa 5 phút", 10, MUTED).grid(row=3, column=1, columnspan=2, sticky="w", pady=(4, 0))
        setup.columnconfigure(0, weight=1)
        actions = tk.Frame(main, bg=BG)
        actions.pack(fill="x", pady=16)
        self.start_button = ttk.Button(actions, text="Bắt đầu đo", style="Accent.TButton", command=self.start)
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(actions, text="Dừng lấy mẫu", command=self.stop, state="disabled")
        self.stop_button.pack(side="left", padx=10)
        self.label(actions, "Mở app và thao tác trên điện thoại khi đang ghi.", 10, MUTED).pack(side="left")
        row = tk.Frame(main, bg=BG)
        row.pack(fill="x")
        self.metrics = {}
        for i, (key, title) in enumerate([("count", "Frame thu được"), ("deadline_miss_pct", "Trễ deadline · mẫu gfxinfo"),
                                          ("frozen_pct", "Frame > 700 ms · mẫu gfxinfo")]):
            panel = self.card(row)
            panel.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 10, 0))
            self.label(panel, title, 10, MUTED).pack(anchor="w")
            value = self.label(panel, "—", 26, bold=True)
            value.pack(anchor="w", pady=(10, 0))
            self.metrics[key] = value
            row.columnconfigure(i, weight=1)
        render = self.card(main)
        render.pack(fill="x", pady=(16, 0))
        self.label(render, "02   Rendering", 14, bold=True).pack(anchor="w")
        self.percentiles = self.label(render, "P50  —       P90  —       P99  —", 15)
        self.percentiles.pack(anchor="w", pady=12)
        self.label(render, "Kết quả lấy mẫu gần đây; chưa xác nhận bao phủ toàn phiên.\nTrace Perfetto lưu riêng để kiểm chứng; chưa tự phân tích trong bản đầu.",
                   10, MUTED, justify="left").pack(anchor="w")
        memory = self.card(main)
        memory.pack(fill="x", pady=(16, 0))
        self.label(memory, "03   Bitmap memory", 14, bold=True).pack(anchor="w")
        self.label(memory, "Chưa hỗ trợ đo riêng bitmap", 16, "#9A6700", True).pack(anchor="w", pady=(10, 6))
        self.label(memory, "Lưu meminfo để chẩn đoán bổ sung. Tổng RAM không được tính thành bitmap.\nCần nguồn cấp phát bitmap được xác thực trước khi hiển thị số MB.",
                   10, MUTED, justify="left").pack(anchor="w")
        tk.Label(main, textvariable=self.status, bg=BG, fg=MUTED, font=("Helvetica Neue", 11),
                 anchor="w", wraplength=800, justify="left").pack(fill="x", pady=(18, 0))

    def worker(self, function, callback):
        def run():
            try:
                self.events.put((callback, function()))
            except Exception as exc:
                self.events.put((self.error, str(exc)))
        threading.Thread(target=run, daemon=True).start()

    def drain(self):
        try:
            while True:
                callback, data = self.events.get_nowait()
                callback(data)
        except queue.Empty:
            pass
        self.root.after(100, self.drain)

    def error(self, text):
        self.status.set(text)
        messagebox.showerror("Frame Lab", text)

    def serial(self):
        value = self.device.get().split(" · ")[0]
        if not value:
            raise ValueError("Chưa chọn điện thoại được cấp quyền USB.")
        return value

    def refresh(self):
        if self.busy:
            return
        self.status.set("Đang kiểm tra kết nối USB…")
        self.worker(self.adb.devices, self.show_devices)

    def show_devices(self, devices):
        authorized = [d for d in devices if d["state"] == "device"]
        values = [d["serial"] + " · " + d["detail"] for d in authorized]
        self.device_box["values"] = values
        if values:
            self.device.set(values[0])
            self.load_packages()
        else:
            self.device.set("")
            self.package.set("")
            self.package_box["values"] = []
            detail = ", ".join(d["serial"] + ": " + d["state"] for d in devices)
            self.status.set("Chưa có thiết bị được cấp quyền. Bật Gỡ lỗi USB và chấp nhận trên điện thoại. " + detail)

    def load_packages(self):
        serial = self.serial()
        self.worker(lambda: self.adb.packages(serial), self.show_packages)

    def show_packages(self, packages):
        self.package_box["values"] = packages
        self.package.set(packages[0] if packages else "")
        self.status.set(f"Đã kết nối · {len(packages)} app người dùng. Chọn app cần đo.")

    def install(self):
        if self.busy:
            return
        try:
            serial = self.serial()
        except ValueError as exc:
            return self.error(str(exc))
        apk = filedialog.askopenfilename(filetypes=[("Android APK", "*.apk")])
        if apk:
            self.status.set("Đang cài APK…")
            self.worker(lambda: self.adb.install(serial, apk), lambda _: self.load_packages())

    def start(self):
        if self.busy:
            return
        try:
            self.capture = Capture(self.adb, self.serial(), self.package.get(), self.duration.get(), self.reports,
                                   lambda data: self.events.put((self.progress, data)))
        except Exception as exc:
            return self.error(str(exc))
        self.busy = True
        self.start_button["state"] = "disabled"
        self.refresh_button["state"] = "disabled"
        self.install_button["state"] = "disabled"
        self.stop_button["state"] = "normal"
        self.device_box["state"] = "disabled"
        self.package_box["state"] = "disabled"
        self.status.set("Đang ghi. Hãy thao tác trong app đã chọn trên điện thoại.")
        self.worker(self.capture.run, self.finished)

    def stop(self):
        if self.capture:
            self.capture.stop.set()
            self.status.set("Đã yêu cầu dừng mẫu. Trace Perfetto sẽ hoàn tất theo thời lượng đã đặt.")

    def progress(self, data):
        if data.get("finalizing"):
            self.status.set("Đang hoàn tất và lưu trace Perfetto…")
            return
        result = data["summary"]
        for key, widget in self.metrics.items():
            value = result.get(key)
            widget.config(text="—" if value is None else str(value) if key == "count" else f"{value:.2f}%")
        self.percentiles.config(text="       ".join(f"P{p}  {result[f'p{p}_ms']:.1f} ms" if result[f'p{p}_ms'] is not None
                                                    else f"P{p}  —" for p in (50, 90, 99)))
        self.status.set(f"Đang ghi · {data['elapsed_s']:.0f} giây · Perfetto: {data['trace']}")

    def finished(self, report):
        self.busy = False
        for widget in [self.start_button, self.refresh_button, self.install_button]:
            widget["state"] = "normal"
        self.stop_button["state"] = "disabled"
        self.device_box["state"] = self.package_box["state"] = "readonly"
        status = "Có lỗi: " + "; ".join(report["errors"]) if report["errors"] else "Đã lưu báo cáo và dữ liệu gốc."
        self.status.set(status + " Kết quả gfxinfo là mẫu, không đại diện Android vitals.")

    def history(self):
        self.reports.mkdir(exist_ok=True)
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(self.reports)])
        else:
            messagebox.showinfo("Báo cáo", str(self.reports))

    def close(self):
        if self.busy:
            messagebox.showinfo("Đang ghi", "Dừng lấy mẫu và đợi trace được lưu trước khi đóng app.")
            return
        self.root.destroy()


def main():
    root = tk.Tk()
    try:
        App(root)
    except Exception as exc:
        messagebox.showerror("Frame Lab", str(exc))
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
