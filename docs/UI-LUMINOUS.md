# Luminous UI — 2026-10-07

Giao diện dùng nền đen tím, ánh sáng tím xanh có kiểm soát, card truyền bo tròn và icon file có chiều sâu dựng bằng CSS. Toolbar, nguồn, thư viện và cài đặt giảm khung viền; thao tác phạm vi chuyển vào modal. Tên file giữ tooltip, menu hỗ trợ Escape và thao tác bàn phím. Mobile xếp card theo cột; reduced-motion tắt chuyển động không cần thiết.

Trạng thái VERIFYING dùng chỉ báo không xác định, hiển thị dung lượng đã truyền xong, không hiển thị 0% hoặc 0 B khi worker đang xác minh. Không tạo phần trăm upload riêng giả lập.

Validation: TypeScript/Vite build PASS; 3 Playwright E2E PASS, gồm sandbox crypt, đăng nhập Telegram giả lập, thao tác queue/topic, desktop/mobile, light/dark, focus và trạng thái xác minh. Tương phản palette chữ chính/phụ và nút chính trên nền kiểm tra đều > 4.5:1; đây không phải audit mọi pixel/trạng thái.

Chỉ thay frontend. Triển khai static không restart worker; giữ concurrency=2 và bandwidth=0. Bằng chứng tại data/reports/ui-luminous.
