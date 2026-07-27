import hashlib
import hmac
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime

from bot_links import bot_base_url, normalize_bot_link_template


LICENSE_KEY_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_-]{6,128}$")


@dataclass(frozen=True)
class LicensePlan:
    plan_code: str
    groups: tuple[str, ...]
    duration_days: int | None
    allow_renew: bool
    aliases: tuple[str, ...] = ()


DEFAULT_LICENSE_PLANS: dict[str, LicensePlan] = {
    "COMBO_30D": LicensePlan("COMBO_30D", ("group_a", "group_b"), 30, True, aliases=("HCV_30D", "VIP_PRO", "VIP_BASIC", "VIP_30D")),
    "COMBO_LIFE": LicensePlan("COMBO_LIFE", ("group_a", "group_b", "group_c"), None, False, aliases=("HCV_LIFETIME", "VIP_LIFE", "VIP_LIFETIME")),
}


def _coerce_bool(value, default=False) -> bool:
    if value is None:
        return bool(default)
    return str(value).strip().upper() in {"ON", "TRUE", "YES", "1", "BẬT", "BAT"}


def _parse_json_config(text: str):
    raw = str(text or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def license_flow_enabled() -> bool:
    return str(os.getenv("LICENSE_FLOW_ENABLED", "ON") or "ON").strip().upper() in {"ON", "TRUE", "YES", "1"}


def license_renewal_enabled() -> bool:
    return str(os.getenv("LICENSE_RENEWAL_ENABLED", "ON") or "ON").strip().upper() in {"ON", "TRUE", "YES", "1"}


def license_verify_required() -> bool:
    return _coerce_bool(os.getenv("LICENSE_VERIFY_REQUIRED", "ON"), default=True)


def normalize_license_key(value: str) -> str:
    text = str(value or "").strip().upper()
    return re.sub(r"[^A-Z0-9_-]", "", text)


def is_valid_license_key(value: str) -> bool:
    return bool(LICENSE_KEY_PATTERN.fullmatch(normalize_license_key(value)))


def normalize_license_start_payload(value: str) -> str:
    payload = str(value or "").strip()
    if payload.lower().startswith("lic_"):
        return f"lic_{normalize_license_key(payload[4:])}"
    return ""


def build_license_deeplink(license_key: str) -> str:
    template = normalize_bot_link_template(
        str(os.getenv("LICENSE_BOT_LINK_TEMPLATE", "") or "").strip(),
        default_payload="lic_{code}",
    )
    normalized = normalize_license_key(license_key)
    if not normalized:
        return f"{bot_base_url()}?start=lic_"
    if "{code}" in template:
        return template.replace("{code}", normalized)
    if "start=lic_" in template:
        return template.replace("start=lic_", f"start=lic_{normalized}")
    return f"{bot_base_url()}?start=lic_{normalized}"


def license_signature_secret() -> str:
    return str(os.getenv("LICENSE_WEBHOOK_SECRET", "") or os.getenv("BOT_API_SECRET", "") or "").strip()


def license_backend_url() -> str:
    """
    Preferred backend for license verification.

    Priority:
    1. LICENSE_WEB_BACKEND_URL
    2. LICENSE_WEB_URL
    3. WEB_BACKEND_URL
    4. empty string
    """
    for key in ("LICENSE_WEB_BACKEND_URL", "LICENSE_WEB_URL", "WEB_BACKEND_URL"):
        value = str(os.getenv(key, "") or "").strip().rstrip("/")
        if value:
            return value
    return ""


def sign_license_request(payload: dict[str, object], secret: str | None = None) -> str:
    key = str(secret or license_signature_secret() or "").strip()
    if not key:
        return ""
    message = "|".join(
        [
            str(payload.get("license_key", "") or ""),
            str(payload.get("telegram_user_id", "") or ""),
            str(payload.get("timestamp", "") or ""),
            str(payload.get("nonce", "") or ""),
        ]
    )
    return hmac.new(key.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_license_signature(payload: dict[str, object], signature: str, secret: str | None = None) -> bool:
    expected = sign_license_request(payload, secret=secret)
    if not expected:
        return False
    return hmac.compare_digest(expected, str(signature or "").strip())


def license_request_payload(license_key: str, telegram_user_id: str, *, nonce: str, timestamp: int | None = None) -> dict[str, object]:
    return {
        "license_key": normalize_license_key(license_key),
        "telegram_user_id": str(telegram_user_id).strip(),
        "timestamp": int(timestamp or time.time()),
        "nonce": str(nonce or "").strip(),
    }


def normalize_license_state(value: str) -> str:
    status = str(value or "").strip().lower()
    mapping = {
        "pending": "pending",
        "issued": "issued",
        "redeemed": "redeemed",
        "active": "active",
        "expired": "expired",
        "revoked": "revoked",
    }
    return mapping.get(status, "pending")


def parse_iso_datetime(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return parsed.isoformat()
    except ValueError:
        return raw


def _normalize_plan_mapping_entry(plan_code: str, raw_value) -> LicensePlan | None:
    code = str(plan_code or "").strip().upper()
    if not code:
        return None
    base = DEFAULT_LICENSE_PLANS.get(code, LicensePlan(code, tuple(), None, True))
    if isinstance(raw_value, dict):
        groups = tuple(str(item).strip() for item in (raw_value.get("groups") or []) if str(item).strip())
        duration_days = raw_value.get("duration_days", base.duration_days)
        allow_renew = raw_value.get("allow_renew", base.allow_renew)
        aliases = tuple(str(item).strip().upper() for item in (raw_value.get("aliases") or []) if str(item).strip())
    else:
        groups = base.groups
        duration_days = base.duration_days
        allow_renew = base.allow_renew
        aliases = base.aliases
    try:
        duration_days = None if duration_days in {None, "", "null"} else int(float(str(duration_days)))
    except Exception:
        duration_days = base.duration_days
    return LicensePlan(code, groups or base.groups, duration_days, _coerce_bool(allow_renew, default=base.allow_renew), aliases=aliases or base.aliases)


def load_license_plan_mapping(db_client=None) -> dict[str, LicensePlan]:
    source = {}
    if db_client is not None:
        try:
            raw = db_client.get_config("LICENSE_PLAN_MAPPING_JSON", "")
            parsed = _parse_json_config(raw)
            if isinstance(parsed, dict):
                source = parsed
        except Exception:
            source = {}
        if not source:
            try:
                raw = db_client.get_config("LICENSE_PLAN_MAPPING", "")
                parsed = _parse_json_config(raw)
                if isinstance(parsed, dict):
                    source = parsed
            except Exception:
                source = {}
    mapping: dict[str, LicensePlan] = dict(DEFAULT_LICENSE_PLANS)
    for plan_code, raw_value in source.items():
        normalized = _normalize_plan_mapping_entry(plan_code, raw_value)
        if normalized:
            mapping[normalized.plan_code] = normalized
            for alias in normalized.aliases:
                alias_code = str(alias or "").strip().upper()
                if alias_code:
                    mapping[alias_code] = normalized
    return mapping
