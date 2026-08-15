from __future__ import annotations

from new_core.ports import KickResult


def classify_telegram_error(exc: Exception) -> str:
    text = str(exc).lower()
    if any(token in text for token in ("user not found", "participant_id_invalid")):
        return "member_absent"
    if "chat not found" in text:
        return "group_not_found"
    if "too many requests" in text or "retry after" in text:
        return "rate_limited"
    if "not enough rights" in text or "administrator" in text or "forbidden" in text:
        return "permission_denied"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    return "telegram_unknown_error"


class TelegramMembershipGateway:
    """Telegram adapter with conservative presence semantics."""

    def __init__(self, bot):
        self.bot = bot

    async def is_present(self, group_id: str, user_id: str) -> bool | None:
        try:
            member = await self.bot.get_chat_member(chat_id=group_id, user_id=int(user_id))
        except Exception as exc:
            reason = classify_telegram_error(exc)
            if reason == "member_absent":
                return False
            return None
        status = str(getattr(getattr(member, "status", ""), "value", getattr(member, "status", ""))).lower()
        if status in {"left", "kicked", "banned"}:
            return False
        if status in {"member", "administrator", "creator", "restricted"}:
            return True
        return None

    async def kick(self, group_id: str, user_id: str) -> KickResult:
        try:
            await self.bot.ban_chat_member(chat_id=group_id, user_id=int(user_id))
            await self.bot.unban_chat_member(chat_id=group_id, user_id=int(user_id))
            return KickResult(ok=True, reason="kick_sent")
        except Exception as exc:
            return KickResult(ok=False, reason=classify_telegram_error(exc))

    async def mute(self, group_id: str, user_id: str) -> KickResult:
        return KickResult(ok=False, reason="mute_not_in_kick_adapter")

    async def unmute(self, group_id: str, user_id: str) -> KickResult:
        return KickResult(ok=False, reason="unmute_not_in_kick_adapter")
