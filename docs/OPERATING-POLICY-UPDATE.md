# Điều chỉnh vận hành theo đánh giá chính sách — 2026-10-06

Đã cập nhật local và VPS `https://tele.hangcu.shop`.

## Thay đổi

- Tên sản phẩm trên UI, HTML title, API title và CLI: **Vault Bridge**. Màn hình đăng nhập công khai nêu rõ đây là ứng dụng độc lập sử dụng Telegram API, không phải sản phẩm chính thức của Telegram. Tên binary, service, thư mục và session giữ nguyên để không đổi dữ liệu runtime.
- Thêm checkbox xác nhận quyền sao chép nội dung khi chọn nguồn. Backend từ chối thêm nguồn nếu thiếu xác nhận; ghi timestamp xác nhận và event. Đây là xác nhận của người dùng, không phải kiểm chứng giấy phép hoặc bảo đảm tuân thủ.
- Nguồn được thêm qua app ở trạng thái **tạm dừng**, kể cả khi khôi phục nguồn qua thao tác thêm. Người dùng chọn topics/bộ lọc, sau đó nhấn **Tiếp tục**. Scanner/claim không chạy nguồn paused; live metadata vẫn có thể được ghi để tránh mất sự kiện.
- Default và cấu hình VPS: một worker, download/upload 1 MiB/s, nhịp thao tác được điều tiết ít nhất 0,5 giây. Đây là giới hạn vận hành tự chọn, không phải quota được Telegram chứng nhận. Nhịp thực tế có thể tăng sau FloodWait.
- Nếu có 3 FloodWait trong cửa sổ 1 giờ, app chờ ít nhất 1 giờ hoặc thời gian Telegram yêu cầu, lấy mức dài hơn. Lịch sử và deadline được persist, không reset khi khởi động lại. Không quay vòng tài khoản/IP hoặc bỏ qua giới hạn.
- Trang Cài đặt hiển thị nhịp thao tác, số worker và hướng dẫn bắt đầu với nguồn nhỏ. Không cung cấp cam kết “không bị khóa”.

## Phần không thay đổi theo yêu cầu người dùng

Không thêm bộ lọc nội dung chống lưu/chuyển tiếp (`noforwards`) hoặc TTL/tự hủy. Chính sách lưu giữ backup khi message/nguồn bị xóa giữ nguyên. Vì vậy bản cập nhật này **không được xem là chứng nhận tuân thủ đầy đủ Telegram API Terms**, đặc biệt nếu sau này chọn nguồn chứa những loại nội dung đó.

Không đổi khóa crypt, remote `gcrypt_kis`, root TEST, Telegram API/session hoặc mật khẩu web. Không tự pause nguồn hiện đang chạy chỉ vì nâng cấp; thao tác thêm nguồn mới có hành vi paused như trên.

## Kiểm thử và triển khai

- E2E 2/2 pass: wizard đăng nhập và luồng thêm nguồn/xác nhận quyền/topics/resume/crypt job/UI desktop-mobile.
- Hai regression mới pass trên Ubuntu VPS: API bắt buộc xác nhận quyền + nguồn mới paused; repeated FloodWait cooldown được giữ qua controller restart.
- **41/41 backend test pass trong 29,63 giây**; test crash dùng upload unlimited trong fixture riêng để kiểm chứng SIGKILL/restart trong timeout ngắn, không phụ thuộc default production 1 MiB/s. Production vẫn giữ giới hạn tải đã nêu.
- VPS health 200, Nginx và service active, kiểm tra authenticated settings xác nhận giới hạn thực tế. Env và rclone config giữ mode private.
- Snapshot code/DB trước update nằm trong `/var/backups/telegram-vault/before-policy-*`.

Bằng chứng: [VPS settings](../data/reports/operating-policy/vps-settings.json), [tests VPS](../data/reports/operating-policy/vps-tests.log), [backend](../data/reports/operating-policy/backend-tests.log), [E2E](../data/reports/operating-policy/e2e.log).

## Sử dụng

Chọn nguồn nhỏ mà bạn sở hữu hoặc được phép sao chép, xác nhận quyền, đặt topics/date/size filter phù hợp rồi nhấn Tiếp tục. Chỉ mở rộng phạm vi sau khi quan sát tải, lỗi và FloodWait. Mã hóa trên Drive không thay thế quyền sao chép nội dung. Giới hạn tài nguyên và xử lý FloodWait không đảm bảo tài khoản/API sẽ không bị Telegram hạn chế.

Nguồn tham chiếu: [Telegram API Terms](https://core.telegram.org/api/terms), [Content Licensing](https://telegram.org/tos/content-licensing), [API error handling](https://core.telegram.org/api/errors).
