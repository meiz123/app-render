# Kiến trúc Frame Lab

| Thư mục/file | Trách nhiệm |
|---|---|
| framelab/app.py | Khởi động, cổng, mở trình duyệt, logging |
| framelab/config.py | Vị trí assets, ADB, dữ liệu người dùng |
| framelab/android/adb.py | Chạy ADB, thiết bị, package, cài APK |
| framelab/collectors/render.py | Thu mẫu frame, trace Perfetto, meminfo |
| framelab/domain/frames.py | Parser, lọc frame, công thức thống kê thuần |
| framelab/services/session.py | Phối hợp phiên đo, khóa tác vụ, worker |
| framelab/repositories/reports.py | Đọc báo cáo và kiểm soát đường dẫn |
| framelab/api/http.py | HTTP, Host/Origin/token, phục vụ assets |
| framelab/static/js/common.js | State, HTTP client, định dạng, controls |
| framelab/static/js/devices.js | Quét thiết bị, tìm/chọn app |
| framelab/static/js/session.js | Poll trạng thái phiên đo |
| framelab/static/js/reports.js | Lịch sử, báo cáo, tải file |
| framelab/static/js/ui.js | Metric, biểu đồ, chuyển view |
| framelab/static/js/main.js | Khởi tạo và sự kiện người dùng |
| framelab/static/styles/ | base, components, responsive |
| framelab/presentation/desktop.py | Giao diện Tk cũ, không đóng gói |
| packaging/ | Spec, entrypoint, dependency build |
| scripts/ | Lệnh build lặp lại được |
| tests/ | Kiểm tra domain, API, lưu báo cáo |
| release/ | App và ZIP để gửi; không chứa báo cáo |

Luồng: browser → HTTP → session service → collector → ADB → Android.
Domain không phụ thuộc ADB, HTTP hay UI. Repository chịu trách nhiệm báo cáo.

## Mở rộng

- Nguồn bitmap: collector riêng, công bố quyền và độ bao phủ; không suy ra từ RAM.
- Phân tích FrameTimeline: analyzer domain riêng, không trộn số liệu với mẫu gfxinfo.
- Chỉ số mới: định nghĩa/test ở domain, đưa vào report rồi thêm UI.
- API mới: logic nghiệp vụ ở service, handler chỉ nhận/trả dữ liệu.
- Giao diện: sửa module JS tương ứng và styles, không thay đổi bộ đo.

## Dữ liệu và build

App bundle chứa Python, ADB, NOTICE và assets. Không chứa APK hoặc báo cáo cá nhân.
Báo cáo nằm ngoài bundle ở Application Support. FRAMELAB_DATA_DIR dành cho kiểm tra hoặc đổi vị trí lưu.
Báo cáo cũ trong reports/ của dự án được giữ nguyên; copy thư mục phiên sang vị trí mới nếu muốn nhập lịch sử.

Build hiện tại là macOS arm64. Ad-hoc signing để chạy cục bộ không tương đương Developer ID/notarization. Phát hành công khai cần ký/notarize với tài khoản Apple Developer và kiểm tra trên phiên bản macOS tối thiểu hỗ trợ.

## Danh mục tên/icon ứng dụng

`android-helper/src/com/framelab/AppCatalog.java` đọc label/icon qua PackageManager trong tiến trình ADB shell được cấp quyền, không cài APK. `scripts/build_android_helper.sh` tạo `framelab/assets/app-catalog.dex` (min API 23). `android/catalog.py` đẩy helper tạm lên thiết bị, lấy metadata, xóa file tạm, cache trong bộ nhớ 5 phút; nút Làm mới đọc lại. Thiết bị hạn chế helper sẽ trả package ID và thông báo rõ, không tự tạo tên/icon giả. `static/js/app-picker.js` quản lý danh sách có icon và chế độ tên/package; package ID vẫn là khóa được gửi vào phép đo.
