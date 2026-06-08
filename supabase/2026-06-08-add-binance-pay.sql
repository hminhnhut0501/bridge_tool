insert into public.bot_config (key, value) values
  ('BINANCE_PAY_SIEUTHICODE_ENABLED', 'ON'),
  ('BINANCE_PAY_SIEUTHICODE_TOKEN', ''),
  ('BINANCE_PAY_SIEUTHICODE_APPROVAL_URL', ''),
  ('BINANCE_PAY_POLL_INTERVAL_SECONDS', '120'),
  ('BINANCE_PAY_POLL_BATCH_LIMIT', '200'),
  ('MSG_BINANCE_PAY_BILL_TEMPLATE', '🏦 <b>BINANCE PAY</b>\n\n🎁 Gói: <b>{plan}</b>\n💵 Số tiền: <b>{amount}</b>\n🧾 Đơn: <code>{desc}</code>\n\nVui lòng thanh toán theo hướng dẫn của cổng và bấm nút kiểm tra sau khi chuyển tiền.'),
  ('BTN_BINANCE_PAY_CHECKOUT', '🏦 Mở Binance Pay')
on conflict (key) do nothing;

update public.bot_config
set value = 'PAYOS,PAYPAL,NOWPAYMENTS,TRON_USDT,BINANCE_PAY'
where key = 'PAYMENT_PROVIDERS_VI'
  and value in ('PAYOS,PAYPAL', 'PAYOS,PAYPAL,NOWPAYMENTS', 'PAYOS,PAYPAL,TRON_USDT', 'PAYOS,PAYPAL,NOWPAYMENTS,TRON_USDT');

update public.bot_config
set value = replace(value, 'TRON_USDT', 'TRON_USDT,BINANCE_PAY')
where key = 'PAYMENT_PROVIDERS_VI'
  and value like '%TRON_USDT%'
  and value not like '%BINANCE_PAY%';

