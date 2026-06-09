from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from helpers import is_admin_user
from i18n import t
from vip_group_audit_utils import build_vip_group_audit_rows

router = Router()


@router.message(Command("scan_vip_groups"))
async def cmd_scan_vip_groups(message: Message):
    if not is_admin_user(message.from_user.id):
        await message.reply(t(message.from_user.id, "MSG_ADMIN_ONLY", "⚠️ Lệnh này chỉ dành cho Admin."))
        return

    live = False
    parts = (message.text or "").split()
    if len(parts) >= 2 and parts[1].strip().lower() in {"live", "on", "1", "true", "yes"}:
        live = True

    await message.reply("⏳ Đang quét VIP group theo dữ liệu đơn hàng...")
    rows = await build_vip_group_audit_rows(live=live)
    if not rows:
        await message.reply("Không tìm thấy khách nào cần kiểm tra.")
        return

    targets = [row for row in rows if row["status"] in {"LEFT_GROUP", "WAITING_CHECK", "KICKED"} or row["needs_action"]]
    if not targets:
        await message.reply("Không phát hiện ai đã out group theo dữ liệu hiện có.")
        return

    lines = ["<b>Kết quả quét VIP group</b>"]
    for row in targets[:40]:
        lines.append(
            f"• <b>{row['customer_name']}</b> | {row['group_name']} | {row['status_label']} | user <code>{row['telegram_user_id']}</code> | order <code>{row['order_id']}</code>"
        )
    if len(targets) > 40:
        lines.append(f"... và {len(targets) - 40} dòng nữa.")

    await message.reply("\n".join(lines), parse_mode="HTML")
