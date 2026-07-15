from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def _text(value) -> str:
    return str(value or "").strip()


def _normalize_currency(value: str) -> str:
    currency = _text(value).upper()
    if currency in {"", "VND", "VNĐ", "VND "}:
        return "VND"
    if currency in {"USD", "USDT", "CRYPTO", "PAYPAL"}:
        return currency
    return currency or "VND"


def _parse_dt(value, tz: ZoneInfo):
    raw = _text(value)
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            return parsed.astimezone(tz)
        return parsed.replace(tzinfo=tz)
    except Exception:
        return None


def _is_lifetime_plan(plan_name: str) -> bool:
    text = _text(plan_name).lower()
    return any(token in text for token in ("trọn đời", "tron doi", "lifetime", "vĩnh viễn", "vinh vien", "life"))


def _plan_bucket(plan_name: str) -> str:
    plan = _text(plan_name)
    return plan or "Không rõ gói"


def _day_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def _hour_key(dt: datetime) -> str:
    return dt.strftime("%H:00")


def _weekday_key(dt: datetime) -> str:
    weekday = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"][dt.weekday()]
    return weekday


def _period_bounds(now: datetime, period: str) -> tuple[datetime, datetime, datetime, datetime]:
    if period == "today":
        current_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        current_end = current_start + timedelta(days=1)
        previous_start = current_start - timedelta(days=1)
        previous_end = current_start
    elif period == "7d":
        current_end = now
        current_start = now - timedelta(days=7)
        previous_end = current_start
        previous_start = current_start - timedelta(days=7)
    elif period == "year":
        current_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        current_end = now
        previous_end = current_start
        previous_start = current_start.replace(year=current_start.year - 1)
    else:
        current_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if current_start.month == 12:
            next_month = current_start.replace(year=current_start.year + 1, month=1)
        else:
            next_month = current_start.replace(month=current_start.month + 1)
        current_end = next_month
        previous_end = current_start
        previous_start = current_start.replace(day=1) - timedelta(days=1)
        previous_start = previous_start.replace(day=1)
    return current_start, current_end, previous_start, previous_end


def _money_sum(orders, key="amount"):
    return sum(float(order.get(key) or 0) for order in orders)


def _period_orders(orders, start: datetime, end: datetime, tz: ZoneInfo):
    result = []
    for order in orders:
        dt = _parse_dt(order.get("created_at"), tz)
        if not dt:
            continue
        if start <= dt < end:
            result.append({**order, "_created_dt": dt})
    return result


def build_marketing_stats_response(orders, *, tz: ZoneInfo, period: str = "month"):
    now = datetime.now(tz)
    current_start, current_end, previous_start, previous_end = _period_bounds(now, period)
    current_orders = _period_orders(orders, current_start, current_end, tz)
    previous_orders = _period_orders(orders, previous_start, previous_end, tz)
    paid_orders = [order for order in current_orders if _text(order.get("status")).upper() == "PAID"]
    previous_paid_orders = [order for order in previous_orders if _text(order.get("status")).upper() == "PAID"]

    revenue = _money_sum(paid_orders)
    previous_revenue = _money_sum(previous_paid_orders)
    paid = len(paid_orders)
    previous_paid = len(previous_paid_orders)
    customers = len({ _text(order.get("telegram_user_id")) for order in paid_orders if _text(order.get("telegram_user_id")) })
    previous_customers = len({ _text(order.get("telegram_user_id")) for order in previous_paid_orders if _text(order.get("telegram_user_id")) })

    status_total = len(current_orders)
    conversion = round((paid / status_total) * 100) if status_total else 0
    prev_conversion = round((previous_paid / len(previous_orders)) * 100) if previous_orders else 0

    grouped_by_plan = defaultdict(list)
    grouped_by_user = defaultdict(list)
    grouped_by_day = defaultdict(list)
    grouped_by_hour = defaultdict(list)
    grouped_by_weekday = defaultdict(list)
    grouped_by_currency = defaultdict(list)
    grouped_by_provider = defaultdict(list)
    grouped_by_plan_day = defaultdict(list)
    grouped_by_plan_hour = defaultdict(list)
    grouped_by_plan_weekday = defaultdict(list)

    for order in paid_orders:
        plan = _plan_bucket(order.get("plan_name"))
        grouped_by_plan[plan].append(order)
        user_id = _text(order.get("telegram_user_id"))
        if user_id:
            grouped_by_user[user_id].append(order)
        dt = order["_created_dt"]
        grouped_by_day[_day_key(dt)].append(order)
        grouped_by_hour[_hour_key(dt)].append(order)
        grouped_by_weekday[_weekday_key(dt)].append(order)
        grouped_by_currency[_normalize_currency(order.get("payment_currency"))].append(order)
        grouped_by_provider[_text(order.get("payment_provider")).upper() or "UNKNOWN"].append(order)
        grouped_by_plan_day[(plan, _day_key(dt))].append(order)
        grouped_by_plan_hour[(plan, _hour_key(dt))].append(order)
        grouped_by_plan_weekday[(plan, _weekday_key(dt))].append(order)

    plan_stats = []
    active_by_plan = defaultdict(int)
    active_customers = set()
    renewals = 0
    renewal_customers = 0
    lifetime_upgrades = 0
    upgrade_from_30d = 0
    lifetime_paid_orders = 0
    first_paid_at_by_user = {}
    last_paid_at_by_user = {}

    for user_id, user_orders in grouped_by_user.items():
        user_orders.sort(key=lambda item: item["_created_dt"])
        first_paid_at_by_user[user_id] = user_orders[0]["_created_dt"].isoformat()
        last_paid_at_by_user[user_id] = user_orders[-1]["_created_dt"].isoformat()
        if len(user_orders) > 1:
            renewal_customers += 1
            renewals += len(user_orders) - 1
        if any(not _is_lifetime_plan(order.get("plan_name")) for order in user_orders) and any(_is_lifetime_plan(order.get("plan_name")) for order in user_orders):
            upgrade_from_30d += 1
        if any(_is_lifetime_plan(order.get("plan_name")) for order in user_orders):
            lifetime_paid_orders += sum(1 for order in user_orders if _is_lifetime_plan(order.get("plan_name")))
        lifetime_index = next((idx for idx, order in enumerate(user_orders) if _is_lifetime_plan(order.get("plan_name"))), None)
        if lifetime_index is not None and lifetime_index > 0:
            lifetime_upgrades += 1

    active_orders = [order for order in paid_orders if _is_lifetime_plan(order.get("plan_name")) or (order.get("expire_at") and _parse_dt(order.get("expire_at"), tz) and _parse_dt(order.get("expire_at"), tz) >= now)]
    for order in active_orders:
        active_customers.add(_text(order.get("telegram_user_id")))
        active_by_plan[_plan_bucket(order.get("plan_name"))] += 1

    for plan, items in grouped_by_plan.items():
        unique_customers = len({ _text(order.get("telegram_user_id")) for order in items if _text(order.get("telegram_user_id")) })
        active_count = len([order for order in active_orders if _plan_bucket(order.get("plan_name")) == plan])
        plan_stats.append({
            "plan_name": plan,
            "orders": len(items),
            "revenue": _money_sum(items),
            "customers": unique_customers,
            "active_customers": active_count,
            "active_share": round((active_count / len(active_orders)) * 100) if active_orders else 0,
            "average_order": round(_money_sum(items) / len(items), 2) if items else 0,
            "lifetime_share": round((sum(1 for order in items if _is_lifetime_plan(order.get("plan_name"))) / len(items)) * 100) if items else 0,
        })

    plan_stats.sort(key=lambda item: (item["revenue"], item["orders"]), reverse=True)
    previous_grouped_by_plan = defaultdict(list)
    for order in previous_paid_orders:
        plan = _plan_bucket(order.get("plan_name"))
        previous_grouped_by_plan[plan].append(order)
    previous_plan_lookup = {
        plan: {
            "plan_name": plan,
            "orders": len(items),
            "revenue": _money_sum(items),
            "customers": len({ _text(order.get("telegram_user_id")) for order in items if _text(order.get("telegram_user_id")) }),
        }
        for plan, items in previous_grouped_by_plan.items()
    }

    top_day = max(grouped_by_day.items(), key=lambda item: (_money_sum(item[1]), len(item[1])), default=(None, []))
    top_weekday = max(grouped_by_weekday.items(), key=lambda item: (_money_sum(item[1]), len(item[1])), default=(None, []))
    top_hour = max(grouped_by_hour.items(), key=lambda item: (_money_sum(item[1]), len(item[1])), default=(None, []))
    top_plan = plan_stats[0] if plan_stats else None
    top_retention_plan = max(plan_stats, key=lambda item: (item["active_customers"], item["orders"]), default=None)

    revenue_compare = {
        "current": revenue,
        "previous": previous_revenue,
        "delta": revenue - previous_revenue,
        "delta_percent": round(((revenue - previous_revenue) / previous_revenue) * 100, 1) if previous_revenue else None,
        "paid_current": paid,
        "paid_previous": previous_paid,
        "customers_current": customers,
        "customers_previous": previous_customers,
        "conversion_current": conversion,
        "conversion_previous": prev_conversion,
    }

    payment_breakdown = {
        "by_currency": [
            {"currency": currency, "revenue": _money_sum(items), "orders": len(items), "customers": len({ _text(order.get("telegram_user_id")) for order in items if _text(order.get("telegram_user_id")) }) }
            for currency, items in sorted(grouped_by_currency.items(), key=lambda item: _money_sum(item[1]), reverse=True)
        ],
        "by_provider": [
            {"provider": provider, "revenue": _money_sum(items), "orders": len(items), "customers": len({ _text(order.get("telegram_user_id")) for order in items if _text(order.get("telegram_user_id")) }) }
            for provider, items in sorted(grouped_by_provider.items(), key=lambda item: _money_sum(item[1]), reverse=True)
        ],
    }

    time_stats = {
        "by_day": [{"day": day, "revenue": _money_sum(items), "orders": len(items), "customers": len({ _text(order.get("telegram_user_id")) for order in items if _text(order.get("telegram_user_id")) })} for day, items in sorted(grouped_by_day.items(), key=lambda item: item[0])],
        "by_hour": [{"hour": hour, "revenue": _money_sum(items), "orders": len(items), "customers": len({ _text(order.get("telegram_user_id")) for order in items if _text(order.get("telegram_user_id")) })} for hour, items in sorted(grouped_by_hour.items(), key=lambda item: item[0])],
        "by_weekday": [{"weekday": day, "revenue": _money_sum(items), "orders": len(items)} for day, items in sorted(grouped_by_weekday.items(), key=lambda item: item[0])],
    }

    def _top_plan_rows(grouped_source, label_key):
        rows = []
        grouped_by_label = defaultdict(list)
        for (plan, label), items in grouped_source.items():
            grouped_by_label[label].append((plan, items))
        for label, plan_items in grouped_by_label.items():
            plan_name, items = max(plan_items, key=lambda item: (len(item[1]), _money_sum(item[1])), default=("", []))
            rows.append({
                label_key: label,
                "plan_name": plan_name,
                "orders": len(items),
                "revenue": _money_sum(items),
                "customers": len({ _text(order.get("telegram_user_id")) for order in items if _text(order.get("telegram_user_id")) }),
            })
        return sorted(rows, key=lambda item: (item["orders"], item["revenue"]), reverse=True)

    top_by_day = _top_plan_rows(grouped_by_plan_day, "day")
    top_by_hour = _top_plan_rows(grouped_by_plan_hour, "hour")
    top_by_weekday = _top_plan_rows(grouped_by_plan_weekday, "weekday")

    cohort_rows = []
    cohort_heatmap = []
    cohort_provider_rows = []
    buyer_type_plan_rows = []
    user_orders_map = {}
    for user_id, user_orders in grouped_by_user.items():
        user_orders_map[user_id] = sorted(user_orders, key=lambda item: item["_created_dt"])
    cohort_windows = {
        "7d": 7,
        "30d": 30,
    }
    for window_label, window_days in cohort_windows.items():
        window_start = now - timedelta(days=window_days)
        base_users = 0
        retained_users = 0
        renewed_users = 0
        upgraded_users = 0
        for user_id, user_orders in user_orders_map.items():
            first_order = user_orders[0]
            if first_order["_created_dt"] < window_start:
                continue
            base_users += 1
            has_retained = len(user_orders) > 1
            if has_retained:
                retained_users += 1
                renewed_users += 1
            if any(_is_lifetime_plan(order.get("plan_name")) for order in user_orders[1:]):
                upgraded_users += 1
        cohort_rows.append({
            "window": window_label,
            "base_users": base_users,
            "retained_users": retained_users,
            "retention_rate": round((retained_users / base_users) * 100, 1) if base_users else 0,
            "renewed_users": renewed_users,
            "renewal_rate": round((renewed_users / base_users) * 100, 1) if base_users else 0,
            "upgraded_users": upgraded_users,
            "upgrade_rate": round((upgraded_users / base_users) * 100, 1) if base_users else 0,
        })
        cohort_heatmap.append({
            "window": window_label,
            "cells": [
                {"key": "base", "label": "Base", "value": base_users, "score": min(100, base_users * 8)},
                {"key": "retention", "label": "Retention", "value": round((retained_users / base_users) * 100, 1) if base_users else 0, "score": round((retained_users / base_users) * 100) if base_users else 0},
                {"key": "renewal", "label": "Renewal", "value": round((renewed_users / base_users) * 100, 1) if base_users else 0, "score": round((renewed_users / base_users) * 100) if base_users else 0},
                {"key": "upgrade", "label": "Upgrade", "value": round((upgraded_users / base_users) * 100, 1) if base_users else 0, "score": round((upgraded_users / base_users) * 100) if base_users else 0},
            ]
        })

    provider_user_orders = defaultdict(list)
    for user_id, user_orders in user_orders_map.items():
        provider = _text(user_orders[0].get("payment_provider")).upper() or "UNKNOWN"
        provider_user_orders[provider].extend(user_orders)

    for provider, provider_orders in sorted(provider_user_orders.items(), key=lambda item: item[0]):
        provider_orders.sort(key=lambda item: item["_created_dt"])
        base_users = len({ _text(order.get("telegram_user_id")) for order in provider_orders if _text(order.get("telegram_user_id")) })
        retained_users = len({
            _text(order.get("telegram_user_id"))
            for order in provider_orders
            if _text(order.get("telegram_user_id")) and len(user_orders_map.get(_text(order.get("telegram_user_id")), [])) > 1
        })
        renewed_users = retained_users
        upgraded_users = len({
            _text(order.get("telegram_user_id"))
            for order in provider_orders
            if _text(order.get("telegram_user_id")) and any(_is_lifetime_plan(item.get("plan_name")) for item in user_orders_map.get(_text(order.get("telegram_user_id")), [])[1:])
        })
        cohort_provider_rows.append({
            "provider": provider,
            "base_users": base_users,
            "retained_users": retained_users,
            "retention_rate": round((retained_users / base_users) * 100, 1) if base_users else 0,
            "renewed_users": renewed_users,
            "renewal_rate": round((renewed_users / base_users) * 100, 1) if base_users else 0,
            "upgraded_users": upgraded_users,
            "upgrade_rate": round((upgraded_users / base_users) * 100, 1) if base_users else 0,
        })

    for plan, items in grouped_by_plan.items():
        first_buyers = 0
        returning_buyers = 0
        first_buyers_revenue = 0
        returning_buyers_revenue = 0
        first_buyers_orders = 0
        returning_buyers_orders = 0
        for order in items:
            user_id = _text(order.get("telegram_user_id"))
            user_history = user_orders_map.get(user_id, [])
            is_first = bool(user_history and user_history[0]["order_id"] == order.get("order_id"))
            if is_first:
                first_buyers += 1
                first_buyers_orders += 1
                first_buyers_revenue += float(order.get("amount") or 0)
            else:
                returning_buyers += 1
                returning_buyers_orders += 1
                returning_buyers_revenue += float(order.get("amount") or 0)
        buyer_type_plan_rows.append({
            "plan_name": plan,
            "first_buyers": first_buyers,
            "first_buyers_orders": first_buyers_orders,
            "first_buyers_revenue": first_buyers_revenue,
            "returning_buyers": returning_buyers,
            "returning_buyers_orders": returning_buyers_orders,
            "returning_buyers_revenue": returning_buyers_revenue,
            "total_orders": len(items),
            "total_revenue": _money_sum(items),
        })
    buyer_type_plan_rows.sort(key=lambda item: (item["total_revenue"], item["total_orders"]), reverse=True)

    opportunity_alerts = []
    scored_alerts = []
    for row in plan_stats:
        prev = previous_plan_lookup.get(row["plan_name"], {"orders": 0, "revenue": 0, "customers": 0})
        revenue_now = float(row["revenue"] or 0)
        revenue_prev = float(prev["revenue"] or 0)
        orders_now = int(row["orders"] or 0)
        orders_prev = int(prev["orders"] or 0)
        customers_now = int(row["customers"] or 0)
        customers_prev = int(prev["customers"] or 0)

        revenue_delta_pct = round(((revenue_now - revenue_prev) / revenue_prev) * 100, 1) if revenue_prev else (100.0 if revenue_now else 0.0)
        order_delta_pct = round(((orders_now - orders_prev) / orders_prev) * 100, 1) if orders_prev else (100.0 if orders_now else 0.0)
        customer_delta_pct = round(((customers_now - customers_prev) / customers_prev) * 100, 1) if customers_prev else (100.0 if customers_now else 0.0)
        active_pressure = round((row["active_customers"] / orders_now) * 100, 1) if orders_now else 0
        decline_score = 0
        if revenue_delta_pct < 0:
            decline_score += min(45, abs(revenue_delta_pct) * 0.6)
        if order_delta_pct < 0:
            decline_score += min(25, abs(order_delta_pct) * 0.45)
        if customer_delta_pct < 0:
            decline_score += min(15, abs(customer_delta_pct) * 0.3)
        if row["active_customers"] and row["active_customers"] > orders_now:
            decline_score += min(20, ((row["active_customers"] - orders_now) / max(1, orders_now)) * 10)
        if row["lifetime_share"] < 25 and row["active_customers"] > 0:
            decline_score += 8

        scored_alerts.append({
            "plan_name": row["plan_name"],
            "score": round(decline_score, 1),
            "revenue_delta_pct": revenue_delta_pct,
            "order_delta_pct": order_delta_pct,
            "customer_delta_pct": customer_delta_pct,
            "active_pressure": active_pressure,
            "orders_now": orders_now,
            "orders_prev": orders_prev,
            "revenue_now": revenue_now,
            "revenue_prev": revenue_prev,
            "active_customers": row["active_customers"],
            "lifetime_share": row["lifetime_share"],
        })

    scored_alerts.sort(key=lambda item: (item["score"], item["revenue_delta_pct"]), reverse=True)
    for item in scored_alerts[:3]:
        if item["score"] >= 18 and (item["revenue_delta_pct"] < 0 or item["order_delta_pct"] < 0 or item["customer_delta_pct"] < 0):
            opportunity_alerts.append({
                "title": f"{item['plan_name']} đang giảm nhịp",
                "detail": f"Score {item['score']}/100 • doanh thu {item['revenue_delta_pct']}% • đơn {item['order_delta_pct']}% • active {item['active_customers']}",
                "tone": "bad" if item["revenue_delta_pct"] <= -15 else "warning",
                "action": "Kiểm tra campaign, giá, và tệp upsell ngay",
                "score": item["score"],
                "signals": {
                    "revenue_delta_pct": item["revenue_delta_pct"],
                    "order_delta_pct": item["order_delta_pct"],
                    "customer_delta_pct": item["customer_delta_pct"],
                    "active_pressure": item["active_pressure"],
                    "lifetime_share": item["lifetime_share"],
                },
            })

    for item in scored_alerts:
        if item["score"] >= 35 and item["revenue_delta_pct"] >= 0 and item["active_pressure"] >= 120:
            opportunity_alerts.append({
                "title": f"{item['plan_name']} có thể đẩy re-activation",
                "detail": f"Score {item['score']}/100 • active pressure cao, doanh thu chưa rơi mạnh. Đây là cửa sổ tốt để giữ khách.",
                "tone": "good",
                "action": "Đẩy early renewal / bundle offer",
                "score": item["score"],
                "signals": {
                    "revenue_delta_pct": item["revenue_delta_pct"],
                    "order_delta_pct": item["order_delta_pct"],
                    "customer_delta_pct": item["customer_delta_pct"],
                    "active_pressure": item["active_pressure"],
                    "lifetime_share": item["lifetime_share"],
                },
            })
            break

    for item in scored_alerts:
        if item["score"] >= 22 and item["lifetime_share"] < 30 and item["orders_now"] >= 3:
            opportunity_alerts.append({
                "title": f"{item['plan_name']} có dư địa nâng lifetime",
                "detail": f"Score {item['score']}/100 • lifetime share thấp, tệp khách đủ lớn để thử upsell gói trọn đời.",
                "tone": "warning",
                "action": "Mở upsell lifetime",
                "score": item["score"],
                "signals": {
                    "revenue_delta_pct": item["revenue_delta_pct"],
                    "order_delta_pct": item["order_delta_pct"],
                    "customer_delta_pct": item["customer_delta_pct"],
                    "active_pressure": item["active_pressure"],
                    "lifetime_share": item["lifetime_share"],
                },
            })
            break

    insights = [
        {
            "title": "Doanh thu so với kỳ trước",
            "detail": f"{revenue:,.0f} so với {previous_revenue:,.0f}",
            "tone": "good" if revenue >= previous_revenue else "warning",
        },
        {
            "title": "Khung giờ mạnh nhất",
            "detail": f"{top_hour[0] or '-'} với { _money_sum(top_hour[1]) if top_hour[1] else 0:,.0f}",
            "tone": "good",
        },
        {
            "title": "Gói bán tốt nhất",
            "detail": f"{top_plan['plan_name'] if top_plan else '-'}",
            "tone": "good",
        },
        {
            "title": "Gói giữ khách tốt nhất",
            "detail": f"{top_retention_plan['plan_name'] if top_retention_plan else '-'}",
            "tone": "warning",
        },
    ]

    retention_stats = {
        "active_customers": len(active_customers),
        "active_orders": len(active_orders),
        "renewal_orders": renewals,
        "renewal_customers": renewal_customers,
        "renewal_rate": round((renewals / len(grouped_by_user)) * 100, 1) if grouped_by_user else 0,
        "lifetime_upgrades": lifetime_upgrades,
        "upgrade_from_30d": upgrade_from_30d,
        "lifetime_upgrade_rate": round((lifetime_upgrades / len(grouped_by_user)) * 100, 1) if grouped_by_user else 0,
        "lifetime_paid_orders": lifetime_paid_orders,
        "first_paid_at_by_user": first_paid_at_by_user,
        "last_paid_at_by_user": last_paid_at_by_user,
        "active_by_plan": dict(active_by_plan),
    }

    return {
        "range": period,
        "period": {
            "current_start": current_start.isoformat(),
            "current_end": current_end.isoformat(),
            "previous_start": previous_start.isoformat(),
            "previous_end": previous_end.isoformat(),
        },
        "overview": {
            "orders": len(current_orders),
            "paid_orders": paid,
            "customers": customers,
            "revenue": revenue,
            "average_order": round(revenue / paid, 2) if paid else 0,
            "conversion": conversion,
        },
        "top_periods": {
            "day": {"label": top_day[0], "revenue": _money_sum(top_day[1]), "orders": len(top_day[1])},
            "weekday": {"label": top_weekday[0], "revenue": _money_sum(top_weekday[1]), "orders": len(top_weekday[1])},
            "hour": {"label": top_hour[0], "revenue": _money_sum(top_hour[1]), "orders": len(top_hour[1])},
        },
        "revenue_compare": revenue_compare,
        "plan_stats": plan_stats,
        "retention_stats": retention_stats,
        "payment_breakdown": payment_breakdown,
        "time_stats": time_stats,
        "top_by_period": {
            "day": top_by_day,
            "hour": top_by_hour,
            "weekday": top_by_weekday,
        },
        "cohorts": cohort_rows,
        "cohort_heatmap": cohort_heatmap,
        "provider_cohorts": cohort_provider_rows,
        "buyer_type_plan_rows": buyer_type_plan_rows,
        "opportunity_alerts": opportunity_alerts,
        "insights": insights,
    }
