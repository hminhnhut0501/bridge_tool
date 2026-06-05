insert into public.bot_config (key, value) values
  ('TRON_USDT_PAYMENT_ENABLED', 'OFF'),
  ('TRON_USDT_WALLET_ADDRESS', ''),
  ('TRON_USDT_UNIQUE_AMOUNT_ENABLED', 'ON'),
  ('TRON_USDT_TTL_SECONDS', '7200'),
  ('MSG_TRON_USDT_BILL_TEMPLATE', '₮ <b>THANH TOÁN USDT TRC20</b>\n\n🎁 Gói: <b>{plan}</b>\n💵 Số tiền: <code>{usdt_amount} USDT</code>\n🌐 Network: <b>TRC20</b>\n👛 Ví nhận:\n<code>{wallet}</code>\n🧾 Đơn: <code>{desc}</code>\n\nVui lòng chuyển đúng số USDT trên. Bot sẽ tự quét blockchain và cấp quyền sau khi giao dịch xác nhận.'),
  ('BTN_TRONSCAN_ADDRESS', '🔎 Xem ví trên Tronscan')
on conflict (key) do nothing;

update public.bot_config
set value = replace(value, 'NOWPAYMENTS', 'TRON_USDT')
where key in ('PAYMENT_PROVIDERS_VI', 'PAYMENT_PROVIDERS_EN')
  and value like '%NOWPAYMENTS%';

update public.bot_config
set value = 'PAYPAL,TRON_USDT'
where key = 'PAYMENT_PROVIDERS_EN'
  and value = 'PAYPAL';
