# Quy tắc tên file

Từ bản cập nhật này tên trước mã hóa dùng mẫu `YYMMDD_G<first_message_id>-<index>_<original_stem>_<short_caption>.<ext>` cho album; file riêng dùng `YYMMDD_M<message_id>_<original_stem>_<short_caption>.<ext>`.

Ngày theo Asia/Ho_Chi_Minh. G là ID tin nhắn đầu tiên còn truy cập được của album, không phải grouped_id 64-bit nội bộ Telegram. Index từ 01 theo thứ tự message ID. Scanner lấy các tin nhắn lân cận để xác định album và cache tối đa 512 album; không đánh số lại theo batch lịch sử hoặc bộ lọc file. Caption riêng được ưu tiên; nếu trống lấy caption chung đầu tiên của album. Caption không có thì bỏ hậu tố caption. Tên và caption loại ký tự không hợp lệ, chuẩn hóa Unicode và rút gọn theo giới hạn UTF-8 (stem 100 byte, caption 80 byte). Extension giữ ở cuối và viết thường.

Thư mục vẫn là TelegramVault_TEST/Telegram/Group/[Topic]/, không có Năm/Tháng. Google Drive qua crypt vẫn hiển thị tên đã mã hóa. File thay nội dung nhưng trùng tên được thêm hậu tố R<revision> để không ghi đè backup cũ.

Áp dụng cho metadata mới; job cũ chưa từng bắt đầu sẽ được lấy metadata và đổi tên ngay trước lần tải đầu tiên. File đã bắt đầu hoặc đã hoàn thành không đổi tên. Bổ sung nhận diện photo ID và stream ảnh để tên .jpg có thể áp dụng khi bộ lọc nguồn cho phép. Bộ lọc loại file và kích thước hiện tại không tự thay đổi.

55 test backend và 3 regression naming trên VPS pass; gồm mẫu album/file riêng, ngày địa phương, extension, sanitization và caption chung/thứ tự album.
