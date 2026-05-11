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
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"📡 Dummy server started at port {PORT}")
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

from bot_instance import bot, dp, set_commands
from database import db

# ==========================================
# 🧩 CƠ CHẾ AUTO-DISCOVERY (TÌM TRONG THƯ MỤC MODULES)
# ==========================================
def load_all_modules():
    print("🔍 Đang quét thư mục 'modules' để nạp tính năng...")
    loaded_count = 0
    module_dir = "modules"
    
    # Nếu chưa có thư mục thì tự động tạo luôn cho chắc ăn
    if not os.path.exists(module_dir):
        os.makedirs(module_dir)
        print(f"📁 Đã tự tạo thư mục '{module_dir}' vì chưa có.")

    for filename in os.listdir(module_dir):
        if filename.startswith("mod_") and filename.endswith(".py"):
            module_name = filename[:-3] 
            full_module_path = f"{module_dir}.{module_name}" # Khai báo đường dẫn: modules.mod_general
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
                
    print(f"🎯 Đã nạp tổng cộng {loaded_count} modules vào hệ thống!")

# ==========================================
# 🚀 KHỞI CHẠY HỆ THỐNG
# ==========================================
async def main():
    db.connect()
    
    # Gọi hàm tự động nạp module
    load_all_modules()
    
    await set_commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())