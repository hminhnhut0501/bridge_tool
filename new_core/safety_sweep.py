from __future__ import annotations

from datetime import datetime, timezone


def build_sweep_query(*, now: datetime | None = None, limit: int = 20) -> dict:
    """Return the bounded due-job query contract used by the safety sweep."""
    now = now or datetime.now(timezone.utc)
    return {
        "status": "in.(PENDING,RETRY)",
        "run_at": f"lte.{now.isoformat()}",
        "order": "run_at.asc",
        "limit": max(1, min(limit, 50)),
    }


def next_retry_delay(attempts: int) -> int | None:
    """Return seconds for bounded exponential retry, or None after the cap."""
    schedule = (60, 300, 900)
    index = max(0, int(attempts))
    return schedule[index] if index < len(schedule) else None
