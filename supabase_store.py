import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

load_dotenv()


def _clean_text(value):
    return str(value or "").strip()


def _parse_int(value, default=0):
    try:
        raw = _clean_text(value).replace(".", "").replace(",", "")
        return int(float(raw))
    except (TypeError, ValueError):
        return default


def _parse_datetime(value):
    raw = _clean_text(value)
    if not raw:
        return None

    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo:
            return parsed.isoformat()
        timezone = _bot_timezone()
        return parsed.replace(tzinfo=timezone).isoformat()
    except ValueError:
        pass

    formats = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    )
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=_bot_timezone()).isoformat()
        except ValueError:
            continue
    return None


def _bot_timezone():
    timezone_name = os.getenv("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh"
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def _now_local_text():
    return datetime.now(_bot_timezone()).strftime("%Y-%m-%d %H:%M:%S")


class SupabaseStore:
    def __init__(self):
        self.url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    @property
    def enabled(self):
        return bool(self.url and self.key)

    def connect(self):
        if not self.enabled:
            raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        return self

    def _headers(self, prefer=None):
        headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _url(self, table):
        return f"{self.url}/rest/v1/{table}"

    def _request(self, method, table, *, params=None, json=None, prefer=None):
        self.connect()
        response = requests.request(
            method,
            self._url(table),
            headers=self._headers(prefer=prefer),
            params=params,
            json=json,
            timeout=30,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Supabase {method} {table} failed: {response.status_code} {response.text}")
        if not response.text:
            return []
        return response.json()

    def list_config(self):
        return self.get_config()

    def list_menu_pages(self):
        return self._request("GET", "menu_pages", params={"select": "*", "order": "page_id.asc"})

    def list_sale_rules(self):
        return self._request("GET", "sale_rules", params={"select": "*", "order": "created_at.asc"})

    def upsert_sale_rule(self, raw):
        payload = {
            "sale_id": _clean_text(raw.get("sale_id") or raw.get("sale_code") or raw.get("code")),
            "price_key": _clean_text(raw.get("price_key") or raw.get("key") or raw.get("config_key")).upper(),
            "discount_percent": _parse_int(raw.get("discount_percent") or raw.get("discount") or raw.get("percent"), 0),
            "sale_price": _parse_int(raw.get("sale_price") or raw.get("price_sale"), 0),
            "slot_limit": _parse_int(raw.get("slot_limit") or raw.get("slots"), 0),
            "enabled": str(raw.get("enabled") or raw.get("status") or "ON").strip().upper() not in {"OFF", "FALSE", "NO", "0", "INACTIVE"},
            "raw_data": raw,
        }
        if not payload["sale_id"]:
            payload["sale_id"] = f"{payload['price_key']}:{raw.get('end_at') or raw.get('end') or 'NO_END'}"
        start_at = raw.get("start_at") or raw.get("start")
        end_at = raw.get("end_at") or raw.get("end")
        if start_at:
            payload["starts_at"] = _parse_datetime(start_at) or start_at
        if end_at:
            payload["ends_at"] = _parse_datetime(end_at) or end_at
        return self._request(
            "POST",
            "sale_rules",
            params={"on_conflict": "sale_id"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )

    def count_orders_by_sale_id(self, sale_id, statuses=("PENDING", "PAID")):
        rows = self._request(
            "GET",
            "orders",
            params={"select": "order_id", "sale_id": f"eq.{sale_id}", "status": f"in.({','.join(statuses)})"},
        )
        return len(rows)

    def patch_order(self, order_id, payload):
        return self._request(
            "PATCH",
            "orders",
            params={"order_id": f"eq.{order_id}"},
            json=payload,
            prefer="return=representation",
        )

    def list_orders(self, limit=200):
        return self._request(
            "GET",
            "orders",
            params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
        )

    def get_order(self, order_id):
        rows = self._request(
            "GET",
            "orders",
            params={"select": "*", "order_id": f"eq.{order_id}", "limit": "1"},
        )
        return rows[0] if rows else None

    def list_paid_orders(self, limit=1000):
        return self._request(
            "GET",
            "orders",
            params={
                "select": "*",
                "status": "eq.PAID",
                "order": "expire_at.asc",
                "limit": str(limit),
            },
        )

    def list_paid_orders_for_user(self, telegram_user_id, limit=100):
        return self._request(
            "GET",
            "orders",
            params={
                "select": "*",
                "telegram_user_id": f"eq.{telegram_user_id}",
                "status": "eq.PAID",
                "order": "expire_at.desc",
                "limit": str(limit),
            },
        )

    def order_to_sheet_row(self, order):
        if not order:
            return []
        def value(key):
            return order.get(key) or ""

        return [
            value("order_id"),
            value("telegram_user_id"),
            value("full_name"),
            value("plan_name"),
            value("amount"),
            value("status"),
            value("paid_at"),
            value("expire_at"),
            value("sale_id"),
            value("original_amount"),
            value("last_reminder_date"),
            value("expired_notice_at"),
            value("coupon_code"),
            value("coupon_discount_percent"),
            value("coupon_discount_amount"),
        ]

    def list_users(self, limit=200):
        rows = self._request(
            "GET",
            "orders",
            params={
                "select": "telegram_user_id,full_name,status,plan_name,expire_at,created_at",
                "order": "created_at.desc",
                "limit": "1000",
            },
        )
        users = {}
        for row in rows:
            user_id = row.get("telegram_user_id")
            if not user_id or user_id in users:
                continue
            users[user_id] = row
            if len(users) >= limit:
                break
        return list(users.values())

    def get_config(self):
        return self._request("GET", "bot_config", params={"select": "*", "order": "key.asc"})

    def set_config(self, key, value):
        payload = {"key": _clean_text(key).upper(), "value": str(value)}
        return self._request(
            "POST",
            "bot_config",
            params={"on_conflict": "key"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )

    def set_configs(self, items):
        payload = [
            {"key": _clean_text(item.get("key")).upper(), "value": str(item.get("value", ""))}
            for item in (items or [])
            if _clean_text(item.get("key"))
        ]
        if not payload:
            return []
        return self._request(
            "POST",
            "bot_config",
            params={"on_conflict": "key"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )

    def get_user_preference(self, telegram_user_id):
        rows = self._request(
            "GET",
            "user_preferences",
            params={
                "select": "*",
                "telegram_user_id": f"eq.{_clean_text(telegram_user_id)}",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    def upsert_user_preference(self, telegram_user_id, language):
        payload = {
            "telegram_user_id": _clean_text(telegram_user_id),
            "language": _clean_text(language).lower() or "vi",
        }
        return self._request(
            "POST",
            "user_preferences",
            params={"on_conflict": "telegram_user_id"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )

    def delete_config(self, key):
        return self._request(
            "DELETE",
            "bot_config",
            params={"key": f"eq.{_clean_text(key).upper()}"},
            prefer="return=representation",
        )

    def create_order(
        self,
        order_id,
        telegram_user_id,
        full_name,
        plan_name,
        amount,
        sale_id="",
        original_amount=None,
        coupon_code="",
        coupon_discount_percent=0,
        coupon_discount_amount=0,
    ):
        payload = {
            "order_id": str(order_id),
            "telegram_user_id": str(telegram_user_id),
            "full_name": _clean_text(full_name),
            "plan_name": _clean_text(plan_name),
            "amount": _parse_int(amount),
            "status": "PENDING",
            "sale_id": _clean_text(sale_id),
            "original_amount": _parse_int(original_amount if original_amount is not None else amount),
        }
        if coupon_code:
            payload["coupon_code"] = _clean_text(coupon_code).upper()
            payload["coupon_discount_percent"] = _parse_int(coupon_discount_percent)
            payload["coupon_discount_amount"] = _parse_int(coupon_discount_amount)
        return self._request(
            "POST",
            "orders",
            params={"on_conflict": "order_id"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )

    def update_order_status(self, order_id, status, paid_at=None, expire_at=None):
        payload = {"status": _clean_text(status).upper()}
        if paid_at is not None:
            payload["paid_at"] = _parse_datetime(paid_at) or paid_at
        if expire_at is not None:
            payload["expire_at"] = _parse_datetime(expire_at) or expire_at
        return self.patch_order(order_id, payload)

    def update_order_fields(self, order_id, raw):
        payload = {}
        if "status" in raw:
            payload["status"] = _clean_text(raw.get("status")).upper()
        if "paid_at" in raw:
            payload["paid_at"] = _parse_datetime(raw.get("paid_at")) or raw.get("paid_at")
        if "expire_at" in raw:
            payload["expire_at"] = _parse_datetime(raw.get("expire_at")) or raw.get("expire_at")
        if "expired_notice_at" in raw:
            value = raw.get("expired_notice_at")
            payload["expired_notice_at"] = (_parse_datetime(value) or value) if value else None
        if "plan_name" in raw:
            payload["plan_name"] = _clean_text(raw.get("plan_name"))
        if "coupon_code" in raw:
            payload["coupon_code"] = _clean_text(raw.get("coupon_code")).upper()
        if not payload:
            return []
        return self.patch_order(order_id, payload)

    def mark_order_paid(self, order_id, paid_at, expire_at):
        return self.update_order_status(order_id, "PAID", paid_at=paid_at, expire_at=expire_at)

    def mark_order_expired(self, order_id, expired_notice_at=None):
        payload = {"status": "EXPIRED"}
        if expired_notice_at is not None:
            payload["expired_notice_at"] = _parse_datetime(expired_notice_at) or expired_notice_at
        return self.patch_order(order_id, payload)

    def mark_expired_notice(self, order_id, expired_notice_at):
        return self.patch_order(order_id, {"expired_notice_at": _parse_datetime(expired_notice_at) or expired_notice_at})

    def expire_pending_order(self, order_id):
        return self.patch_order(order_id, {"status": "EXPIRED"})

    def mark_reminder_sent(self, order_id, reminder_date):
        return self.patch_order(order_id, {"last_reminder_date": str(reminder_date)})

    def set_payment_message(self, order_id, chat_id, message_id):
        return self.patch_order(order_id, {
            "payment_message_chat_id": str(chat_id),
            "payment_message_id": int(message_id),
        })

    def upsert_menu_page(self, page_id, image_url, body, layout):
        payload = {
            "page_id": _clean_text(page_id),
            "image_url": _clean_text(image_url),
            "body": str(body or ""),
            "layout": str(layout or ""),
        }
        return self._request(
            "POST",
            "menu_pages",
            params={"on_conflict": "page_id"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )

    def delete_menu_page(self, page_id):
        return self._request(
            "DELETE",
            "menu_pages",
            params={"page_id": f"eq.{_clean_text(page_id)}"},
            prefer="return=representation",
        )

    def upsert_coupon(self, payload):
        return self._request(
            "POST",
            "coupons",
            params={"on_conflict": "code"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )

    def list_coupons(self):
        return self._request("GET", "coupons", params={"select": "*", "order": "created_at.desc"})

    def delete_sale_rule(self, sale_id):
        return self._request(
            "DELETE",
            "sale_rules",
            params={"sale_id": f"eq.{_clean_text(sale_id)}"},
            prefer="return=representation",
        )

    def delete_coupon(self, code):
        return self._request(
            "DELETE",
            "coupons",
            params={"code": f"eq.{_clean_text(code).upper()}"},
            prefer="return=representation",
        )

    def list_blacklist(self, limit=500):
        return self._request(
            "GET",
            "security_blacklist",
            params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
        )

    def get_blacklist_entry(self, telegram_user_id):
        rows = self._request(
            "GET",
            "security_blacklist",
            params={
                "select": "*",
                "telegram_user_id": f"eq.{telegram_user_id}",
                "is_active": "eq.true",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    def upsert_blacklist(self, raw):
        telegram_user_id = _clean_text(raw.get("telegram_user_id") or raw.get("Telegram_User_ID") or raw.get("user_id"))
        if not telegram_user_id:
            return []
        is_active_raw = raw.get("is_active", True)
        is_active = str(is_active_raw).strip().upper() not in {"OFF", "FALSE", "NO", "0", "INACTIVE"}
        payload = {
            "telegram_user_id": telegram_user_id,
            "username": _clean_text(raw.get("username") or raw.get("Username") or ""),
            "full_name": _clean_text(raw.get("full_name") or raw.get("Full_Name") or ""),
            "reason": _clean_text(raw.get("reason") or raw.get("Reason") or "Manual blacklist"),
            "source": _clean_text(raw.get("source") or raw.get("Source") or "dashboard"),
            "is_active": is_active,
            "raw_data": raw.get("raw_data") or {},
        }
        return self._request(
            "POST",
            "security_blacklist",
            params={"on_conflict": "telegram_user_id"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )

    def delete_blacklist(self, telegram_user_id):
        return self._request(
            "DELETE",
            "security_blacklist",
            params={"telegram_user_id": f"eq.{telegram_user_id}"},
            prefer="return=representation",
        )

    def record_support_event(self, event_type, telegram_user_id=None, **kwargs):
        payload = {
            "event_type": _clean_text(event_type),
            "telegram_user_id": _clean_text(telegram_user_id),
            "username": _clean_text(kwargs.get("username")),
            "full_name": _clean_text(kwargs.get("full_name")),
            "chat_id": _clean_text(kwargs.get("chat_id")),
            "chat_title": _clean_text(kwargs.get("chat_title")),
            "order_id": _clean_text(kwargs.get("order_id")),
            "plan_name": _clean_text(kwargs.get("plan_name")),
            "raw_data": kwargs.get("raw_data") or {},
        }
        return self._request("POST", "support_events", json=payload, prefer="return=representation")

    def list_support_events(self, limit=500):
        return self._request(
            "GET",
            "support_events",
            params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
        )

    def get_coupon(self, code):
        rows = self._request("GET", "coupons", params={"select": "*", "code": f"eq.{_clean_text(code).upper()}", "limit": "1"})
        return rows[0] if rows else None

    def _coupon_payload_from_sheet_row(self, raw):
        code = _clean_text(raw.get("Code") or raw.get("code")).upper()
        if not code:
            return None
        canonical = dict(raw)
        canonical.setdefault("Code", code)
        canonical.setdefault("Enabled", raw.get("enabled") or raw.get("status") or "ON")
        canonical.setdefault("Plan_Name", raw.get("plan_name") or raw.get("plan") or raw.get("goi") or raw.get("gói") or "")
        canonical.setdefault("Duration_Days", raw.get("duration_days") or raw.get("days") or raw.get("so_ngay") or raw.get("số_ngày") or "")
        canonical.setdefault("Max_Uses", raw.get("max_uses") or raw.get("max_use") or raw.get("max") or "1")
        canonical.setdefault("Used_Count", raw.get("used_count") or raw.get("used") or "0")
        canonical.setdefault("Valid_Until", raw.get("valid_until") or raw.get("expires_at") or "")
        canonical.setdefault("Coupon_Type", raw.get("coupon_type") or raw.get("type") or raw.get("loai") or "ACTIVATION")
        canonical.setdefault("Discount_Percent", raw.get("discount_percent") or raw.get("discount") or raw.get("percent") or "")
        canonical.setdefault("Applies_To", raw.get("applies_to") or raw.get("apply_to") or raw.get("packages") or "")
        max_uses = _parse_int(canonical.get("Max_Uses"), 1)
        used_count = _parse_int(canonical.get("Used_Count"), 0)
        enabled = str(canonical.get("Enabled") or "ON").strip().upper() not in {"OFF", "FALSE", "NO", "0", "INACTIVE"}
        payload = {
            "code": code,
            "plan_name": canonical.get("Plan_Name"),
            "amount": 0,
            "status": "ACTIVE" if enabled else "INACTIVE",
            "max_uses": max_uses,
            "used_count": used_count,
            "raw_data": canonical,
        }
        valid_until = canonical.get("Valid_Until")
        if valid_until:
            payload["expires_at"] = _parse_datetime(valid_until) or valid_until
        return payload

    def create_coupon_from_sheet_row(self, raw):
        payload = self._coupon_payload_from_sheet_row(raw)
        if not payload:
            return []
        return self.upsert_coupon(payload)

    def create_coupons_from_sheet_rows(self, rows):
        payloads = [payload for payload in (self._coupon_payload_from_sheet_row(row or {}) for row in rows or []) if payload]
        if not payloads:
            return []
        return self.upsert_coupon(payloads)

    def consume_coupon_for_order(self, order):
        code = _clean_text((order or {}).get("coupon_code")).upper()
        if not code:
            return []

        coupon = self.get_coupon(code)
        if not coupon:
            return []

        raw = dict(coupon.get("raw_data") or {})
        used_count = _parse_int(raw.get("Used_Count") or coupon.get("used_count"), 0) + 1
        used_at = _now_local_text()
        raw.update({
            "Used_Count": str(used_count),
            "Last_Used_At": used_at,
            "Last_Used_By": str(order.get("telegram_user_id") or ""),
        })
        updated = self._request(
            "PATCH",
            "coupons",
            params={"code": f"eq.{code}"},
            json={"used_count": used_count, "raw_data": raw},
            prefer="return=representation",
        )
        self.record_coupon_redemption(
            code,
            order.get("telegram_user_id"),
            order_id=order.get("order_id"),
            raw_data={
                "Redeemed_At": used_at,
                "Code": code,
                "User_ID": str(order.get("telegram_user_id") or ""),
                "Full_Name": order.get("full_name") or "",
                "Plan_Name": order.get("plan_name") or "",
                "Status": "PAID_DISCOUNT",
                "User_Order_ID": str(order.get("order_id") or ""),
                "Discount_Percent": str(order.get("coupon_discount_percent") or ""),
                "Discount_Amount": str(order.get("coupon_discount_amount") or ""),
            },
        )
        return updated

    def update_coupon_raw(self, code, raw_updates):
        coupon = self.get_coupon(code)
        if not coupon:
            return []
        raw = dict(coupon.get("raw_data") or {})
        raw.update(raw_updates)
        payload = {
            "used_count": _parse_int(raw.get("Used_Count") or raw.get("used_count"), coupon.get("used_count") or 0),
            "raw_data": raw,
        }
        return self._request(
            "PATCH",
            "coupons",
            params={"code": f"eq.{_clean_text(code).upper()}"},
            json=payload,
            prefer="return=representation",
        )

    def has_coupon_redemption(self, code, telegram_user_id):
        rows = self._request(
            "GET",
            "coupon_redemptions",
            params={
                "select": "id",
                "coupon_code": f"eq.{_clean_text(code).upper()}",
                "telegram_user_id": f"eq.{telegram_user_id}",
                "limit": "1",
            },
        )
        return bool(rows)

    def record_coupon_redemption(self, code, telegram_user_id, order_id=None, raw_data=None):
        payload = {
            "coupon_code": _clean_text(code).upper(),
            "telegram_user_id": str(telegram_user_id),
            "order_id": str(order_id or ""),
            "raw_data": raw_data or {},
        }
        return self._request("POST", "coupon_redemptions", json=payload, prefer="return=representation")

    def list_coupon_redemptions(self, code=None):
        params = {"select": "*", "order": "redeemed_at.desc"}
        if code:
            params["coupon_code"] = f"eq.{_clean_text(code).upper()}"
        return self._request("GET", "coupon_redemptions", params=params)

    def insert_analytics_events(self, events):
        payload = [
            {
                "event_name": event.get("event_type") or "event",
                "telegram_user_id": event.get("user_id") or None,
                "payload": event,
            }
            for event in events
        ]
        if not payload:
            return []
        return self._request("POST", "analytics_events", json=payload)

    def list_analytics_events(self, limit=500):
        return self._request(
            "GET",
            "analytics_events",
            params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
        )


supabase_store = SupabaseStore()
