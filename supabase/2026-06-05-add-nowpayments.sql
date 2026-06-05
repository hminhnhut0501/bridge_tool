insert into public.bot_config (key, value) values
  ('NOWPAYMENTS_PAYMENT_ENABLED', 'OFF'),
  ('NOWPAYMENTS_PRICE_CURRENCY', 'USD'),
  ('NOWPAYMENTS_PAY_CURRENCY', ''),
  ('NOWPAYMENTS_IPN_CALLBACK_URL', ''),
  ('NOWPAYMENTS_TTL_SECONDS', '3600'),
  ('MSG_CHOOSE_PAYMENT_PROVIDER', 'Chọn phương thức thanh toán. VietQR dùng VNĐ; PayPal và Crypto dùng giá USD riêng.'),
  ('MSG_PAYPAL_BILL_TEMPLATE', '💳 <b>PAYPAL PAYMENT</b>\n\n🎁 Plan: <b>{plan}</b>\n💵 Amount: <b>${paypal_amount} USD</b>\n🧾 Order: <code>{desc}</code>'),
  ('MSG_NOWPAYMENTS_BILL_TEMPLATE', '₿ <b>THANH TOÁN CRYPTO</b>\n\n🎁 Gói: <b>{plan}</b>\n💵 Số tiền: <b>{amount}</b>\n🧾 Đơn: <code>{desc}</code>\n\nSau khi blockchain xác nhận xong, bot sẽ tự cấp quyền. Quá trình này có thể mất vài phút.'),
  ('BTN_PAYPAL_CHECKOUT', '💳 Pay with PayPal'),
  ('BTN_NOWPAYMENTS_CHECKOUT', '₿ Thanh toán Crypto')
on conflict (key) do nothing;

update public.bot_config
set value = 'PAYOS,PAYPAL,NOWPAYMENTS'
where key = 'PAYMENT_PROVIDERS_VI'
  and value in ('PAYOS', 'PAYOS,PAYPAL');

update public.bot_config
set value = 'PAYPAL,NOWPAYMENTS'
where key = 'PAYMENT_PROVIDERS_EN'
  and value in ('PAYPAL', '');
