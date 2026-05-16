import asyncio
import importlib
import os

from aiogram.types import Update
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from bot_instance import bot, dp, set_commands
from database import db
from supabase_store import supabase_store

load_dotenv()

app = FastAPI(title="Prive Bot Backend")
_booted = False


def _allowed_origins():
    raw = os.getenv("ADMIN_ALLOWED_ORIGINS", "")
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or ["http://localhost:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_admin(x_admin_secret: str | None = Header(default=None)):
    expected = os.getenv("ADMIN_SECRET")
    if not expected:
        raise HTTPException(status_code=503, detail="ADMIN_SECRET is not configured")
    if x_admin_secret != expected:
        raise HTTPException(status_code=401, detail="Invalid admin secret")
    return True


def load_all_modules():
    loaded_count = 0
    module_dir = "modules"
    if not os.path.exists(module_dir):
        return loaded_count

    for filename in os.listdir(module_dir):
        if not filename.startswith("mod_") or not filename.endswith(".py"):
            continue
        module_name = filename[:-3]
        try:
            module = importlib.import_module(f"{module_dir}.{module_name}")
            if hasattr(module, "router"):
                dp.include_router(module.router)
                loaded_count += 1
        except Exception as exc:
            print(f"❌ Lỗi khi nạp module {module_name}: {exc}")
    return loaded_count


async def start_background_workers():
    try:
        from modules.mod_maintenance import maintenance_worker
    except Exception:
        maintenance_worker = None

    try:
        from scheduler import main as scheduler_worker
    except Exception:
        scheduler_worker = None

    try:
        from modules.mod_coupon import coupon_cleanup_worker
    except Exception:
        coupon_cleanup_worker = None

    if maintenance_worker:
        asyncio.create_task(maintenance_worker())
    if scheduler_worker:
        asyncio.create_task(scheduler_worker())
    if coupon_cleanup_worker:
        asyncio.create_task(coupon_cleanup_worker())


@app.on_event("startup")
async def startup():
    global _booted
    if _booted:
        return

    db.connect()
    if supabase_store.enabled:
        supabase_store.connect()
    await set_commands()
    try:
        from analytics import setup_analytics

        setup_analytics(dp)
    except Exception as exc:
        print(f"⚠️ Không thể bật analytics middleware: {exc}")
    load_all_modules()
    await start_background_workers()

    webhook_url = os.getenv("WEBHOOK_URL")
    webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if webhook_url:
        await bot.set_webhook(webhook_url, secret_token=webhook_secret or None, allowed_updates=dp.resolve_used_update_types())
        print(f"✅ Telegram webhook set: {webhook_url}")
    else:
        print("⚠️ WEBHOOK_URL chưa được cấu hình, backend chỉ chạy API/health.")

    _booted = True


@app.on_event("shutdown")
async def shutdown():
    await bot.session.close()


@app.get("/health")
async def health():
    return {
        "ok": True,
        "supabase": supabase_store.enabled,
        "webhook_url_configured": bool(os.getenv("WEBHOOK_URL")),
    }


@app.get("/")
async def root():
    return {"ok": True, "service": "prive-bot-backend"}


@app.get("/admin-api/webhook-info", dependencies=[Depends(require_admin)])
async def admin_webhook_info():
    return {"data": await bot.get_webhook_info()}


@app.post("/admin-api/webhook-reset", dependencies=[Depends(require_admin)])
async def admin_webhook_reset():
    webhook_url = os.getenv("WEBHOOK_URL")
    webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if not webhook_url:
        raise HTTPException(status_code=503, detail="WEBHOOK_URL is not configured")
    await bot.set_webhook(
        webhook_url,
        secret_token=webhook_secret or None,
        drop_pending_updates=False,
        allowed_updates=dp.resolve_used_update_types(),
    )
    return {"data": await bot.get_webhook_info()}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    expected = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    if expected:
        received = request.headers.get("x-telegram-bot-api-secret-token")
        if received != expected:
            raise HTTPException(status_code=401, detail="Invalid Telegram webhook secret")

    payload = await request.json()
    update = Update.model_validate(payload, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/admin-api/orders", dependencies=[Depends(require_admin)])
async def admin_orders(limit: int = 200):
    return {"data": supabase_store.list_orders(limit=limit)}


@app.patch("/admin-api/orders/{order_id}", dependencies=[Depends(require_admin)])
async def admin_update_order(order_id: str, request: Request):
    body = await request.json()
    data = supabase_store.update_order_status(
        order_id=order_id,
        status=body.get("status", "PENDING"),
        paid_at=body.get("paid_at"),
        expire_at=body.get("expire_at"),
    )
    return {"data": data}


@app.get("/admin-api/users", dependencies=[Depends(require_admin)])
async def admin_users(limit: int = 200):
    return {"data": supabase_store.list_users(limit=limit)}


@app.get("/admin-api/config", dependencies=[Depends(require_admin)])
async def admin_config():
    return {"data": supabase_store.get_config()}


@app.patch("/admin-api/config/{key}", dependencies=[Depends(require_admin)])
async def admin_set_config(key: str, request: Request):
    body = await request.json()
    data = supabase_store.set_config(key, body.get("value", ""))
    db.cache_config[str(key).strip().upper()] = str(body.get("value", ""))
    if str(key).strip().upper() == "COUPON_COMMAND_ENABLED":
        await set_commands()
    return {"data": data}


@app.delete("/admin-api/config/{key}", dependencies=[Depends(require_admin)])
async def admin_delete_config(key: str):
    data = supabase_store.delete_config(key)
    db.cache_config.pop(str(key).strip().upper(), None)
    return {"data": data}


@app.get("/admin-api/menu-pages", dependencies=[Depends(require_admin)])
async def admin_menu_pages():
    return {"data": supabase_store.list_menu_pages()}


@app.patch("/admin-api/menu-pages/{page_id}", dependencies=[Depends(require_admin)])
async def admin_set_menu_page(page_id: str, request: Request):
    body = await request.json()
    data = supabase_store.upsert_menu_page(
        page_id=page_id,
        image_url=body.get("image_url", ""),
        body=body.get("body", ""),
        layout=body.get("layout", ""),
    )
    db.reload_config(force=True)
    return {"data": data}


@app.delete("/admin-api/menu-pages/{page_id}", dependencies=[Depends(require_admin)])
async def admin_delete_menu_page(page_id: str):
    data = supabase_store.delete_menu_page(page_id)
    db.reload_config(force=True)
    return {"data": data}


@app.get("/admin-api/sale-rules", dependencies=[Depends(require_admin)])
async def admin_sale_rules():
    return {"data": supabase_store.list_sale_rules()}


@app.post("/admin-api/sale-rules", dependencies=[Depends(require_admin)])
async def admin_upsert_sale_rule(request: Request):
    body = await request.json()
    data = supabase_store.upsert_sale_rule(body)
    db.reload_config(force=True)
    return {"data": data}


@app.delete("/admin-api/sale-rules/{sale_id}", dependencies=[Depends(require_admin)])
async def admin_delete_sale_rule(sale_id: str):
    data = supabase_store.delete_sale_rule(sale_id)
    db.reload_config(force=True)
    return {"data": data}


@app.get("/admin-api/coupons", dependencies=[Depends(require_admin)])
async def admin_coupons():
    return {"data": supabase_store.list_coupons()}


@app.post("/admin-api/coupons", dependencies=[Depends(require_admin)])
async def admin_create_coupon(request: Request):
    body = await request.json()
    return {"data": supabase_store.create_coupon_from_sheet_row(body)}


@app.delete("/admin-api/coupons/{code}", dependencies=[Depends(require_admin)])
async def admin_delete_coupon(code: str):
    return {"data": supabase_store.delete_coupon(code)}


@app.get("/admin-api/blacklist", dependencies=[Depends(require_admin)])
async def admin_blacklist(limit: int = 500):
    try:
        return {"data": supabase_store.list_blacklist(limit=limit)}
    except Exception as exc:
        print(f"⚠️ Không đọc được security_blacklist: {exc}")
        return {"data": []}


@app.post("/admin-api/blacklist", dependencies=[Depends(require_admin)])
async def admin_upsert_blacklist(request: Request):
    body = await request.json()
    return {"data": supabase_store.upsert_blacklist(body)}


@app.delete("/admin-api/blacklist/{telegram_user_id}", dependencies=[Depends(require_admin)])
async def admin_delete_blacklist(telegram_user_id: str):
    return {"data": supabase_store.delete_blacklist(telegram_user_id)}


@app.get("/admin-api/support-events", dependencies=[Depends(require_admin)])
async def admin_support_events(limit: int = 500):
    try:
        return {"data": supabase_store.list_support_events(limit=limit)}
    except Exception as exc:
        print(f"⚠️ Không đọc được support_events: {exc}")
        return {"data": []}
