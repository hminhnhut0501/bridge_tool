"""Shared bilingual template for successful access delivery."""

from html import escape

from database import db


def _configured_template(is_en, default):
    try:
        localized_key = "MSG_DELIVERY_EN" if is_en else "MSG_DELIVERY_VI"
        localized = str(db.get_config(localized_key, "") or "").strip()
        if localized:
            return localized.replace("\\n", "\n")
        if not is_en:
            legacy = str(db.get_config("MSG_DELIVERY", "") or "").strip()
            if legacy:
                return legacy.replace("\\n", "\n")
    except Exception as exc:
        print(f"⚠️ Delivery template config unavailable, using default: {exc}")
    return default


def build_delivery_message(*, locale="vi", plan_name="", expires_at="", license_code="", links="", support_name=""):
    is_en = str(locale or "vi").lower().startswith("en")
    plan = escape(str(plan_name or "-"))
    expiry = escape(str(expires_at or ("Active" if is_en else "Đang hoạt động")))
    license_value = escape(str(license_code or "-"))
    links_value = links.strip() or ("No invitation link is available yet." if is_en else "Chưa có link tham gia.")
    support = escape(str(support_name or ("Support group" if is_en else "Nhóm hỗ trợ")))

    if is_en:
        default = (
            "✅ <b>PAYMENT SUCCESSFUL!</b>\n\n"
            f"🎁 Subscription: <b>{plan}</b>\n"
            f"📅 Valid until: <code>{expiry}</code>\n\n"
            "🔐 <b>LICENSE ACTIVATED</b>\n"
            f"<code>{license_value}</code>\n\n"
            "🔒 <b>YOUR INVITATION LINK(S):</b>\n\n"
            f"{links_value}\n\n"
            f"💌 Please tap the button below to join {support} for warranty, updates, and assistance.\n\n"
            "⚠️ <i>Each invitation link is valid for one account and one use. Do not share it.</i>"
        )
    else:
        default = (
        "✅ <b>THANH TOÁN THÀNH CÔNG!</b>\n\n"
        f"🎁 Gói truy cập: <b>{plan}</b>\n"
        f"📅 Hạn sử dụng: <code>{expiry}</code>\n\n"
        "🔐 <b>LICENSE ĐÃ TỰ ĐỘNG KÍCH HOẠT</b>\n"
        f"<code>{license_value}</code>\n\n"
        "🔒 <b>LINK THAM GIA CỦA BẠN:</b>\n\n"
        f"{links_value}\n\n"
        f"💌 Vui lòng nhấn nút bên dưới để tham gia {support} và nhận hỗ trợ.\n\n"
        "⚠️ <i>Link chỉ sử dụng cho một tài khoản và một lần tham gia. Vui lòng không chia sẻ.</i>"
        )

    template = _configured_template(is_en, default)
    replacements = {
        "{plan}": plan,
        "{date}": expiry,
        "{expire}": expiry,
        "{links}": links_value,
        "{support}": support,
        "{license}": license_value,
        "{code}": license_value,
    }
    for token, value in replacements.items():
        template = template.replace(token, value)
    return template
