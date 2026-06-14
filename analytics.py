import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from database import db, normalize_key
from supabase_store import supabase_store
from helpers import create_background_task

USERS_HEADERS = [
    "User_ID",
    "Username",
    "Full_Name",
    "First_Seen",
    "Last_Seen",
    "Total_Events",
    "Messages",
    "Callbacks",
    "Commands",
    "Starts",
    "Policy_Clicks",
    "Support_Clicks",
    "Buy_Clicks",
    "Renew_Clicks",
    "Private_Events",
    "Last_Command",
    "Last_Callback",
]

DAILY_HEADERS = [
    "Date",
    "Total_Events",
    "Unique_Users",
    "Private_Users",
    "Messages",
    "Callbacks",
    "Commands",
    "Starts",
    "Policy_Clicks",
    "Support_Clicks",
    "Buy_Clicks",
    "Renew_Clicks",
    "User_IDs",
    "Private_User_IDs",
]

PERIOD_HEADERS = [
    "Period",
    "Total_Events",
    "Unique_Users",
    "Private_Users",
    "Messages",
    "Callbacks",
    "Commands",
    "Starts",
    "Policy_Clicks",
    "Support_Clicks",
    "Buy_Clicks",
    "Renew_Clicks",
    "User_IDs",
    "Private_User_IDs",
]

USERS_SHEET = "AnalyticsUsers"
DAILY_SHEET = "AnalyticsDaily"
MONTHLY_SHEET = "AnalyticsMonthly"
YEARLY_SHEET = "AnalyticsYearly"

_queue = None
_worker_task = None


def _now():
    return datetime.now()


def _extract_event(event):
    now = _now()
    base = {
        "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "user_id": "",
        "username": "",
        "full_name": "",
        "chat_id": "",
        "chat_type": "",
        "event_type": "",
        "command": "",
        "callback_data": "",
    }

    if isinstance(event, Message):
        text = event.text or event.caption or ""
        command = text.split()[0][1:].split("@")[0] if text.startswith("/") else ""
        chat_type = event.chat.type if event.chat else ""

        # Dashboard analytics chỉ phục vụ tương tác riêng User -> Bot.
        # Group/supergroup quá nhiễu cho admin và có log riêng ở support_events khi cần.
        if chat_type != "private":
            return None

        base.update(
            {
                "user_id": str(event.from_user.id) if event.from_user else "",
                "username": event.from_user.username or "" if event.from_user else "",
                "full_name": event.from_user.full_name or "" if event.from_user else "",
                "chat_id": str(event.chat.id) if event.chat else "",
                "chat_type": chat_type,
                "event_type": "message",
                "command": command,
            }
        )
        return base

    if isinstance(event, CallbackQuery):
        message = event.message
        chat = message.chat if message else None
        chat_type = chat.type if chat else ""
        if chat_type and chat_type != "private":
            return None

        base.update(
            {
                "user_id": str(event.from_user.id) if event.from_user else "",
                "username": event.from_user.username or "" if event.from_user else "",
                "full_name": event.from_user.full_name or "" if event.from_user else "",
                "chat_id": str(chat.id) if chat else "",
                "chat_type": chat_type,
                "event_type": "callback",
                "callback_data": event.data or "",
            }
        )
        return base

    return None


def _is_policy(event):
    command = normalize_key(event["command"]).lower()
    callback = normalize_key(event["callback_data"]).lower()
    return command == "policy" or callback in {"policy", "policy_page", "nav:policy_page"}


def _is_support(event):
    command = normalize_key(event["command"]).lower()
    callback = normalize_key(event["callback_data"]).lower()
    return command == "support" or callback in {"support_info", "nav:support_page"}


def _is_buy(event):
    callback = normalize_key(event["callback_data"]).lower()
    return callback.startswith("buy_") or callback.startswith("confirm_") or callback.startswith("upsell_")


def _is_renew(event):
    callback = normalize_key(event["callback_data"]).lower()
    return callback.startswith("renew_")


def _split_ids(value):
    return {item for item in str(value or "").split(",") if item}


def _join_ids(values):
    return ",".join(sorted(str(value) for value in values if value))


def _safe_int(value, default=0):
    try:
        return int(float(str(value or "").strip()))
    except (TypeError, ValueError):
        return default


def _col_name(index):
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def _apply_user_stats(stats, event):
    user_id = event["user_id"]
    if not user_id:
        return

    row = stats.setdefault(
        user_id,
        {
            "user_id": user_id,
            "username": event["username"],
            "full_name": event["full_name"],
            "first_seen": event["timestamp"],
            "last_seen": event["timestamp"],
            "total_events": 0,
            "messages": 0,
            "callbacks": 0,
            "commands": 0,
            "starts": 0,
            "policy_clicks": 0,
            "support_clicks": 0,
            "buy_clicks": 0,
            "renew_clicks": 0,
            "private_events": 0,
            "last_command": "",
            "last_callback": "",
        },
    )
    row["username"] = event["username"] or row["username"]
    row["full_name"] = event["full_name"] or row["full_name"]
    row["last_seen"] = event["timestamp"]
    row["total_events"] += 1
    if event["event_type"] == "message":
        row["messages"] += 1
    if event["event_type"] == "callback":
        row["callbacks"] += 1
    if event["command"]:
        row["commands"] += 1
        row["last_command"] = event["command"]
    if normalize_key(event["command"]).lower() == "start":
        row["starts"] += 1
    if _is_policy(event):
        row["policy_clicks"] += 1
    if _is_support(event):
        row["support_clicks"] += 1
    if _is_buy(event):
        row["buy_clicks"] += 1
    if _is_renew(event):
        row["renew_clicks"] += 1
    if event["chat_type"] == "private":
        row["private_events"] += 1
    if event["callback_data"]:
        row["last_callback"] = event["callback_data"]


def _apply_daily_stats(stats, event):
    date = event["date"]
    row = stats.setdefault(
        date,
        {
            "date": date,
            "total_events": 0,
            "users": set(),
            "private_users": set(),
            "messages": 0,
            "callbacks": 0,
            "commands": 0,
            "starts": 0,
            "policy_clicks": 0,
            "support_clicks": 0,
            "buy_clicks": 0,
            "renew_clicks": 0,
        },
    )
    row["total_events"] += 1
    if event["user_id"]:
        row["users"].add(event["user_id"])
        if event["chat_type"] == "private":
            row["private_users"].add(event["user_id"])
    if event["event_type"] == "message":
        row["messages"] += 1
    if event["event_type"] == "callback":
        row["callbacks"] += 1
    if event["command"]:
        row["commands"] += 1
    if normalize_key(event["command"]).lower() == "start":
        row["starts"] += 1
    if _is_policy(event):
        row["policy_clicks"] += 1
    if _is_support(event):
        row["support_clicks"] += 1
    if _is_buy(event):
        row["buy_clicks"] += 1
    if _is_renew(event):
        row["renew_clicks"] += 1


def _apply_period_stats(stats, period, event):
    row = stats.setdefault(
        period,
        {
            "period": period,
            "total_events": 0,
            "users": set(),
            "private_users": set(),
            "messages": 0,
            "callbacks": 0,
            "commands": 0,
            "starts": 0,
            "policy_clicks": 0,
            "support_clicks": 0,
            "buy_clicks": 0,
            "renew_clicks": 0,
        },
    )
    row["total_events"] += 1
    if event["user_id"]:
        row["users"].add(event["user_id"])
        if event["chat_type"] == "private":
            row["private_users"].add(event["user_id"])
    if event["event_type"] == "message":
        row["messages"] += 1
    if event["event_type"] == "callback":
        row["callbacks"] += 1
    if event["command"]:
        row["commands"] += 1
    if normalize_key(event["command"]).lower() == "start":
        row["starts"] += 1
    if _is_policy(event):
        row["policy_clicks"] += 1
    if _is_support(event):
        row["support_clicks"] += 1
    if _is_buy(event):
        row["buy_clicks"] += 1
    if _is_renew(event):
        row["renew_clicks"] += 1


def _get_or_create_sheet(title, headers):
    try:
        sheet = db.sh.worksheet(title)
    except Exception:
        sheet = db.sh.add_worksheet(title=title, rows=1000, cols=max(12, len(headers)))
        sheet.append_row(headers)
        return sheet

    values = sheet.get_all_values()
    if not values:
        sheet.append_row(headers)
    elif values[0][: len(headers)] != headers:
        end_col = _col_name(len(headers))
        sheet.update(f"A1:{end_col}1", [headers])
    return sheet


def _load_existing_users(sheet):
    values = sheet.get_all_values()
    data = {}
    for idx, row in enumerate(values[1:], start=2):
        if not row or not row[0]:
            continue
        user_id = str(row[0]).strip()
        data[user_id] = {
            "row": idx,
            "user_id": user_id,
            "username": row[1] if len(row) > 1 else "",
            "full_name": row[2] if len(row) > 2 else "",
            "first_seen": row[3] if len(row) > 3 else "",
            "last_seen": row[4] if len(row) > 4 else "",
            "total_events": int(float(row[5] or 0)) if len(row) > 5 else 0,
            "messages": int(float(row[6] or 0)) if len(row) > 6 else 0,
            "callbacks": int(float(row[7] or 0)) if len(row) > 7 else 0,
            "commands": int(float(row[8] or 0)) if len(row) > 8 else 0,
            "starts": int(float(row[9] or 0)) if len(row) > 9 else 0,
            "policy_clicks": int(float(row[10] or 0)) if len(row) > 10 else 0,
            "support_clicks": int(float(row[11] or 0)) if len(row) > 11 else 0,
            "buy_clicks": int(float(row[12] or 0)) if len(row) > 12 else 0,
            "renew_clicks": int(float(row[13] or 0)) if len(row) > 13 else 0,
            "private_events": int(float(row[14] or 0)) if len(row) > 14 else 0,
            "last_command": row[15] if len(row) > 15 else "",
            "last_callback": row[16] if len(row) > 16 else "",
        }
    return data


def _load_existing_daily(sheet):
    values = sheet.get_all_values()
    data = {}
    for idx, row in enumerate(values[1:], start=2):
        if not row or not row[0]:
            continue
        date = str(row[0]).strip()
        data[date] = {
            "row": idx,
            "date": date,
            "total_events": int(float(row[1] or 0)) if len(row) > 1 else 0,
            "unique_users": int(float(row[2] or 0)) if len(row) > 2 else 0,
            "private_users": int(float(row[3] or 0)) if len(row) > 3 else 0,
            "messages": int(float(row[4] or 0)) if len(row) > 4 else 0,
            "callbacks": int(float(row[5] or 0)) if len(row) > 5 else 0,
            "commands": int(float(row[6] or 0)) if len(row) > 6 else 0,
            "starts": int(float(row[7] or 0)) if len(row) > 7 else 0,
            "policy_clicks": int(float(row[8] or 0)) if len(row) > 8 else 0,
            "support_clicks": int(float(row[9] or 0)) if len(row) > 9 else 0,
            "buy_clicks": int(float(row[10] or 0)) if len(row) > 10 else 0,
            "renew_clicks": int(float(row[11] or 0)) if len(row) > 11 else 0,
            "user_ids": _split_ids(row[12] if len(row) > 12 else ""),
            "private_user_ids": _split_ids(row[13] if len(row) > 13 else ""),
        }
    return data


def _load_existing_periods(sheet):
    values = sheet.get_all_values()
    data = {}
    for idx, row in enumerate(values[1:], start=2):
        if not row or not row[0]:
            continue
        period = str(row[0]).strip()
        data[period] = {
            "row": idx,
            "period": period,
            "total_events": _safe_int(row[1] if len(row) > 1 else 0),
            "unique_users": _safe_int(row[2] if len(row) > 2 else 0),
            "private_users": _safe_int(row[3] if len(row) > 3 else 0),
            "messages": _safe_int(row[4] if len(row) > 4 else 0),
            "callbacks": _safe_int(row[5] if len(row) > 5 else 0),
            "commands": _safe_int(row[6] if len(row) > 6 else 0),
            "starts": _safe_int(row[7] if len(row) > 7 else 0),
            "policy_clicks": _safe_int(row[8] if len(row) > 8 else 0),
            "support_clicks": _safe_int(row[9] if len(row) > 9 else 0),
            "buy_clicks": _safe_int(row[10] if len(row) > 10 else 0),
            "renew_clicks": _safe_int(row[11] if len(row) > 11 else 0),
            "user_ids": _split_ids(row[12] if len(row) > 12 else ""),
            "private_user_ids": _split_ids(row[13] if len(row) > 13 else ""),
        }
    return data


def _user_row(user):
    return [
        user["user_id"],
        user["username"],
        user["full_name"],
        user["first_seen"],
        user["last_seen"],
        user["total_events"],
        user["messages"],
        user["callbacks"],
        user["commands"],
        user["starts"],
        user["policy_clicks"],
        user["support_clicks"],
        user["buy_clicks"],
        user["renew_clicks"],
        user["private_events"],
        user["last_command"],
        user["last_callback"],
    ]


def _daily_row(day):
    users_value = day.get("users", day.get("unique_users", 0))
    private_users_value = day.get("private_users", 0)
    unique_users = len(users_value) if isinstance(users_value, set) else users_value
    private_users = len(private_users_value) if isinstance(private_users_value, set) else private_users_value
    user_ids = day.get("user_ids", day.get("users", set()))
    private_user_ids = day.get("private_user_ids", day.get("private_users", set()))

    return [
        day["date"],
        day["total_events"],
        unique_users,
        private_users,
        day["messages"],
        day["callbacks"],
        day["commands"],
        day["starts"],
        day["policy_clicks"],
        day["support_clicks"],
        day["buy_clicks"],
        day["renew_clicks"],
        _join_ids(user_ids),
        _join_ids(private_user_ids),
    ]


def _period_row(period):
    users_value = period.get("users", period.get("unique_users", 0))
    private_users_value = period.get("private_users", 0)
    unique_users = len(users_value) if isinstance(users_value, set) else users_value
    private_users = len(private_users_value) if isinstance(private_users_value, set) else private_users_value
    user_ids = period.get("user_ids", period.get("users", set()))
    private_user_ids = period.get("private_user_ids", period.get("private_users", set()))

    return [
        period["period"],
        period["total_events"],
        unique_users,
        private_users,
        period["messages"],
        period["callbacks"],
        period["commands"],
        period["starts"],
        period["policy_clicks"],
        period["support_clicks"],
        period["buy_clicks"],
        period["renew_clicks"],
        _join_ids(user_ids),
        _join_ids(private_user_ids),
    ]


def _update_period_sheet(sheet, aggregate_periods):
    existing = _load_existing_periods(sheet)
    batch_updates = []
    new_rows = []
    for period, delta in aggregate_periods.items():
        current = existing.get(period)
        if current:
            user_ids = current.get("user_ids", set()) | delta["users"]
            private_user_ids = current.get("private_user_ids", set()) | delta["private_users"]
            current.update(
                {
                    "total_events": current["total_events"] + delta["total_events"],
                    "unique_users": len(user_ids),
                    "private_users": len(private_user_ids),
                    "messages": current["messages"] + delta["messages"],
                    "callbacks": current["callbacks"] + delta["callbacks"],
                    "commands": current["commands"] + delta["commands"],
                    "starts": current["starts"] + delta["starts"],
                    "policy_clicks": current["policy_clicks"] + delta["policy_clicks"],
                    "support_clicks": current["support_clicks"] + delta["support_clicks"],
                    "buy_clicks": current["buy_clicks"] + delta["buy_clicks"],
                    "renew_clicks": current["renew_clicks"] + delta["renew_clicks"],
                    "user_ids": user_ids,
                    "private_user_ids": private_user_ids,
                }
            )
            batch_updates.append({"range": f"A{current['row']}:N{current['row']}", "values": [_period_row(current)]})
        else:
            delta["user_ids"] = delta["users"]
            delta["private_user_ids"] = delta["private_users"]
            new_rows.append(_period_row(delta))

    if new_rows:
        sheet.append_rows(new_rows, value_input_option="USER_ENTERED")
    if batch_updates:
        sheet.batch_update(batch_updates, value_input_option="USER_ENTERED")


def _prune_old_daily_rows(sheet):
    retention_days = _safe_int(db.get_config("ANALYTICS_DAILY_RETENTION_DAYS", "120"), 120)
    if retention_days <= 0:
        return

    cutoff = (_now() - timedelta(days=retention_days)).date()
    values = sheet.get_all_values()
    rows_to_delete = []
    for idx, row in enumerate(values[1:], start=2):
        if not row or not row[0]:
            continue
        try:
            row_date = datetime.strptime(str(row[0]).strip(), "%Y-%m-%d").date()
        except ValueError:
            continue
        if row_date < cutoff:
            rows_to_delete.append(idx)

    for idx in reversed(rows_to_delete):
        sheet.delete_rows(idx)

    if rows_to_delete:
        logging.info(f"📊 AnalyticsDaily đã xoá {len(rows_to_delete)} dòng cũ hơn {retention_days} ngày.")


def _flush_to_sheets(events):
    if supabase_store.enabled:
        supabase_store.insert_analytics_events(events)
        return

    if not events or not db.sh:
        return

    users_sheet = _get_or_create_sheet(USERS_SHEET, USERS_HEADERS)
    daily_sheet = _get_or_create_sheet(DAILY_SHEET, DAILY_HEADERS)
    monthly_sheet = _get_or_create_sheet(MONTHLY_SHEET, PERIOD_HEADERS)
    yearly_sheet = _get_or_create_sheet(YEARLY_SHEET, PERIOD_HEADERS)

    existing_users = _load_existing_users(users_sheet)
    batch_user_updates = []
    new_user_rows = []
    aggregate_users = {}
    for event in events:
        _apply_user_stats(aggregate_users, event)

    for user_id, delta in aggregate_users.items():
        current = existing_users.get(user_id)
        if current:
            current.update(
                {
                    "username": delta["username"] or current["username"],
                    "full_name": delta["full_name"] or current["full_name"],
                    "last_seen": delta["last_seen"],
                    "total_events": current["total_events"] + delta["total_events"],
                    "messages": current["messages"] + delta["messages"],
                    "callbacks": current["callbacks"] + delta["callbacks"],
                    "commands": current["commands"] + delta["commands"],
                    "starts": current["starts"] + delta["starts"],
                    "policy_clicks": current["policy_clicks"] + delta["policy_clicks"],
                    "support_clicks": current["support_clicks"] + delta["support_clicks"],
                    "buy_clicks": current["buy_clicks"] + delta["buy_clicks"],
                    "renew_clicks": current["renew_clicks"] + delta["renew_clicks"],
                    "private_events": current["private_events"] + delta["private_events"],
                    "last_command": delta["last_command"] or current["last_command"],
                    "last_callback": delta["last_callback"] or current["last_callback"],
                }
            )
            batch_user_updates.append({"range": f"A{current['row']}:Q{current['row']}", "values": [_user_row(current)]})
        else:
            new_user_rows.append(_user_row(delta))

    if new_user_rows:
        users_sheet.append_rows(new_user_rows, value_input_option="USER_ENTERED")
    if batch_user_updates:
        users_sheet.batch_update(batch_user_updates, value_input_option="USER_ENTERED")

    existing_daily = _load_existing_daily(daily_sheet)
    aggregate_daily = {}
    for event in events:
        _apply_daily_stats(aggregate_daily, event)

    batch_daily_updates = []
    new_daily_rows = []
    for date, delta in aggregate_daily.items():
        current = existing_daily.get(date)
        if current:
            user_ids = current.get("user_ids", set()) | delta["users"]
            private_user_ids = current.get("private_user_ids", set()) | delta["private_users"]
            current.update(
                {
                    "total_events": current["total_events"] + delta["total_events"],
                    "unique_users": len(user_ids),
                    "private_users": len(private_user_ids),
                    "messages": current["messages"] + delta["messages"],
                    "callbacks": current["callbacks"] + delta["callbacks"],
                    "commands": current["commands"] + delta["commands"],
                    "starts": current["starts"] + delta["starts"],
                    "policy_clicks": current["policy_clicks"] + delta["policy_clicks"],
                    "support_clicks": current["support_clicks"] + delta["support_clicks"],
                    "buy_clicks": current["buy_clicks"] + delta["buy_clicks"],
                    "renew_clicks": current["renew_clicks"] + delta["renew_clicks"],
                    "user_ids": user_ids,
                    "private_user_ids": private_user_ids,
                }
            )
            batch_daily_updates.append({"range": f"A{current['row']}:N{current['row']}", "values": [_daily_row(current)]})
        else:
            delta["user_ids"] = delta["users"]
            delta["private_user_ids"] = delta["private_users"]
            new_daily_rows.append(_daily_row(delta))

    if new_daily_rows:
        daily_sheet.append_rows(new_daily_rows, value_input_option="USER_ENTERED")
    if batch_daily_updates:
        daily_sheet.batch_update(batch_daily_updates, value_input_option="USER_ENTERED")

    aggregate_monthly = {}
    aggregate_yearly = {}
    for event in events:
        _apply_period_stats(aggregate_monthly, event["date"][:7], event)
        _apply_period_stats(aggregate_yearly, event["date"][:4], event)

    _update_period_sheet(monthly_sheet, aggregate_monthly)
    _update_period_sheet(yearly_sheet, aggregate_yearly)
    _prune_old_daily_rows(daily_sheet)


async def _analytics_worker():
    pending = []
    while True:
        try:
            event = await asyncio.wait_for(_queue.get(), timeout=30)
            pending.append(event)
            while len(pending) < 25:
                try:
                    pending.append(_queue.get_nowait())
                except asyncio.QueueEmpty:
                    break
        except asyncio.TimeoutError:
            pass

        if not pending:
            continue

        batch = pending
        pending = []
        try:
            await asyncio.to_thread(_flush_to_sheets, batch)
        except Exception as e:
            logging.error(f"❌ Lỗi ghi Analytics: {e}")


class AnalyticsMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        extracted = _extract_event(event)
        if extracted and _queue:
            try:
                _queue.put_nowait(extracted)
            except asyncio.QueueFull:
                logging.warning("⚠️ Analytics queue đầy, bỏ qua một event.")
        return await handler(event, data)


def setup_analytics(dp):
    global _queue, _worker_task
    if _queue is None:
        _queue = asyncio.Queue(maxsize=1000)
    if _worker_task is None or _worker_task.done():
        _worker_task = create_background_task(_analytics_worker(), name="analytics_worker", context="analytics")

    middleware = AnalyticsMiddleware()
    dp.message.outer_middleware(middleware)
    dp.callback_query.outer_middleware(middleware)
    target = "Supabase analytics_events" if supabase_store.enabled else "AnalyticsUsers / AnalyticsDaily / AnalyticsMonthly / AnalyticsYearly"
    print(f"📊 Analytics đã bật: ghi vào {target}.")
