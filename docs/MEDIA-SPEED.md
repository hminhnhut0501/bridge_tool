# Kiểm tra tốc độ truyền — 2026-10-06

VPS không có giới hạn download/upload trong runtime (cả hai bằng 0), không FloodWait và không CPU throttling khi kiểm tra. Khoảng nghỉ file chỉ xảy ra sau khi hoàn thành. UI đang hiển thị tốc độ trung bình từ đầu file, bao gồm thời gian chờ pipeline.

Điểm nghẽn đã sửa: mỗi chunk 512 KiB trước đây dùng chung lock của các RPC metadata và phải nghỉ thêm request_pace (0,5 giây) sau mỗi lần đọc. Scanner cạnh tranh với luồng tải. Chunk nay có lock riêng, chạy tuần tự theo backpressure của pipe, không có khoảng nghỉ metadata nhân tạo. Metadata vẫn giữ pacing; deadline và lịch sử FloodWait được dùng chung, kể cả cooldown sau FloodWait lặp lại. Không tăng số worker hoặc thay khoảng nghỉ 5–60 giây.

Đo production trước sửa: UI 291 KiB/s, API khoảng 267 KiB/s. Sau sửa: khoảng 676 KiB/s trên cửa sổ đo 31,8 giây (tăng từ 2 MiB lên 23 MiB), đoạn cuối khoảng 811 KiB/s. Đây là pipeline thực tế, không phải benchmark độc lập Telegram hoặc Drive và không đảm bảo tốc độ cố định. VPS có tác vụ rclone khác cùng sử dụng mạng; chưa can thiệp những tác vụ đó. Không thể quy toàn bộ độ chậm còn lại cho một bên từ dữ liệu hiện có.

Restart để áp dụng làm transfer chưa hoàn thành tải lại từ đầu theo thiết kế hiện tại. Snapshot trước sửa trong /var/backups/telegram-vault/before-media-speed-*.

50 bài kiểm thử backend pass; 2 regression pacing/FloodWait pass trên VPS. Bằng chứng: data/reports/media-speed/.
