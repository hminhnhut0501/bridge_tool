alter table public.orders
add column if not exists payment_provider text,
add column if not exists payment_provider_order_id text,
add column if not exists payment_approval_url text,
add column if not exists payment_currency text not null default 'VND';

insert into public.bot_config (key, value)
values
  ('PAYOS_PAYMENT_ENABLED', 'ON'),
  ('PAYPAL_PAYMENT_ENABLED', 'OFF'),
  ('PAYMENT_PROVIDER_VI', 'PAYOS'),
  ('PAYMENT_PROVIDER_EN', 'PAYPAL'),
  ('PAYMENT_PROVIDERS_VI', 'PAYOS,PAYPAL'),
  ('PAYMENT_PROVIDERS_EN', 'PAYPAL'),
  ('PAYPAL_BRAND_NAME', 'Prive Bot')
on conflict (key) do nothing;
