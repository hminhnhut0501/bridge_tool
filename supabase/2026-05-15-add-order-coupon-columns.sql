alter table public.orders
add column if not exists coupon_code text,
add column if not exists coupon_discount_percent integer,
add column if not exists coupon_discount_amount integer;

create index if not exists idx_orders_coupon_code on public.orders (coupon_code);
