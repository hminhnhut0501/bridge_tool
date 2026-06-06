import os
import unittest

os.environ.setdefault("BOT_TOKEN", "123456:TEST")

import config_utils
import hidden_group_utils
import modules.mod_coupon as mod_coupon
import modules.mod_payment as mod_payment


class FakeDb:
    def __init__(self):
        self.config = {
            "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
            "GROUP_COUNT": "2",
            "BTN_G1": "Hang Cú Prime",
            "ID_G1": "-100111",
            "BTN_G2": "Hang Cú Asia",
            "ID_G2": "-100222",
        }

    def get_config(self, key, default=""):
        return self.config.get(key, default)

    def set_config(self, key, value):
        self.config[key] = value

    def connect(self):
        return None


class FakeHiddenStore:
    enabled = True

    def list_hidden_groups(self):
        return [{
            "id": "prime_x",
            "name": "Prime X",
            "description": "extra",
            "chat_id": "-100999",
            "price_1m_vnd": 150000,
            "price_life_vnd": 900000,
            "price_1m_usd": 9.99,
            "price_life_usd": 49.99,
            "duration_1m_days": 30,
            "lifetime_days": 3650,
            "requirement_type": "SVIP_LIFETIME",
            "requirement_value": "",
            "sort_order": 1,
            "is_active": True,
        }]

    def list_hidden_codes(self):
        return [
            {
                "code": "HIDEVIP",
                "name": "VIP code",
                "scope_type": "SELECTED_GROUPS",
                "group_ids": ["prime_x"],
                "requirement_type": "SVIP_LIFETIME",
                "requirement_value": "",
                "max_uses": 5,
                "used_count": 0,
                "is_active": True,
            },
            {
                "code": "USEDUP",
                "name": "Used up",
                "scope_type": "SELECTED_GROUPS",
                "group_ids": ["prime_x"],
                "requirement_type": "NONE",
                "requirement_value": "",
                "max_uses": 1,
                "used_count": 1,
                "is_active": True,
            },
        ]

    def list_hidden_code_redemptions(self, limit=500):
        return []

    def list_paid_orders_for_user(self, user_id, limit=500):
        orders = [
            {"order_id": "1", "telegram_user_id": "42", "full_name": "User", "plan_name": "SVIP+ TRỌN ĐỜI", "status": "PAID", "expire_at": "2036-01-01 00:00:00"},
            {"order_id": "2", "telegram_user_id": "99", "full_name": "Other", "plan_name": "VIP 30 Ngày - Hang Cú Prime", "status": "PAID", "expire_at": "2030-01-01 00:00:00"},
        ]
        return [item for item in orders if item["telegram_user_id"] == str(user_id)]


class HiddenGroupTests(unittest.TestCase):
    def setUp(self):
        self.fake_db = FakeDb()
        self.fake_store = FakeHiddenStore()
        self.original_config_db = config_utils.db
        self.original_hidden_store = hidden_group_utils.supabase_store
        config_utils.db = self.fake_db
        hidden_group_utils.supabase_store = self.fake_store

    def tearDown(self):
        config_utils.db = self.original_config_db
        hidden_group_utils.supabase_store = self.original_hidden_store

    def test_validate_hidden_code_requires_svip_lifetime(self):
        hidden_code, reason = hidden_group_utils.validate_hidden_code_for_user("HIDEVIP", "42")
        self.assertIsNotNone(hidden_code)
        self.assertEqual(reason, "")

        denied_code, denied_reason = hidden_group_utils.validate_hidden_code_for_user("HIDEVIP", "99")
        self.assertIsNone(denied_code)
        self.assertIn("SVIP trọn đời", denied_reason)

    def test_validate_hidden_code_respects_max_uses(self):
        hidden_code, reason = hidden_group_utils.validate_hidden_code_for_user("USEDUP", "42")
        self.assertIsNone(hidden_code)
        self.assertIn("hết lượt", reason)

    def test_resolve_plan_groups_supports_main_and_hidden_plans(self):
        main_groups = hidden_group_utils.resolve_plan_groups("VIP 30 Ngày - Hang Cú Prime")
        self.assertEqual(main_groups, [("-100111", "Hang Cú Prime")])

        hidden_group = hidden_group_utils.get_hidden_group("prime_x")
        hidden_plan_name = hidden_group_utils.build_hidden_plan_name(hidden_group, "1M")
        hidden_groups = hidden_group_utils.resolve_plan_groups(hidden_plan_name)
        self.assertEqual(hidden_groups, [("-100999", "Prime X")])

    def test_hidden_offer_contains_token_and_price(self):
        offer = mod_payment.hidden_offer_for_action("hgbuy|HIDEVIP|prime_x|1M", user_id="42", provider="PAYOS")
        self.assertEqual(offer["amount"], 150000)
        self.assertEqual(offer["source_ref"], "HIDEVIP")
        self.assertEqual(offer["metadata"]["hidden_group_id"], "prime_x")
        self.assertTrue(hidden_group_utils.extract_plan_token(offer["plan_name"]).startswith("HG:prime_x"))

    def test_hidden_group_can_be_lifetime_only_when_monthly_price_is_zero(self):
        group = {
            "id": "life_only",
            "name": "Life Only",
            "price_1m_vnd": 0,
            "price_life_vnd": 900000,
            "price_1m_usd": 0,
            "price_life_usd": 49.99,
            "duration_1m_days": 30,
            "lifetime_days": 3650,
        }

        markup = mod_coupon.hidden_buy_buttons("42", "HIDEVIP", [group])
        button_callbacks = [
            button.callback_data
            for row in markup.inline_keyboard
            for button in row
            if button.callback_data
        ]

        self.assertIn("hgbuy|HIDEVIP|life_only|LIFE", button_callbacks)
        self.assertNotIn("hgbuy|HIDEVIP|life_only|1M", button_callbacks)

    def test_hidden_code_is_detected_without_coupon_prefix(self):
        self.assertTrue(mod_coupon.code_is_hidden_exact_match("HIDEVIP"))
        self.assertTrue(mod_coupon.code_is_hidden_exact_match(" hidevip "))
        self.assertFalse(mod_coupon.code_is_hidden_exact_match("THOSANCU_NOPE"))
