from hidden_group_utils import get_hidden_code


def normalize_message_text(message) -> str:
    if not message:
        return ""
    text = str(getattr(message, "text", "") or getattr(message, "caption", "") or "").strip()
    return text


def normalize_coupon_code(text: str) -> str:
    raw = "".join(ch for ch in str(text or "").strip().upper() if ch.isalnum() or ch == "_")
    return raw.replace(" ", "")


def _looks_like_coupon_code(text: str, coupon_prefixes=None) -> bool:
    normalized = str(text or "").strip().upper()
    if not normalized:
        return False
    if coupon_prefixes:
        for prefix in coupon_prefixes:
            if normalized.startswith(str(prefix or "").strip().upper()):
                return True
    if normalized.startswith("HANGCU_"):
        return True
    return False


def classify_private_message(message, *, coupon_prefixes=None):
    """
    Unified classifier for private inbound user content.

    Returns:
        {
            "kind": one of: activation, coupon, hidden, support, other,
            "text": normalized text,
            "code": normalized code for coupon/hidden/activation,
            "reason": short debug reason,
        }
    """
    text = normalize_message_text(message)
    has_media = bool(
        getattr(message, "photo", None)
        or getattr(message, "document", None)
        or getattr(message, "video", None)
        or getattr(message, "voice", None)
        or getattr(message, "audio", None)
        or getattr(message, "sticker", None)
    )
    if not text and not has_media:
        return {"kind": "other", "text": "", "code": "", "reason": "empty"}

    if text.startswith("/start "):
        payload = text.split(maxsplit=1)[1].strip() if len(text.split(maxsplit=1)) > 1 else ""
        payload_lower = payload.lower()
        if payload_lower.startswith("src_"):
            return {"kind": "other", "text": text, "code": payload[4:].strip(), "reason": "start_source"}
        if payload_lower.startswith("act_"):
            return {"kind": "activation", "text": text, "code": payload[4:].strip(), "reason": "start_activation"}
        if payload:
            return {"kind": "activation", "text": text, "code": payload, "reason": "start_legacy_activation"}
        return {"kind": "other", "text": text, "code": "", "reason": "start_no_payload"}
    if text.startswith("/"):
        return {"kind": "other", "text": text, "code": "", "reason": "command"}

    code = normalize_coupon_code(text)
    if code:
        try:
            hidden_code = get_hidden_code(code)
        except Exception:
            hidden_code = None
        if hidden_code:
            return {"kind": "hidden", "text": text, "code": code, "reason": "hidden_match"}
        if _looks_like_coupon_code(code, coupon_prefixes=coupon_prefixes):
            return {"kind": "coupon", "text": text, "code": code, "reason": "coupon_prefix"}

    return {"kind": "support", "text": text, "code": code if code else "", "reason": "plain_text" if text else "media_only"}


def classify_message_text(text: str, *, coupon_prefixes=None):
    class _Message:
        def __init__(self, text):
            self.text = text
            self.caption = ""

    return classify_private_message(_Message(text), coupon_prefixes=coupon_prefixes)
