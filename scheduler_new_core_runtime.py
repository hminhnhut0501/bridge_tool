from __future__ import annotations

from datetime import datetime
import os
from typing import Any, Callable

from adapters.supabase_renewal import SupabaseKickTaskRepository, SupabaseRenewalRepository
from adapters.telegram_membership import TelegramMembershipGateway
from new_core.orchestrator import RenewalCycleResult, RenewalRuntime, run_renewal_cycle
from new_core.kick_workflow import process_due_kick_groups


def renewal_mutation_frozen() -> bool:
    """Global emergency stop for all new-core writes and Telegram mutations."""
    return str(os.getenv("RENEWAL_MUTATION_FREEZE", "OFF")).strip().upper() in {
        "ON", "TRUE", "YES", "1"
    }


class CallableClock:
    def __init__(self, callback):
        self.callback = callback

    def now(self):
        return self.callback()


def full_cutover_gate(config: dict[str, str]) -> tuple[bool, str]:
    required = {
        "RENEWAL_NEW_CORE_FULL_CUTOVER": "ON",
        "RENEWAL_NEW_CORE_DRY_RUN": "OFF",
        "RENEWAL_NEW_CORE_LIMITED_MUTATION": "OFF",
        "RENEWAL_NEW_CORE_CUTOVER_ACK": "I_UNDERSTAND",
    }
    for key, expected in required.items():
        if str(config.get(key) or "").strip().upper() != expected:
            return False, f"{key} must be {expected}"
    return True, "full cutover gate passed"


def build_runtime(*, store, bot, clock, parse_datetime: Callable[[Any], datetime | None], active_order_check, plan_group_resolver=None):
    return RenewalRuntime(
        orders=SupabaseRenewalRepository(store),
        tasks=SupabaseKickTaskRepository(store),
        membership=TelegramMembershipGateway(bot),
        clock=clock,
        parse_datetime=parse_datetime,
        active_order_check=active_order_check,
        plan_group_resolver=plan_group_resolver,
    )


async def run_cycle(*, store, bot, clock, parse_datetime, active_order_check, plan_group_resolver=None) -> RenewalCycleResult:
    if renewal_mutation_frozen():
        raise RuntimeError("renewal mutation freeze is enabled")
    runtime = build_runtime(
        store=store,
        bot=bot,
        clock=clock,
        parse_datetime=parse_datetime,
        active_order_check=active_order_check,
        plan_group_resolver=plan_group_resolver,
    )
    return await run_renewal_cycle(runtime)


async def run_read_only_cycle(*, store, bot, clock, active_order_check, plan_group_resolver=None):
    """Read-only canary: no workflow writer and no Telegram mutation."""
    orders = store.list_scheduler_orders(limit=5000) if hasattr(store, "list_scheduler_orders") else []
    tasks = store.list_renewal_kick_tasks_v2(limit=5000)
    groups = store.list_due_renewal_kick_group_tasks_v2(limit=10000)
    membership = TelegramMembershipGateway(bot)
    counts = {"orders": len(orders), "tasks": len(tasks), "groups": len(groups), "present": 0, "absent": 0, "unknown": 0, "active_order_blocked": 0, "mapping_unavailable": 0}
    for group in groups:
        user_id = str(group.get("telegram_user_id") or "")
        order_id = str(group.get("order_id") or "")
        group_id = str(group.get("group_id") or "")
        if not user_id or not group_id:
            counts["unknown"] += 1
            continue
        if active_order_check(user_id, order_id, group_id):
            counts["active_order_blocked"] += 1
            continue
        presence = await membership.is_present(group_id, user_id)
        counts[{True: "present", False: "absent", None: "unknown"}[presence]] += 1
    return {"mode": "read_only", "counts": counts, "supabase_write_count": 0, "telegram_mutation_count": 0}


class CohortTaskRepository:
    def __init__(self, repository, *, user_ids=None, order_ids=None):
        self.repository = repository
        self.user_ids = {str(value) for value in (user_ids or set()) if str(value).strip()}
        self.order_ids = {str(value) for value in (order_ids or set()) if str(value).strip()}

    def _allowed(self, row):
        if self.user_ids and str(row.get("telegram_user_id") or "") in self.user_ids:
            return True
        if self.order_ids and str(row.get("order_id") or "") in self.order_ids:
            return True
        return False

    def list_due_group_tasks(self, *, before, limit):
        rows = self.repository.list_due_group_tasks(before=before, limit=limit)
        return [row for row in rows if self._allowed(row)]

    def update_group_task(self, group_task_id, payload):
        return self.repository.update_group_task(group_task_id, payload)


async def run_limited_mutation_cycle(*, store, bot, clock, active_order_check, cohort_user_ids=None, cohort_order_ids=None, limit=300):
    if renewal_mutation_frozen():
        raise RuntimeError("renewal mutation freeze is enabled")
    if not cohort_user_ids and not cohort_order_ids:
        raise ValueError("limited mutation requires a non-empty cohort")
    tasks = CohortTaskRepository(
        SupabaseKickTaskRepository(store),
        user_ids=cohort_user_ids,
        order_ids=cohort_order_ids,
    )
    result = await process_due_kick_groups(
        tasks,
        TelegramMembershipGateway(bot),
        clock,
        active_order_check=active_order_check,
        limit=limit,
    )
    return {"mode": "limited_mutation", "cohort_users": len(cohort_user_ids or set()), "cohort_orders": len(cohort_order_ids or set()), "result": result}
