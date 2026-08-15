import asyncio
import unittest
from datetime import datetime
from types import SimpleNamespace

from adapters.supabase_renewal import SupabaseKickTaskRepository, SupabaseRenewalRepository
from adapters.telegram_membership import TelegramMembershipGateway


class Store:
    def list_scheduler_due_rows(self, before, limit):
        return [{"order_id": "o1"}]

    def update_order_status(self, order_id, status):
        return [{"order_id": order_id, "status": status}]

    def get_renewal_kick_task_v2(self, order_id, user_id):
        return None

    def upsert_renewal_kick_task_v2(self, payload):
        return [{"id": "t1", **payload}]

    def update_renewal_kick_task_v2(self, task_id, payload):
        return [{"id": task_id, **payload}]

    def list_due_renewal_kick_group_tasks_v2(self, **kwargs):
        return []

    def update_renewal_kick_group_task_v2(self, task_id, payload):
        return [{"id": task_id, **payload}]


class Bot:
    def __init__(self, status="member"):
        self.status = status
        self.calls = []

    async def get_chat_member(self, **kwargs):
        self.calls.append(("get", kwargs))
        return SimpleNamespace(status=SimpleNamespace(value=self.status))

    async def ban_chat_member(self, **kwargs):
        self.calls.append(("ban", kwargs))

    async def unban_chat_member(self, **kwargs):
        self.calls.append(("unban", kwargs))


class Phase6ProductionAdapterTests(unittest.TestCase):
    def test_supabase_adapter_maps_existing_store_api(self):
        store = Store()
        orders = SupabaseRenewalRepository(store)
        tasks = SupabaseKickTaskRepository(store)
        self.assertEqual(orders.list_expiry_candidates(before=datetime.now(), limit=1)[0]["order_id"], "o1")
        self.assertEqual(orders.update_status("o1", "EXPIRED", changed_at=datetime.now())[0]["status"], "EXPIRED")
        self.assertEqual(tasks.create_task({"order_id": "o1"})["id"], "t1")
        self.assertEqual(tasks.update_group_task("g1", {"group_state": "kicked"})["id"], "g1")

    def test_telegram_adapter_maps_presence_and_kick(self):
        bot = Bot()
        gateway = TelegramMembershipGateway(bot)

        async def run():
            self.assertTrue(await gateway.is_present("-1001", "42"))
            result = await gateway.kick("-1001", "42")
            self.assertTrue(result.ok)

        asyncio.run(run())
        self.assertEqual([item[0] for item in bot.calls], ["get", "ban", "unban"])

    def test_unknown_telegram_error_is_conservative(self):
        class BrokenBot(Bot):
            async def get_chat_member(self, **kwargs):
                raise RuntimeError("temporary telegram outage")

        async def run():
            self.assertIsNone(await TelegramMembershipGateway(BrokenBot()).is_present("-1001", "42"))

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
