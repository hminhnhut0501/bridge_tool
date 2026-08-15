from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from .entitlement_resolver import has_newer_active_entitlement
from .kick_policy import evaluate_kick_eligibility


class JobRepository(Protocol):
    def claim_due(self, *, before: datetime, limit: int) -> list[dict]: ...
    def update(self, job_id: str, payload: dict) -> None: ...


class MembershipReader(Protocol):
    async def is_present(self, group_id: str, user_id: str) -> bool | None: ...
    async def kick(self, group_id: str, user_id: str): ...


@dataclass(frozen=True, slots=True)
class WorkerResult:
    scanned: int = 0
    kicked: int = 0
    retained: int = 0
    already_absent: int = 0
    review: int = 0
    retry: int = 0


async def run_delayed_kick_worker(
    jobs: JobRepository,
    membership: MembershipReader,
    entitlements: list[dict],
    *,
    now: datetime | None = None,
    limit: int = 10,
) -> WorkerResult:
    """Process a small claimed batch. The caller controls scheduling frequency."""
    now = now or datetime.now(timezone.utc)
    rows = jobs.claim_due(before=now, limit=max(1, min(limit, 50)))
    result = WorkerResult(scanned=len(rows))
    for job in rows:
        job_id = str(job.get("id") or "")
        user_id = str(job.get("telegram_user_id") or "")
        group_id = str(job.get("group_id") or "")
        group_code = str(job.get("group_code") or "")
        order_id = str(job.get("source_order_id") or "")
        matching = [
            e for e in entitlements
            if str(e.get("telegram_user_id")) == user_id
            and str(e.get("group_code") or "") == group_code
        ]
        newer = has_newer_active_entitlement(
            matching,
            telegram_user_id=user_id,
            group_code=group_code,
            source_order_id=order_id,
            now=now,
        )
        entitlement = next((e for e in matching if str(e.get("group_code")) == group_code), None)
        decision = evaluate_kick_eligibility(entitlement or {}, now=now, newer_active_exists=newer)
        if decision.action == "BLOCK":
            jobs.update(job_id, {"status": "RETAINED", "completed_at": now, "last_error": None})
            result = _add(result, retained=1)
            continue
        if not decision.eligible:
            jobs.update(job_id, {"status": "REVIEW", "last_error": decision.reason})
            result = _add(result, review=1)
            continue
        try:
            present = await membership.is_present(group_id, user_id)
            if present is False:
                jobs.update(job_id, {"status": "DONE", "completed_at": now, "last_error": None})
                result = _add(result, already_absent=1)
                continue
            if present is None:
                jobs.update(job_id, {"status": "REVIEW", "last_error": "membership_unknown"})
                result = _add(result, review=1)
                continue
            outcome = await membership.kick(group_id, user_id)
            if getattr(outcome, "ok", False):
                jobs.update(job_id, {"status": "DONE", "completed_at": now, "last_error": None})
                result = _add(result, kicked=1)
            else:
                jobs.update(job_id, {"status": "RETRY", "attempts": int(job.get("attempts") or 0) + 1, "last_error": getattr(outcome, "reason", "kick_failed")})
                result = _add(result, retry=1)
        except Exception as exc:
            jobs.update(job_id, {"status": "RETRY", "attempts": int(job.get("attempts") or 0) + 1, "last_error": type(exc).__name__})
            result = _add(result, retry=1)
    return result


def _add(result: WorkerResult, **changes: int) -> WorkerResult:
    values = {name: getattr(result, name) for name in WorkerResult.__dataclass_fields__}
    values.update({key: getattr(result, key) + value for key, value in changes.items()})
    return WorkerResult(**values)
