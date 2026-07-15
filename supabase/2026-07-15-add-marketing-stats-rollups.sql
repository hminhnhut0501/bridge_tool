create table if not exists public.marketing_stats_rollups (
  range_key text not null,
  range_label text not null,
  orders_count integer not null default 0,
  paid_orders_count integer not null default 0,
  unique_customers_count integer not null default 0,
  revenue numeric(14,2) not null default 0,
  plan_breakdown jsonb not null default '[]'::jsonb,
  provider_breakdown jsonb not null default '[]'::jsonb,
  currency_breakdown jsonb not null default '[]'::jsonb,
  updated_at timestamptz not null default now(),
  primary key (range_key, range_label)
);

create index if not exists idx_marketing_stats_rollups_updated_at on public.marketing_stats_rollups (updated_at desc);

create or replace function public.refresh_marketing_stats_rollups()
returns void
language plpgsql
security definer
as $$
begin
  with base as (
    select
      coalesce(created_at, now())::date as day_key,
      coalesce(nullif(trim(plan_name), ''), 'Không rõ gói') as plan_name,
      coalesce(nullif(trim(upper(payment_provider)), ''), 'UNKNOWN') as payment_provider,
      coalesce(nullif(trim(upper(payment_currency)), ''), 'VND') as payment_currency,
      upper(status) as status,
      coalesce(amount, 0) as amount,
      telegram_user_id
    from public.orders
  ),
  day_totals as (
    select
      day_key,
      count(*)::int as orders_count,
      count(*) filter (where status = 'PAID')::int as paid_orders_count,
      count(distinct telegram_user_id)::int as unique_customers_count,
      coalesce(sum(amount) filter (where status = 'PAID'), 0)::numeric(14,2) as revenue
    from base
    group by day_key
  ),
  plan_rows as (
    select
      day_key,
      jsonb_agg(
        jsonb_build_object('label', plan_name, 'orders', orders_count, 'revenue', revenue)
        order by revenue desc, orders_count desc
      ) as plan_breakdown
    from (
      select
        day_key,
        plan_name,
        count(*)::int as orders_count,
        coalesce(sum(amount) filter (where status = 'PAID'), 0)::numeric(14,2) as revenue
      from base
      group by day_key, plan_name
    ) grouped_plan
    group by day_key
  ),
  provider_rows as (
    select
      day_key,
      jsonb_agg(
        jsonb_build_object('label', payment_provider, 'orders', orders_count, 'revenue', revenue)
        order by revenue desc, orders_count desc
      ) as provider_breakdown
    from (
      select
        day_key,
        payment_provider,
        count(*)::int as orders_count,
        coalesce(sum(amount) filter (where status = 'PAID'), 0)::numeric(14,2) as revenue
      from base
      group by day_key, payment_provider
    ) grouped_provider
    group by day_key
  ),
  currency_rows as (
    select
      day_key,
      jsonb_agg(
        jsonb_build_object('label', payment_currency, 'orders', orders_count, 'revenue', revenue)
        order by revenue desc, orders_count desc
      ) as currency_breakdown
    from (
      select
        day_key,
        payment_currency,
        count(*)::int as orders_count,
        coalesce(sum(amount) filter (where status = 'PAID'), 0)::numeric(14,2) as revenue
      from base
      group by day_key, payment_currency
    ) grouped_currency
    group by day_key
  )
  insert into public.marketing_stats_rollups (
    range_key,
    range_label,
    orders_count,
    paid_orders_count,
    unique_customers_count,
    revenue,
    plan_breakdown,
    provider_breakdown,
    currency_breakdown,
    updated_at
  )
  select
    'day'::text as range_key,
    to_char(day_totals.day_key, 'YYYY-MM-DD') as range_label,
    day_totals.orders_count,
    day_totals.paid_orders_count,
    day_totals.unique_customers_count,
    day_totals.revenue,
    coalesce(plan_rows.plan_breakdown, '[]'::jsonb),
    coalesce(provider_rows.provider_breakdown, '[]'::jsonb),
    coalesce(currency_rows.currency_breakdown, '[]'::jsonb),
    now()
  from day_totals
  left join plan_rows using (day_key)
  left join provider_rows using (day_key)
  left join currency_rows using (day_key)
  on conflict (range_key, range_label) do update set
    orders_count = excluded.orders_count,
    paid_orders_count = excluded.paid_orders_count,
    unique_customers_count = excluded.unique_customers_count,
    revenue = excluded.revenue,
    plan_breakdown = excluded.plan_breakdown,
    provider_breakdown = excluded.provider_breakdown,
    currency_breakdown = excluded.currency_breakdown,
    updated_at = now();
end;
$$;

select public.refresh_marketing_stats_rollups();
