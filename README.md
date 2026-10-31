# Vault Bridge

Đã [khắc phục 4 lỗi P1](docs/P1-REMEDIATION.md) và kiểm thử hồi quy.
Ba lỗi P2 trong [báo cáo giả lập](docs/SIMULATION-AUDIT.md) vẫn còn; tích hợp thật và VPS chưa nghiệm thu.

Service backup video Telegram → bounded stream → rclone crypt → encrypted storage.
Core Python/FastAPI + SQLite WAL, Web UI React/TypeScript. Một process, một tài
khoản Telegram, mặc định một worker; không cần Redis.

Ứng dụng độc lập sử dụng Telegram API; không liên kết với hoặc được Telegram bảo chứng.

Đã [điều chỉnh tên sản phẩm và giới hạn vận hành](docs/OPERATING-POLICY-UPDATE.md). Nguồn mới cần xác nhận quyền sao chép và nhấn Tiếp tục sau khi chọn phạm vi.

## VPS

Đã triển khai tại **https://tele.hangcu.shop** với storage `gcrypt_kis:`.
Mở **Kết nối Telegram** để nhập API, số điện thoại, OTP và 2FA ([hướng dẫn](docs/TELEGRAM-WEB-LOGIN.md)); [báo cáo triển khai](docs/VPS-DEPLOYMENT-2026-10-06.md).

## Bản local đã chuẩn bị

Mở **http://127.0.0.1:8787**. Tài khoản/mật khẩu nằm trong file private
`data/local-access.txt`; mật khẩu không nằm trong source. Bản đang chạy dùng
**Telegram mock + rclone crypt thật trên local**, và UI ghi rõ TEST mode.
Thêm nguồn, chọn topics, bật backup; job được scanner/worker xử lý trên backend.

```sh
.venv/bin/telegram-vault serve --port 8787
```

Không chạy hai service cùng DB. Mật khẩu có thể đổi bằng
`.venv/bin/telegram-vault init-admin`; các phiên web cũ sẽ bị thu hồi.

## Cài trên máy khác

Python 3.11+, Node 22+, rclone 1.75.1. Chạy từ thư mục repository.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/pip install --no-deps -e .
cd frontend
npm ci
npm run build
cd ..
```

Để tạo local test mới (chỉ khi chưa có `.env`):

```sh
.venv/bin/python scripts/setup_local.py
.venv/bin/telegram-vault serve
```

Script tạo config crypt local độc lập, mật khẩu web ngẫu nhiên và `.env` riêng tư.
Không sửa remote của người dùng. Giữ `data/local-crypt/rclone.conf` để giải mã
các file test; không upload thư mục data cùng source.

## Chuyển sang Telegram / Google Drive thật

1. Chọn DATA_DIR/DB mới cho account thật để không trộn với dữ liệu mock; chạy
   init-admin cho DB mới. Đổi `.env`: `TELEGRAM_MODE=real`, API ID/hash từ https://my.telegram.org,
   đường dẫn session và `RCLONE_CONFIG` tới config crypt của bạn. File config phải
   chmod 600. CLI tự đọc `.env`; biến environment đang có được ưu tiên.
2. Dừng service, chạy `.venv/bin/telegram-vault login` trong terminal để nhập
   phone/OTP/2FA và persist session. Khởi động lại service.
3. Dùng `STORAGE_ROOT=TelegramVault_TEST` cho lần nghiệm thu đầu, discover group,
   chọn một TEST group có video bạn được phép truy cập.
4. UI Add Source → Topics → Enable. Scanner đi theo batch; job và checkpoint
   persist trong SQLite. Chọn root production riêng **trước khi** tạo DB/source
   production, không đổi root của DB đã có media.

Telegram/Drive thật và Docker trên Linux chưa được nghiệm thu tại máy này vì
chưa có credentials/Docker daemon. Test local không thay thế phép nghiệm thu đó.

## Tính năng core và UI

- Discover group/supergroup/forum, topics phân trang; lịch sử incremental,
  listener message mới/edit và recent reconciliation.
- Dedupe `(chat_id, message_id, media_index, telegram_file_id)`; media revision
  giữ bản cũ. Name dùng display/path, không làm identity.
- Persistent priority/fair queue; pause/resume/rescan, filters kích thước/ngày/topics.
- Streaming 512 KiB chunks với pipe backpressure, không full-file plaintext spool.
- SHA-256 trong stream; stat, decrypted hash, promotion và final verification.
- FloodWait account-wide persist qua reboot; retries backoff+jitter, cancel/recovery.
- Login Argon2id, HttpOnly/SameSite cookie, CSRF, rate limit; HTTPS secure cookie
  khi deploy. API cursor pagination, event history, resource/transfer metrics.
- Dashboard, Sources, Topics, Transfers, Library, Failed, Storage, Settings;
  dark/light, responsive desktop/mobile. Không fake Google progress độc lập.
- DB snapshot hằng ngày, retention 14 bản; reconcile không xóa object lạ.

MVP hiện hỗ trợ **stream mode**. Cache/adaptive transfer, lịch chạy, notifications
và tích hợp Encrypted Web Drive là các phase tiếp theo, chưa bật trong sản phẩm.

## CLI

```sh
telegram-vault login
telegram-vault serve
telegram-vault init-admin
telegram-vault status
telegram-vault scan --source 1
telegram-vault scan --source 1 --full
telegram-vault retry-failed
telegram-vault reconcile
telegram-vault backup-db
telegram-vault doctor
```

`reconcile` CLI yêu cầu service đã dừng; khi service chạy dùng Storage → Reconcile.
`doctor` chỉ kiểm tra read-only rclone crypt; trạng thái app/SQLite/account xem ở UI.
POC `synthetic` và `poc CHAT_ID MESSAGE_ID` vẫn khả dụng, luôn giới hạn TEST root.

## Kiểm thử

```sh
.venv/bin/pip install -r requirements-dev.txt
RCLONE_CONFIG="$PWD/data/local-crypt/rclone.conf" .venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check telegram_vault scripts tests
cd frontend
npm run build
npx playwright install chromium
npx playwright test
cd ..
.venv/bin/python scripts/history_benchmark.py
```

E2E dùng bản local ở cổng 8787 và credentials file; không chạy trên production.
Benchmark lịch sử sinh metadata lazy, không gọi Telegram hoặc Google. POC 10 GiB
đã đo riêng; payload ciphertext test được xóa sau phép đo, báo cáo vẫn giữ.

Xem [implementation report](docs/IMPLEMENTATION-REPORT.md),
[deployment](docs/DEPLOYMENT.md), [architecture](docs/ARCHITECTURE.md) và
[backup/recovery](docs/BACKUP-RECOVERY.md).

Cấu hình nghỉ giữa các file: [hướng dẫn](docs/FILE-REST.md).
