import os
import sys

from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import db
from supabase_store import supabase_store

load_dotenv()


EN_CONFIG = {
    "BTN_G1_EN": "Hang Cu Prime",
    "BTN_G2_EN": "Hang Cu Boy",
    "BTN_G3_EN": "Hang Cu Black",
    "BTN_G4_EN": "Hang Cu Asia",
    "PLAN_FULL_1M_EN": "SVIP+ 30 days",
    "PLAN_FULL_LIFE_EN": "SVIP+ Lifetime",
    "PLAN_G_1M_EN": "VIP 30 days",
    "PLAN_G_LIFE_EN": "VIP lifetime",
    "BTN_BUY_SVIP_30D_EN": "BUY 30 DAYS",
    "BTN_BUY_SVIP_LIFE_EN": "BUY LIFETIME",
    "BTN_BUY_1M_EN": "VIP 30 DAYS",
    "BTN_BUY_LIFE_EN": "VIP LIFETIME",
    "BTN_VIEW_SVIP_PAGE_EN": "VIEW SVIP+ VALUE PLAN",
    "BTN_BACK_EN": "Back to menu",
    "BTN_LANGUAGE_SWITCH_TO_EN": "English",
    "BTN_LANGUAGE_SWITCH_TO_VI": "Tieng Viet",
    "BTN_SWITCH_TO_VIETNAMESE": "Switch to Vietnamese",
    "BTN_CONTACT_ADMIN_PAYMENT": "Contact admin",
    "BOT_COMMAND_DESC_START_EN": "Home / Buy plan",
    "BOT_COMMAND_DESC_ME_EN": "Check memberships and expiry",
    "BOT_COMMAND_DESC_COUPON_EN": "Enter discount or activation code",
    "BOT_COMMAND_DESC_SUPPORT_EN": "Contact admin support",
    "BOT_COMMAND_DESC_POLICY_EN": "Read group rules",
    "EN_VIETQR_PAYMENT_ENABLED": "OFF",
    "MSG_EN_VIETQR_UNAVAILABLE": (
        "<b>VietQR payment is currently supported only for Vietnam bank transfers.</b>\\n\\n"
        "Please switch to Vietnamese to pay by VietQR, or contact admin to pay by PayPal or crypto."
    ),
}


def clean_text(value):
    return str(value or "").strip().strip('"')


def page_payloads(existing_pages):
    image = ""
    for key in ("main_menu", "group1_page", "support_page"):
        page = existing_pages.get(key) or {}
        if page.get("img"):
            image = page.get("img")
            break

    return {
        "main_menu_en": {
            "image_url": image,
            "body": (
                "<b>WELCOME TO HANG CU PRIVE+ VIP</b>\\n\\n"
                "Curated private collections, updated regularly.\\n"
                "After payment, your invite link is issued automatically.\\n"
                "Full HD quality, clear categories, private access.\\n\\n"
                "<b>PRIVE+ ACCESS</b>\\n\\n"
                "<b>Hang Cu Prime</b> - curated Vietnam creator content\\n"
                "<b>Hang Cu Boy</b> - curated boy-focused collections\\n"
                "<b>Hang Cu Black</b> - leaked-clip, hidden-cam and private collections\\n"
                "<b>Hang Cu Asia</b> - curated Thai, Chinese, Korean and Japanese creator content\\n\\n"
                "Choose SVIP+ 30 days, lifetime all-access, or a single-group VIP plan below."
            ),
            "layout": (
                "SVIP+ LIFETIME • {PRICE_SVIP_LIFE} => nav:svip_page_en\\n"
                "SVIP+ 30 DAYS • {PRICE_SVIP_30D} => nav:svip_page_en\\n"
                "Hang Cu Prime => nav:group1_page_en\\n"
                "Hang Cu Boy => nav:group2_page_en\\n"
                "Hang Cu Black => nav:group3_page_en\\n"
                "Hang Cu Asia => nav:group4_page_en\\n"
                "Account => my_info | Rules => nav:policy_page_en | Support => nav:support_page_en"
            ),
        },
        "svip_page_en": {
            "image_url": image,
            "body": (
                "<b>SVIP+ ALL-ACCESS</b>\\n\\n"
                "Unlock the full Prive+ ecosystem with all available groups.\\n"
                "Best value if you want access to every collection.\\n\\n"
                "Choose your access below."
            ),
            "layout": (
                "SVIP+ LIFETIME • {PRICE_SVIP_LIFE} => buy_full_life\\n"
                "SVIP+ 30 DAYS • {PRICE_SVIP_30D} => buy_full_1m\\n"
                "Back to menu => nav:main_menu_en"
            ),
        },
        "group1_page_en": {
            "image_url": image,
            "body": (
                "<b>HANG CU PRIME</b>\\n\\n"
                "Curated Vietnam creator content for Prive+ VIP members.\\n\\n"
                "More than <b>5,000+</b> high-quality videos.\\n"
                "Updated regularly.\\n"
                "Selected videos and images, organized for easy browsing.\\n"
                "VIP members only.\\n\\n"
                "Demo channel: @hangcuprime\\n\\n"
                "Choose SVIP+ Lifetime for better value and unlock all 4 groups in the Prive+ ecosystem.\\n\\n"
                "Choose your access below."
            ),
            "layout": (
                "VIP LIFETIME • {PRICE_G1_LIFE} => buy_G1_life\\n"
                "VIP 30 DAYS • {PRICE_G1_1M} => buy_G1_1m\\n"
                "VIEW SVIP+ VALUE PLAN => nav:svip_page_en\\n"
                "Back to menu => nav:main_menu_en"
            ),
        },
        "group2_page_en": {
            "image_url": image,
            "body": (
                "<b>HANG CU BOY</b>\\n\\n"
                "Curated boy-focused private collections for Prive+ VIP members.\\n\\n"
                "More than <b>5,000+</b> high-quality videos.\\n"
                "Updated regularly.\\n"
                "Selected videos and images, organized for easy browsing.\\n"
                "VIP members only.\\n\\n"
                "Demo channel: @hangcuboy\\n\\n"
                "Choose SVIP+ Lifetime for better value and unlock all 4 groups in the Prive+ ecosystem.\\n\\n"
                "Choose your access below."
            ),
            "layout": (
                "VIP LIFETIME • {PRICE_G2_LIFE} => buy_G2_life\\n"
                "VIP 30 DAYS • {PRICE_G2_1M} => buy_G2_1m\\n"
                "VIEW SVIP+ VALUE PLAN => nav:svip_page_en\\n"
                "Back to menu => nav:main_menu_en"
            ),
        },
        "group3_page_en": {
            "image_url": image,
            "body": (
                "<b>HANG CU BLACK</b>\\n\\n"
                "Curated private and hidden-clip collections for Prive+ VIP members.\\n\\n"
                "More than <b>5,000+</b> high-quality videos.\\n"
                "Updated regularly.\\n"
                "Selected content for VIP members only.\\n\\n"
                "Demo channel: @hangcublack\\n\\n"
                "Choose SVIP+ Lifetime for better value and unlock all 4 groups in the Prive+ ecosystem.\\n\\n"
                "Choose your access below."
            ),
            "layout": (
                "VIP LIFETIME • {PRICE_G3_LIFE} => buy_G3_life\\n"
                "VIP 30 DAYS • {PRICE_G3_1M} => buy_G3_1m\\n"
                "VIEW SVIP+ VALUE PLAN => nav:svip_page_en\\n"
                "Back to menu => nav:main_menu_en"
            ),
        },
        "group4_page_en": {
            "image_url": image,
            "body": (
                "<b>HANG CU PRIVE ASIA</b>\\n\\n"
                "Curated Thai, Chinese, Korean and Japanese creator content.\\n\\n"
                "High-quality videos, updated regularly.\\n"
                "VIP members only.\\n\\n"
                "Demo channel: https://t.me/hangcuprive_vn/\\n\\n"
                "Want better value? Upgrade to all-access lifetime and unlock the full Prive+ ecosystem.\\n\\n"
                "Choose your access below."
            ),
            "layout": (
                "VIP LIFETIME • {PRICE_G4_LIFE} => buy_G4_life\\n"
                "VIP 30 DAYS • {PRICE_G4_1M} => buy_G4_1m\\n"
                "VIEW SVIP+ VALUE PLAN => nav:svip_page_en\\n"
                "Back to menu => nav:main_menu_en"
            ),
        },
        "support_page_en": {
            "image_url": image,
            "body": (
                "<b>CUSTOMER SUPPORT</b>\\n\\n"
                "If you have a payment issue, did not receive your invite link, or want to pay by PayPal or crypto, contact admin directly."
            ),
            "layout": (
                "Message admin => url:https://t.me/thamtucu\\n"
                "Back to menu => nav:main_menu_en"
            ),
        },
        "policy_page_en": {
            "image_url": image,
            "body": (
                "<b>HANG CU PRIVE+ VIP POLICY</b>\\n\\n"
                "You receive access based on the plan you purchased. Content is updated regularly and invite links are issued automatically after payment.\\n\\n"
                "Refund support is available within 24 hours if the group or content does not match the description.\\n\\n"
                "Leaking, reposting, sharing invite links, or reselling content is strictly prohibited. Access may be permanently revoked if a violation is detected.\\n\\n"
                "Each plan supports one Telegram account only. By joining, you agree to the system policy."
            ),
            "layout": "Back to menu => nav:main_menu_en",
        },
    }


def seed_supabase():
    pages = {row["page_id"]: row for row in supabase_store.list_menu_pages()}
    for key, value in EN_CONFIG.items():
        supabase_store.set_config(key, value)
    for page_id, page in page_payloads(pages).items():
        current = pages.get(page_id) or {}
        image_url = page["image_url"] or current.get("image_url", "")
        supabase_store.upsert_menu_page(page_id, image_url, page["body"], page["layout"])
    print("seeded english menu pages to Supabase")


def seed_sheets():
    db.connect_google()
    rows = db.menu_sheet.get_all_values()
    index_by_page = {clean_text(row[0]): idx for idx, row in enumerate(rows[1:], start=2) if row}
    existing_pages = {
        clean_text(row[0]): {
            "img": row[1] if len(row) > 1 else "",
            "text": row[2] if len(row) > 2 else "",
            "layout": row[3] if len(row) > 3 else "",
        }
        for row in rows[1:]
        if row and clean_text(row[0])
    }

    for key, value in EN_CONFIG.items():
        db.set_config(key, value)

    for page_id, page in page_payloads(existing_pages).items():
        row = [page_id, page["image_url"], page["body"], page["layout"]]
        if page_id in index_by_page:
            db.menu_sheet.update(f"A{index_by_page[page_id]}:D{index_by_page[page_id]}", [row])
        else:
            db.menu_sheet.append_row(row)
    print("seeded english menu pages to Google Sheets")


if __name__ == "__main__":
    if supabase_store.enabled:
        seed_supabase()
    else:
        seed_sheets()
