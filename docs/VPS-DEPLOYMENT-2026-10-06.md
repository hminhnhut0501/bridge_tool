# Triển khai VPS — 2026-10-06

Đã triển khai bản core/UI có 4 bản sửa P1 lên **https://tele.hangcu.shop**, VPS `103.252.93.156`, Ubuntu 24.04, Python 3.12 và rclone 1.75.1.

## Cấu hình đã áp dụng

- Native systemd: `/etc/systemd/system/telegram-vault.service`, user riêng `telegram-vault`, tự khởi động khi boot và restart khi process lỗi.
- Code: `/opt/telegram-vault`; data riêng: `/var/lib/telegram-vault`; env: `/etc/telegram-vault/vault.env`, owner root:telegram-vault, mode 640.
- Backend chỉ lắng nghe `127.0.0.1:8787`. Nginx hiện có proxy riêng domain; cổng 8080 và các domain khác tiếp tục dùng cấu hình cũ.
- HTTPS Let's Encrypt, chứng chỉ ban đầu hết hạn 2027-01-04; certbot timer hoạt động. Đã thêm deploy hook reload Nginx sau renew. HTTP chuyển sang HTTPS, đường dẫn ACME vẫn được phục vụ.
- VPS có khoảng 961 MiB RAM và swap 8 GiB. Service giới hạn MemoryHigh=256 MiB, MemoryMax=384 MiB, CPUQuota=100%, một worker. Đây là ngân sách ban đầu cần đo lại với video thật.
- Storage **gcrypt_kis:** theo lựa chọn người dùng; chỉ copy remote này và dependency vào config riêng mode 600 do service user sở hữu. Không ghi vào cấu hình rclone đang dùng bởi service khác.
- Root dữ liệu `TelegramVault_TEST`, SHA-256 bật, stream, giới hạn download/upload 4 MiB/s. Không tự chuyển sang root production khi chưa nghiệm thu video thật.
- Telegram mode **real**, trạng thái **not_configured**: chưa có API ID/API hash/session. Không chuyển sang mock trên VPS.
- Mật khẩu web được sinh riêng, không dùng mật khẩu SSH. File đăng nhập private trên local: `data/private/vps-deployment/access.txt`. Không đưa vào source/release/báo cáo.

## Kết quả kiểm tra

- SHA-256 archive local và bản upload khớp: `4c2a9d2f33c0af1080ab1d01241623f9f2b5397f4f652e58bf7f51f53e94e443`.
- HTTPS health 200, đăng nhập và logout thành công; cookie Secure/HttpOnly; request không đăng nhập bị 401, mutation thiếu CSRF bị 403.
- Storage check thật bằng API báo **connected** với `gcrypt_kis:`. Đây là kiểm tra truy cập/list, không phải thử upload và xác minh video end-to-end.
- Browser Chromium desktop/mobile pass, không lỗi JavaScript hoặc overflow ngang.
- **8/8 regression P1 pass trực tiếp trên VPS trong 22,70 giây**, dùng DB và local crypt tạm riêng; không ghi video thử lên Drive.
- Restart systemd thật thành công, service enabled; chưa reboot toàn VPS.
- Kiểm tra domain có sẵn `drive.hangcu.shop` và `monitor.hangcu.shop`: đều trả 200 sau triển khai.
- Chứng nhận tự renew được cấu hình; chưa chạy một lần renewal dry-run.

Bằng chứng local: [API](../data/reports/vps/api-smoke.json), [UI](../data/reports/vps/ui-smoke.json), [tests Ubuntu](../data/reports/vps/p1-tests.log), [desktop](../data/reports/vps/desktop.png), [mobile](../data/reports/vps/mobile.png).

## Kết nối Telegram và vận hành

**Cập nhật:** đăng nhập Telegram đã có trên Web UI. Mở [Kết nối Telegram](https://tele.hangcu.shop/#telegram); xem [hướng dẫn mới](TELEGRAM-WEB-LOGIN.md). CLI bên dưới vẫn là lựa chọn thay thế.

Điền `TELEGRAM_API_ID` và `TELEGRAM_API_HASH` vào `/etc/telegram-vault/vault.env` qua kênh riêng. Dừng service trước khi CLI đăng nhập để tránh tranh chấp session/DB:

```sh
systemctl stop telegram-vault
systemd-run --wait --pty --collect \
  -p User=telegram-vault \
  -p WorkingDirectory=/opt/telegram-vault \
  -p EnvironmentFile=/etc/telegram-vault/vault.env \
  /opt/telegram-vault/.venv/bin/telegram-vault login
systemctl start telegram-vault
```

CLI hỏi số điện thoại, OTP và 2FA nếu có. Sau đó thêm một nguồn nhỏ, xác minh video thật giải mã khớp SHA-256 và retry/restart trước khi mở rộng. Ba lỗi P2 trong [báo cáo giả lập](SIMULATION-AUDIT.md) còn tồn tại.

```sh
systemctl status telegram-vault
journalctl -u telegram-vault -n 50 --no-pager
curl -fsS https://tele.hangcu.shop/api/health
```

Không sao chép DB/session mock local lên VPS. Không đưa credentials vào Git hoặc archive source. Cấu hình và dữ liệu runtime trên VPS phải được backup riêng; config crypt chứa khóa cần thiết để phục hồi ciphertext.
