from __future__ import annotations

from typing import Iterable


def _text(value) -> str:
    return str(value or "").strip()


def _matches_query(row: dict, query: str) -> bool:
    if not query:
        return True
    haystack = " ".join([
        _text(row.get("event_type")),
        _text(row.get("telegram_user_id")),
        _text(row.get("username")),
        _text(row.get("full_name")),
        _text(row.get("chat_id")),
        _text(row.get("chat_title")),
        _text(row.get("order_id")),
        _text(row.get("plan_name")),
        _text(row.get("created_at")),
        _text(row.get("updated_at")),
        _text(row.get("raw_data")),
    ]).lower()
    return query.lower() in haystack


def build_support_events_read_model(rows: Iterable[dict], *, limit: int = 1000, updated_after: str | None = None, query: str = ""):
    safe_limit = max(1, min(int(limit or 1000), 2000))
    updated_after_value = _text(updated_after)
    query_value = _text(query)
    items = []
    for row in rows:
        created_at = _text(row.get("created_at"))
        if updated_after_value and created_at and created_at <= updated_after_value:
            continue
        if not _matches_query(row, query_value):
            continue
        items.append({
            "id": row.get("id"),
            "event_type": _text(row.get("event_type")),
            "telegram_user_id": _text(row.get("telegram_user_id")),
            "username": _text(row.get("username")),
            "full_name": _text(row.get("full_name")),
            "chat_id": _text(row.get("chat_id")),
            "chat_title": _text(row.get("chat_title")),
            "order_id": _text(row.get("order_id")),
            "plan_name": _text(row.get("plan_name")),
            "raw_data": row.get("raw_data") if isinstance(row.get("raw_data"), dict) else {},
            "created_at": created_at,
            "updated_at": _text(row.get("updated_at")),
        })

    items.sort(key=lambda item: item.get("created_at") or "", reverse=True)
    return {
        "data": items[:safe_limit],
        "total": len(items),
        "limit": safe_limit,
        "updated_after": updated_after_value,
        "query": query_value,
    }
