import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

load_dotenv()


def _clean_text(value):
    return str(value or "").strip()


def _norm_filter_text(value):
    return _clean_text(value).casefold()


def _clean_display_text(value):
    text = _clean_text(value)
    return "" if text == "-" else text


def _parse_int(value, default=0):
    try:
        raw = _clean_text(value).replace(".", "").replace(",", "")
        return int(float(raw))
    except (TypeError, ValueError):
        return default


def _parse_number(value, default=0):
    try:
        raw = _clean_text(value).replace(",", ".")
        number = float(raw)
        return int(number) if number.is_integer() else round(number, 2)
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


def _datetime_value(value):
    parsed = _parse_datetime(value)
    if not parsed:
        return None
    try:
        return datetime.fromisoformat(parsed)
    except ValueError:
        return None


def _bot_timezone():
    timezone_name = os.getenv("BOT_TIMEZONE", "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh"
    try:
        return ZoneInfo(timezone_name)
    except Exception:
        return ZoneInfo("Asia/Ho_Chi_Minh")


def _now_local_text():
    return datetime.now(_bot_timezone()).strftime("%Y-%m-%d %H:%M:%S")


def _now_iso():
    return datetime.now(_bot_timezone()).isoformat()


def _normalize_payment_provider(order):
    if not isinstance(order, dict):
        return order
    provider = _clean_text(order.get("payment_provider")).upper()
    if provider:
        order["payment_provider"] = provider
        return order
    metadata = order.get("metadata") if isinstance(order.get("metadata"), dict) else {}
    metadata_provider = _clean_text(
        metadata.get("payment_provider")
        or metadata.get("payment_method")
        or metadata.get("provider")
        or metadata.get("provider_name")
        or metadata.get("payment_gateway")
    ).upper()
    if metadata_provider in {"PAYOS", "PAYPAL", "NOWPAYMENTS", "TRON_USDT", "BINANCE_PAY"}:
        order["payment_provider"] = metadata_provider
        return order
    approval_url = _clean_text(order.get("payment_approval_url") or metadata.get("payment_approval_url") or metadata.get("approval_url")).lower()
    provider_order_id = _clean_text(order.get("payment_provider_order_id") or metadata.get("payment_provider_order_id") or metadata.get("provider_order_id")).lower()
    source_type = _clean_text(order.get("source_type") or metadata.get("source_type")).upper()
    if "payos" in approval_url or "vietqr" in approval_url or source_type == "PAYOS" or provider_order_id.startswith("payos_"):
        order["payment_provider"] = "PAYOS"
    elif "paypal" in approval_url or source_type == "PAYPAL" or provider_order_id.startswith("paypal_"):
        order["payment_provider"] = "PAYPAL"
    elif "nowpayments" in approval_url or source_type == "NOWPAYMENTS" or provider_order_id.startswith("nowpayments_"):
        order["payment_provider"] = "NOWPAYMENTS"
    elif "trc20" in approval_url or source_type == "TRON_USDT":
        order["payment_provider"] = "TRON_USDT"
    elif "sieuthicode" in approval_url or source_type == "BINANCE_PAY" or provider_order_id.startswith("binance_pay_"):
        order["payment_provider"] = "BINANCE_PAY"
    return order


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
            "sale_price": _parse_number(raw.get("sale_price") or raw.get("price_sale"), 0),
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
        rows = self._request(
            "GET",
            "orders",
            params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
        )
        return [_normalize_payment_provider(row) for row in rows]

    def get_order(self, order_id):
        rows = self._request(
            "GET",
            "orders",
            params={"select": "*", "order_id": f"eq.{order_id}", "limit": "1"},
        )
        return _normalize_payment_provider(rows[0]) if rows else None

    def list_paid_orders(self, limit=1000):
        rows = self._request(
            "GET",
            "orders",
            params={
                "select": "*",
                "status": "eq.PAID",
                "order": "expire_at.asc",
                "limit": str(limit),
            },
        )
        return [_normalize_payment_provider(row) for row in rows]

    def list_pending_orders(self, limit=1000):
        rows = self._request(
            "GET",
            "orders",
            params={
                "select": "*",
                "status": "eq.PENDING",
                "order": "created_at.asc",
                "limit": str(limit),
            },
        )
        return [_normalize_payment_provider(row) for row in rows]

    def list_scheduler_orders(self, limit=1000):
        rows = self._request(
            "GET",
            "orders",
            params={
                "select": "*",
                "status": "in.(PAID,EXPIRED)",
                "order": "expire_at.asc",
                "limit": str(limit),
            },
        )
        return [_normalize_payment_provider(row) for row in rows]

    def list_scheduler_due_orders(self, due_before, limit=1000):
        due_value = _parse_datetime(due_before) or str(due_before)
        paid_rows = self._request(
            "GET",
            "orders",
            params={
                "select": "*",
                "status": "eq.PAID",
                "expire_at": f"lte.{due_value}",
                "order": "expire_at.asc",
                "limit": str(limit),
            },
        )
        paid_rows = [_normalize_payment_provider(row) for row in paid_rows]
        remaining = max(0, int(limit) - len(paid_rows))
        if remaining <= 0:
            return paid_rows
        expired_rows = self._request(
            "GET",
            "orders",
            params={
                "select": "*",
                "status": "eq.EXPIRED",
                "order": "expire_at.asc",
                "limit": str(remaining),
            },
        )
        expired_rows = [_normalize_payment_provider(row) for row in expired_rows]
        seen = {str(row.get("order_id")) for row in paid_rows}
        return paid_rows + [row for row in expired_rows if str(row.get("order_id")) not in seen]

    def list_paid_orders_for_user(self, telegram_user_id, limit=100):
        rows = self._request(
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
        return [_normalize_payment_provider(row) for row in rows]

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
        rows = self._request(
            "POST",
            "bot_config",
            params={"on_conflict": "key"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )
        try:
            from helpers import invalidate_bot_runtime_state_cache

            invalidate_bot_runtime_state_cache()
        except Exception:
            pass
        return rows

    def set_configs(self, items):
        payload = [
            {"key": _clean_text(item.get("key")).upper(), "value": str(item.get("value", ""))}
            for item in (items or [])
            if _clean_text(item.get("key"))
        ]
        if not payload:
            return []
        rows = self._request(
            "POST",
            "bot_config",
            params={"on_conflict": "key"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )
        try:
            from helpers import invalidate_bot_runtime_state_cache

            invalidate_bot_runtime_state_cache()
        except Exception:
            pass
        return rows

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
        rows = self._request(
            "DELETE",
            "bot_config",
            params={"key": f"eq.{_clean_text(key).upper()}"},
            prefer="return=representation",
        )
        try:
            from helpers import invalidate_bot_runtime_state_cache

            invalidate_bot_runtime_state_cache()
        except Exception:
            pass
        return rows

    def get_bot_runtime_state(self):
        rows = self._request(
            "GET",
            "bot_runtime_state",
            params={"select": "*", "id": "eq.main", "limit": "1"},
        )
        return rows[0] if rows else None

    def list_bot_schedule_rules(self, limit=200):
        return self._request(
            "GET",
            "bot_schedule_rules",
            params={"select": "*", "order": "active_from.asc", "limit": str(limit)},
        )

    def upsert_bot_schedule_rule(self, raw):
        payload = {
            "bot_key": _clean_text((raw or {}).get("bot_key") or "main") or "main",
            "channel_post_id": _parse_int((raw or {}).get("channel_post_id"), 0),
            "enabled": bool((raw or {}).get("enabled", True)),
            "repeat_daily": bool((raw or {}).get("repeat_daily", False)),
            "sync_bot_schedule": bool((raw or {}).get("sync_bot_schedule", False)),
            "active_from": _parse_datetime((raw or {}).get("active_from")) if (raw or {}).get("active_from") else None,
            "active_to": _parse_datetime((raw or {}).get("active_to")) if (raw or {}).get("active_to") else None,
            "timezone": _clean_text((raw or {}).get("timezone") or "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh",
            "source_post_title": _clean_text((raw or {}).get("source_post_title") or ""),
            "source_post_status": _clean_text((raw or {}).get("source_post_status") or ""),
            "source_post_target_chat_id": _clean_text((raw or {}).get("source_post_target_chat_id") or ""),
            "notes": _clean_text((raw or {}).get("notes") or ""),
        }
        return self._request(
            "POST",
            "bot_schedule_rules",
            params={"on_conflict": "channel_post_id"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )

    def delete_bot_schedule_rule(self, channel_post_id):
        return self._request(
            "DELETE",
            "bot_schedule_rules",
            params={"channel_post_id": f"eq.{_clean_text(channel_post_id)}"},
            prefer="return=representation",
        )

    def upsert_bot_runtime_state(self, raw):
        payload = {
            "id": _clean_text((raw or {}).get("id") or "main") or "main",
            "effective_mode": _clean_text((raw or {}).get("effective_mode") or (raw or {}).get("source") or "always") or "always",
            "source": _clean_text((raw or {}).get("source") or (raw or {}).get("effective_mode") or "always") or "always",
            "active": bool((raw or {}).get("active", True)),
            "title": _clean_text((raw or {}).get("title") or ""),
            "window": _clean_text((raw or {}).get("window") or ""),
            "detail": _clean_text((raw or {}).get("detail") or ""),
            "timezone": _clean_text((raw or {}).get("timezone") or "Asia/Ho_Chi_Minh") or "Asia/Ho_Chi_Minh",
            "linked_count": _parse_int((raw or {}).get("linked_count"), 0),
            "maintenance_mode": bool((raw or {}).get("maintenance_mode", False)),
            "maintenance_override": bool((raw or {}).get("maintenance_override", False)),
            "fixed_schedule_enabled": bool((raw or {}).get("fixed_schedule_enabled", False)),
            "active_hours": _clean_text((raw or {}).get("active_hours") or ""),
            "source_post_id": _clean_text((raw or {}).get("source_post_id") or ""),
            "source_post_title": _clean_text((raw or {}).get("source_post_title") or ""),
            "window_start": _parse_datetime((raw or {}).get("window_start")) if (raw or {}).get("window_start") else None,
            "window_end": _parse_datetime((raw or {}).get("window_end")) if (raw or {}).get("window_end") else None,
            "raw_data": (raw or {}).get("raw_data") or {},
        }
        return self._request(
            "POST",
            "bot_runtime_state",
            params={"on_conflict": "id"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
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
        payment_provider="",
        payment_provider_order_id="",
        payment_approval_url="",
        payment_currency="VND",
        plan_token="",
        plan_category="",
        source_type="",
        source_ref="",
        metadata=None,
    ):
        payload = {
            "order_id": str(order_id),
            "telegram_user_id": str(telegram_user_id),
            "full_name": _clean_text(full_name),
            "plan_name": _clean_text(plan_name),
            "amount": _parse_number(amount),
            "status": "PENDING",
            "sale_id": _clean_text(sale_id),
            "original_amount": _parse_number(original_amount if original_amount is not None else amount),
        }
        if coupon_code:
            payload["coupon_code"] = _clean_text(coupon_code).upper()
            payload["coupon_discount_percent"] = _parse_int(coupon_discount_percent)
            payload["coupon_discount_amount"] = _parse_number(coupon_discount_amount)
        if payment_provider:
            payload["payment_provider"] = _clean_text(payment_provider).upper()
        if payment_provider_order_id:
            payload["payment_provider_order_id"] = _clean_text(payment_provider_order_id)
        if payment_approval_url:
            payload["payment_approval_url"] = _clean_text(payment_approval_url)
        if payment_currency:
            payload["payment_currency"] = _clean_text(payment_currency).upper()
        if plan_token:
            payload["plan_token"] = _clean_text(plan_token)
        if plan_category:
            payload["plan_category"] = _clean_text(plan_category).upper()
        if source_type:
            payload["source_type"] = _clean_text(source_type).upper()
        if source_ref:
            payload["source_ref"] = _clean_text(source_ref)
        if metadata is not None:
            payload["metadata"] = metadata
        try:
            return self._request(
                "POST",
                "orders",
                params={"on_conflict": "order_id"},
                json=payload,
                prefer="resolution=merge-duplicates,return=representation",
            )
        except RuntimeError as exc:
            # Keep existing PayOS orders working while the payment-provider
            # migration is waiting to be applied in Supabase.
            missing_optional_column = any(
                column in str(exc)
                for column in (
                    "payment_provider",
                    "payment_currency",
                    "plan_token",
                    "plan_category",
                    "source_type",
                    "source_ref",
                    "metadata",
                )
            )
            if not missing_optional_column:
                raise
            legacy_payload = dict(payload)
            legacy_payload.pop("payment_provider", None)
            legacy_payload.pop("payment_provider_order_id", None)
            legacy_payload.pop("payment_approval_url", None)
            legacy_payload.pop("payment_currency", None)
            legacy_metadata = legacy_payload.get("metadata") if isinstance(legacy_payload.get("metadata"), dict) else {}
            if payment_provider:
                legacy_metadata["payment_provider"] = _clean_text(payment_provider).upper()
            if payment_provider_order_id:
                legacy_metadata["payment_provider_order_id"] = _clean_text(payment_provider_order_id)
            if payment_approval_url:
                legacy_metadata["payment_approval_url"] = _clean_text(payment_approval_url)
            if payment_currency:
                legacy_metadata["payment_currency"] = _clean_text(payment_currency).upper()
            if legacy_metadata:
                legacy_payload["metadata"] = legacy_metadata
            for optional_column in ("plan_token", "plan_category", "source_type", "source_ref", "metadata"):
                if optional_column in str(exc):
                    legacy_payload.pop(optional_column, None)
            return self._request(
                "POST",
                "orders",
                params={"on_conflict": "order_id"},
                json=legacy_payload,
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
        if "plan_token" in raw:
            payload["plan_token"] = _clean_text(raw.get("plan_token"))
        if "plan_category" in raw:
            payload["plan_category"] = _clean_text(raw.get("plan_category")).upper()
        if "source_type" in raw:
            payload["source_type"] = _clean_text(raw.get("source_type")).upper()
        if "source_ref" in raw:
            payload["source_ref"] = _clean_text(raw.get("source_ref"))
        if "metadata" in raw:
            payload["metadata"] = raw.get("metadata")
        if "payment_provider" in raw:
            payload["payment_provider"] = _clean_text(raw.get("payment_provider")).upper()
        if "payment_provider_order_id" in raw:
            payload["payment_provider_order_id"] = _clean_text(raw.get("payment_provider_order_id"))
        if "payment_approval_url" in raw:
            payload["payment_approval_url"] = _clean_text(raw.get("payment_approval_url"))
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
        coupons = self._request("GET", "coupons", params={"select": "*", "order": "created_at.desc"})
        try:
            redemptions = self.list_coupon_redemptions(limit=5000)
        except Exception:
            redemptions = []
        latest_redemption_by_code = {}
        redemption_count_by_code = {}
        for redemption in redemptions or []:
            code = _clean_text(redemption.get("coupon_code")).upper()
            if not code:
                continue
            redemption_count_by_code[code] = redemption_count_by_code.get(code, 0) + 1
            current = latest_redemption_by_code.get(code)
            if not current or str(redemption.get("redeemed_at") or "") > str(current.get("redeemed_at") or ""):
                latest_redemption_by_code[code] = redemption
        for coupon in coupons:
            code = _clean_text(coupon.get("code")).upper()
            latest = latest_redemption_by_code.get(code) or {}
            raw = dict(coupon.get("raw_data") or {})
            coupon["redemption_count"] = redemption_count_by_code.get(code, _parse_int(coupon.get("used_count"), 0))
            coupon["last_redeemed_at"] = latest.get("redeemed_at")
            coupon["last_redeemed_by"] = latest.get("telegram_user_id")
            coupon["last_redeemed_order_id"] = latest.get("order_id")
            latest_raw = dict(latest.get("raw_data") or {})
            coupon["last_redeemed_full_name"] = latest_raw.get("Full_Name") or latest_raw.get("full_name") or ""
            coupon["last_redeemed_username"] = latest_raw.get("Username") or latest_raw.get("username") or ""
            raw.setdefault("Last_Redeemed_At", coupon["last_redeemed_at"] or "")
            raw.setdefault("Last_Redeemed_By", coupon["last_redeemed_by"] or "")
            raw.setdefault("Last_Redeemed_Full_Name", coupon["last_redeemed_full_name"] or "")
            raw.setdefault("Last_Redeemed_Username", coupon["last_redeemed_username"] or "")
            coupon["raw_data"] = raw
        return coupons

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
            "username": _clean_display_text(kwargs.get("username")),
            "full_name": _clean_display_text(kwargs.get("full_name")),
            "chat_id": _clean_text(kwargs.get("chat_id")),
            "chat_title": _clean_text(kwargs.get("chat_title")),
            "order_id": _clean_text(kwargs.get("order_id")),
            "plan_name": _clean_text(kwargs.get("plan_name")),
            "raw_data": kwargs.get("raw_data") or {},
        }
        return self._request("POST", "support_events", json=payload, prefer="return=representation")

    def get_user_identity(self, telegram_user_id):
        user_id = _clean_text(telegram_user_id)
        if not user_id:
            return {}

        try:
            rows = self._request(
                "GET",
                "orders",
                params={
                    "select": "telegram_user_id,full_name",
                    "telegram_user_id": f"eq.{user_id}",
                    "order": "created_at.desc",
                    "limit": "1",
                },
            )
            if rows and _clean_text(rows[0].get("full_name")):
                return {"full_name": _clean_text(rows[0].get("full_name"))}
        except Exception:
            pass

        try:
            rows = self._request(
                "GET",
                "support_events",
                params={
                    "select": "username,full_name",
                    "telegram_user_id": f"eq.{user_id}",
                    "order": "created_at.desc",
                    "limit": "1",
                },
            )
            if rows:
                return {
                    "username": _clean_text(rows[0].get("username")),
                    "full_name": _clean_text(rows[0].get("full_name")),
                }
        except Exception:
            pass

        return {}

    def _order_names_by_user_ids(self, telegram_user_ids):
        ids = sorted({_clean_text(item) for item in telegram_user_ids if _clean_text(item)})
        if not ids:
            return {}

        names = {}
        chunk_size = 80
        for start in range(0, len(ids), chunk_size):
            chunk = ids[start:start + chunk_size]
            try:
                rows = self._request(
                    "GET",
                    "orders",
                    params={
                        "select": "telegram_user_id,full_name,created_at",
                        "telegram_user_id": f"in.({','.join(chunk)})",
                        "order": "created_at.desc",
                        "limit": "1000",
                    },
                )
            except Exception:
                continue

            for row in rows:
                user_id = _clean_text(row.get("telegram_user_id"))
                full_name = _clean_display_text(row.get("full_name"))
                if user_id and full_name and user_id not in names:
                    names[user_id] = full_name
        return names

    def _enrich_support_event_names(self, rows):
        names_by_user_id = {}
        usernames_by_user_id = {}

        for row in rows:
            user_id = _clean_text(row.get("telegram_user_id"))
            if not user_id:
                continue

            full_name = _clean_display_text(row.get("full_name"))
            username = _clean_display_text(row.get("username"))
            raw = row.get("raw_data") or {}
            raw_full_name = _clean_display_text(raw.get("full_name") or raw.get("Full_Name"))
            raw_username = _clean_display_text(raw.get("username") or raw.get("Username"))

            if full_name and user_id not in names_by_user_id:
                names_by_user_id[user_id] = full_name
            elif raw_full_name and user_id not in names_by_user_id:
                names_by_user_id[user_id] = raw_full_name

            if username and user_id not in usernames_by_user_id:
                usernames_by_user_id[user_id] = username
            elif raw_username and user_id not in usernames_by_user_id:
                usernames_by_user_id[user_id] = raw_username

        missing_name_ids = [
            _clean_text(row.get("telegram_user_id"))
            for row in rows
            if _clean_text(row.get("telegram_user_id")) and not names_by_user_id.get(_clean_text(row.get("telegram_user_id")))
        ]
        names_by_user_id.update(self._order_names_by_user_ids(missing_name_ids))

        for row in rows:
            user_id = _clean_text(row.get("telegram_user_id"))
            if not user_id:
                continue
            if not _clean_display_text(row.get("full_name")) and names_by_user_id.get(user_id):
                row["full_name"] = names_by_user_id[user_id]
            if not _clean_display_text(row.get("username")) and usernames_by_user_id.get(user_id):
                row["username"] = usernames_by_user_id[user_id]
        return rows

    def list_support_events(self, limit=500):
        rows = self._request(
            "GET",
            "support_events",
            params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
        )
        return self._enrich_support_event_names(rows)

    def latest_support_event(self, event_type, telegram_user_id=None, order_id=None, chat_id=None):
        params = {
            "select": "*",
            "event_type": f"eq.{_clean_text(event_type)}",
            "order": "created_at.desc",
            "limit": "1",
        }
        if telegram_user_id is not None:
            params["telegram_user_id"] = f"eq.{_clean_text(telegram_user_id)}"
        if order_id is not None:
            params["order_id"] = f"eq.{_clean_text(order_id)}"
        if chat_id is not None:
            params["chat_id"] = f"eq.{_clean_text(chat_id)}"
        rows = self._request("GET", "support_events", params=params)
        return rows[0] if rows else None

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

    def list_hidden_groups(self):
        return self._request("GET", "hidden_groups", params={"select": "*", "order": "sort_order.asc,name.asc"})

    def upsert_hidden_group(self, raw):
        payload = {
            "id": _clean_text(raw.get("id")),
            "name": _clean_text(raw.get("name")),
            "description": _clean_text(raw.get("description")),
            "chat_id": _clean_text(raw.get("chat_id")),
            "price_1m_vnd": _parse_number(raw.get("price_1m_vnd"), 0),
            "price_life_vnd": _parse_number(raw.get("price_life_vnd"), 0),
            "price_1m_usd": _parse_number(raw.get("price_1m_usd"), 0),
            "price_life_usd": _parse_number(raw.get("price_life_usd"), 0),
            "duration_1m_days": _parse_int(raw.get("duration_1m_days"), 30),
            "lifetime_days": _parse_int(raw.get("lifetime_days"), 3650),
            "image_url": _clean_text(raw.get("image_url")),
            "requirement_type": _clean_text(raw.get("requirement_type")).upper() or "NONE",
            "requirement_value": _clean_text(raw.get("requirement_value")),
            "sort_order": _parse_int(raw.get("sort_order"), 0),
            "is_active": bool(raw.get("is_active")) if isinstance(raw.get("is_active"), bool) else str(raw.get("is_active", "ON")).strip().upper() not in {"OFF", "FALSE", "NO", "0"},
        }
        return self._request(
            "POST",
            "hidden_groups",
            params={"on_conflict": "id"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )

    def delete_hidden_group(self, hidden_group_id):
        return self._request(
            "DELETE",
            "hidden_groups",
            params={"id": f"eq.{_clean_text(hidden_group_id)}"},
            prefer="return=representation",
        )

    def list_hidden_codes(self):
        return self._request("GET", "hidden_codes", params={"select": "*", "order": "code.asc"})

    def upsert_hidden_code(self, raw):
        payload = {
            "code": _clean_text(raw.get("code")).upper(),
            "name": _clean_text(raw.get("name")),
            "description": _clean_text(raw.get("description")),
            "scope_type": _clean_text(raw.get("scope_type")).upper() or "SELECTED_GROUPS",
            "group_ids": raw.get("group_ids") or [],
            "requirement_type": _clean_text(raw.get("requirement_type")).upper() or None,
            "requirement_value": _clean_text(raw.get("requirement_value")),
            "max_uses": _parse_int(raw.get("max_uses"), 0),
            "used_count": _parse_int(raw.get("used_count"), 0),
            "valid_from": _parse_datetime(raw.get("valid_from")) or None,
            "valid_until": _parse_datetime(raw.get("valid_until")) or None,
            "is_active": bool(raw.get("is_active")) if isinstance(raw.get("is_active"), bool) else str(raw.get("is_active", "ON")).strip().upper() not in {"OFF", "FALSE", "NO", "0"},
        }
        return self._request(
            "POST",
            "hidden_codes",
            params={"on_conflict": "code"},
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
        )

    def delete_hidden_code(self, code):
        return self._request(
            "DELETE",
            "hidden_codes",
            params={"code": f"eq.{_clean_text(code).upper()}"},
            prefer="return=representation",
        )

    def list_hidden_code_redemptions(self, limit=500):
        return self._request(
            "GET",
            "hidden_code_redemptions",
            params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
        )

    def record_hidden_code_redemption(self, raw):
        payload = {
            "code": _clean_text(raw.get("code")).upper(),
            "telegram_user_id": _clean_text(raw.get("telegram_user_id")),
            "full_name": _clean_text(raw.get("full_name")),
            "username": _clean_text(raw.get("username")),
            "revealed_group_ids": raw.get("revealed_group_ids") or [],
            "created_at": _parse_datetime(raw.get("created_at")) or _now_iso(),
        }
        return self._request(
            "POST",
            "hidden_code_redemptions",
            json=payload,
            prefer="return=representation",
        )

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

    def list_coupon_redemptions(self, code=None, limit=500):
        params = {"select": "*", "order": "redeemed_at.desc", "limit": str(limit)}
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
        fetch_limit = min(max(int(limit) * 5, int(limit)), 5000)
        rows = self._request(
            "GET",
            "analytics_events",
            params={"select": "*", "order": "created_at.desc", "limit": str(fetch_limit)},
        )
        visible = []
        for row in rows:
            payload = row.get("payload") or {}
            chat_type = _clean_text(payload.get("chat_type")).lower()
            if chat_type in {"group", "supergroup", "channel"}:
                continue
            visible.append(row)
            if len(visible) >= int(limit):
                break
        return visible

    def _recent_interacted_users(self, limit=5000):
        rows = self._request(
            "GET",
            "analytics_events",
            params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
        )
        users = {}
        for row in rows or []:
            payload = row.get("payload") or {}
            chat_type = _clean_text(payload.get("chat_type")).lower()
            user_id = _clean_text(row.get("telegram_user_id") or payload.get("user_id"))
            if not user_id or chat_type in {"group", "supergroup", "channel"}:
                continue
            users.setdefault(user_id, {
                "telegram_user_id": user_id,
                "username": _clean_display_text(payload.get("username")),
                "full_name": _clean_display_text(payload.get("full_name")),
                "last_interaction_at": row.get("created_at"),
            })
        return users

    def _orders_by_user_for_campaigns(self, limit=5000):
        rows = self._request(
            "GET",
            "orders",
            params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
        )
        grouped = {}
        for order in rows or []:
            user_id = _clean_text(order.get("telegram_user_id"))
            if not user_id:
                continue
            grouped.setdefault(user_id, []).append(order)
        return grouped

    def _broadcast_plan_matches(self, plan_name, plan_filter):
        target = _norm_filter_text(plan_filter)
        if not target or target == "all":
            return True
        return _norm_filter_text(plan_name) == target

    def build_broadcast_recipients(self, segment="ALL", limit=5000, plan_filter="ALL", plan_match_scope="ANY_PAID"):
        segment_key = _clean_text(segment).upper() or "ALL"
        plan_filter = _clean_text(plan_filter) or "ALL"
        plan_match_scope = _clean_text(plan_match_scope).upper() or "ANY_PAID"
        interacted = self._recent_interacted_users(limit=limit)
        orders_by_user = self._orders_by_user_for_campaigns(limit=limit)
        blacklist_ids = set()
        try:
            blacklist_ids = {
                _clean_text(item.get("telegram_user_id"))
                for item in self.list_blacklist(limit=5000)
                if item.get("is_active") and _clean_text(item.get("telegram_user_id"))
            }
        except Exception:
            blacklist_ids = set()

        now = datetime.now(_bot_timezone())
        user_ids = set(interacted) | set(orders_by_user)
        recipients = []
        for user_id in sorted(user_ids):
            if user_id in blacklist_ids:
                continue
            user_orders = orders_by_user.get(user_id, [])
            paid_orders = [item for item in user_orders if _clean_text(item.get("status")).upper() == "PAID"]
            active_orders = []
            for order in paid_orders:
                plan_name = _clean_text(order.get("plan_name")).upper()
                expire_at = _datetime_value(order.get("expire_at"))
                if "TRỌN ĐỜI" in plan_name or "TRON DOI" in plan_name or "LIFE" in plan_name or (expire_at and expire_at > now):
                    active_orders.append(order)

            user_segment = "NO_PURCHASE"
            if active_orders:
                user_segment = "VIP_ACTIVE"
            elif paid_orders:
                user_segment = "VIP_EXPIRED"

            if segment_key in {"VIP", "VIP_PAID"} and not paid_orders:
                continue
            if segment_key == "VIP_ACTIVE" and not active_orders:
                continue
            if segment_key == "VIP_EXPIRED" and (not paid_orders or active_orders):
                continue
            if segment_key in {"NO_PURCHASE", "NOT_PAID"} and paid_orders:
                continue
            if _norm_filter_text(plan_filter) not in {"", "all"}:
                latest_paid_order = paid_orders[0] if paid_orders else {}
                if plan_match_scope == "ACTIVE_ONLY":
                    scoped_orders = active_orders
                elif plan_match_scope == "LATEST":
                    scoped_orders = [latest_paid_order] if latest_paid_order else []
                else:
                    scoped_orders = paid_orders
                if not any(self._broadcast_plan_matches(order.get("plan_name"), plan_filter) for order in scoped_orders):
                    continue

            identity = interacted.get(user_id) or {}
            latest_order = user_orders[0] if user_orders else {}
            paid_plan_names = sorted({_clean_text(item.get("plan_name")) for item in paid_orders if _clean_text(item.get("plan_name"))})
            active_plan_names = sorted({_clean_text(item.get("plan_name")) for item in active_orders if _clean_text(item.get("plan_name"))})
            recipients.append({
                "telegram_user_id": user_id,
                "username": identity.get("username") or "",
                "full_name": identity.get("full_name") or _clean_display_text(latest_order.get("full_name")),
                "segment": user_segment,
                "raw_data": {
                    "paid_orders": len(paid_orders),
                    "active_orders": len(active_orders),
                    "last_interaction_at": identity.get("last_interaction_at"),
                    "latest_plan_name": latest_order.get("plan_name") or "",
                    "paid_plan_names": paid_plan_names,
                    "active_plan_names": active_plan_names,
                },
            })
        return recipients

    def preview_broadcast_recipients(self, segment="ALL", limit=5000, plan_filter="ALL", plan_match_scope="ANY_PAID"):
        recipients = self.build_broadcast_recipients(
            segment=segment,
            limit=limit,
            plan_filter=plan_filter,
            plan_match_scope=plan_match_scope,
        )
        counts = {}
        for recipient in recipients:
            counts[recipient["segment"]] = counts.get(recipient["segment"], 0) + 1
        return {"total": len(recipients), "counts": counts, "sample": recipients[:20]}

    def list_broadcast_campaigns(self, limit=100):
        campaigns = self._request(
            "GET",
            "broadcast_campaigns",
            params={"select": "*", "order": "created_at.desc", "limit": str(limit)},
        )
        return campaigns

    def get_broadcast_campaign(self, campaign_id):
        rows = self._request(
            "GET",
            "broadcast_campaigns",
            params={"select": "*", "id": f"eq.{_clean_text(campaign_id)}", "limit": "1"},
        )
        return rows[0] if rows else None

    def list_broadcast_recipients(self, campaign_id, limit=500, status=None):
        params = {
            "select": "*",
            "campaign_id": f"eq.{_clean_text(campaign_id)}",
            "order": "created_at.asc",
            "limit": str(limit),
        }
        if status:
            params["status"] = f"eq.{_clean_text(status).upper()}"
        return self._request("GET", "broadcast_recipients", params=params)

    def create_broadcast_campaign(self, raw):
        title = _clean_text(raw.get("title") or raw.get("name"))
        message = str(raw.get("message") or "").strip()
        if not title:
            raise ValueError("Thiếu tên campaign.")
        if not message:
            raise ValueError("Thiếu nội dung gửi.")
        delay_seconds = max(2, min(_parse_int(raw.get("delay_seconds"), 5), 300))
        batch_size = max(1, min(_parse_int(raw.get("batch_size"), 20), 100))
        target_segment = _clean_text(raw.get("target_segment") or "ALL").upper() or "ALL"
        plan_filter = _clean_text(raw.get("plan_filter") or "ALL") or "ALL"
        plan_match_scope = _clean_text(raw.get("plan_match_scope") or "ANY_PAID").upper() or "ANY_PAID"
        recipients = self.build_broadcast_recipients(
            target_segment,
            limit=_parse_int(raw.get("recipient_limit"), 5000),
            plan_filter=plan_filter,
            plan_match_scope=plan_match_scope,
        )
        campaign_payload = {
            "title": title,
            "message": message,
            "parse_mode": _clean_text(raw.get("parse_mode") or "HTML").upper() or "HTML",
            "target_segment": target_segment,
            "status": "DRAFT",
            "delay_seconds": delay_seconds,
            "batch_size": batch_size,
            "total_recipients": len(recipients),
            "raw_data": {
                **(raw.get("raw_data") or {}),
                "plan_filter": plan_filter,
                "plan_match_scope": plan_match_scope,
            },
        }
        campaign = self._request("POST", "broadcast_campaigns", json=campaign_payload, prefer="return=representation")[0]
        campaign_id = campaign.get("id")
        recipient_payload = [
            {
                "campaign_id": campaign_id,
                "telegram_user_id": item["telegram_user_id"],
                "username": item.get("username") or "",
                "full_name": item.get("full_name") or "",
                "segment": item.get("segment") or "",
                "status": "PENDING",
                "raw_data": item.get("raw_data") or {},
            }
            for item in recipients
        ]
        if recipient_payload:
            chunk_size = 500
            for start in range(0, len(recipient_payload), chunk_size):
                self._request(
                    "POST",
                    "broadcast_recipients",
                    json=recipient_payload[start:start + chunk_size],
                    prefer="return=representation",
                )
        self.record_broadcast_event(campaign_id, None, "campaign_created", {"recipients": len(recipients)})
        return self.get_broadcast_campaign(campaign_id)

    def patch_broadcast_campaign(self, campaign_id, payload):
        return self._request(
            "PATCH",
            "broadcast_campaigns",
            params={"id": f"eq.{_clean_text(campaign_id)}"},
            json=payload,
            prefer="return=representation",
        )

    def start_broadcast_campaign(self, campaign_id):
        campaign = self.get_broadcast_campaign(campaign_id)
        if not campaign:
            return []
        if campaign.get("status") in {"DONE", "CANCELLED"}:
            return [campaign]
        payload = {"status": "RUNNING", "started_at": campaign.get("started_at") or _now_iso()}
        self.record_broadcast_event(campaign_id, None, "campaign_started", {})
        return self.patch_broadcast_campaign(campaign_id, payload)

    def pause_broadcast_campaign(self, campaign_id):
        self.record_broadcast_event(campaign_id, None, "campaign_paused", {})
        return self.patch_broadcast_campaign(campaign_id, {"status": "PAUSED"})

    def cancel_broadcast_campaign(self, campaign_id):
        self._request(
            "PATCH",
            "broadcast_recipients",
            params={"campaign_id": f"eq.{_clean_text(campaign_id)}", "status": "eq.PENDING"},
            json={"status": "SKIPPED", "error": "Campaign cancelled"},
        )
        self.record_broadcast_event(campaign_id, None, "campaign_cancelled", {})
        return self.patch_broadcast_campaign(campaign_id, {"status": "CANCELLED", "finished_at": _now_iso()})

    def next_running_broadcast_campaign(self):
        rows = self._request(
            "GET",
            "broadcast_campaigns",
            params={"select": "*", "status": "eq.RUNNING", "order": "created_at.asc", "limit": "1"},
        )
        return rows[0] if rows else None

    def next_pending_broadcast_recipient(self, campaign_id):
        rows = self._request(
            "GET",
            "broadcast_recipients",
            params={
                "select": "*",
                "campaign_id": f"eq.{_clean_text(campaign_id)}",
                "status": "eq.PENDING",
                "order": "created_at.asc",
                "limit": "1",
            },
        )
        return rows[0] if rows else None

    def update_broadcast_recipient(self, recipient_id, payload):
        return self._request(
            "PATCH",
            "broadcast_recipients",
            params={"id": f"eq.{_clean_text(recipient_id)}"},
            json=payload,
            prefer="return=representation",
        )

    def refresh_broadcast_campaign_counts(self, campaign_id):
        rows = self._request(
            "GET",
            "broadcast_recipients",
            params={"select": "status", "campaign_id": f"eq.{_clean_text(campaign_id)}", "limit": "10000"},
        )
        counts = {"PENDING": 0, "SENT": 0, "FAILED": 0, "SKIPPED": 0}
        for row in rows or []:
            status = _clean_text(row.get("status")).upper()
            counts[status] = counts.get(status, 0) + 1
        done = counts.get("PENDING", 0) == 0
        payload = {
            "total_recipients": len(rows or []),
            "sent_count": counts.get("SENT", 0),
            "failed_count": counts.get("FAILED", 0),
            "skipped_count": counts.get("SKIPPED", 0),
        }
        if done:
            payload["status"] = "DONE"
            payload["finished_at"] = _now_iso()
        return self.patch_broadcast_campaign(campaign_id, payload)

    def record_broadcast_event(self, campaign_id, telegram_user_id, event_type, raw_data=None):
        payload = {
            "campaign_id": _clean_text(campaign_id) or None,
            "telegram_user_id": _clean_text(telegram_user_id),
            "event_type": _clean_text(event_type),
            "raw_data": raw_data or {},
        }
        return self._request("POST", "broadcast_events", json=payload, prefer="return=representation")

    def _channel_post_payload(self, raw, partial=False):
        allowed = {
            "bot_key",
            "target_chat_id",
            "title",
            "image_ref",
            "content",
            "buttons_text",
            "parse_mode",
            "disable_web_page_preview",
            "status",
            "sent_message_id",
            "sent_at",
            "scheduled_at",
            "delete_at",
            "deleted_at",
            "error",
            "error_code",
            "enabled",
            "repeat_daily",
            "sync_bot_schedule",
            "notes",
            "attempt_count",
            "last_attempt_at",
            "created_by",
            "deleted_by",
        }
        payload = {}
        for key in allowed:
            if partial and key not in raw:
                continue
            value = raw.get(key)
            if key in {"sent_at", "scheduled_at", "delete_at", "deleted_at", "last_attempt_at"}:
                payload[key] = _parse_datetime(value) if value else None
            elif key in {"disable_web_page_preview", "enabled", "repeat_daily", "sync_bot_schedule"}:
                payload[key] = str(value).strip().upper() not in {"OFF", "FALSE", "NO", "0", "INACTIVE"} if value is not None else (True if key == "enabled" else False)
            elif key == "attempt_count":
                payload[key] = _parse_int(value, 0)
            elif key == "parse_mode":
                normalized = _clean_text(value or "HTML").upper() or "HTML"
                payload[key] = normalized if normalized in {"HTML", "MARKDOWN", "MARKDOWNV2", "NONE"} else "HTML"
            elif key == "status":
                payload[key] = _clean_text(value or "draft").lower() or "draft"
            elif key == "bot_key":
                payload[key] = _clean_text(value or "main") or "main"
            else:
                payload[key] = _clean_text(value) if value is not None else None

        if not partial:
            payload.setdefault("bot_key", "main")
            payload.setdefault("status", "draft")
            payload.setdefault("parse_mode", "HTML")
            payload.setdefault("disable_web_page_preview", False)
            payload.setdefault("enabled", True)
            payload.setdefault("repeat_daily", False)
            payload.setdefault("sync_bot_schedule", False)
            payload.setdefault("image_ref", None)
        return payload

    def _request_channel_post_write(self, method, params=None, payload=None, prefer="return=representation"):
        try:
            return self._request(method, "channel_posts", params=params, json=payload, prefer=prefer)
        except RuntimeError as exc:
            missing_optional_column = any(column in str(exc) for column in ("repeat_daily", "sync_bot_schedule", "image_ref"))
            if not missing_optional_column:
                raise
            legacy_payload = dict(payload or {})
            legacy_payload.pop("image_ref", None)
            legacy_payload.pop("repeat_daily", None)
            legacy_payload.pop("sync_bot_schedule", None)
            return self._request(method, "channel_posts", params=params, json=legacy_payload, prefer=prefer)

    def list_channel_posts(self, limit=200, status=None):
        params = {"select": "*", "order": "updated_at.desc", "limit": str(limit)}
        if status:
            params["status"] = f"eq.{_clean_text(status).lower()}"
        return self._request("GET", "channel_posts", params=params)

    def get_channel_post(self, post_id):
        rows = self._request(
            "GET",
            "channel_posts",
            params={"select": "*", "id": f"eq.{_clean_text(post_id)}", "limit": "1"},
        )
        return rows[0] if rows else None

    def create_channel_post(self, raw):
        payload = self._channel_post_payload(raw, partial=False)
        if not payload.get("target_chat_id"):
            raise ValueError("Thiếu channel/group nhận bài.")
        if not payload.get("content"):
            raise ValueError("Thiếu nội dung bài đăng.")
        rows = self._request_channel_post_write("POST", payload=payload, prefer="return=representation")
        try:
            from helpers import invalidate_channel_schedule_cache
            from helpers import recompute_bot_runtime_state
            from helpers import sync_bot_schedule_rule_from_post

            invalidate_channel_schedule_cache()
            recompute_bot_runtime_state()
            if rows:
                sync_bot_schedule_rule_from_post(rows[0])
        except Exception:
            pass
        return rows[0]

    def patch_channel_post(self, post_id, raw, status=None):
        params = {"id": f"eq.{_clean_text(post_id)}"}
        if status:
            params["status"] = f"eq.{_clean_text(status).lower()}"
        payload = self._channel_post_payload(raw, partial=True)
        if not payload:
            return []
        rows = self._request_channel_post_write("PATCH", params=params, payload=payload, prefer="return=representation")
        try:
            from helpers import invalidate_channel_schedule_cache
            from helpers import recompute_bot_runtime_state
            from helpers import sync_bot_schedule_rule_from_post

            invalidate_channel_schedule_cache()
            recompute_bot_runtime_state()
            if rows:
                sync_bot_schedule_rule_from_post(rows[0])
        except Exception:
            pass
        return rows

    def list_bot_schedule_channel_posts(self, limit=200):
        try:
            return self._request(
                "GET",
                "channel_posts",
                params={
                    "select": "id,status,scheduled_at,delete_at,repeat_daily,sync_bot_schedule,enabled,notes",
                    "enabled": "eq.true",
                    "status": "in.(scheduled,sending,sent,delete_scheduled,deleting)",
                    "order": "scheduled_at.asc",
                    "limit": str(limit),
                },
            )
        except RuntimeError as exc:
            if "sync_bot_schedule" in str(exc) or "repeat_daily" in str(exc):
                return []
            raise

    def channel_post_action(self, post_id, action, raw=None):
        raw = raw or {}
        now = _now_iso()
        details = {"scheduled_at": raw.get("scheduled_at"), "delete_at": raw.get("delete_at")}
        if action in {"send_now", "retry"}:
            values = {"status": "queued", "scheduled_at": None, "error": None, "error_code": None}
            event_type = "send_retry_queued" if action == "retry" else "send_queued"
            message = "Admin yêu cầu thử gửi lại." if action == "retry" else "Admin yêu cầu gửi ngay."
        elif action == "schedule":
            scheduled_at = _parse_datetime(raw.get("scheduled_at"))
            if not scheduled_at or datetime.fromisoformat(scheduled_at) <= datetime.now(_bot_timezone()):
                raise ValueError("Giờ gửi phải nằm trong tương lai.")
            values = {"status": "scheduled", "scheduled_at": scheduled_at, "error": None, "error_code": None}
            event_type = "send_scheduled"
            message = "Admin đã hẹn giờ gửi bài."
        elif action == "cancel_schedule":
            values = {"status": "draft", "scheduled_at": None, "error": None, "error_code": None}
            event_type = "send_schedule_cancelled"
            message = "Admin đã hủy lịch gửi."
        elif action == "delete_now":
            values = {"status": "delete_scheduled", "delete_at": now, "deleted_by": "admin_cp", "error": None, "error_code": None}
            event_type = "delete_queued"
            message = "Admin yêu cầu xóa bài ngay."
        elif action == "retry_delete":
            values = {"status": "delete_scheduled", "delete_at": now, "error": None, "error_code": None}
            event_type = "delete_retry_queued"
            message = "Admin yêu cầu thử xóa lại."
        elif action == "schedule_delete":
            delete_at = _parse_datetime(raw.get("delete_at"))
            if not delete_at or datetime.fromisoformat(delete_at) <= datetime.now(_bot_timezone()):
                raise ValueError("Giờ xóa phải nằm trong tương lai.")
            values = {"status": "delete_scheduled", "delete_at": delete_at, "error": None, "error_code": None}
            event_type = "delete_scheduled"
            message = "Admin đã hẹn giờ xóa bài."
        elif action == "cancel_delete":
            values = {"status": "sent", "delete_at": None, "error": None, "error_code": None}
            event_type = "delete_schedule_cancelled"
            message = "Admin đã hủy lịch xóa."
        else:
            raise ValueError("Hành động không được hỗ trợ.")

        rows = self.patch_channel_post(post_id, values)
        row = rows[0] if rows else None
        if row:
            self.record_channel_post_event(post_id, event_type, message, details, bot_key=row.get("bot_key") or "main")
            try:
                from helpers import recompute_bot_runtime_state

                recompute_bot_runtime_state()
            except Exception:
                pass
        return row

    def list_channel_post_events(self, post_id=None, limit=200):
        params = {"select": "*", "order": "created_at.desc", "limit": str(limit)}
        if post_id:
            params["channel_post_id"] = f"eq.{_clean_text(post_id)}"
        return self._request("GET", "channel_post_events", params=params)

    def record_channel_post_event(self, post_id, event_type, message, details=None, bot_key="main"):
        payload = {
            "bot_key": _clean_text(bot_key) or "main",
            "channel_post_id": post_id,
            "event_type": _clean_text(event_type),
            "message": _clean_text(message),
            "details": details or {},
        }
        return self._request("POST", "channel_post_events", json=payload, prefer="return=representation")


supabase_store = SupabaseStore()
