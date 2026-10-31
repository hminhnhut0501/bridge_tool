# Nghỉ ngẫu nhiên giữa các file

Đã triển khai local và https://tele.hangcu.shop ngày 2026-10-06.

Trong **Cài đặt → Transfers & retry**, bật/tắt nghỉ giữa các file và chỉnh thời gian tối thiểu/tối đa. Mặc định bật, khoảng **5–60 giây**; chấp nhận 0–3600 giây và tối thiểu không lớn hơn tối đa. Dashboard hiển thị thời gian nghỉ còn lại.

Sau khi upload và xác minh thành công, app chọn ngẫu nhiên thời gian trong khoảng đã cấu hình rồi chặn lấy file tiếp theo. Lỗi tải không kích hoạt nghỉ thành công; retry và FloodWait vẫn áp dụng. Deadline được ghi cùng transaction hoàn thành file, giữ qua restart. Timer dùng chung cho các worker; file đang chạy được phép hoàn tất. Scanner vẫn hoạt động trong lúc nghỉ.

Đổi khoảng nghỉ áp dụng từ lần hoàn thành tiếp theo. Tắt tính năng xóa deadline hiện tại; worker có thể lấy file tiếp theo ở lần kiểm tra kế tiếp (khoảng 0,5 giây), nếu không còn điều kiện chờ khác. Các trường API mới là tùy chọn để client cũ không ghi đè cấu hình đã lưu.

Env: FILE_PAUSE_ENABLED=true, FILE_PAUSE_MIN_SECONDS=5, FILE_PAUSE_MAX_SECONDS=60. Cấu hình lưu qua UI được ưu tiên. Cấu hình tốc độ đang có được giữ nguyên; nghỉ ngẫu nhiên không bảo đảm tài khoản không bị Telegram hạn chế.

Sửa kèm kiểm tra readiness để tác vụ reconcile phụ không làm health báo lỗi sai.

Kiểm thử: **45 backend, 2 E2E và 4 regression trên VPS đều pass**. Bao gồm hoàn thành/xác minh, lỗi tải, deadline qua mở lại DB, validate/persist cấu hình, client cũ, tắt nghỉ và readiness. E2E dùng storage crypt/DB riêng; không tải file thử lên Drive production.

Bằng chứng trong `data/reports/file-rest/`: backend-tests.log, e2e.log, vps-tests.log, vps-settings.json. Snapshot trước cập nhật trong `/var/backups/telegram-vault/before-file-rest-*`.
