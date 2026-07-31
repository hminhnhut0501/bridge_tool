"""Best-effort PayPal evidence sink for Hangcu_web.

The bot remains authoritative for payment, license, expiry and groups. The web
only stores the evidence needed for merchant reconciliation.
"""

import hashlib
import hmac
import json
import os
import secrets
import time

import requests
from supabase_store import supabase_store


def _secret():
    return str(
        os.getenv("WEB_RECONCILIATION_SECRET")
        or os.getenv("BOT_WEB_HMAC_SECRET")
        or os.getenv("WEB_PAYMENT_SECRET")
        or ""
    ).strip()


def _url():
    base = str(os.getenv("LICENSE_WEB_BACKEND_URL") or os.getenv("LICENSE_WEB_URL") or "").strip().rstrip("/")
    if not base:
        return ""
    return base if base.endswith("/api/v1/reconciliation/orders") else f"{base}/api/v1/reconciliation/orders"


def report_paypal_reconciliation(order: dict, *, license_code: str = "", license_status: str = "", delivery_evidence=None):
    """Send one idempotent evidence snapshot; never changes bot delivery state."""
    url = _url()
    secret = _secret()
    if not url or not secret:
        print(f"[reconciliation] skipped order={order.get('order_id')} reason=missing_url_or_secret")
        return False

    metadata = dict(order.get("metadata") or {})
    if metadata.get("reconciliation_sent_at"):
        return True
    timestamp = int(time.time())
    nonce = secrets.token_hex(12)
    payload = {
        "timestamp": timestamp,
        "nonce": nonce,
        "orderNumber": str(order.get("order_id") or ""),
        "botOrderId": str(order.get("order_id") or ""),
        "paymentProvider": "PAYPAL",
        "paypalOrderId": str(order.get("payment_provider_order_id") or metadata.get("payment_provider_order_id") or ""),
        "paypalCaptureId": str(metadata.get("paypal_capture_id") or metadata.get("payment_id") or ""),
        "paypalPayerId": str(metadata.get("paypal_payer_id") or ""),
        "payerEmail": str(metadata.get("paypal_payer_email") or order.get("customer_email") or ""),
        "amountMinor": int(order.get("amount") or 0),
        "currency": "USD",
        "productType": "support",
        "productName": "Support package",
        "paymentStatus": "paid" if str(order.get("status") or "").upper() == "PAID" else "pending",
        "telegramUserId": str(order.get("telegram_user_id") or ""),
        "internalPlanCode": str(order.get("plan_token") or metadata.get("plan_code") or ""),
        "licenseCode": str(license_code or metadata.get("activation_code") or ""),
        "licenseStatus": license_status,
        "fulfilledAt": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "fulfillmentType": "telegram_delivery",
        "deliveryEvidence": delivery_evidence or {},
    }
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    payload["signature"] = hmac.new(secret.encode(), f"{timestamp}.{nonce}.{raw}".encode(), hashlib.sha256).hexdigest()
    try:
        response = requests.post(url, json=payload, timeout=8)
        if not response.ok:
            print(f"[reconciliation] failed order={order.get('order_id')} status={response.status_code} body={response.text[:300]}")
            return False
        metadata["reconciliation_sent_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        try:
            supabase_store.patch_order(str(order.get("order_id") or ""), {"metadata": metadata})
        except Exception as marker_error:
            print(f"[reconciliation] marker_failed order={order.get('order_id')} error={marker_error}")
        print(f"[reconciliation] delivered botOrderId={order.get('order_id')} paypalOrderId={payload['paypalOrderId']}")
        return True
    except Exception as exc:
        print(f"[reconciliation] failed order={order.get('order_id')} error={exc}")
        return False
