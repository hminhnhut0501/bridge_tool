# Thao tác nhanh với lịch backup

Trong **Đang truyền**, **Thư viện backup** và **Cần xử lý**, chọn phạm vi tất cả nguồn, một group hoặc một topic rồi dùng thanh Thao tác nhanh. Thao tác áp dụng cho toàn bộ job trong phạm vi, không chỉ trang đang xem.

- **Tạm dừng**: chặn lập lịch/scanner và dừng transfer trong phạm vi, giữ hàng đợi. Transfer bị dừng chuyển RETRY_WAIT; tiếp tục tải lại từ đầu. Tiếp tục toàn hệ thống mở global gate; nguồn đã paused riêng vẫn giữ trạng thái paused riêng.
- **Tiếp tục**: mở phạm vi đã dừng. Topic được chọn lại và quét lịch sử để bắt kịp nội dung bỏ lỡ. Job CANCELLED không tự retry; dùng Retry từng job nếu cần.
- **Hủy**: dừng phạm vi và chuyển các job chưa hoàn thành thành CANCELLED. Bản ghi còn để xem hoặc retry. Scanner/live không tiếp tục lập lịch trong phạm vi đã dừng.
- **Xóa lịch**: dừng phạm vi, hủy transfer rồi xóa job chưa hoàn thành. Với tất cả, lịch toàn hệ thống tạm dừng và nguồn vẫn còn; với group, nguồn được gỡ; với topic, topic bỏ chọn. Backup COMPLETED và file trên Drive giữ nguyên.
- **Xóa job**: nút thùng rác trên dòng hoặc trong Chi tiết job trên mobile. Hủy transfer nếu cần, xóa job và lịch sử transfer của job đó. Metadata media giữ lại để scanner không tự tạo lại job cùng file. Không gọi lệnh xóa file trên Drive, kể cả incomplete.

Khi thao tác một topic trong nguồn Backup tất cả topics, app chuyển sang chọn riêng: các topic hiện có khác giữ selected, topic được thao tác được bật/tắt riêng. Topic mới sau đó cần chọn bằng UI. Không xóa group/topic trên Telegram.

Các hành động dừng/xóa có hộp xác nhận ghi rõ phạm vi. Backend chờ worker cleanup trước khi xóa, xử lý cả trường hợp task bị hủy trước khi chạy. Trạng thái global pause persist trong SQLite qua restart; scanner/claim dùng cùng gate.

Kiểm thử: 60 backend, 2 E2E và 5 regression trên VPS pass. E2E bao gồm pause/resume toàn hệ thống, hủy/xóa lịch topic và giữ backup đã hoàn thành; bộ DB/crypt riêng, không hủy/xóa lịch production để thử. UI desktop/mobile đã kiểm tra. Evidence tại data/reports/queue-controls/. Snapshot trước deploy trong /var/backups/telegram-vault/before-queue-controls-*.
