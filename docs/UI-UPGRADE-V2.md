# UI V2 — bản nâng cấp đã triển khai

Ngày 06/10/2026. Thực hiện lần lượt: kiến trúc tác vụ → hệ màu/component → các page → QA local và kiểm tra VPS.

## 1. Tổ chức chức năng

- Sidebar 8 mục; Topics được mở từ nguồn forum, không còn mục riêng trong menu. Giữ URL #topics cũ. Group/channel thường không có nút Topics; truy cập URL cũ không hiện form All media vô nghĩa.
- Truyền & hàng đợi có hai tab Đang truyền và Hàng đợi. Hàng đợi gồm QUEUED/RETRY_WAIT; Cần xử lý mặc định FAILED, có lọc CANCELLED/SKIPPED.
- Thư viện chỉ yêu cầu COMPLETED từ backend, không chứa job chưa xong và không có điều khiển toàn queue.
- Điều khiển phạm vi nguồn/topic mở theo nhu cầu. Pause/Resume phụ thuộc trạng thái; cancel/delete có dialog phạm vi. Đóng dialog sau thành công, giữ lại khi thất bại.
- Hủy/xóa một file nằm trong xác nhận/chi tiết; file COMPLETED không có nút xóa lịch/hủy. Các thao tác chỉ giữ nguyên semantics backend hiện có.

## 2. Thiết kế chung

Neutral navy/gray thay nền xanh; primary blue; completed emerald; verifying violet; warning amber; danger coral. Branding emerald nhỏ. Nút/icon kích thước nhất quán; metadata đọc rõ hơn, input border tách nền. Bỏ eyebrow và mô tả page lặp, thẻ workspace đơn và slogan footer.

Dialog có focus trap, Escape, phục hồi focus. Icon thao tác có title/aria-label. Hỗ trợ reduced motion, dark/light, menu mobile và hàng file mobile có status/dung lượng.

## 3. Các page

- Dashboard: bỏ shield artwork lớn, Việt hóa hoạt động và thuật ngữ vận hành, làm rõ số liệu và tốc độ.
- Sources: bỏ guide thường trực; trạng thái/số file/thao tác chạy giữ trên card; chi tiết quét/bộ lọc và gỡ nguồn mở khi cần. Thông báo thêm nguồn ngắn.
- Topics: chỉ forum; tất cả topic không cần nhiều checkbox; lựa chọn riêng hiện danh sách. Lưu chỉ bật khi dirty; chuyển nguồn nhắc bỏ thay đổi.
- Transfers: tốc độ và % nổi bật; verifying tách màu/tốc độ; bỏ lời giải thích pipe/upload trên mọi card. Search và source filter dùng server, quản lý scope compact.
- Library: completed-only, tìm tên gốc/tên đường dẫn đích toàn bộ dataset trước phân trang; source filter. Bảng giảm cột; chi tiết kỹ thuật mở rộng; copy logical path với xử lý lỗi clipboard.
- Failed: danh sách mục cần can thiệp, thử lại từng mục; error dài mở trong chi tiết.
- Storage: root/cấu trúc đích rõ, mã hóa gọn, giải thích và thiết lập kỹ thuật mở rộng; tác vụ đối chiếu dễ đọc.
- Settings: nhóm Việt hóa, văn bản ngắn; security details đóng mặc định, thanh lưu xuất hiện khi dirty, có hủy thay đổi/loading.
- Telegram: wizard ẩn sau kết nối, guide mở rộng; OTP/2FA giữ flow và API hiện có.
- Login: bỏ nửa màn hình artwork, form tập trung có logo nhỏ.

Polling không hiển thị data thuộc URL cũ khi đổi tab/filter; response cũ trong cùng chu kỳ không ghi đè response mới.

## 4. Kiểm tra

- 65 backend tests pass, gồm search được áp dụng trước pagination, tìm tên đích, kết hợp scope/status và literal ký tự %/_.
- 3 Playwright E2E pass: Telegram auth mô phỏng; backup thật qua crypt sandbox; V2 queue/library, search, xác nhận, focus, mobile và themes. Database/storage riêng, không thử pause/cancel/xóa trên production.
- Build TypeScript/Vite pass; Python Ruff pass.
- Contrast của palette render trong browser: text/panel dark ~16:1, muted/panel ~9.27:1; light ~17.74:1/~7.58:1; chữ trắng/primary ~5.17:1. Đây là các cặp màu chính, không phải chứng nhận mọi pixel/trạng thái đạt accessibility.
- VPS read-only sau login: UI, completed-only API, mobile không overflow, 2 concurrency và bandwidth=0 được giữ.
- Evidence: data/reports/ui-v2 và data/reports/audit-web. Các ảnh v2-transfers dùng fixture minh họa trạng thái; ảnh vps-* dùng dữ liệu thật.

## 5. Ranh giới bản này

Đây là bản V2 đầu tiên của giao diện vận hành. Các hướng sâu hơn trong đánh giá như source drawer nhiều tab, chọn nhiều job tùy ý, sắp xếp tên/ngày tùy chọn, bộ lọc ngày/loại, ánh xạ link object Drive và chỉnh concurrency runtime chưa được bổ sung; không dựng các điều khiển giả chỉ hoạt động trên trang hiện tại. Backend bulk scope hiện tại được giữ. Topics vẫn dùng màn cấu hình riêng mở từ nguồn, chưa gộp thành drawer nhiều tab.

Không đổi đường dẫn/naming backup, encrypted remote, giới hạn tốc độ, khoảng nghỉ, policy nội dung hoặc lịch thực trên VPS để test UI. Restart triển khai ban đầu có thể khiến file đang truyền phải thử lại theo semantics streaming hiện có. Bản sửa UI cuối được thay static assets, không cần restart worker thêm.
