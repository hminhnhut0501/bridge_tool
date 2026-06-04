alter table public.orders
alter column amount type numeric(14,2) using amount::numeric,
alter column original_amount type numeric(14,2) using original_amount::numeric,
alter column coupon_discount_amount type numeric(14,2) using coupon_discount_amount::numeric;

alter table public.orders
add column if not exists payment_currency text not null default 'VND';

alter table public.sale_rules
alter column sale_price type numeric(14,2) using sale_price::numeric;

insert into public.bot_config (key, value)
values
  ('PAYMENT_PROVIDERS_VI', 'PAYOS,PAYPAL'),
  ('PAYMENT_PROVIDERS_EN', 'PAYPAL'),
  ('PRICE_SVIP_30D_USD', '0'),
  ('PRICE_SVIP_LIFE_USD', '0')
on conflict (key) do nothing;
