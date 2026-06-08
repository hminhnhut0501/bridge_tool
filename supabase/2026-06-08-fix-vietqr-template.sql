insert into public.bot_config (key, value) values
  ('PAYOS_VIETQR_TEMPLATE', 'qr_only'),
  ('PAYOS_VIETQR_SHOW_ACCOUNT_NAME', 'OFF')
on conflict (key) do nothing;

