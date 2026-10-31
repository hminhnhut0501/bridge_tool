# Đăng nhập Telegram trên Web UI — 2026-10-06

Đã cập nhật core và UI trên **https://tele.hangcu.shop/#telegram**. Đăng nhập web bằng tài khoản quản trị, sau đó mở **Kết nối Telegram** trong menu; nếu chưa thấy mục mới, refresh trang. Mobile mở menu bằng biểu tượng góc trên trái.

## Các bước

1. Mở [my.telegram.org/apps](https://my.telegram.org/apps), đăng nhập và vào API development tools để lấy API ID/API hash. Điền cả hai vào trang Kết nối Telegram và chọn **Lưu API và tiếp tục**.
2. Nhập số điện thoại quốc tế, ví dụ `+84901234567`, chọn **Gửi mã đăng nhập**. Kiểm tra ứng dụng Telegram hoặc SMS theo kênh Telegram sử dụng.
3. Nhập OTP, chọn **Xác nhận mã OTP**. Nếu tài khoản bật xác minh hai bước, nhập mật khẩu Telegram 2FA và chọn **Kết nối tài khoản**.
4. Khi hiện **Telegram đã kết nối**, chọn **Chọn nguồn Telegram**, xác nhận quyền sao chép, thêm group và chọn topics/bộ lọc cần backup, sau đó quay lại Nguồn và nhấn Tiếp tục. Nguồn mới mặc định tạm dừng.

Đừng gửi OTP hoặc mật khẩu 2FA vào chat. Mật khẩu quản trị web và mật khẩu Telegram 2FA là hai thông tin khác nhau.

## Xử lý tình huống

- OTP sai: sửa mã và thử lại; session quản trị web không bị đăng xuất.
- OTP hết hạn hoặc server restart giữa chừng: bắt đầu lại với mã mới. Chỉ gửi lại sau ít nhất 60 giây.
- Tối đa 5 lần gửi OTP/2FA để xác minh mỗi challenge; quá giới hạn phải chờ 60 giây và yêu cầu mã mới.
- FloodWait: UI hiển thị thời gian chờ; mọi thao tác Telegram dùng chung deadline lưu trong DB.
- Một session quản trị khác đang đăng nhập: session đó hoàn thành, hủy hoặc hết hạn trong 10 phút trước khi bạn bắt đầu.
- Ngắt kết nối: tạm dừng các nguồn và chờ transfer kết thúc trước khi xác nhận. Session Telegram được đăng xuất; backup vẫn được giữ.
- Đổi tài khoản: xóa các nguồn cũ trước khi kết nối tài khoản khác. Có kiểm tra account ID lúc đăng nhập và lúc phục hồi session để tránh chạy nguồn cũ bằng nhầm tài khoản.

## Lưu trữ và vận hành

API ID/API hash được ghi atomically vào `DATA_DIR/telegram-api.json`, mode 600, ưu tiên hơn giá trị API trong env. OTP/2FA chỉ dùng trong RAM, không lưu vào DB/config/log ứng dụng. REST không trả API hash, phone đầy đủ, code hash hoặc bytes session. Login challenge chỉ tồn tại trong process, gắn với session quản trị khởi tạo; session Telegram đã đăng nhập được lưu riêng và tiếp tục hoạt động sau restart.

Không tạo TelegramClient thứ hai cho web: dùng client/provider của engine. Maintenance reconnect và auth dùng chung operation lock; auth theo account-wide pacing/FloodWait. Mọi endpoint cần session quản trị, CSRF và origin hợp lệ. Lỗi validation không trả lại submitted input có thể chứa bí mật.

VPS giữ env và rclone config cũ; đã snapshot code/DB trước update vào `/var/backups/telegram-vault/`. Package Python dùng quyền đọc thông thường, credentials vẫn private. Khi cập nhật tiếp, cài package với umask 022, sau đó dùng 077 cho các thao tác tạo secrets; không áp dụng chmod public cho thư mục data/env.

## Kiểm chứng

- **39/39 backend test pass**, 29,62 giây, gồm P1 regression, crash/restart và 9 test auth mới.
- **2/2 Playwright E2E pass**: UI hiện có và wizard API → phone → OTP sai → OTP đúng → 2FA → connected. Các request Telegram trong wizard được giả lập; không gửi OTP thật.
- **9/9 test auth pass trên Ubuntu VPS**, 8,45 giây, Telethon client giả lập với DB tạm riêng.
- Smoke trên domain thật: HTTPS health 200, endpoint auth không đăng nhập trả 401, menu/form API hiển thị trên desktop/mobile, không lỗi JavaScript hoặc overflow ngang.
- Chưa hoàn tất đăng nhập tài khoản Telegram thật vì API ID/API hash/OTP chưa được cung cấp. Người dùng nhập trực tiếp trên web; không gửi qua chat.
- Ba lỗi P2 F04/F06/F07 trong báo cáo đối kháng vẫn ngoài phạm vi thay đổi này.

Bằng chứng: [backend](../data/reports/telegram-web/backend-tests.log), [E2E](../data/reports/telegram-web/e2e.log), [test VPS](../data/reports/telegram-web/vps-auth-tests.log), [UI smoke](../data/reports/telegram-web/vps-ui-smoke.json), [desktop](../data/reports/telegram-web/vps-telegram-desktop.png), [mobile](../data/reports/telegram-web/vps-telegram-mobile.png).

Tham khảo API chính thức: [Telegram API ID](https://core.telegram.org/api/obtaining_api_id), [Telethon authentication](https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.auth.AuthMethods.sign_in).
