from __future__ import annotations


def should_skip_manual_active_code(body: dict[str, object] | None) -> bool:
    payload = body or {}
    if payload.get("skip_active_code") is None:
        return True
    value = payload.get("skip_active_code")
    return str(value).lower() == "true" or value is True
