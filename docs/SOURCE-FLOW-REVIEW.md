# Đánh giá và nâng cấp luồng backup

## Điểm gây rối trước đây

1. Nguồn được tạo ở trạng thái paused nhưng người dùng không có một bước tiếp theo nổi bật; thông báo thành công dễ bị hiểu là backup đã chạy.
2. Nút Quét vẫn hoạt động khi paused; chỉ đặt scan_requested, nên không thực sự quét. Badge Active/Paused không diễn đạt quét, chờ, truyền hay giới hạn chờ.
3. Tiến độ tin nhắn và file nằm ở nhiều trang. Không có file không phân biệt được chưa chạy với đã quét nhưng bộ lọc không khớp. Nguồn vừa thêm có thể ở ngoài trang đầu.
4. Trạng thái global pause có thể chặn cả nguồn mới; người dùng bấm tiếp tục nguồn nhưng hệ thống vẫn dừng.

## Luồng hiện tại

Dán link, xác nhận quyền, chọn **Thêm và bắt đầu backup**: app mở nguồn, yêu cầu quét, tự xếp hàng và truyền file. Nếu cần chọn topics, ngày, loại file hoặc kích thước trước, chọn **Thêm để cấu hình**; nút màu xanh trên thẻ nguồn là bước bắt đầu rõ ràng. Default API vẫn tạo nguồn paused để không đổi hành vi client cũ; start=true là hành động chủ động mới.

Sau khi thêm, chuyển đến trang chứa nguồn đó, tự cuộn và làm nổi bật nguồn mới. Trên mobile nguồn không bị khuất phía dưới các thông báo.

Thẻ nguồn hiển thị phase có lời hướng dẫn: chưa bắt đầu, paused, global paused, chờ kết nối Telegram, chưa chọn topics, lỗi quét, đã lên lịch quét, đang quét, đang truyền, có hàng đợi, cần xử lý hoặc theo dõi file mới. Hiển thị loại file/topic đang áp dụng, tin nhắn đã kiểm tra, mốc ID quét, số file chờ/hoàn thành, file đang truyền và tốc độ. Mốc ID không phải tỷ lệ phần trăm vì lịch sử Telegram có thể bị xóa hoặc thiếu ID. Thanh phần trăm là tỷ lệ backup hoàn tất, có nhãn riêng.

Quét và truyền có thể diễn ra đồng thời; không bắt người dùng chờ quét xong mới bắt đầu truyền. Liên kết Đang truyền, Thư viện backup và Cần xử lý nằm ngay trên thẻ. Quét lại bị vô hiệu hóa khi paused/global paused hoặc đã có scan_requested; API trả hướng dẫn 409 thay vì âm thầm đặt lịch bị chặn. Global pause có banner và nút Tiếp tục toàn hệ thống; nguồn paused riêng vẫn giữ trạng thái riêng.

Nguồn không có file phù hợp sau khi quét được hướng dẫn kiểm tra bộ lọc. Topics chỉ hiện cho nguồn forum. Bộ lọc có nhãn thay vì chỉ một icon dấu ba chấm. Thông báo thành công thêm nguồn phân biệt đã yêu cầu bắt đầu với chưa chạy. Khởi động lại không tự mở nguồn đang paused.

## Kiểm thử và triển khai

63 backend, 2 E2E và 2 regression luồng nguồn trên VPS pass. E2E kiểm tra thêm qua link và bắt đầu ngay, cấu hình nguồn, topics, queue controls, desktop/mobile và không tràn màn hình. Regression API kiểm tra ready/scan queued/scanning/watch, thông tin file đang truyền, start=true và global pause, từ chối scan trên nguồn paused. Chỉ test trên DB/crypt riêng; không mở chạy nguồn production để thử.

Đã triển khai local và https://tele.hangcu.shop. Evidence trong data/reports/source-flow/. Snapshot trước deploy tại /var/backups/telegram-vault/before-source-flow-*. Cấu hình hai file song song, nghỉ giữa các file, crypt remote, tên file và folder giữ nguyên.
