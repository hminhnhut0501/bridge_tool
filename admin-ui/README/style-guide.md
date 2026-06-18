# Prive Admin UI Style Guide

Tài liệu này là nguồn chuẩn cho mọi màn hình mới trong `admin-ui`.

## Mục Tiêu

- Giao diện sáng, sạch, hiện đại, theo tinh thần `mui.com`
- Có nhiều màu nhấn để dễ scan, nhưng không rời rạc
- Toàn app phải dùng chung một hệ token về màu, border, radius, shadow, font và trạng thái
- Hạn chế tối đa custom CSS khi MUI đã có component tương ứng

## Nguyên Tắc Tổng Quát

1. Ưu tiên MUI trước: `Button`, `IconButton`, `TextField`, `FormControl`, `Select`, `MenuItem`, `Tabs`, `Tab`, `Card`, `Chip`, `Dialog`, `Table`, `Stack`, `Box`
2. Dùng `sx` hoặc theme override cho style nhỏ, tránh tạo CSS mới nếu không cần
3. Mỗi screen nên có một accent tone riêng, nhưng vẫn nằm trong cùng hệ palette
4. Không trộn nhiều hệ màu khác nhau trong cùng một view
5. Không render raw date / raw ISO string trực tiếp lên UI
6. Hạn chế nút, chip, badge custom nếu đã có helper chung

## Token Chuẩn

### Màu

- `primary`: xanh dương cho action chính và tab active
- `secondary`: tím cho accent phụ
- `success`: emerald cho trạng thái tốt / active / paid
- `warning`: amber cho trạng thái cần chú ý
- `error`: rose / red cho trạng thái lỗi / hủy / hết hạn
- `background`: nền sáng, card trắng, shadow mềm

### Radius

- Card: bo vừa phải, không quá tròn
- Dialog: bo rõ hơn card nhưng vẫn gọn
- Input: bo ổn định, đồng nhất với Select
- Button/Chip/Tab: bo pill

### Shadow

- Card: shadow nhẹ, có thể thêm line top gradient
- Dialog: shadow rõ hơn card để nổi layer
- Button contained: có glow rất nhẹ để tạo nhịp

### Font

- Font chính: `Inter`
- Heading: đậm, letter-spacing âm nhẹ
- Body: vừa phải, line-height thoáng nhưng không lỏng
- Tab, chip, button: chữ đậm để dễ đọc nhanh

## Component Mapping

- Form nhập liệu: `TextField` cho text/numeric/date
- Select box: `FormControl` + `InputLabel` + `Select` + `MenuItem`
- Checkbox: `Checkbox` + `FormControlLabel`
- Tabs: `Tabs` + `Tab`
- Dialog: `AppDialog` hoặc `MuiDialogShell`
- Section card: `AppSection`
- Header section: `PanelHead`
- Toolbar action row: `AppToolbar`

## Quy Ước Theo Khu Vực

### Tabs

- Dùng `Tab` dạng pill
- Active state phải rõ, nhưng không quá chói
- Tabs trong popup và trong page phải cùng token
- Không tự set nhiều border/radius riêng lẻ nếu theme đã xử lý

### FormControl / Select

- Dùng `size="small"`
- Dùng `variant="outlined"`
- Select phải cùng radius và border với input
- MenuItem nên có hover/selected rõ nhưng nhẹ

### TextField

- Luôn đồng bộ bo góc, border, focus ring
- `helperText` dùng cho giải thích ngắn, không nhồi nhiều nội dung
- `datetime-local` phải đi qua helper format chung trước khi hiển thị

### Dialog

- Nút đóng đặt góc phải trên
- Header dialog rõ ràng, action phụ đặt ở footer hoặc toolbar riêng
- Card trong dialog không bo quá mạnh để tránh cảm giác “bị lỗi”

## Màu Theo Màn

- Overview: xanh dương + cyan + emerald
- Orders: xanh dương + amber + rose
- Customers: tím + emerald + blue
- Campaigns / Channel posts: cyan + purple + amber

## Trạng Thái

- `PAID` và trạng thái active: dùng màu sống động, dễ nổi
- `PENDING`: dùng amber
- `EXPIRED`, `CANCELLED`, `DISABLED`: dùng style đơn sắc, thiên về disabled
- Badge trong popup phải nhất quán giữa mọi tab

## Cách Làm Màn Mới

1. Dựng khung bằng `AppSection`
2. Đặt header bằng `PanelHead`
3. Dùng `Metric` cho KPI
4. Dùng `Tabs` và `Tab` theo token chung
5. Dùng `TextField`/`FormControl`/`Select` thay vì HTML form control
6. Chỉ thêm CSS mới khi thật sự không thể biểu diễn bằng MUI

## Không Nên Làm

- Dùng lại style cũ của `input`, `select`, `textarea`, `button` HTML
- Tạo thêm màu riêng cho từng màn nếu đã có token phù hợp
- Dùng raw ISO string trong popup, table, timeline
- Làm card quá bo tròn hoặc border quá dày khiến nhìn lệch hệ

## File Hỗ Trợ

- `app/style-guide.ts`: token, palette, screen tone
- `app/theme-registry.tsx`: theme override MUI toàn app
- `app/dashboard-components.tsx`: `AppDialog`, `AppSection`, `AppToolbar`, `PanelHead`, `Metric`
- `app/dashboard-helpers.ts`: helper format ngày giờ, trạng thái, tiền tệ

