# Frame Lab 0.2

Web cục bộ đo hiệu năng Android qua USB. Không đưa APK hoặc báo cáo lên mạng.

## Mở bằng một cú nhấp

- App: `release/Frame Lab.app` (Mac chip Apple).
- File gửi: `release/Frame-Lab-0.2.0-macOS-Apple-Silicon.zip`.
- Hướng dẫn: [docs/QUICK_START_VI.md](docs/QUICK_START_VI.md).

Không cần cài Python, Android Studio hoặc ADB trên máy người nhận. Bản macOS thử nội bộ chưa có Developer ID/notarization, macOS có thể chặn khi nhận từ Internet. Chưa có bản Mac Intel.

### Windows portable

File: `release/Frame-Lab-0.2.0-Windows-x64-Portable.zip`. Giải nén toàn bộ rồi nhấp đúp `Mo Frame Lab.cmd`. Gói có Python embeddable x64 và ADB/DLL bản Windows; không cần cài riêng. Đây là launcher CMD dùng runtime đi kèm, không phải một EXE độc lập do PyInstaller build. Chưa thử trực tiếp trên Windows. [Hướng dẫn Windows](docs/QUICK_START_WINDOWS_VI.md).

Tạo lại gói từ ZIP chính thức của Python và Google:

```sh
python3 scripts/package_windows_portable.py --python-zip build/windows-downloads/python-3.14.9-embed-amd64.zip --adb-zip build/windows-downloads/platform-tools-windows.zip
```

Script kiểm tra SHA-256 Python theo Python.org, định dạng PE của runtime, giữ thông báo giấy phép và ghi BUILD_INFO.json/checksum. ADB tải từ Google qua HTTPS, checksum thực tế được lưu để truy vết. Thư mục build/reports, APK, môi trường Python máy tác giả không được đóng gói.

## Chạy từ mã nguồn

Python 3.11+ và Android SDK Platform Tools, không có dependency runtime ngoài.

```sh
python3 -m framelab.web
```

Hoặc mở `run.command`. App tự mở web tại http://127.0.0.1:8765, thử cổng 8766–8774 nếu cổng đã bị chiếm. Mở lại app dùng phiên đang chạy. Bấm **Thoát Frame Lab** trên web để dừng server sau khi tác vụ hoàn tất.

```sh
python3 -m framelab.web --port 8766 --no-browser
```

ADB được tìm từ ADB_PATH, bundle, PATH hoặc Android SDK mặc định trên macOS.

## Tổ chức code

`android/` kết nối; `collectors/` thu dữ liệu; `domain/` công thức; `services/` phối hợp; `repositories/` báo cáo; `api/` HTTP; `static/js/` các chức năng UI riêng; `static/styles/` nền tảng/thành phần/responsive; `packaging/`, `scripts/`, `tests/`, `docs/` cho build và bảo trì.

Chi tiết: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Nơi lưu dữ liệu

- macOS: `~/Library/Application Support/Frame Lab/reports/`
- Log: `~/Library/Application Support/Frame Lab/app.log`
- Có thể đặt FRAMELAB_DATA_DIR để đổi vị trí.
- Báo cáo cũ trong thư mục dự án reports/ không bị xóa; copy các thư mục phiên sang vị trí mới nếu cần nhập lịch sử.

## Phạm vi đo

- Chọn app, tìm package, cài APK tối đa 140 MB.
- Gfxinfo: lọc frame lỗi, loại trùng IntendedVsync + FrameCompleted. Thời gian `(FrameCompleted - IntendedVsync) / 1e6` ms, percentile nearest rank.
- Trễ deadline tính trên frame có FrameDeadline hợp lệ. Frozen là frame >700 ms trong mẫu. Mẫu không bảo đảm bao phủ toàn phiên, định danh đa cửa sổ còn hạn chế.
- Android 12+: ghi trace Perfetto thô tối đa 256 MiB; chưa tự phân tích hoặc xác nhận độ bao phủ.
- Dừng lấy mẫu không dừng ngay Perfetto; đợi hết thời lượng gốc. Không kill phiên Perfetto khác.
- Biểu đồ: tối đa 90 nhóm theo thời gian thật, lấy frame chậm nhất của mỗi nhóm; giữ khoảng trống khi không có mẫu. Có trục ms/giây, màu theo deadline thực, thông tin từng nhóm và thang chi tiết 0–50 ms hoặc toàn bộ giá trị. Đỉnh vượt thang có ký hiệu, không bị xóa khỏi dữ liệu.
- **Chưa hỗ trợ đo bitmap riêng**. Meminfo chỉ là thông tin bổ sung, không dùng tổng RAM thay thế.
- Không phải số liệu Android vitals; chưa xác thực trên điện thoại thật trong môi trường hiện tại.

## Kiểm tra và build

```sh
python3 -m unittest discover -s tests -v
./scripts/build_macos.sh
```

Build trên macOS arm64, có Android SDK hoặc FRAMELAB_ADB_DIR trỏ tới platform-tools chứa adb và NOTICE.txt. Dependencies build được ghim ở packaging/requirements-build.txt. Không đóng gói dữ liệu cá nhân.

## Chọn ứng dụng

Có hai chế độ: **Tên app + icon** (tên/icon thật từ điện thoại; tìm tên không dấu) và **Tên package** (lọc package ID). Helper chỉ đọc danh mục, không cài app. Thiết bị không cho đọc tên/icon vẫn chọn được bằng package. Cache metadata trong bộ nhớ 5 phút; bấm Làm mới để cập nhật ngay.

Nếu sửa helper Java, chạy `./scripts/build_android_helper.sh` trước khi đóng gói. File DEX có sẵn được đưa vào cả bản Mac và Windows.

### Sửa lỗi phiên không có frame

App tự mở đúng launcher trước khi reset và ghi, đọc đúng CSV framestats có dấu phẩy cuối dòng và lọc frame trước mốc reset nếu có timestamp. Biểu đồ cập nhật theo mẫu khi đang ghi (tối đa 200 frame gần nhất trong phản hồi live; báo cáo giữ toàn bộ mẫu thu được). Perfetto nhận cấu hình qua stdin, ghi vào /data/misc/perfetto-traces để tránh lỗi quyền trên Android 12. Đã chạy thử 5 giây trên M2010J19SG/Android 12 và thu được frame cùng file trace; điều này không chứng minh độ bao phủ trên mọi thiết bị.

### Kiểm toán số frame — quy tắc v2

Frame được gộp theo tiến trình + cửa sổ + FrameTimelineVsyncId dương; khi không có ID thì dùng IntendedVsync. FrameCompleted chỉ cập nhật giá trị, không làm khóa định danh. Giữ bản cập nhật cuối của cùng frame. UI hiển thị số mẫu duy nhất, tổng Android báo ở lần đọc cuối (chỉ cộng counter cấp tiến trình, không cộng thêm subtotal cửa sổ), và số lần cập nhật được gộp. Hai tổng không đồng nghĩa độ bao phủ/FPS.

`docs/frame-count-audit.json` lưu kết quả đối chiếu phiên 60 giây: cách cũ 2570, tính lại 2568, Android lần cuối 2750. Báo cáo gốc được giữ nguyên; báo cáo chưa có count_audit.version=2 được cảnh báo dùng quy tắc cũ và cần đo lại.
