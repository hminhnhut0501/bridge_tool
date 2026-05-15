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


supabase_store = SupabaseStore()
