update public.bot_config
set
  value = case
    when key in ('MANUAL_ORDER_LINK_TEMPLATE', 'MANUAL_ORDER_MESSAGE_LINK_TEMPLATE') then 'https://t.me/hangcuvipbot?start={code}'
    else value
  end,
  updated_at = now()
where key in ('MANUAL_ORDER_LINK_TEMPLATE', 'MANUAL_ORDER_MESSAGE_LINK_TEMPLATE')
  and (
    value ilike '%hangcuprivebot%'
    or value ilike '%your_bot_username%'
    or value = ''
  );
