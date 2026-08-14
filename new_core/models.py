from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class OrderSnapshot:
    order_id: str
    telegram_user_id: str
    plan_name: str
    status: str
    expire_at: Any = None
    plan_token: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class KickState:
    order_id: str
    telegram_user_id: str
    chat_id: str
    state: str
    source: str = ""
    detail: str = ""


@dataclass(frozen=True, slots=True)
class KickDecision:
    should_kick: bool
    reason: str
    state: str = "none"


@dataclass(frozen=True, slots=True)
class RenewalTaskState:
    task_state: str
    group_state: str = ""
    reason: str = ""

