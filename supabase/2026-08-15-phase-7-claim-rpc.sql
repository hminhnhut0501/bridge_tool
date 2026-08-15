-- Phase 7: atomic job claim RPC.
-- The worker must use this RPC rather than selecting and updating separately.

create or replace function public.claim_entitlement_kick_jobs(
    p_before timestamptz,
    p_limit integer
)
returns setof public.entitlement_kick_jobs
language plpgsql
security definer
set search_path = public
as $$
begin
    return query
    with claimed as (
        select j.id
        from public.entitlement_kick_jobs j
        where j.status in ('PENDING', 'RETRY')
          and j.run_at <= p_before
          and (j.locked_at is null or j.locked_at < now() - interval '10 minutes')
        order by j.run_at asc
        limit greatest(1, least(coalesce(p_limit, 10), 50))
        for update skip locked
    )
    update public.entitlement_kick_jobs j
       set status = 'PROCESSING',
           locked_at = now(),
           updated_at = now()
      from claimed c
     where j.id = c.id
    returning j.*;
end;
$$;
