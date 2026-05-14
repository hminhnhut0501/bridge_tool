import os
import threading
import http.server
import socketserver
import asyncio
import importlib

# 1. Tạo server giả để Render không báo lỗi Port
def run_dummy_server():
    PORT = 8080
    handler = http.server.SimpleHTTPRequestHandler
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            print(f"📡 Dummy server started at port {PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"⚠️ Dummy server warning: {e}")

threading.Thread(target=run_dummy_server, daemon=True).start()

from bot_instance import bot, dp, set_commands
from database import db
from analytics import setup_analytics

# Import các hàm worker chạy ngầm từ các module
# Lưu ý: Đảm bảo đường dẫn file chính xác theo cấu trúc của bạn
try:
    from modules.mod_maintenance import maintenance_worker
except: maintenance_worker = None

try:
    from scheduler import main as scheduler_worker
except: 
    try:
        from modules.scheduler import main as scheduler_worker
    except: scheduler_worker = None

# ==========================================
# 🧩 CƠ CHẾ AUTO-DISCOVERY (NẠP ROUTERS)
# ==========================================
def load_all_modules():
    print("🔍 Đang quét thư mục 'modules' để nạp tính năng...")
    loaded_count = 0
    module_dir = "modules"
    
    if not os.path.exists(module_dir):
        os.makedirs(module_dir)

    for filename in os.listdir(module_dir):
        if filename.startswith("mod_") and filename.endswith(".py"):
            module_name = filename[:-3] 
            full_module_path = f"{module_dir}.{module_name}"
            try:
                module = importlib.import_module(full_module_path)
                if hasattr(module, 'router'):
                    dp.include_router(module.router)
                    print(f"  ✅ Đã nạp thành công: {module_name}")
                    loaded_count += 1
                else:
                    print(f"  ⚠️ Bỏ qua {module_name} vì không tìm thấy 'router'.")
            except Exception as e:
                print(f"  ❌ Lỗi khi nạp module {module_name}: {e}")
                
    print(f"🎯 Đã nạp tổng cộng {loaded_count} routers vào hệ thống!")

# ==========================================
# 🚀 KHỞI CHẠY HỆ THỐNG
# ==========================================
async def main():
    # 1. Kết nối Database
    db.connect()
    
    # 2. Cài đặt Menu Command cho Telegram
    await set_commands()
    
    # 3. Nạp các module giao diện (Routers)
    setup_analytics(dp)
    load_all_modules()
    
    # 4. 🔥 KÍCH HOẠT CÁC TÁC VỤ CHẠY NGẦM (WORKERS)
    if maintenance_worker:
        asyncio.create_task(maintenance_worker())
        print("🛠 [Worker] Đã kích hoạt Lao công (Maintenance)")
        
    if scheduler_worker:
        asyncio.create_task(scheduler_worker())
        print("⏰ [Worker] Đã kích hoạt Scheduler (Quét hết hạn)")

    print("🤖 Bot Hang Cu Privé+ đang sẵn sàng nhận lệnh...")
    
    # 5. Xóa bỏ Webhook cũ để tránh xung đột và bắt đầu Polling
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("👋 Bot đã dừng.")
