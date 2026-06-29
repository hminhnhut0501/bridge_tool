from hidden_group_utils import get_hidden_code


def normalize_message_text(message) -> str:
    if not message:
        return ""
    text = str(getattr(message, "text", "") or getattr(message, "caption", "") or "").strip()
    return text


def normalize_coupon_code(text: str) -> str:
    raw = "".join(ch for ch in str(text or "").strip().upper() if ch.isalnum() or ch == "_")
    return raw.replace(" ", "")


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
    if not text:
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

    code = normalize_coupon_code(text)
    if not code:
        return {"kind": "support", "text": text, "code": "", "reason": "plain_text"}

    if coupon_prefixes:
        if any(code.startswith(prefix) for prefix in coupon_prefixes):
            return {"kind": "coupon", "text": text, "code": code, "reason": "coupon_prefix"}

    try:
        if get_hidden_code(code):
            return {"kind": "hidden", "text": text, "code": code, "reason": "hidden_match"}
    except Exception:
        pass

    return {"kind": "support", "text": text, "code": code, "reason": "plain_text"}


def classify_message_text(text: str, *, coupon_prefixes=None):
    class _Message:
        def __init__(self, text):
            self.text = text
            self.caption = ""

    return classify_private_message(_Message(text), coupon_prefixes=coupon_prefixes)
