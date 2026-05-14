import asyncio
import logging
from collections import defaultdict
from datetime import datetime

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from database import db, normalize_key

EVENT_HEADERS = [
    "Timestamp",
    "Date",
    "User_ID",
    "Username",
    "Full_Name",
    "Chat_ID",
    "Chat_Type",
    "Event_Type",
    "Command",
    "Callback_Data",
    "Text_Preview",
]

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
]

EVENT_SHEET = "AnalyticsEvents"
USERS_SHEET = "AnalyticsUsers"
DAILY_SHEET = "AnalyticsDaily"

_queue = None
_worker_task = None


def _now():
    return datetime.now()


def _text_preview(text):
    return str(text or "").replace("\n", " ")[:120]


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
        "text_preview": "",
    }

    if isinstance(event, Message):
        text = event.text or event.caption or ""
        command = text.split()[0][1:].split("@")[0] if text.startswith("/") else ""
        base.update(
            {
                "user_id": str(event.from_user.id) if event.from_user else "",
                "username": event.from_user.username or "" if event.from_user else "",
                "full_name": event.from_user.full_name or "" if event.from_user else "",
                "chat_id": str(event.chat.id) if event.chat else "",
                "chat_type": event.chat.type if event.chat else "",
                "event_type": "message",
                "command": command,
                "text_preview": _text_preview(text),
            }
        )
        return base

    if isinstance(event, CallbackQuery):
        message = event.message
        chat = message.chat if message else None
        base.update(
            {
                "user_id": str(event.from_user.id) if event.from_user else "",
                "username": event.from_user.username or "" if event.from_user else "",
                "full_name": event.from_user.full_name or "" if event.from_user else "",
                "chat_id": str(chat.id) if chat else "",
                "chat_type": chat.type if chat else "",
                "event_type": "callback",
                "callback_data": event.data or "",
                "text_preview": _text_preview(message.text or message.caption if message else ""),
            }
        )
        return base

    return None


def _event_row(event):
    return [
        event["timestamp"],
        event["date"],
        event["user_id"],
        event["username"],
        event["full_name"],
        event["chat_id"],
        event["chat_type"],
        event["event_type"],
        event["command"],
        event["callback_data"],
        event["text_preview"],
    ]


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
            "private_events": int(float(row[13] or 0)) if len(row) > 13 else 0,
            "last_command": row[14] if len(row) > 14 else "",
            "last_callback": row[15] if len(row) > 15 else "",
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
        }
    return data


def _compute_daily_from_events(event_sheet, dates):
    rows = event_sheet.get_all_values()
    computed = {}
    target_dates = set(dates)
    for row in rows[1:]:
        if len(row) < 10:
            continue
        date = row[1]
        if date not in target_dates:
            continue

        item = computed.setdefault(
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
            },
        )
        user_id = row[2]
        chat_type = row[6]
        event_type = row[7]
        command = normalize_key(row[8]).lower()
        callback = normalize_key(row[9]).lower()

        item["total_events"] += 1
        if user_id:
            item["users"].add(user_id)
            if chat_type == "private":
                item["private_users"].add(user_id)
        if event_type == "message":
            item["messages"] += 1
        if event_type == "callback":
            item["callbacks"] += 1
        if command:
            item["commands"] += 1
        if command == "start":
            item["starts"] += 1
        if command == "policy" or callback in {"policy", "policy_page", "nav:policy_page"}:
            item["policy_clicks"] += 1
        if command == "support" or callback in {"support_info", "nav:support_page"}:
            item["support_clicks"] += 1
        if callback.startswith("buy_") or callback.startswith("confirm_") or callback.startswith("upsell_"):
            item["buy_clicks"] += 1
    return computed


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
        user["private_events"],
        user["last_command"],
        user["last_callback"],
    ]


def _daily_row(day):
    users_value = day.get("users", day.get("unique_users", 0))
    private_users_value = day.get("private_users", 0)
    unique_users = len(users_value) if isinstance(users_value, set) else users_value
    private_users = len(private_users_value) if isinstance(private_users_value, set) else private_users_value

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
    ]


def _flush_to_sheets(events):
    if not events or not db.sh:
        return

    event_sheet = _get_or_create_sheet(EVENT_SHEET, EVENT_HEADERS)
    users_sheet = _get_or_create_sheet(USERS_SHEET, USERS_HEADERS)
    daily_sheet = _get_or_create_sheet(DAILY_SHEET, DAILY_HEADERS)

    event_sheet.append_rows([_event_row(event) for event in events], value_input_option="USER_ENTERED")

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
                    "private_events": current["private_events"] + delta["private_events"],
                    "last_command": delta["last_command"] or current["last_command"],
                    "last_callback": delta["last_callback"] or current["last_callback"],
                }
            )
            batch_user_updates.append({"range": f"A{current['row']}:P{current['row']}", "values": [_user_row(current)]})
        else:
            new_user_rows.append(_user_row(delta))

    if new_user_rows:
        users_sheet.append_rows(new_user_rows, value_input_option="USER_ENTERED")
    if batch_user_updates:
        users_sheet.batch_update(batch_user_updates, value_input_option="USER_ENTERED")

    existing_daily = _load_existing_daily(daily_sheet)
    affected_dates = {event["date"] for event in events}
    aggregate_daily = _compute_daily_from_events(event_sheet, affected_dates)
    batch_daily_updates = []
    new_daily_rows = []
    for date, delta in aggregate_daily.items():
        current = existing_daily.get(date)
        if current:
            current.update(delta)
            current["unique_users"] = len(delta["users"])
            current["private_users"] = len(delta["private_users"])
            batch_daily_updates.append({"range": f"A{current['row']}:K{current['row']}", "values": [_daily_row(current)]})
        else:
            new_daily_rows.append(_daily_row(delta))

    if new_daily_rows:
        daily_sheet.append_rows(new_daily_rows, value_input_option="USER_ENTERED")
    if batch_daily_updates:
        daily_sheet.batch_update(batch_daily_updates, value_input_option="USER_ENTERED")


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
            logging.error(f"❌ Lỗi ghi Analytics vào Sheet: {e}")


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
        _worker_task = asyncio.create_task(_analytics_worker())

    middleware = AnalyticsMiddleware()
    dp.message.outer_middleware(middleware)
    dp.callback_query.outer_middleware(middleware)
    print("📊 Analytics đã bật: ghi vào AnalyticsEvents / AnalyticsUsers / AnalyticsDaily.")
