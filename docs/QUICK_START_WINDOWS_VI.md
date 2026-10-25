# Frame Lab — Windows x64 portable

## Mở app

1. Chọn **Extract All / Giải nén tất cả** cho file ZIP.
2. Mở thư mục **Frame Lab Windows** đã giải nén.
3. Nhấp đúp **Mo Frame Lab.cmd**. Trình duyệt mặc định sẽ mở giao diện.
4. Kết nối điện thoại Android bằng USB, bật Gỡ lỗi USB và chấp nhận máy tính trên điện thoại.
5. Quét thiết bị, chọn app rồi bắt đầu đo.
6. Khi dùng xong, bấm **Thoát Frame Lab** trong giao diện. Đóng tab không dừng máy chủ.

Giữ nguyên cấu trúc thư mục; không lấy riêng file CMD hoặc pythonw.exe ra ngoài. Không chạy trực tiếp từ cửa sổ xem nội dung ZIP.

Không cần cài Python, Android Studio hoặc ADB. Gói chứa Python embeddable từ Python.org, ADB và DLL từ Google, cùng giấy phép đi kèm. Khi chạy app không cần tải thêm thư viện từ Internet.

## Yêu cầu và giới hạn

- Mục tiêu: Windows 10/11 x64 (máy Intel/AMD 64-bit). Chưa xác thực ARM64/Windows 32-bit.
- Gói được lắp ráp trên macOS, **chưa chạy thử trực tiếp trên Windows**. Không coi đây là bản Windows đã kiểm thử đầy đủ.
- Một số điện thoại cần USB driver của hãng để ADB nhận thiết bị. Nếu không thấy điện thoại, kiểm tra cáp truyền dữ liệu, USB driver và hộp thoại cấp quyền trên điện thoại.
- Chưa có chữ ký số của nhà phát triển. Chính sách của Windows/máy công ty có thể chặn CMD; không thay đổi chính sách bảo mật để chạy app. Khi cần, nhờ quản trị viên duyệt gói hoặc dùng bản được ký phù hợp.
- Render: mẫu gfxinfo và trace thô trên thiết bị hỗ trợ. Chưa bảo đảm độ bao phủ toàn phiên.
- Bitmap: **chưa hỗ trợ đo riêng**, không dùng tổng RAM thay thế.

## Dữ liệu và xử lý lỗi

- Báo cáo: `%LOCALAPPDATA%\Frame Lab\reports\`
- Log: `%LOCALAPPDATA%\Frame Lab\app.log`
- Lỗi khởi động: `%LOCALAPPDATA%\Frame Lab\startup-error.log`
- Web: `http://127.0.0.1:8765` hoặc một cổng tiếp theo đến 8774.
- Có thể mở **Kiem tra loi.cmd** để xem tiến trình trong cửa sổ dòng lệnh.
- Tất cả dữ liệu được lưu cục bộ; APK và báo cáo không được gửi lên mạng.

Để chia sẻ, gửi nguyên ZIP. Không gửi thư mục báo cáo cá nhân.
