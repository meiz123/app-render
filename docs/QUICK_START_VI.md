# Frame Lab 0.2 — macOS Apple Silicon

1. Giải nén ZIP, kéo **Frame Lab.app** vào Applications hoặc một thư mục bạn muốn.
2. Mở **Frame Lab.app**. Giao diện tự mở trong trình duyệt mặc định.
3. Kết nối Android bằng USB, bật Gỡ lỗi USB và chấp nhận máy tính trên điện thoại.
4. Bấm Quét thiết bị, chọn app hoặc cài APK, bắt đầu đo và thao tác trên điện thoại.
5. Xem lịch sử, tải báo cáo và trace từ giao diện web.
6. Bấm **Thoát Frame Lab** trên giao diện sau khi phiên đo kết thúc. Chỉ đóng tab không dừng máy chủ.

Không cần cài Python, Android Studio hay ADB: bản macOS này chứa Python và ADB cùng thông báo giấy phép.

## Nơi lưu dữ liệu

- Báo cáo: `~/Library/Application Support/Frame Lab/reports/`
- Nhật ký khởi động: `~/Library/Application Support/Frame Lab/app.log`
- Địa chỉ: `http://127.0.0.1:8765` hoặc một cổng trống trong 8766–8774.
- App chỉ truy cập cục bộ, không tải APK hoặc báo cáo lên mạng.

## Phạm vi và giới hạn

- Bản này dành cho Mac chip Apple (M1/M2/M3/M4 hoặc mới hơn), chưa có bản Windows/Intel.
- App là bản thử nội bộ, chưa có chứng chỉ Developer ID và chưa được Apple notarize. macOS có thể chặn khi nhận từ Internet; không coi đây là bản phân phối đã được Apple xác minh. Nếu chính sách máy chặn, cần bản được ký/notarize từ nhà phát triển.
- Render: thống kê mẫu gfxinfo, trace Perfetto thô trên thiết bị hỗ trợ; chưa bảo đảm bao phủ toàn phiên.
- Bitmap: **chưa hỗ trợ đo riêng**, không lấy tổng RAM thay thế.
- Chưa xác thực trên thiết bị Android thật trong môi trường hiện tại.
- Dừng lấy mẫu không dừng ngay trace Perfetto; đợi thời lượng đã đặt để lưu trace xong.
- APK cùng package/chữ ký có thể cập nhật bản đã cài; dữ liệu APK tạm được xóa sau cài đặt.

Khi gửi cho người khác, gửi file ZIP và hướng dẫn này. Không gửi thư mục báo cáo cá nhân.
