insert into public.bot_config (key, value) values
  ('NOWPAYMENTS_PAYMENT_ENABLED', 'OFF'),
  ('NOWPAYMENTS_PRICE_CURRENCY', 'USD'),
  ('NOWPAYMENTS_PAY_CURRENCY', ''),
  ('NOWPAYMENTS_IPN_CALLBACK_URL', ''),
  ('NOWPAYMENTS_TTL_SECONDS', '3600')
on conflict (key) do nothing;

update public.bot_config
set value = 'PAYOS,PAYPAL,NOWPAYMENTS'
where key = 'PAYMENT_PROVIDERS_VI'
  and value in ('PAYOS', 'PAYOS,PAYPAL');

update public.bot_config
set value = 'PAYPAL,NOWPAYMENTS'
where key = 'PAYMENT_PROVIDERS_EN'
  and value in ('PAYPAL', '');
