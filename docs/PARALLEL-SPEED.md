# Tối ưu tải song song — 2026-10-06

Triển khai tối đa 8 lane đọc các khối 512 KiB của cùng file bằng offset/stride, trả dữ liệu đúng thứ tự cho rclone crypt. Mỗi lane chỉ đọc trước một khối, không lưu plaintext vào disk hoặc giữ toàn bộ file trong RAM. Lane được nạp lại khi chunk trước được tiêu thụ, không phải chờ cả batch. Khi lỗi hoặc hủy, hủy task đang đọc và đóng toàn bộ iterator.

Bổ sung cryptg 0.6.0 để Telethon dùng mã hóa native; dependency được pin trong pyproject.toml và requirements.lock. Khối upload Drive tăng từ 8 lên 32 MiB. Chunk Telegram vẫn 512 KiB và tuân thủ hợp đồng stream bounded. Service thực tế dùng khoảng 135 MiB RAM trong lần đo; giới hạn systemd giữ nguyên.

Metadata vẫn có request pacing; các lane media dùng chung deadline FloodWait và cooldown lặp lại. Không tăng concurrency file, không bỏ nghỉ 5–60 giây giữa các file và không thay khóa crypt hoặc storage remote.

Đo production: trước các tối ưu khoảng 267–291 KiB/s. Sau bản song song khoảng 1,2 MiB/s trung bình; có đoạn gần 2 MiB/s. Số UI là trung bình từ đầu file, có startup và backpressure Drive. Không đảm bảo tốc độ cố định hoặc coi đây là benchmark riêng của Telegram/Drive. VPS có workload mạng khác không thuộc service này.

52 backend test pass. Regression kiểm chứng peak 8 lane, thứ tự byte chính xác, tail không đủ chunk và cleanup khi dừng stream. Production không còn lỗi transfer trong cửa sổ đo; file thực vẫn cần hoàn thành upload/xác minh trước khi đánh dấu COMPLETED. Các lần restart cập nhật tải lại transfer chưa hoàn thành từ đầu.

Bằng chứng trong data/reports/parallel-speed/. Snapshot trước sửa tại /var/backups/telegram-vault/before-parallel-*.
