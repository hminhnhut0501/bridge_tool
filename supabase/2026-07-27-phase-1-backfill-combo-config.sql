-- Phase 1: backfill Combo canonical keys alongside legacy ALL_ACCESS keys.
-- This keeps the bot working while code/config_aliases still accepts old names.

insert into public.bot_config (key, value, updated_at)
select 'PLAN_COMBO_30D', coalesce((select value from public.bot_config where key = 'PLAN_ALL_ACCESS_30D'), 'Combo 30 Ngày'), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PLAN_COMBO_LIFE', coalesce((select value from public.bot_config where key = 'PLAN_ALL_ACCESS_LIFE'), 'Combo Trọn Đời'), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PLAN_COMBO_30D_ALIASES', coalesce((select value from public.bot_config where key = 'PLAN_ALL_ACCESS_30D_ALIASES'), 'All Access 30 Ngày, SVIP 30 Ngày, FULL 30D'), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PLAN_COMBO_LIFE_ALIASES', coalesce((select value from public.bot_config where key = 'PLAN_ALL_ACCESS_LIFE_ALIASES'), 'All Access Trọn Đời, SVIP Trọn Đời, FULL LIFE'), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PRICE_COMBO_30D', coalesce((select value from public.bot_config where key = 'PRICE_ALL_ACCESS_30D'), '0'), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PRICE_COMBO_LIFE', coalesce((select value from public.bot_config where key = 'PRICE_ALL_ACCESS_LIFE'), '0'), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PRICE_COMBO_30D_USD', coalesce((select value from public.bot_config where key = 'PRICE_ALL_ACCESS_30D_USD'), '0'), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PRICE_COMBO_LIFE_USD', coalesce((select value from public.bot_config where key = 'PRICE_ALL_ACCESS_LIFE_USD'), '0'), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'BTN_BUY_COMBO_30D', coalesce((select value from public.bot_config where key = 'BTN_BUY_ALL_ACCESS_30D'), 'MUA 30 NGÀY'), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'BTN_BUY_COMBO_LIFE', coalesce((select value from public.bot_config where key = 'BTN_BUY_ALL_ACCESS_LIFE'), 'MUA TRỌN ĐỜI'), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'BTN_VIEW_COMBO_PAGE', coalesce((select value from public.bot_config where key = 'BTN_VIEW_ALL_ACCESS_PAGE'), '🌟 XEM COMBO'), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'TXT_COMBO_DESCRIPTION', coalesce((select value from public.bot_config where key = 'TXT_ALL_ACCESS_DESCRIPTION'), '🔥 <b>ĐẶC QUYỀN COMBO</b> 🔥\n\n👇 <i>Chọn gói đăng ký bên dưới:</i>'), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'IMG_COMBO_PAGE', coalesce((select value from public.bot_config where key = 'IMG_ALL_ACCESS_PAGE'), ''), now()
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
values
  (
    'LICENSE_PLAN_MAPPING_JSON',
    '{
      "COMBO_30D":{"groups":["group_a"],"duration_days":30,"allow_renew":true},
      "COMBO_LIFE":{"groups":["group_a","group_b"],"duration_days":null,"allow_renew":false}
    }',
    now()
  ),
  (
    'MSG_LICENSE_REMINDER',
    '⏰ License <b>{plan}</b> của bạn sẽ hết hạn sau <b>{days} ngày</b> nữa.\n\nVui lòng gia hạn để giữ quyền truy cập không gián đoạn.',
    now()
  ),
  (
    'MSG_LICENSE_REVOKED',
    '⛔ License <b>{plan}</b> của bạn đã bị thu hồi. Vui lòng liên hệ hỗ trợ nếu cần kiểm tra lại.',
    now()
  ),
  (
    'BTN_LICENSE_RENEW',
    '🔄 Gia hạn license',
    now()
  )
on conflict (key) do update
set
  value = excluded.value,
  updated_at = now()
where public.bot_config.key in (
  'LICENSE_PLAN_MAPPING_JSON',
  'MSG_LICENSE_REMINDER',
  'MSG_LICENSE_REVOKED',
  'BTN_LICENSE_RENEW'
);
