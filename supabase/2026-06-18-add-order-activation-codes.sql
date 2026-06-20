create table if not exists public.order_activation_codes (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  order_id text not null unique,
  telegram_user_id text not null,
  full_name text,
  plan_name text not null,
  expire_at timestamptz,
  activation_status text not null default 'PENDING',
  activated_at timestamptz,
  activated_by_user_id text,
  used_at timestamptz,
  used_by_user_id text,
  activation_url text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_order_activation_codes_code on public.order_activation_codes (code);
create index if not exists idx_order_activation_codes_order_id on public.order_activation_codes (order_id);
create index if not exists idx_order_activation_codes_telegram_user_id on public.order_activation_codes (telegram_user_id);

insert into public.bot_config (key, value) values
  ('MANUAL_ORDER_LINK_TITLE', '🔗 Link kích hoạt'),
  ('MANUAL_ORDER_LINK_SUBTITLE', 'Nhấn vào link bên dưới để mở bot và nhận link nhóm riêng.'),
  ('MANUAL_ORDER_LINK_BUTTON_LABEL', 'Copy link bot'),
  ('MANUAL_ORDER_LINK_COPY_LABEL', 'Copy link bot'),
  ('MANUAL_ORDER_LINK_OPEN_LABEL', 'Mở Telegram'),
  ('MANUAL_ORDER_LINK_SUCCESS_TITLE', '✅ Đã tạo link kích hoạt'),
  ('MANUAL_ORDER_LINK_SUCCESS_BODY', 'Gửi link này cho khách để họ bấm vào bot và nhận quyền truy cập.'),
  ('MANUAL_ORDER_LINK_INVALID_TEXT', '❌ Mã kích hoạt không hợp lệ hoặc đã bị vô hiệu hoá.'),
  ('MANUAL_ORDER_LINK_USED_TEXT', 'ℹ️ Mã này đã được sử dụng. Nếu cần, admin hãy tạo lại link mới.'),
  ('MANUAL_ORDER_LINK_WRONG_USER_TEXT', '❌ Mã này không dành cho tài khoản Telegram hiện tại.'),
  ('MANUAL_ORDER_LINK_EXPIRED_TEXT', '⏰ Mã kích hoạt đã hết hạn. Vui lòng liên hệ admin.'),
  ('MANUAL_ORDER_LINK_PROCESSING_TEXT', '⏳ Bot đang xác minh đơn và tạo link nhóm...'),
  ('MANUAL_ORDER_LINK_FAIL_TEXT', '❌ Bot chưa tạo được link nhóm. Vui lòng thử lại sau.'),
  ('MANUAL_ORDER_LINK_SUCCESS_TEXT', '✅ Đơn của bạn đã được xác minh.'),
  ('MANUAL_ORDER_LINK_TEMPLATE', 't.me/hangcuprivebot?start={code}'),
  ('MANUAL_ORDER_INFO_TEMPLATE', '🧾 Đơn hàng: {order_id}\n👤 Khách hàng: {full_name} - ID: {telegram_user_id}\n📦 Gói: {plan_name}\n⏳ Hạn dùng: {expire_at}'),
  ('MANUAL_ORDER_MESSAGE_TEMPLATE', '{success_text}\n\n{order_text}\n\n{bot_link_title}\n{activation_url}\n\n{bot_link_subtitle}\n\n{support_text}'),
  ('MANUAL_ORDER_START_TEMPLATE', '{processing_text}'),
  ('MANUAL_ORDER_DELIVERY_TEMPLATE', '{success_text}\n\n{order_text}\n\n{links_text}\n\n{support_text}')
on conflict (key) do update set value = excluded.value, updated_at = now();
