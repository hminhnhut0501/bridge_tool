import base64
import hashlib
import hmac
import json
import os
import time

import requests
from dotenv import load_dotenv

from database import db
from supabase_store import supabase_store

load_dotenv()

PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
PAYPAL_BASE_URL = os.getenv("PAYPAL_BASE_URL", "https://api-m.paypal.com").rstrip("/")
PAYPAL_RETURN_URL = os.getenv("PAYPAL_RETURN_URL", "https://t.me/hangcuprivebot")
PAYPAL_CANCEL_URL = os.getenv("PAYPAL_CANCEL_URL", PAYPAL_RETURN_URL)
NOWPAYMENTS_API_KEY = os.getenv("NOWPAYMENTS_API_KEY")
NOWPAYMENTS_BASE_URL = os.getenv("NOWPAYMENTS_BASE_URL", "https://api.nowpayments.io/v1").rstrip("/")


def _enabled(key, default):
    value = str(db.get_config(key, default) or default).strip().upper()
    return value in {"ON", "TRUE", "YES", "1", "BAT", "BẬT"}


class PayOSManager:
    provider = "PAYOS"

    @property
    def enabled(self):
        return _enabled("PAYOS_PAYMENT_ENABLED", "ON") and bool(
            PAYOS_CLIENT_ID and PAYOS_API_KEY and PAYOS_CHECKSUM_KEY
        )

    @property
    def headers(self):
        return {
            "x-client-id": PAYOS_CLIENT_ID,
            "x-api-key": PAYOS_API_KEY,
            "Content-Type": "application/json",
        }

    def get_payment_status(self, order_code):
        try:
            response = requests.get(
                f"https://api-merchant.payos.vn/v2/payment-requests/{order_code}",
                headers=self.headers,
                timeout=10,
            )
            data = response.json()
            return data["data"]["status"] if data.get("code") == "00" else "ERROR"
        except Exception as exc:
            print(f"⚠️ Lỗi kết nối PayOS: {exc}")
            return "ERROR"

    def create_payment_link(self, order_code, amount, description):
        if not self.enabled:
            return None
        return_url = str(db.get_config("PAYMENT_RETURN_URL", PAYPAL_RETURN_URL) or PAYPAL_RETURN_URL)
        cancel_url = str(db.get_config("PAYMENT_CANCEL_URL", PAYPAL_CANCEL_URL) or PAYPAL_CANCEL_URL)
        sign_string = (
            f"amount={int(amount)}&cancelUrl={cancel_url}&description={description}"
            f"&orderCode={int(order_code)}&returnUrl={return_url}"
        )
        signature = hmac.new(
            PAYOS_CHECKSUM_KEY.encode("utf-8"),
            sign_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        payload = {
            "orderCode": int(order_code),
            "amount": int(amount),
            "description": description,
            "returnUrl": return_url,
            "cancelUrl": cancel_url,
            "signature": signature,
        }
        try:
            response = requests.post(
                "https://api-merchant.payos.vn/v2/payment-requests",
                json=payload,
                headers=self.headers,
                timeout=20,
            )
            result = response.json()
            if result.get("code") != "00":
                print(f"❌ Lỗi PayOS: {result.get('desc')}")
                return None
            data = result["data"]
            return {
                **data,
                "provider": self.provider,
                "provider_order_id": str(order_code),
                "approval_url": data.get("checkoutUrl") or data.get("paymentLink") or "",
                "currency_code": "VND",
            }
        except Exception as exc:
            print(f"❌ Lỗi kết nối PayOS: {exc}")
            return None


class PayPalManager:
    provider = "PAYPAL"

    def __init__(self):
        self._access_token = ""
        self._token_expires_at = 0

    @property
    def enabled(self):
        return _enabled("PAYPAL_PAYMENT_ENABLED", "OFF") and bool(PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET)

    def _access(self):
        if self._access_token and time.time() < self._token_expires_at - 60:
            return self._access_token
        if not self.enabled:
            raise RuntimeError("PayPal chưa được bật hoặc chưa cấu hình credentials")
        basic = base64.b64encode(f"{PAYPAL_CLIENT_ID}:{PAYPAL_CLIENT_SECRET}".encode()).decode()
        response = requests.post(
            f"{PAYPAL_BASE_URL}/v1/oauth2/token",
            headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"},
            data="grant_type=client_credentials",
            timeout=20,
        )
        data = response.json()
        if not response.ok or not data.get("access_token"):
            raise RuntimeError(f"PayPal OAuth failed: {response.status_code} {data}")
        self._access_token = data["access_token"]
        self._token_expires_at = time.time() + int(data.get("expires_in") or 0)
        return self._access_token

    def _headers(self):
        return {"Authorization": f"Bearer {self._access()}", "Content-Type": "application/json"}

    def _usd_value(self, amount_usd):
        return f"{max(0.01, float(amount_usd)):.2f}"

    def create_payment_link(self, order_code, amount, description):
        if not self.enabled:
            return None
        try:
            payload = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": str(order_code),
                    "custom_id": str(order_code),
                    "invoice_id": str(order_code),
                    "description": description,
                    "amount": {"currency_code": "USD", "value": self._usd_value(amount)},
                }],
                "application_context": {
                    "brand_name": str(db.get_config("PAYPAL_BRAND_NAME", "Prive Bot") or "Prive Bot"),
                    "landing_page": "BILLING",
                    "user_action": "PAY_NOW",
                    "return_url": str(db.get_config("PAYMENT_RETURN_URL", PAYPAL_RETURN_URL) or PAYPAL_RETURN_URL),
                    "cancel_url": str(db.get_config("PAYMENT_CANCEL_URL", PAYPAL_CANCEL_URL) or PAYPAL_CANCEL_URL),
                    "locale": "en-US",
                },
            }
            response = requests.post(
                f"{PAYPAL_BASE_URL}/v2/checkout/orders",
                headers=self._headers(),
                json=payload,
                timeout=20,
            )
            data = response.json()
            if not response.ok or not data.get("id"):
                print(f"❌ Lỗi PayPal: {response.status_code} {data}")
                return None
            approval_url = next(
                (str(link.get("href") or "") for link in data.get("links", []) if link.get("rel") == "approve"),
                "",
            )
            if not approval_url:
                print(f"❌ PayPal không trả approval URL cho đơn {order_code}")
                return None
            return {
                "provider": self.provider,
                "provider_order_id": str(data["id"]),
                "approval_url": approval_url,
                "currency_code": "USD",
                "paypal_amount": self._usd_value(amount),
            }
        except Exception as exc:
            print(f"❌ Lỗi kết nối PayPal: {exc}")
            return None

    def get_payment_status(self, provider_order_id):
        try:
            response = requests.get(
                f"{PAYPAL_BASE_URL}/v2/checkout/orders/{provider_order_id}",
                headers=self._headers(),
                timeout=20,
            )
            data = response.json()
            status = str(data.get("status") or "").upper()
            if status == "COMPLETED":
                return "PAID"
            if status == "APPROVED":
                captured = requests.post(
                    f"{PAYPAL_BASE_URL}/v2/checkout/orders/{provider_order_id}/capture",
                    headers=self._headers(),
                    json={},
                    timeout=20,
                ).json()
                return "PAID" if str(captured.get("status") or "").upper() == "COMPLETED" else "PENDING"
            return "PENDING" if status in {"CREATED", "SAVED", "APPROVED"} else "ERROR"
        except Exception as exc:
            print(f"⚠️ Lỗi kiểm tra PayPal: {exc}")
            return "ERROR"


class NowPaymentsManager:
    provider = "NOWPAYMENTS"

    @property
    def enabled(self):
        return _enabled("NOWPAYMENTS_PAYMENT_ENABLED", "OFF") and bool(NOWPAYMENTS_API_KEY)

    @property
    def headers(self):
        return {
            "x-api-key": NOWPAYMENTS_API_KEY or "",
            "Content-Type": "application/json",
        }

    def _currency(self):
        return str(db.get_config("NOWPAYMENTS_PRICE_CURRENCY", "USD") or "USD").strip().upper() or "USD"

    def _amount_value(self, amount):
        return round(max(0.01, float(amount)), 2)

    def create_payment_link(self, order_code, amount, description):
        if not self.enabled:
            return None
        currency = self._currency()
        return_url = str(db.get_config("PAYMENT_RETURN_URL", PAYPAL_RETURN_URL) or PAYPAL_RETURN_URL)
        cancel_url = str(db.get_config("PAYMENT_CANCEL_URL", PAYPAL_CANCEL_URL) or PAYPAL_CANCEL_URL)
        callback_url = str(
            db.get_config(
                "NOWPAYMENTS_IPN_CALLBACK_URL",
                os.getenv("NOWPAYMENTS_IPN_CALLBACK_URL", ""),
            )
            or os.getenv("NOWPAYMENTS_IPN_CALLBACK_URL", "")
            or ""
        ).strip()
        if not callback_url:
            public_base = str(os.getenv("PUBLIC_BASE_URL") or os.getenv("RENDER_EXTERNAL_URL") or "").rstrip("/")
            if public_base:
                callback_url = f"{public_base}/payment-webhooks/nowpayments"

        payload = {
            "price_amount": self._amount_value(amount),
            "price_currency": currency,
            "order_id": str(order_code),
            "order_description": str(description)[:1024],
            "success_url": return_url,
            "cancel_url": cancel_url,
        }
        if callback_url:
            payload["ipn_callback_url"] = callback_url

        pay_currency = str(db.get_config("NOWPAYMENTS_PAY_CURRENCY", "") or "").strip().lower()
        if pay_currency:
            payload["pay_currency"] = pay_currency

        try:
            response = requests.post(
                f"{NOWPAYMENTS_BASE_URL}/invoice",
                json=payload,
                headers=self.headers,
                timeout=20,
            )
            data = response.json()
            invoice_url = str(data.get("invoice_url") or "")
            invoice_id = data.get("id") or data.get("invoice_id") or order_code
            if not response.ok or not invoice_url:
                print(f"❌ Lỗi NOWPayments: {response.status_code} {data}")
                return None
            return {
                "provider": self.provider,
                "provider_order_id": str(invoice_id),
                "approval_url": invoice_url,
                "currency_code": currency,
                "crypto_amount": f"{self._amount_value(amount):.2f}",
            }
        except Exception as exc:
            print(f"❌ Lỗi kết nối NOWPayments: {exc}")
            return None

    def get_payment_status(self, provider_order_id):
        try:
            response = requests.get(
                f"{NOWPAYMENTS_BASE_URL}/invoice/{provider_order_id}",
                headers=self.headers,
                timeout=20,
            )
            data = response.json()
            status = str(data.get("payment_status") or data.get("status") or "").lower()
            return self.normalize_status(status)
        except Exception as exc:
            print(f"⚠️ Lỗi kiểm tra NOWPayments: {exc}")
            return "ERROR"

    @staticmethod
    def normalize_status(status):
        normalized = str(status or "").strip().lower()
        if normalized == "finished":
            return "PAID"
        if normalized in {"waiting", "confirming", "confirmed", "sending", "partially_paid"}:
            return "PENDING"
        if normalized in {"failed", "expired", "refunded"}:
            return "ERROR"
        return "PENDING" if normalized else "ERROR"

    @staticmethod
    def verify_ipn_signature(payload, signature, secret):
        if not secret or not signature:
            return False
        raw = payload if isinstance(payload, bytes) else bytes(payload or b"")
        provided = str(signature).strip().lower()
        expected_raw = hmac.new(str(secret).encode("utf-8"), raw, hashlib.sha512).hexdigest()
        if hmac.compare_digest(expected_raw, provided):
            return True
        try:
            data = json.loads(raw.decode("utf-8"))
            normalized = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
            expected_normalized = hmac.new(str(secret).encode("utf-8"), normalized, hashlib.sha512).hexdigest()
            return hmac.compare_digest(expected_normalized, provided)
        except Exception:
            return False


class PaymentManager:
    def __init__(self):
        self.payos = PayOSManager()
        self.paypal = PayPalManager()
        self.nowpayments = NowPaymentsManager()

    def enabled_providers(self):
        return [provider for provider in ("PAYOS", "PAYPAL", "NOWPAYMENTS") if self.provider_enabled(provider)]

    def manager_for(self, provider):
        selected = str(provider or "PAYOS").upper()
        if selected == "PAYPAL":
            return self.paypal
        if selected == "NOWPAYMENTS":
            return self.nowpayments
        return self.payos

    def provider_enabled(self, provider):
        return self.manager_for(provider).enabled

    def preferred_provider(self, language="vi"):
        key = "PAYMENT_PROVIDER_EN" if str(language).lower() == "en" else "PAYMENT_PROVIDER_VI"
        preferred = str(db.get_config(key, "PAYPAL" if key.endswith("_EN") else "PAYOS") or "").upper()
        if self.provider_enabled(preferred):
            return preferred
        enabled = self.enabled_providers()
        return enabled[0] if enabled else ""

    def providers_for_language(self, language="vi"):
        key = "PAYMENT_PROVIDERS_EN" if str(language).lower() == "en" else "PAYMENT_PROVIDERS_VI"
        default = "PAYPAL" if key.endswith("_EN") else "PAYOS"
        configured = str(db.get_config(key, default) or default).upper().replace(";", ",")
        providers = []
        for item in configured.split(","):
            provider = item.strip()
            if provider in {"PAYOS", "PAYPAL", "NOWPAYMENTS"} and provider not in providers and self.provider_enabled(provider):
                providers.append(provider)
        if providers:
            return providers
        return []

    def create_payment_link(self, order_code, amount, description, provider=""):
        selected = str(provider or self.preferred_provider()).upper()
        manager = self.manager_for(selected)
        return manager.create_payment_link(order_code, amount, description)

    def get_payment_status(self, order_ref):
        order = supabase_store.get_order(str(order_ref)) if supabase_store.enabled else None
        provider = str((order or {}).get("payment_provider") or "PAYOS").upper()
        provider_order_id = str((order or {}).get("payment_provider_order_id") or order_ref)
        manager = self.manager_for(provider)
        return manager.get_payment_status(provider_order_id)


payment_manager = PaymentManager()
payos_manager = payment_manager
