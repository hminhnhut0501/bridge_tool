from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from new_core.ports import KickResult


@dataclass
class FixedClock:
    current: datetime

    def now(self) -> datetime:
        return self.current


@dataclass
class InMemoryOrderRepository:
    orders: list[dict[str, Any]] = field(default_factory=list)
    updates: list[tuple[str, str, datetime]] = field(default_factory=list)

    def list_expiry_candidates(self, *, before: datetime, limit: int):
        return self.orders[:limit]

    def get_order(self, order_id: str):
        return next((row for row in self.orders if str(row.get("order_id")) == str(order_id)), None)

    def update_status(self, order_id: str, status: str, *, changed_at: datetime):
        row = self.get_order(order_id)
        if row is None:
            return None
        row["status"] = status
        self.updates.append((str(order_id), status, changed_at))
        return row


@dataclass
class InMemoryKickTaskRepository:
    tasks: list[dict[str, Any]] = field(default_factory=list)
    group_tasks: list[dict[str, Any]] = field(default_factory=list)
    task_updates: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    group_updates: list[tuple[str, dict[str, Any]]] = field(default_factory=list)

    def get_task(self, order_id: str, user_id: str):
        return next(
            (row for row in self.tasks if str(row.get("order_id")) == str(order_id) and str(row.get("telegram_user_id")) == str(user_id)),
            None,
        )

    def create_task(self, payload):
        row = dict(payload)
        row.setdefault("id", f"task-{len(self.tasks) + 1}")
        self.tasks.append(row)
        return row

    def create_group_task(self, payload):
        row = dict(payload)
        row.setdefault("id", f"group-{len(self.group_tasks) + 1}")
        self.group_tasks.append(row)
        return row

    def update_task(self, task_id: str, payload):
        row = next((item for item in self.tasks if str(item.get("id")) == str(task_id)), None)
        if row is None:
            return None
        row.update(payload)
        self.task_updates.append((str(task_id), dict(payload)))
        return row

    def list_due_group_tasks(self, *, before: datetime, limit: int):
        return self.group_tasks[:limit]

    def update_group_task(self, group_task_id: str, payload):
        row = next((item for item in self.group_tasks if str(item.get("id")) == str(group_task_id)), None)
        if row is None:
            return None
        row.update(payload)
        self.group_updates.append((str(group_task_id), dict(payload)))
        return row


@dataclass
class FakeMembershipGateway:
    presence: dict[tuple[str, str], bool | None] = field(default_factory=dict)
    actions: list[tuple[str, str, str]] = field(default_factory=list)

    async def is_present(self, group_id: str, user_id: str):
        return self.presence.get((str(group_id), str(user_id)))

    async def kick(self, group_id: str, user_id: str):
        self.actions.append(("kick", str(group_id), str(user_id)))
        self.presence[(str(group_id), str(user_id))] = False
        return KickResult(ok=True, reason="kicked")

    async def mute(self, group_id: str, user_id: str):
        self.actions.append(("mute", str(group_id), str(user_id)))
        return KickResult(ok=True, reason="muted")

    async def unmute(self, group_id: str, user_id: str):
        self.actions.append(("unmute", str(group_id), str(user_id)))
        return KickResult(ok=True, reason="unmuted")


@dataclass
class InMemoryLegacyEventSink:
    events: list[tuple[str, str, dict[str, Any]]] = field(default_factory=list)

    def append(self, event_type: str, user_id: str, *, payload=None):
        self.events.append((event_type, str(user_id), dict(payload or {})))
