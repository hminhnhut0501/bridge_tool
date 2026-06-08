import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from zoneinfo import ZoneInfo

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
TRONGRID_API_KEY = os.getenv("TRONGRID_API_KEY")
TRONGRID_BASE_URL = os.getenv("TRONGRID_BASE_URL", "https://api.trongrid.io").rstrip("/")
TRON_USDT_CONTRACT = os.getenv("TRON_USDT_CONTRACT", "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj")
SIEUTHICODE_BINANCE_PAY_TOKEN = os.getenv("SIEUTHICODE_BINANCE_PAY_TOKEN")
SIEUTHICODE_BINANCE_PAY_BASE_URL = os.getenv("SIEUTHICODE_BINANCE_PAY_BASE_URL", "https://api.sieuthicode.net").rstrip("/")


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


class TronUsdtManager:
    provider = "TRON_USDT"

    @property
    def enabled(self):
        return _enabled("TRON_USDT_PAYMENT_ENABLED", "OFF") and bool(self.wallet_address)

    @property
    def wallet_address(self):
        return str(db.get_config("TRON_USDT_WALLET_ADDRESS", os.getenv("TRON_USDT_WALLET_ADDRESS", "")) or "").strip()

    @property
    def headers(self):
        headers = {"Accept": "application/json"}
        api_key = str(db.get_config("TRONGRID_API_KEY", TRONGRID_API_KEY or "") or TRONGRID_API_KEY or "").strip()
        if api_key:
            headers["TRON-PRO-API-KEY"] = api_key
        return headers

    def _unique_amount_enabled(self):
        return _enabled("TRON_USDT_UNIQUE_AMOUNT_ENABLED", "ON")

    def usdt_amount(self, order_code, amount):
        base = Decimal(str(amount or "0")).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
        if not self._unique_amount_enabled():
            return base
        try:
            suffix = (int(str(order_code)) % 999) + 1
        except Exception:
            suffix = 1
        return (base + (Decimal(suffix) / Decimal("1000000"))).quantize(Decimal("0.000001"))

    def create_payment_link(self, order_code, amount, description):
        if not self.enabled:
            return None
        amount_usdt = self.usdt_amount(order_code, amount)
        return {
            "provider": self.provider,
            "provider_order_id": str(order_code),
            "approval_url": f"https://tronscan.org/#/address/{self.wallet_address}",
            "currency_code": "USDT",
            "network": "TRC20",
            "wallet_address": self.wallet_address,
            "usdt_amount": f"{amount_usdt:.6f}",
            "base_usd_amount": f"{Decimal(str(amount or '0')).quantize(Decimal('0.000001'), rounding=ROUND_DOWN):.6f}",
            "description": description,
        }

    def _order_created_at(self, order):
        raw = str((order or {}).get("created_at") or "").strip()
        if not raw:
            return datetime.now(ZoneInfo("UTC")) - timedelta(hours=2)
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=ZoneInfo("UTC"))
        except Exception:
            return datetime.now(ZoneInfo("UTC")) - timedelta(hours=2)

    def _transaction_amount(self, tx):
        token_info = tx.get("token_info") or {}
        decimals = int(token_info.get("decimals") or 6)
        raw_value = Decimal(str(tx.get("value") or "0"))
        return (raw_value / (Decimal(10) ** decimals)).quantize(Decimal("0.000001"))

    def _transaction_time(self, tx):
        timestamp = tx.get("block_timestamp")
        try:
            return datetime.fromtimestamp(int(timestamp) / 1000, tz=ZoneInfo("UTC"))
        except Exception:
            return None

    def _transaction_confirmed(self, tx):
        if tx.get("confirmed") is False:
            return False
        if str(tx.get("type") or "").lower() == "transfer":
            return True
        return True

    def _recent_incoming_transfers(self, min_timestamp_ms):
        response = requests.get(
            f"{TRONGRID_BASE_URL}/v1/accounts/{self.wallet_address}/transactions/trc20",
            params={
                "only_confirmed": "true",
                "limit": "200",
                "contract_address": TRON_USDT_CONTRACT,
                "min_timestamp": str(max(0, int(min_timestamp_ms))),
                "order_by": "block_timestamp,desc",
            },
            headers=self.headers,
            timeout=20,
        )
        data = response.json()
        if not response.ok:
            raise RuntimeError(f"TronGrid failed: {response.status_code} {data}")
        return data.get("data") or []

    def get_payment_status(self, order_ref):
        order = supabase_store.get_order(str(order_ref)) if supabase_store.enabled else None
        if not order:
            return "PENDING"
        if str(order.get("status") or "").upper() != "PENDING":
            return "PAID" if str(order.get("status") or "").upper() == "PAID" else "ERROR"
        try:
            expected = self.usdt_amount(order_ref, order.get("amount") or 0)
            created_at = self._order_created_at(order)
            min_time = created_at - timedelta(minutes=10)
            min_timestamp_ms = int(min_time.timestamp() * 1000)
            for tx in self._recent_incoming_transfers(min_timestamp_ms):
                if not self._transaction_confirmed(tx):
                    continue
                if str(tx.get("to") or "").strip() != self.wallet_address:
                    continue
                amount = self._transaction_amount(tx)
                if amount != expected:
                    continue
                tx_time = self._transaction_time(tx)
                if tx_time and tx_time < min_time:
                    continue
                tx_id = str(tx.get("transaction_id") or "").strip()
                if tx_id:
                    try:
                        existing = order.get("metadata") if isinstance(order.get("metadata"), dict) else {}
                        supabase_store.update_order_fields(str(order_ref), {
                            "metadata": {
                                **existing,
                                "tron_usdt_tx_id": tx_id,
                                "tron_usdt_amount": f"{amount:.6f}",
                                "tron_usdt_confirmed_at": tx_time.isoformat() if tx_time else "",
                            },
                        })
                    except Exception as meta_err:
                        print(f"⚠️ Không lưu được metadata TRON USDT cho đơn {order_ref}: {meta_err}")
                return "PAID"
            return "PENDING"
        except Exception as exc:
            print(f"⚠️ Lỗi quét TRON USDT đơn {order_ref}: {exc}")
            return "ERROR"


class BinancePaySieuthicodeManager:
    provider = "BINANCE_PAY"

    @property
    def enabled(self):
        return _enabled("BINANCE_PAY_SIEUTHICODE_ENABLED", "OFF") and bool(SIEUTHICODE_BINANCE_PAY_TOKEN)

    @property
    def token(self):
        return str(db.get_config("BINANCE_PAY_SIEUTHICODE_TOKEN", SIEUTHICODE_BINANCE_PAY_TOKEN or "") or "").strip()

    def _history_v2_url(self):
        return f"{SIEUTHICODE_BINANCE_PAY_BASE_URL}/historyapibinancev2/{self.token}"

    def _history_url(self):
        return f"{SIEUTHICODE_BINANCE_PAY_BASE_URL}/historyapibinance/{self.token}"

    def create_payment_link(self, order_code, amount, description):
        if not self.enabled:
            return None
        return {
            "provider": self.provider,
            "provider_order_id": str(order_code),
            "approval_url": str(db.get_config("BINANCE_PAY_SIEUTHICODE_APPROVAL_URL", "") or ""),
            "currency_code": "VND",
            "binance_pay_amount": f"{Decimal(str(amount or 0)).quantize(Decimal('0.01')):.2f}",
            "description": description,
            "payment_note": str(order_code),
        }

    def _fetch_history_v2(self):
        response = requests.get(self._history_v2_url(), timeout=20)
        data = response.json()
        if not response.ok:
            raise RuntimeError(f"Sieuthicode Binance Pay v2 failed: {response.status_code} {data}")
        if str(data.get("status") or "").lower() == "success" or str(data.get("code") or "") == "000000":
            return data.get("transactions") or []
        return []

    def _fetch_history_raw(self):
        response = requests.get(self._history_url(), timeout=20)
        data = response.json()
        if not response.ok:
            raise RuntimeError(f"Sieuthicode Binance Pay failed: {response.status_code} {data}")
        if str(data.get("code") or "") == "000000":
            return data.get("data") or []
        return []

    @staticmethod
    def _normalize_amount(value):
        try:
            return Decimal(str(value or "0")).quantize(Decimal("0.01"))
        except Exception:
            return Decimal("0.00")

    @staticmethod
    def _normalize_text(value):
        return str(value or "").strip().casefold()

    def _matches_order(self, tx, order_ref, amount):
        order_ref = self._normalize_text(order_ref)
        tx_amount = self._normalize_amount(tx.get("amount"))
        if tx_amount != self._normalize_amount(amount):
            return False
        candidates = [
            tx.get("orderId"),
            tx.get("transactionID"),
            tx.get("transactionId"),
            tx.get("description"),
            tx.get("note"),
        ]
        if any(order_ref and order_ref in self._normalize_text(candidate) for candidate in candidates):
            return True
        payer = tx.get("payerInfo") if isinstance(tx.get("payerInfo"), dict) else {}
        if any(order_ref and order_ref in self._normalize_text(payer.get(field)) for field in ("name", "binanceId")):
            return True
        return False

    def get_payment_status(self, order_ref):
        order = supabase_store.get_order(str(order_ref)) if supabase_store.enabled else None
        if not order:
            return "PENDING"
        if str(order.get("status") or "").upper() != "PENDING":
            return "PAID" if str(order.get("status") or "").upper() == "PAID" else "ERROR"
        try:
            expected_amount = Decimal(str(order.get("amount") or "0")).quantize(Decimal("0.01"))
            transactions = []
            try:
                transactions = self._fetch_history_v2()
            except Exception:
                transactions = self._fetch_history_raw()
            for tx in transactions:
                if not isinstance(tx, dict):
                    continue
                if str(tx.get("type") or "").upper() not in {"IN", "RECEIVE", "RECEIVED"} and not tx.get("payerInfo"):
                    continue
                if self._normalize_amount(tx.get("amount")) != expected_amount:
                    continue
                if self._matches_order(tx, order_ref, expected_amount):
                    try:
                        existing = order.get("metadata") if isinstance(order.get("metadata"), dict) else {}
                        supabase_store.update_order_fields(str(order_ref), {
                            "metadata": {
                                **existing,
                                "binance_pay_transaction_id": str(tx.get("transactionID") or tx.get("transactionId") or ""),
                                "binance_pay_order_id": str(tx.get("orderId") or ""),
                                "binance_pay_amount": str(tx.get("amount") or ""),
                                "binance_pay_currency": str(tx.get("currency") or ""),
                                "binance_pay_note": str(tx.get("description") or tx.get("note") or ""),
                            },
                        })
                    except Exception as meta_err:
                        print(f"⚠️ Không lưu được metadata Binance Pay cho đơn {order_ref}: {meta_err}")
                    return "PAID"
            return "PENDING"
        except Exception as exc:
            print(f"⚠️ Lỗi kiểm tra Binance Pay Sieuthicode: {exc}")
            return "ERROR"

    def scan_pending_orders(self, limit=200):
        if not self.enabled:
            return []
        try:
            orders = supabase_store.list_pending_orders(limit=limit) if supabase_store.enabled else []
        except Exception as exc:
            print(f"⚠️ Lỗi đọc danh sách đơn pending Binance Pay: {exc}")
            return []

        matched = []
        for order in orders:
            if str(order.get("payment_provider") or "").upper() != self.provider:
                continue
            order_id = str(order.get("order_id") or "").strip()
            if not order_id:
                continue
            if self.get_payment_status(order_id) == "PAID":
                matched.append(order_id)
        return matched


class PaymentManager:
    def __init__(self):
        self.payos = PayOSManager()
        self.paypal = PayPalManager()
        self.nowpayments = NowPaymentsManager()
        self.tron_usdt = TronUsdtManager()
        self.binance_pay = BinancePaySieuthicodeManager()

    def enabled_providers(self):
        return [provider for provider in ("PAYOS", "PAYPAL", "NOWPAYMENTS", "TRON_USDT", "BINANCE_PAY") if self.provider_enabled(provider)]

    def manager_for(self, provider):
        selected = str(provider or "PAYOS").upper()
        if selected == "PAYPAL":
            return self.paypal
        if selected == "NOWPAYMENTS":
            return self.nowpayments
        if selected == "TRON_USDT":
            return self.tron_usdt
        if selected == "BINANCE_PAY":
            return self.binance_pay
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
        default = "PAYPAL,TRON_USDT" if key.endswith("_EN") else "PAYOS"
        configured = str(db.get_config(key, default) or default).upper().replace(";", ",")
        providers = []
        for item in configured.split(","):
            provider = item.strip()
            if provider in {"PAYOS", "PAYPAL", "NOWPAYMENTS", "TRON_USDT", "BINANCE_PAY"} and provider not in providers and self.provider_enabled(provider):
                providers.append(provider)
        if key.endswith("_EN") and "TRON_USDT" not in providers and self.provider_enabled("TRON_USDT"):
            providers.append("TRON_USDT")
        if key.endswith("_VI") and "BINANCE_PAY" not in providers and self.provider_enabled("BINANCE_PAY"):
            providers.append("BINANCE_PAY")
        if providers:
            return providers
        return []

    def create_payment_link(self, order_code, amount, description, provider=""):
        selected = str(provider or self.preferred_provider()).upper()
        manager = self.manager_for(selected)
        return manager.create_payment_link(order_code, amount, description)

    def get_payment_status(self, order_ref):
        order = supabase_store.get_order(str(order_ref)) if supabase_store.enabled else None
        metadata = (order or {}).get("metadata") if isinstance((order or {}).get("metadata"), dict) else {}
        provider = str((order or {}).get("payment_provider") or metadata.get("payment_provider") or "PAYOS").upper()
        provider_order_id = str((order or {}).get("payment_provider_order_id") or metadata.get("payment_provider_order_id") or order_ref)
        manager = self.manager_for(provider)
        return manager.get_payment_status(provider_order_id)

    def scan_pending_orders(self, provider=""):
        selected = str(provider or "BINANCE_PAY").upper()
        manager = self.manager_for(selected)
        if hasattr(manager, "scan_pending_orders"):
            return manager.scan_pending_orders()
        return []


payment_manager = PaymentManager()
payos_manager = payment_manager
