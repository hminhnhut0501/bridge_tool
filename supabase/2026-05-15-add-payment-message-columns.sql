alter table public.orders
add column if not exists payment_message_chat_id text,
add column if not exists payment_message_id integer;
