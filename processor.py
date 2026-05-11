import asyncio
from datetime import datetime, timedelta
from database import db
from bot_instance import bot 
from payment import payos_manager

# Tập hợp chứa các ID đơn hàng bị khách bấm Hủy
cancelled_orders = set()

# Hàm lọc ký tự đặc biệt chống sập định dạng HTML
def escape_html(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ======================================================
# 1. HÀM XỬ LÝ GIAO HÀNG (TỐI ƯU CỰC SẠCH)
# ======================================================
async def process_successful_payment(order_code: str):
    try:
        target_code = str(order_code).strip()
        print(f"🔄 Đang bắt đầu xử lý giao hàng cho đơn: {target_code}")
        
        db.connect() # Làm mới dữ liệu
        users_data = db.users_sheet.get_all_values()
        row_index = -1
        user_id = None
        plan_name = None 
        
        # Duyệt ngược từ dưới lên lấy đơn hàng
        for i in range(len(users_data) - 1, 0, -1):
            row = users_data[i]
            if str(row[0]).strip() == target_code:
                if len(row) > 5 and row[5].strip() == "PAID":
                    print(f"⚠️ Đơn {target_code} đã được xử lý trước đó.")
                    return
                row_index = i + 1
                user_id = str(row[1])
                plan_name = str(row[3])
                break

        if row_index == -1:
            print(f"❌ Không tìm thấy đơn {target_code} trong Google Sheets.")
            return

        # ---------------------------------------------------------
        # TÍNH TOÁN NGÀY HẾT HẠN (CỰC KỲ ĐƠN GIẢN)
        # ---------------------------------------------------------
        plan_lower = plan_name.lower()
        is_1m = any(kw in plan_lower for kw in ["1 tháng", "1m", "30 ngày"])
        
        if is_1m:
            expire_date = datetime.now() + timedelta(days=30)
            expire_str = expire_date.strftime("%d/%m/%Y %H:%M:%S")
        else:
            expire_str = db.get_config("MSG_DELIVERY_LIFETIME_TEXT", "Vĩnh viễn")

        # Cập nhật trạng thái PAID và Ngày hết hạn lên Sheet
        db.users_sheet.update(f"F{row_index}:H{row_index}", [["PAID", datetime.now().strftime("%d/%m/%Y %H:%M:%S"), expire_str]])

        # ---------------------------------------------------------
        # THUẬT TOÁN TÌM LINK NHÓM THÔNG MINH
        # ---------------------------------------------------------
        target_groups = []
        g_names = [db.get_config(f"BTN_G{i}", f"Nhóm {i}") for i in range(1, 5)]
        g_ids = [db.get_config(f"GROUP_{i}_ID") for i in range(1, 5)]
        
        is_full = any(kw in plan_lower for kw in ["full", "svip", "trọn bộ", "tất cả"])
            
        if is_full:
            for i in range(4):
                if g_ids[i]: target_groups.append({"name": g_names[i], "id": g_ids[i]})
        else:
            for i in range(4):
                if g_names[i].lower() in plan_lower or f"nhóm {i+1}" in plan_lower or f"g{i+1}" in plan_lower:
                    if g_ids[i]: target_groups.append({"name": g_names[i], "id": g_ids[i]})
                    break
        
        support_id = db.get_config("GROUP_SUPPORT_ID")
        support_name = db.get_config("BTN_SUPPORT_GROUP", "Nhóm Cập Nhật & Hỗ Trợ")
        if support_id:
            target_groups.append({"name": support_name, "id": support_id})

        # ---------------------------------------------------------
        # TẠO LINK MỜI DUY NHẤT & LẮP RÁP TIN NHẮN
        # ---------------------------------------------------------
        links_text_list = []
        msg_link_item = db.get_config("MSG_DELIVERY_LINK_ITEM", "👉 <b>{g_name}:</b> {link}")
        
        if not target_groups:
             links_text_list.append("⚠️ <i>Chưa có link nhóm nào được cấu hình. Báo Admin nhé!</i>")
        else:
            for grp in target_groups:
                try:
                    await bot.unban_chat_member(chat_id=int(grp["id"]), user_id=int(user_id))
                except Exception: pass # Lỗi Unban thì cứ bơ đi

                try:
                    invite = await bot.create_chat_invite_link(chat_id=int(grp["id"]), member_limit=1)
                    safe_grp_name = escape_html(grp["name"])
                    item = msg_link_item.replace("{g_name}", safe_grp_name).replace("{link}", invite.invite_link)
                    links_text_list.append(item)
                except Exception as e:
                    print(f"❌ Lỗi tạo link nhóm {grp['name']}: {e}")
                    links_text_list.append(f"👉 <b>{escape_html(grp['name'])}:</b> Lỗi bot chưa có quyền tạo link!")

        links_compiled = "\n".join(links_text_list)
        
        # --- LẤY TEMPLATE GIAO HÀNG TỪ SHEET ---
        raw_delivery_template = db.get_config("MSG_DELIVERY_TEMPLATE", (
            "🎉 <b>THANH TOÁN THÀNH CÔNG!</b>\n"
            "────────────────────\n"
            "🎁 Gói: <b>{plan}</b>\n"
            "⏳ Hạn sử dụng: <b>{expire_date}</b>\n\n"
            "🔗 <b>LINK THAM GIA NHÓM CỦA BẠN:</b>\n"
            "{links}\n"
            "────────────────────\n"
            "⚠️ <i>Lưu ý: Mỗi link dưới đây chỉ nhấp được 1 lần!</i>"
        ))
        
        # Xoá dấu ngoặc kép rác và xử lý xuống dòng
        delivery_template = raw_delivery_template.strip().strip('"').replace("\\n", "\n")
        safe_plan_name = escape_html(plan_name)
        
        # Thay thế các biến động
        final_msg = delivery_template.replace("{plan}", safe_plan_name)
        final_msg = final_msg.replace("{links}", str(links_compiled))
        
        # Hỗ trợ cả 2 từ khoá (Phòng hờ bạn chưa đổi trên Sheet)
        final_msg = final_msg.replace("{expire_date}", str(expire_str))
        final_msg = final_msg.replace("{expiry_text}", f"⏳ Hạn sử dụng: <b>{expire_str}</b>")

        # --- GỬI TIN NHẮN AN TOÀN ---
        try:
            await bot.send_message(chat_id=user_id, text=final_msg, parse_mode="HTML", disable_web_page_preview=True)
            print(f"✅ Đã giao hàng (HTML) thành công cho user {user_id}")
        except Exception as html_err:
            print(f"⚠️ LỖI HTML TỪ SHEET: {html_err}")
            await bot.send_message(chat_id=user_id, text=final_msg, parse_mode=None, disable_web_page_preview=True)

    except Exception as e:
        print(f"❌ Lỗi giao hàng tổng quát: {e}")

# =====================================================
# 2. HÀM TỰ ĐỘNG CHECK TRẠNG THÁI (AUTO LOOP TỐI ƯU HÓA)
# =====================================================
async def auto_check_loop(order_code, user_id):
    str_code = str(order_code).strip()
    print(f"🕵️ Bắt đầu Auto-check đơn (Async Mode): {str_code}")
    
    for i in range(40): 
        if str_code in cancelled_orders:
            try: cancelled_orders.remove(str_code)
            except: pass
            return

        await asyncio.sleep(15)
        
        # Đẩy việc kiểm tra PayOS sang một luồng riêng để không kẹt Bot
        try:
            status = await asyncio.to_thread(payos_manager.get_payment_status, str_code)
        except Exception as api_err:
            print(f"⚠️ Lỗi check PayOS: {api_err}")
            continue
        
        if status == "PAID":
            print(f"💰 Đơn {str_code} đã thanh toán! Đang giao hàng...")
            await process_successful_payment(str_code)
            return

    msg_timeout = db.get_config("MSG_TIMEOUT_QR", "⏳ Mã QR đã hết hạn. Vui lòng tạo đơn mới!").replace("\\n", "\n")
    try: await bot.send_message(chat_id=user_id, text=msg_timeout, parse_mode="HTML")
    except: pass