from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .expiry_workflow import ExpiryRunResult, reconcile_expired_orders
from .kick_workflow import KickRunResult, process_due_kick_groups
from .ports import Clock, KickTaskRepository, MembershipGateway, OrderRepository


@dataclass(frozen=True, slots=True)
class RenewalCycleResult:
    expiry: ExpiryRunResult | None = None
    kick: KickRunResult | None = None
    expiry_error: str = ""
    kick_error: str = ""


@dataclass(frozen=True, slots=True)
class RenewalRuntime:
    orders: OrderRepository
    tasks: KickTaskRepository
    membership: MembershipGateway
    clock: Clock
    parse_datetime: Callable[[Any], Any]
    active_order_check: Callable[[str, str, str], bool]
    plan_group_resolver: Callable[[str], list[str]] | None = None
    expiry_limit: int = 5000
    kick_limit: int = 300


async def run_renewal_cycle(runtime: RenewalRuntime) -> RenewalCycleResult:
    """Run expiry then kick, isolating failures between workflow boundaries."""
    try:
        expiry = reconcile_expired_orders(
            runtime.orders,
            runtime.tasks,
            runtime.clock,
            parser=runtime.parse_datetime,
            plan_group_resolver=runtime.plan_group_resolver,
            limit=runtime.expiry_limit,
        )
    except Exception as exc:
        return RenewalCycleResult(expiry_error=str(exc))

    try:
        kick = await process_due_kick_groups(
            runtime.tasks,
            runtime.membership,
            runtime.clock,
            active_order_check=runtime.active_order_check,
            limit=runtime.kick_limit,
        )
    except Exception as exc:
        return RenewalCycleResult(expiry=expiry, kick_error=str(exc))

    return RenewalCycleResult(expiry=expiry, kick=kick)
