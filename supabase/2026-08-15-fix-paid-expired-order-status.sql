-- Safe repair for the two PAID orders proven to be stale.
-- This migration intentionally does not backfill expire_at for historical rows.

begin;

update public.orders o
   set status = 'EXPIRED'
 where o.order_id::text in ('1782656343842', '1782123274164')
       and upper(coalesce(o.status, '')) = 'PAID'
       and o.expire_at is not null
       and o.expire_at <= now()
       and not exists (
           select 1
             from public.orders newer
            where newer.telegram_user_id = o.telegram_user_id
              and upper(coalesce(newer.status, '')) = 'PAID'
              and newer.expire_at is not null
              and newer.expire_at > now()
              and newer.order_id::text <> o.order_id::text
       )
returning o.order_id, o.telegram_user_id, o.status, o.expire_at;

commit;
