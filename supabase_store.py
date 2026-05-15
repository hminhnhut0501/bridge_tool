import os
from datetime import datetime

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
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).isoformat()
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
            return datetime.strptime(raw, fmt).isoformat()
        except ValueError:
            continue
    return None


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
        return [
            order.get("order_id", ""),
            order.get("telegram_user_id", ""),
            order.get("full_name", ""),
            order.get("plan_name", ""),
            order.get("amount", ""),
            order.get("status", ""),
            order.get("paid_at", ""),
            order.get("expire_at", ""),
            order.get("sale_id", ""),
            order.get("original_amount", ""),
            order.get("last_reminder_date", ""),
            order.get("expired_notice_at", ""),
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

    def create_order(self, order_id, telegram_user_id, full_name, plan_name, amount, sale_id="", original_amount=None):
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

    def mark_order_paid(self, order_id, paid_at, expire_at):
        return self.update_order_status(order_id, "PAID", paid_at=paid_at, expire_at=expire_at)

    def mark_order_expired(self, order_id, expired_notice_at=None):
        payload = {"status": "EXPIRED"}
        if expired_notice_at is not None:
            payload["expired_notice_at"] = _parse_datetime(expired_notice_at) or expired_notice_at
        return self.patch_order(order_id, payload)

    def mark_reminder_sent(self, order_id, reminder_date):
        return self.patch_order(order_id, {"last_reminder_date": str(reminder_date)})

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

    def get_coupon(self, code):
        rows = self._request("GET", "coupons", params={"select": "*", "code": f"eq.{_clean_text(code).upper()}", "limit": "1"})
        return rows[0] if rows else None

    def create_coupon_from_sheet_row(self, raw):
        code = _clean_text(raw.get("Code") or raw.get("code")).upper()
        if not code:
            return []
        canonical = dict(raw)
        canonical.setdefault("Code", code)
        canonical.setdefault("Enabled", raw.get("enabled") or raw.get("status") or "ON")
        canonical.setdefault("Plan_Name", raw.get("plan_name") or raw.get("plan") or raw.get("goi") or raw.get("gói") or "")
        canonical.setdefault("Duration_Days", raw.get("duration_days") or raw.get("days") or raw.get("so_ngay") or raw.get("số_ngày") or "")
        canonical.setdefault("Max_Uses", raw.get("max_uses") or raw.get("max_use") or raw.get("max") or "1")
        canonical.setdefault("Used_Count", raw.get("used_count") or raw.get("used") or "0")
        canonical.setdefault("Valid_Until", raw.get("valid_until") or raw.get("expires_at") or "")
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
        return self.upsert_coupon(payload)

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


supabase_store = SupabaseStore()
