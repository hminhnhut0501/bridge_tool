import asyncio
import time
import logging
from aiogram import Router
from database import db
from supabase_store import supabase_store

# Khai báo router để main.py tự động nạp module này mà không bị lỗi
router = Router()

async def maintenance_worker():
    """Người lao công chạy ngầm: Dọn rác và Phân loại khách hàng VIP"""
    logging.info("🛠 [MODULE] Maintenance (Lao công) đã sẵn sàng. Sẽ bắt đầu dọn dẹp sau 5 phút...")
    
    # Đợi 5 phút sau khi boot để nhường RAM/CPU cho các tính năng chính khởi động trước
    await asyncio.sleep(300) 

    while True:
        try:
            logging.info("🧹 Bắt đầu chu kỳ dọn dẹp Database...")

            if supabase_store.enabled:
                current_time = int(time.time())
                for order in supabase_store.list_orders(limit=1000):
                    try:
                        order_id = int(str(order.get("order_id") or "0"))
                    except ValueError:
                        continue
                    status = str(order.get("status") or "").upper()
                    if status == "PENDING" and (current_time - order_id > 2592000):
                        supabase_store.update_order_status(order_id, "CANCELLED")
                        logging.info(f"🗑 Đã chuyển đơn PENDING quá hạn sang CANCELLED: {order_id}")

                logging.info("💤 Dọn dẹp Supabase xong! Module Maintenance sẽ ngủ 12 tiếng.")
                await asyncio.sleep(43200)
                continue
            
            # Kết nối thẳng vào Sheet (Không dùng cache vì thao tác này cần dữ liệu realtime)
            sh = db.client.open_by_key(db.sh.id)
            users_sheet = sh.worksheet("Users")
            
            # Kiểm tra xem Sếp đã tạo tab LifetimeUsers chưa
            try:
                vip_sheet = sh.worksheet("LifetimeUsers")
            except Exception:
                logging.error("⚠️ Chưa có tab 'LifetimeUsers' trên Sheets. Hãy tạo tab này để lưu khách VIP!")
                vip_sheet = None

            records = users_sheet.get_all_values()
            current_time = int(time.time())
            
            # TIỂU XẢO LẬP TRÌNH: Duyệt TỪ DƯỚI LÊN TRÊN (Reverse Loop)
            # Lý do: Nếu quét từ trên xuống, khi bạn xóa dòng số 5, dòng 6 sẽ bị đẩy lên thành 5 làm sai lệch index.
            # Quét ngược từ dưới lên sẽ triệt tiêu hoàn toàn rủi ro này!
            for i in range(len(records) - 1, 0, -1):
                row = records[i]
                if len(row) < 6:
                    continue # Bỏ qua dòng thiếu dữ liệu
                
                try:
                    order_id = int(row[0])
                except:
                    continue # Bỏ qua nếu cột đầu không phải mã Order ID
                    
                status = str(row[5]).strip().upper()
                plan_name = str(row[3]).strip().upper()
                
                # Vị trí thực tế của dòng trên Sheet (Index mảng + 1 do mảng bắt đầu từ 0)
                row_number_in_sheet = i + 1

                # ---------------------------------------------------------
                # NHIỆM VỤ 1: XÓA ĐƠN PENDING QUÁ 30 NGÀY
                # 30 ngày = 30 * 24 * 60 * 60 = 2,592,000 giây
                # ---------------------------------------------------------
                if status == "PENDING" and (current_time - order_id > 2592000):
                    users_sheet.delete_rows(row_number_in_sheet)
                    logging.info(f"🗑 Đã xóa vĩnh viễn đơn PENDING quá hạn rác: {order_id}")
                    
                    # Nghỉ 2 giây sau khi xóa để không bị Google chửi là Spam API
                    await asyncio.sleep(2) 
                    continue # Xóa rồi thì bỏ qua không xét tiếp nữa
                
                # ---------------------------------------------------------
                # NHIỆM VỤ 2: DI CHUYỂN ĐƠN VIP TRỌN ĐỜI ĐÃ THANH TOÁN SANG TAB LIFETIME
                # ---------------------------------------------------------
                if status == "PAID" and ("TRỌN ĐỜI" in plan_name or "LIFE" in plan_name):
                    if vip_sheet:
                        # 1. Ghi khách này sang tab VIP
                        vip_sheet.append_row(row)
                        await asyncio.sleep(1) # Nghỉ tí
                        
                        # 2. Xóa khỏi tab Users (Giúp tab Users nhẹ như lông hồng)
                        users_sheet.delete_rows(row_number_in_sheet)
                        logging.info(f"💎 Đã nâng cấp & chuyển đơn VIP Trọn Đời sang tab LifetimeUsers: {order_id}")
                        
                        await asyncio.sleep(2)

        except Exception as e:
            logging.error(f"❌ Lỗi vòng lặp Maintenance: {e}")

        # Làm việc xong, cho Lao công đi ngủ 12 tiếng (43200 giây) rồi mới quét lại
        logging.info("💤 Dọn dẹp xong! Module Maintenance sẽ ngủ 12 tiếng.")
        await asyncio.sleep(43200)
