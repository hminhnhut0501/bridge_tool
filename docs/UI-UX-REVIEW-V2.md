# Vault Bridge — đánh giá UI/UX vòng 1 và thiết kế nâng cấp V2

Ngày: 06/10/2026. Phạm vi: 4 ảnh người dùng cung cấp và mã giao diện hiện tại main.tsx/style.css, gồm toàn bộ page. Đây là đánh giá chuyên môn dựa trên ảnh và cấu trúc code; chưa phải kết quả thử nghiệm người dùng hoặc đo accessibility bằng browser. Vòng này không thay giao diện hay triển khai production.

## 1. Kết luận và nguyên nhân

Giao diện đã có nhiều chức năng nhưng thiếu thứ bậc thông tin. Thêm từng chức năng bằng panel, banner và đoạn giải thích khiến các thao tác phụ cạnh tranh với nội dung chính. Cần thiết kế lại hệ component và kiến trúc điều hướng trước khi trang trí riêng từng page.

Các vấn đề nhìn thấy trực tiếp:
- Màu nền, sidebar, panel, input và hover đều pha xanh. Accent xanh lá còn dùng cho logo, menu, file icon, thành công, progress và nút chính. Không rõ đâu là hành động chính, đâu là trạng thái.
- Khối “Thao tác nhanh” chiếm phần lớn vùng đầu màn hình Đang truyền/Thư viện. Trong khi chỉ có 2 file chạy, người dùng phải đi qua một bảng điều khiển lớn trước khi thấy file.
- Heading gồm eyebrow tiếng Anh, tên page và mô tả dài, tạo khoảng cách lớn trước nội dung. Breadcrumb và heading lặp ý.
- Panel, nền panel và border gần nhau; nhiều vùng đều có cùng mức nhấn. Chữ phụ nhỏ, màu nhạt dù chứa thông tin vận hành quan trọng.
- Hai card truyền file kéo ngang quá rộng nhưng tốc độ lại nằm nhỏ ở mép dưới. Hướng dẫn pipe/retry lặp trên card và banner cuối page.
- “Thư viện backup” hiển thị cả job đang chờ; tên page không khớp kỳ vọng xem file đã lưu.
- Trang Topics cho group không forum vẫn có “Backup tất cả topics”, checkbox All media và Lưu lựa chọn. Đây là một quyết định không cần người dùng thực hiện.
- Các icon chevron, X, thùng rác, dấu ba chấm cạnh nhau thiếu phân cấp. X có thể bị hiểu là đóng thay vì hủy job.
- Ngôn ngữ trộn Anh/Việt, thông tin DB/SQLite/rclone/pipe/worker xuất hiện trong tác vụ thông thường.

Các vấn đề suy ra từ code, cần kiểm tra trực quan khi triển khai: Sources nhiều trạng thái và mô tả cùng lúc; Settings/Storage có nhiều giải thích kỹ thuật; Dashboard dành nhiều diện tích cho minh họa bảo vệ thay vì trạng thái backup.

## 2. Mục tiêu V2

Trong vài giây, người dùng phải xác định được: hệ thống có chạy không, đang làm gì, có lỗi cần can thiệp không. Thêm nguồn phải dẫn đến quét và hàng đợi rõ ràng. Quản lý file dùng tìm kiếm/lọc/chọn hàng; hành động phá hủy chỉ xuất hiện đúng ngữ cảnh.

Mục tiêu nghiệm thu thiết kế:
- Mỗi page có một hành động chính rõ ràng; không hiển thị đồng thời Pause và Resume cho cùng trạng thái/phạm vi.
- Nội dung tác nghiệp xuất hiện ngay sau header/toolbar, không có banner giải thích thường trực ở giữa.
- Giảm tối thiểu 50% text hướng dẫn thường trực ở Đang truyền, Thư viện và Topics so với hiện tại; giữ thông tin ảnh hưởng đến quyết định trong tooltip, chi tiết và xác nhận.
- Mọi trạng thái có icon + nhãn, không dựa riêng vào màu.
- Mục tiêu contrast: chữ thông thường ≥4.5:1, thành phần điều khiển quan trọng ≥3:1. Đo trên màu thực tế của cả light/dark trước nghiệm thu; không mặc định palette đề xuất đã đạt.
- Không tràn ngang ở viewport 390px. Icon button có vùng bấm ít nhất 40px desktop, 44px mobile.

## 3. Hệ hình ảnh và component

### Màu

Đề xuất dark neutral thay nền xanh: canvas #0B0F16, sidebar #101620, panel #161E2B, panel nổi #1C2736, border #334155. Text chính #F8FAFC, phụ #B6C2D2. Màu thương hiệu xanh lá chỉ giữ ở logo hoặc chi tiết nhận diện nhỏ.

Primary/action: xanh dương #2563EB, chữ trắng. Selected navigation: nền xanh dương nhạt trong dark với vạch chỉ báo nhỏ. Đang truyền: blue; đang kiểm tra: violet #C4B5FD; hoàn tất/kết nối: emerald #6EE7B7; nghỉ/chờ giới hạn: amber #FCD34D; lỗi/phá hủy: coral #FDA4AF; chờ/đã hủy: slate #CBD5E1. Mỗi status dùng nền tint nhẹ cùng icon/nhãn. Đỏ chỉ dành lỗi và hành động nguy hiểm.

Light theme dùng canvas #F3F5F9, panel trắng, text #111827, secondary #475569; kiểm tra lại màu trạng thái riêng. Không đảo màu dark một cách máy móc.

### Bố cục và typography

Sidebar 216–232px, có chế độ thu gọn; topbar 56–64px. Nội dung padding 24px desktop, 16px mobile; spacing theo nhịp 4/8/12/16/24/32. Page title 24–28px; nội dung 14px; metadata 12–13px. Số tốc độ/dung lượng dùng tabular numerals. Border mỏng, radius 10–12px; hạn chế card lồng card và drop shadow.

Bỏ eyebrow tiếng Anh, slogan footer và thẻ Personal vault nếu chưa có nhiều workspace. Giữ menu có tên bên cạnh icon khi sidebar mở. Một header gồm tên page, số lượng nếu có, hành động chính; mô tả chỉ dùng khi cần thiết cho trạng thái trống.

### Icon

Dùng Lucide thống nhất stroke và kích thước 18–20px: Plus thêm, Search tìm, SlidersHorizontal lọc, Pause tạm dừng, Play tiếp tục, RotateCw thử lại/quét, FolderOpen đường dẫn, Copy sao chép, Ellipsis thêm, CircleX hủy, Trash2 xóa lịch. Không dùng X cho hủy truyền; X chỉ đóng dialog.

Icon-only cho thao tác lặp tại hàng, refresh, copy, mở chi tiết. Tooltip tiếng Việt xuất hiện khi hover/focus, aria-label rõ đối tượng và phạm vi. Primary CTA và xác nhận nguy hiểm giữ chữ ngắn kèm icon. Mobile không phụ thuộc tooltip: menu chứa nhãn, nút có tên accessible. Không thay mọi chữ bằng icon vì các thao tác hủy/xóa/dừng dễ bị hiểu nhầm.

### Hệ component dùng chung

PageHeader; compact Toolbar; SearchInput; FilterPopover; StatusBadge; IconButton; RowActionMenu; SelectionActionBar; ConfirmDialog; DetailDrawer; EmptyState; InlineError; Toast. Tooltip/popover dùng chung cho hover, focus, Escape và click bên ngoài. Toast thông báo kết quả thao tác, lỗi liên quan dữ liệu giữ tại vị trí thao tác. Vùng trạng thái live không tự giành focus hoặc đọc lại toàn bộ bảng mỗi lần poll.

## 4. Kiến trúc điều hướng và flow

Menu chính: Tổng quan / Nguồn / Truyền & hàng đợi / Thư viện / Cần xử lý. Nhóm Hệ thống: Telegram / Lưu trữ / Cài đặt. Topics chuyển thành tab trong chi tiết Nguồn; chỉ hiện cho forum. URL cũ #topics vẫn mở đúng nguồn/tab để giữ liên kết hiện có.

Flow: dán link → xem nguồn và cấu hình mặc định → thêm & bắt đầu → card nguồn tự hiện trạng thái Đã lên lịch/Đang quét → số file phát hiện/đang chờ cập nhật → mở Truyền & hàng đợi → Hoàn tất xuất hiện trong Thư viện. Không tự chuyển trang làm mất ngữ cảnh; có link hành động rõ trong thông báo và trạng thái nguồn.

## 5. Thiết kế từng page

### Tổng quan
- Header “Tổng quan”; CTA + Thêm nguồn.
- Một dòng trạng thái Telegram, Drive, bộ xử lý. Lỗi cần chú ý đứng đầu, có hành động sửa cụ thể.
- Bốn số: Đang truyền, Chờ tải, Đã lưu, Cần xử lý; bỏ nhãn VIDEO nếu hệ thống hỗ trợ loại khác.
- Trung tâm là hai file đang chạy và tổng tốc độ đo được. Cột bên là nguồn đang quét/nghỉ, thời điểm hoặc thời gian nghỉ còn lại.
- Hoạt động gần đây dùng tiếng Việt, gom sự kiện quá dày; không hiện raw event keys.
- RAM/disk/uptime đặt trong mục “Hệ thống” mở rộng. Thu nhỏ thông tin mã hóa thành trạng thái, bỏ shield artwork lớn.
- Trống: một lời hướng dẫn và nút Thêm nguồn. Ngắt kết nối: hiện CTA Kết nối Telegram.

### Nguồn Telegram
- Toolbar tìm tên, filter trạng thái/loại, CTA + Thêm nguồn. Desktop ưu tiên danh sách có hàng; mobile dùng card gọn.
- Mỗi nguồn: icon group/channel, tên, trạng thái, số đã lưu/chờ/lỗi; thao tác Play/Pause và menu. Quét riêng là thao tác phụ.
- Quét đang chạy hiển thị số tin đã đọc và số file phát hiện; không giả % khi không biết tổng. Nghỉ hiển thị “Tiếp tục sau 32s”. Lỗi có một dòng ngắn và nút xem chi tiết.
- Click nguồn mở drawer/tab Tổng quan, Topics (forum), Bộ lọc, Đích lưu, Hoạt động. Cấu hình và đường dẫn không nằm toàn bộ trên card.
- Dialog thêm: ô dán link nổi bật → xác nhận nguồn → tùy chọn nâng cao thu gọn; CTA Thêm & bắt đầu, lựa chọn phụ “Cấu hình trước”. Discovery là link phụ “Chọn từ tài khoản”. Giữ xác nhận quyền sao chép đã có.
- Khi hệ thống tạm dừng toàn cục, phân biệt rõ “Nguồn sẵn sàng — hệ thống đang dừng”, không báo đang chạy.

### Topics
- Không còn page riêng mặc định. Forum: tab Topics trong nguồn, có tìm kiếm, số đã chọn, radio “Tất cả”/“Chọn riêng”. Chỉ hiện checkbox khi chọn riêng.
- Danh sách gồm tên topic, số đã lưu/chờ/lỗi nếu có số liệu thật. Topic ID nằm trong chi tiết.
- Nút Lưu chỉ active khi thay đổi, sticky dưới vùng chọn; trước khi rời có cảnh báo thay đổi chưa lưu.
- Group/channel không forum: ẩn tab Topics hoàn toàn; trong bộ lọc nguồn chỉ ghi “Toàn bộ nội dung phù hợp”. Không hiện checkbox All media.
- Đổi lựa chọn thông báo ngắn về ảnh hưởng công việc tương lai; ý nghĩa hủy/xóa lịch để trong dialog của thao tác tương ứng.

### Truyền & hàng đợi
- Header gồm tổng tốc độ, số đang truyền / số chờ, Pause hoặc Resume toàn hệ thống kèm nhãn phạm vi.
- Tab Đang truyền / Hàng đợi. Filter nguồn/topic gọn trong toolbar, không đặt một panel “Thao tác nhanh” khổng lồ.
- Card active: icon loại file, tên tối đa hai dòng, nguồn/topic; progress; % và tốc độ nổi bật; bytes đã đọc/tổng nhỏ hơn. Pause và menu đặt góc phải.
- Có hai file song song: hai card cân đối, không kéo rộng vô ích; desktop rộng có thể dùng hàng compact. Khi VERIFYING dùng badge tím “Đang kiểm tra”, ẩn tốc độ tải không còn ý nghĩa, giữ 100% dữ liệu đọc với trạng thái kiểm tra riêng.
- Một progress phản ánh pipeline đo được; không dựng phần trăm upload độc lập hoặc ETA khi chưa có dữ liệu đáng tin.
- Cảnh báo retry tải lại từ đầu đặt trong tooltip Pause và xác nhận hủy; bỏ banner cuối page thường trực.
- Hàng đợi có tìm/lọc/chọn nhiều; selection bar mới hiện thao tác hàng loạt. Menu “Quản lý phạm vi” hỗ trợ group/topic và mọi job ngoài trang; dialog hiển thị rõ phạm vi, số bị ảnh hưởng từ server nếu có.

### Thư viện backup
- Mặc định chỉ file COMPLETED. Các job chưa xong nằm trong Truyền & hàng đợi; tổng file trong Thư viện không tính queue.
- Toolbar: tìm tên/caption, nguồn/topic, ngày, loại file, sort ngày/tên. Có nút mở bộ lọc thay vì mọi dropdown cùng xuất hiện.
- Table: tên file (rộng nhất), nguồn/topic, dung lượng, thời gian backup, thao tác. Lần thử, job ID, checksum, raw path nằm trong drawer.
- File hoàn tất chỉ có mở chi tiết/copy đường dẫn/menu phù hợp, không bày Pause/Cancel/Delete job cạnh nhau.
- Phân biệt ngày đăng và ngày hoàn tất trong sort/chi tiết. Caption và tên gốc trình bày riêng trong drawer nếu dữ liệu có.
- Path là logical path đã giải mã. Hiện breadcrumb thư mục + nút copy; không gắn link Drive giả khi chưa ánh xạ object thực.
- Mobile dùng danh sách gọn, mở drawer khi chạm; không giữ bảng nhiều cột ép ngang.

### Cần xử lý
- Chỉ những việc cần hành động, không coi FloodWait đang tự chờ là lỗi cần retry.
- Hàng gồm tên file/nguồn, nguyên nhân dễ hiểu, thời điểm, CTA Thử lại khi hợp lệ. Chi tiết kỹ thuật mở trong drawer.
- Gom nhóm lỗi Telegram, lưu trữ, xác minh. Có selection bar Thử lại các mục chọn; lỗi toàn kết nối dẫn đến Telegram/Lưu trữ.
- Ví dụ copy: “Không kết nối được Drive — kiểm tra kết nối” thay cho exception dài.

### Lưu trữ
- Vùng đầu trả lời “Lưu ở đâu?”: tên remote, root logical, cấu trúc Source/[Topic]/File; icon copy đường dẫn và kiểm tra kết nối.
- Ba chỉ báo mã hóa gọn trên một hàng; thông tin keys/rclone thu gọn vào Chi tiết kỹ thuật.
- “Đối chiếu backup” thành tác vụ bảo trì: lần chạy gần nhất, kết quả, nút chạy; trạng thái đang chạy/hoàn tất/lỗi rõ.
- Không hiển thị dung lượng quota dạng số khi chưa đo được; dùng “Chưa có dữ liệu”. Hướng dẫn terminal chỉ hiện khi chưa cấu hình hoặc trong trợ giúp.

### Cài đặt
- Nhóm “Truyền tải”, “Nghỉ & thử lại”, “Xác minh”, “Giao diện”. Một trang dùng anchor/tab, tránh nhiều panel cùng giải thích dài.
- Nghỉ ngẫu nhiên: toggle, hai input có suffix giây, dòng tóm tắt “Nghỉ 5–60 giây sau mỗi file”. Lời giải thích shared workers mở bằng info icon.
- Bandwidth: “Không giới hạn” / “Giới hạn”, chỉ hiện input khi giới hạn. Đơn vị dễ hiểu, validation tại trường.
- Không hiển thị điều chỉnh số file song song nếu backend chưa hỗ trợ cập nhật runtime; có thể hiện giá trị thực ở mục trạng thái.
- Sticky save bar chỉ xuất hiện khi dirty; có Hủy thay đổi. Lưu thất bại giữ nguyên form và chỉ rõ lỗi.
- FloodWait/cooldown vào phần chính sách vận hành thu gọn, trừ khi trạng thái này đang diễn ra.

### Kết nối Telegram
- Khi đã kết nối: card tài khoản và badge, CTA Đi tới nguồn; sửa API/ngắt kết nối trong menu. Không giữ wizard và hướng dẫn dài.
- Khi chưa kết nối: form tập trung rộng khoảng 480–560px, stepper 3 bước API / Điện thoại / Xác minh. Hiện duy nhất bước hiện tại.
- OTP/2FA: field phù hợp, nút gửi lại có countdown thực, lỗi gắn bước; không show thông tin nhạy cảm trong toast/log.
- Hướng dẫn API chỉ ở bước API hoặc accordion. Ngắt kết nối yêu cầu xác nhận rõ ảnh hưởng các nguồn.

### Đăng nhập quản trị
- Form nhỏ, ít text, username/password, hiển thị lỗi inline và loading. Branding gọn; không dành nửa màn hình cho lời quảng cáo.
- Password toggle có aria-label; Enter gửi form, focus đầu tiên hợp lý.

## 6. Quy tắc hành động và phạm vi

Tạm dừng: nguồn/job vẫn còn; transfer đang chạy bị dừng và lần tiếp tục có thể tải lại từ đầu. Hủy: chấm dứt job hiện có, không tự retry. Xóa lịch: xóa bản ghi công việc chưa hoàn tất theo semantics hiện tại; không xóa backup Drive. Ba ý nghĩa phải được diễn đạt riêng trong dialog, không gom bằng icon X.

Checkbox chọn hàng chỉ thao tác những job đã chọn, không tự chọn mọi job ngoài trang. “Toàn nguồn/toàn topic/toàn hệ thống” là chế độ khác trong menu quản lý phạm vi, xác nhận tên nguồn/topic và số lượng nếu backend cung cấp. Không áp dụng filter của giao diện một cách ngầm cho API queue/control. Backend hiện hỗ trợ một scope hoặc một job; bulk nhiều ID/số affected cần hợp đồng API riêng nếu bổ sung.

## 7. Thứ tự thực hiện

P0: tách Library/Queue, ẩn Topics không forum, thu gọn QueueControls, chuẩn hóa trạng thái Pause/Resume và phạm vi. Đây là bước giảm nhầm thao tác lớn nhất.

P1: design tokens neutral/semantic, PageHeader/Toolbar/IconButton/StatusBadge/Drawer/ConfirmDialog; làm Truyền & hàng đợi và Sources trước. Chuyển thông tin kỹ thuật vào disclosure và loại text lặp.

P2: Dashboard, Library, Failed; sau đó Storage, Settings, Telegram/Login. Bổ sung search/sort/bulk API khi dữ liệu/backend hiện tại chưa đủ, không chỉ lọc trang hiện có rồi trình bày như toàn bộ thư viện.

P3: keyboard/mobile/light theme, contrast, empty/error/loading states, kiểm tra thực tế rồi deploy cùng gói. Làm local/mock trước; QA production chỉ đọc, không pause/cancel job thật để thử UI.

## 8. Kiểm thử và giới hạn

Kiểm tra 390/768/1440/1920px, dark/light; bàn phím Tab/Enter/Escape; tooltip focus; menu/drawer giữ và trả focus; tên/caption dài; 0/1/2 active file; nhiều nguồn/topic; quét chưa biết tổng; global/source pause; rest countdown; VERIFYING; lỗi; pending mutations; form dirty.

Luồng nghiệm thu: thêm channel bằng link → scan visible → queue → 2 transfers → verify → completed ở Library; forum chọn topics → save → chạy; pause/resume scope; confirm cancel/delete đúng đối tượng; copy logical path; Telegram reconnect; update settings.

Dữ liệu poll không làm mất search/sort/selection hoặc focus. Cần định nghĩa cách xử lý selected job biến mất/đổi trạng thái trước khi gửi action. Không tạo upload speed/ETA/quota/Drive URL giả. Contrast phải đo trên render thực tế, icon-only không thể nghiệm thu chỉ bằng ảnh. Thu thập một vòng người dùng thao tác để xác nhận mức dễ hiểu sau V2.
