from __future__ import annotations

from datetime import datetime
from typing import Any


class SupabaseRenewalRepository:
    """Production adapter for the new-core renewal ports.

    The adapter owns the existing Supabase store method names and response
    shapes; workflows only see the Phase 2 protocols.
    """

    def __init__(self, store):
        self.store = store

    def list_expiry_candidates(self, *, before: datetime, limit: int):
        return self.store.list_scheduler_due_rows(before, limit=limit)

    def get_order(self, order_id: str):
        getter = getattr(self.store, "get_order", None)
        return getter(order_id) if getter else None

    def update_status(self, order_id: str, status: str, *, changed_at: datetime):
        return self.store.update_order_status(order_id, status)


class SupabaseKickTaskRepository:
    def __init__(self, store):
        self.store = store

    def get_task(self, order_id: str, user_id: str):
        return self.store.get_renewal_kick_task_v2(order_id, user_id)

    def create_task(self, payload: dict[str, Any]):
        rows = self.store.upsert_renewal_kick_task_v2(payload) or []
        return rows[0] if isinstance(rows, list) and rows else (rows or payload)

    def create_group_task(self, payload: dict[str, Any]):
        rows = self.store.upsert_renewal_kick_group_task_v2(payload) or []
        return rows[0] if isinstance(rows, list) and rows else (rows or payload)

    def update_task(self, task_id: str, payload: dict[str, Any]):
        rows = self.store.update_renewal_kick_task_v2(task_id, payload) or []
        return rows[0] if isinstance(rows, list) and rows else (rows or None)

    def list_due_group_tasks(self, *, before: datetime, limit: int):
        return self.store.list_due_renewal_kick_group_tasks_v2(due_before=before, limit=limit)

    def update_group_task(self, group_task_id: str, payload: dict[str, Any]):
        rows = self.store.update_renewal_kick_group_task_v2(group_task_id, payload) or []
        return rows[0] if isinstance(rows, list) and rows else (rows or None)
