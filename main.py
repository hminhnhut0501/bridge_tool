import threading
import http.server
import socketserver

# Tạo server giả để Render không báo lỗi Port
def run_dummy_server():
    PORT = 8080
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"📡 Dummy server started at port {PORT}")
        httpd.serve_forever()

# Chạy server ở luồng riêng
threading.Thread(target=run_dummy_server, daemon=True).start()

import asyncio
from bot_instance import bot, dp, set_commands
from bot_handlers import router
from database import db

async def main():
    db.connect()
    dp.include_router(router)
    await set_commands() # Thêm dòng này
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())