insert into public.bot_config (key, value, updated_at)
values
  (
    'PLAN_COMBO_30D',
    'Combo 30 Ngày',
    now()
  ),
  (
    'PLAN_COMBO_30D_ALIASES',
    'All Access 30 Ngày, SVIP 30 Ngày, FULL 30D',
    now()
  ),
  (
    'PLAN_COMBO_LIFE',
    'Combo Trọn Đời',
    now()
  ),
  (
    'PLAN_COMBO_LIFE_ALIASES',
    'All Access Trọn Đời, SVIP Trọn Đời, FULL LIFE',
    now()
  ),
  (
    'BTN_RENEW_FULL',
    '🌟 Gia hạn / Lên Combo',
    now()
  ),
  (
    'BTN_VIEW_ALL_ACCESS_PAGE',
    '🌟 XEM COMBO',
    now()
  ),
  (
    'TXT_ALL_ACCESS_DESCRIPTION',
    '🔥 <b>ĐẶC QUYỀN COMBO</b> 🔥\n\n👇 <i>Chọn gói đăng ký bên dưới:</i>',
    now()
  ),
  (
    'IMG_ALL_ACCESS_PAGE',
    '',
    now()
  ),
  (
    'MSG_HIDDEN_REQUIREMENT_SVIP_ACTIVE',
    'Bạn cần có gói Combo còn hạn để mở mã này.',
    now()
  ),
  (
    'MSG_HIDDEN_REQUIREMENT_SVIP_LIFETIME',
    'Bạn cần có gói Combo trọn đời để mở mã này.',
    now()
  )
on conflict (key) do update
set
  value = excluded.value,
  updated_at = now()
where public.bot_config.key in (
  'PLAN_COMBO_30D',
  'PLAN_COMBO_30D_ALIASES',
  'PLAN_COMBO_LIFE',
  'PLAN_COMBO_LIFE_ALIASES',
  'BTN_RENEW_FULL',
  'BTN_VIEW_ALL_ACCESS_PAGE',
  'TXT_ALL_ACCESS_DESCRIPTION',
  'IMG_ALL_ACCESS_PAGE',
  'MSG_HIDDEN_REQUIREMENT_SVIP_ACTIVE',
  'MSG_HIDDEN_REQUIREMENT_SVIP_LIFETIME'
);
