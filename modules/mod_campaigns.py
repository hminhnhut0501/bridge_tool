import asyncio
import logging
from html import escape

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from bot_instance import bot
from supabase_store import _now_iso, supabase_store


def render_campaign_message(template, recipient):
    raw = recipient.get("raw_data") or {}
    values = {
        "telegram_user_id": recipient.get("telegram_user_id") or "",
        "user_id": recipient.get("telegram_user_id") or "",
        "name": recipient.get("full_name") or "bạn",
        "full_name": recipient.get("full_name") or "",
        "username": recipient.get("username") or "",
        "segment": recipient.get("segment") or "",
        "latest_plan_name": raw.get("latest_plan_name") or "",
    }
    text = str(template or "")
    for key, value in values.items():
        text = text.replace("{" + key + "}", escape(str(value)))
    return text


async def send_campaign_recipient(campaign, recipient):
    text = render_campaign_message(campaign.get("message"), recipient)
    parse_mode = str(campaign.get("parse_mode") or "HTML").upper()
    if parse_mode == "NONE":
        parse_mode = None

    try:
        await bot.send_message(
            chat_id=int(recipient.get("telegram_user_id")),
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=True,
        )
        supabase_store.update_broadcast_recipient(
            recipient.get("id"),
            {
                "status": "SENT",
                "sent_at": _now_iso(),
                "last_attempt_at": _now_iso(),
                "attempt_count": int(recipient.get("attempt_count") or 0) + 1,
                "error": None,
            },
        )
        supabase_store.record_broadcast_event(campaign.get("id"), recipient.get("telegram_user_id"), "recipient_sent", {})
        return True
    except TelegramForbiddenError as exc:
        status = "SKIPPED"
        error = f"User blocked bot or chat unavailable: {exc}"
    except TelegramBadRequest as exc:
        status = "FAILED"
        error = str(exc)
    except Exception as exc:
        status = "FAILED"
        error = str(exc)

    supabase_store.update_broadcast_recipient(
        recipient.get("id"),
        {
            "status": status,
            "last_attempt_at": _now_iso(),
            "attempt_count": int(recipient.get("attempt_count") or 0) + 1,
            "error": error[:1000],
        },
    )
    supabase_store.record_broadcast_event(
        campaign.get("id"),
        recipient.get("telegram_user_id"),
        "recipient_failed" if status == "FAILED" else "recipient_skipped",
        {"error": error},
    )
    return False


async def campaign_worker():
    logging.info("📣 Campaign worker đã khởi động.")
    await asyncio.sleep(10)
    while True:
        if not supabase_store.enabled:
            await asyncio.sleep(30)
            continue

        try:
            campaign = supabase_store.next_running_broadcast_campaign()
            if not campaign:
                await asyncio.sleep(10)
                continue

            sent_this_round = 0
            batch_size = max(1, min(int(campaign.get("batch_size") or 20), 100))
            delay_seconds = max(2, min(int(campaign.get("delay_seconds") or 5), 300))
            while sent_this_round < batch_size:
                refreshed = supabase_store.get_broadcast_campaign(campaign.get("id"))
                if not refreshed or refreshed.get("status") != "RUNNING":
                    break

                recipient = supabase_store.next_pending_broadcast_recipient(campaign.get("id"))
                if not recipient:
                    supabase_store.refresh_broadcast_campaign_counts(campaign.get("id"))
                    break

                await send_campaign_recipient(refreshed, recipient)
                supabase_store.refresh_broadcast_campaign_counts(campaign.get("id"))
                sent_this_round += 1
                await asyncio.sleep(delay_seconds)
        except Exception as exc:
            logging.error("❌ Campaign worker lỗi: %s", exc)
            await asyncio.sleep(15)
