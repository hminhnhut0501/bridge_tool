from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Iterable


@dataclass(frozen=True, slots=True)
class RenewalMetrics:
    scanned_orders: int = 0
    reconciled_orders: int = 0
    created_tasks: int = 0
    scanned_groups: int = 0
    kick_sent: int = 0
    blocked: int = 0
    review_required: int = 0
    retry_scheduled: int = 0
    errors: int = 0


def metrics_from_cycle(result) -> RenewalMetrics:
    expiry = result.expiry
    kick = result.kick
    return RenewalMetrics(
        scanned_orders=getattr(expiry, "scanned", 0),
        reconciled_orders=getattr(expiry, "reconciled", 0),
        created_tasks=getattr(expiry, "tasks_created", 0),
        scanned_groups=getattr(kick, "scanned", 0),
        kick_sent=getattr(kick, "kicked", 0),
        blocked=getattr(kick, "blocked", 0),
        review_required=getattr(kick, "review_required", 0),
        retry_scheduled=getattr(kick, "retry_scheduled", 0),
        errors=int(bool(result.expiry_error)) + int(bool(result.kick_error)) + getattr(kick, "failed", 0),
    )


def structured_cycle_log(result, *, correlation_id: str, occurred_at: datetime) -> dict[str, Any]:
    metrics = metrics_from_cycle(result)
    return {
        "event": "renewal_cycle_completed",
        "correlation_id": correlation_id,
        "occurred_at": occurred_at.isoformat(),
        "ok": not result.expiry_error and not result.kick_error,
        "metrics": asdict(metrics),
        "errors": {"expiry": result.expiry_error, "kick": result.kick_error},
    }


def find_stale_tasks(tasks: Iterable[dict[str, Any]], *, now: datetime, stale_minutes: int = 15) -> list[dict[str, Any]]:
    stale = []
    for task in tasks:
        if str(task.get("task_state") or task.get("group_state") or "").lower() not in {"processing", "waiting_confirm"}:
            continue
        raw = task.get("last_transition_at") or task.get("updated_at") or task.get("locked_at")
        if not raw:
            stale.append(task)
            continue
        try:
            timestamp = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            compare_now = now if timestamp.tzinfo == now.tzinfo else now.replace(tzinfo=timestamp.tzinfo)
            if (compare_now - timestamp).total_seconds() >= stale_minutes * 60:
                stale.append(task)
        except ValueError:
            stale.append(task)
    return stale


def validate_feature_flags(values: dict[str, Any]) -> list[str]:
    errors = []
    for key, value in values.items():
        normalized = str(value or "").strip().upper()
        if normalized not in {"ON", "OFF", "TRUE", "FALSE", "1", "0", "YES", "NO"}:
            errors.append(f"{key}: invalid boolean value")
    return errors


def dynamic_cutover_gate(metrics: dict[str, Any], *, require_zero_unknown: bool = True) -> tuple[bool, list[str]]:
    """Evaluate production evidence before allowing full worker cutover."""
    failures = []
    if not metrics.get("baseline_available", False):
        failures.append("baseline is unavailable")
    if metrics.get("duplicate_claims", 0):
        failures.append("duplicate claims detected")
    if metrics.get("orphan_tasks", 0):
        failures.append("orphan tasks detected")
    if metrics.get("attempt_write_failures", 0):
        failures.append("attempt writes failed")
    if metrics.get("finalizer_failures", 0):
        failures.append("finalizer failures detected")
    if metrics.get("mutation_outside_cohort", 0):
        failures.append("mutation occurred outside cohort")
    if require_zero_unknown and metrics.get("unknown_membership", 0):
        failures.append("unknown membership remains")
    return not failures, failures
