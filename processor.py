import asyncio
from datetime import datetime, timedelta
from database import db
from bot_instance import bot 
from payment import payos_manager

# Tập hợp chứa các ID đơn hàng bị khách bấm Hủy
cancelled_orders = set()

# ======================================================
# 1. HÀM XỬ LÝ GIAO HÀNG (TÍCH HỢP TÙY CHỈNH GOOGLE SHEETS)
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
        
        # Duyệt ngược từ dưới lên lấy đơn hàng mới nhất
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
        # TÍNH TOÁN NGÀY HẾT HẠN THÔNG MINH
        # ---------------------------------------------------------
        plan_lower = plan_name.lower()
        is_1m = any(kw in plan_lower for kw in ["1 tháng", "1m", "30 ngày"])
        
        if is_1m:
            expire_date = datetime.now() + timedelta(days=30)
            expire_str = expire_date.strftime("%d/%m/%Y %H:%M:%S")
            expiry_text = db.get_config("MSG_DELIVERY_EXPIRY", "⏳ Hạn sử dụng: <code>{date}</code>").replace("{date}", expire_str)
        else:
            expire_str = db.get_config("MSG_DELIVERY_LIFETIME_TEXT", "Vĩnh viễn")
            expiry_text = db.get_config("MSG_DELIVERY_EXPIRY_LIFE", "⏳ Hạn sử dụng: <b>Vĩnh viễn</b>")

        # Cập nhật trạng thái PAID và Ngày hết hạn
        db.users_sheet.update(f"F{row_index}:H{row_index}", [["PAID", datetime.now().strftime("%d/%m/%Y %H:%M:%S"), expire_str]])

        # ---------------------------------------------------------
        # THUẬT TOÁN TÌM LINK NHÓM THÔNG MINH
        # ---------------------------------------------------------
        target_groups = []
        g_names = [db.get_config(f"BTN_G{i}", f"Nhóm {i}") for i in range(1, 5)]
        g_ids = [db.get_config(f"GROUP_{i}_ID") for i in range(1, 5)]
        
        # Nhận diện gói FULL (SVIP+)
        is_full = False
        full_keywords = ["full", "svip", "trọn bộ", "tất cả"]
        if any(kw in plan_lower for kw in full_keywords):
            is_full = True
            
        if is_full:
            for i in range(4):
                if g_ids[i]: target_groups.append({"name": g_names[i], "id": g_ids[i]})
        else:
            # Nhận diện gói lẻ
            for i in range(4):
                if g_names[i].lower() in plan_lower or f"nhóm {i+1}" in plan_lower or f"g{i+1}" in plan_lower:
                    if g_ids[i]: target_groups.append({"name": g_names[i], "id": g_ids[i]})
                    break
        
        # Thêm nhóm Hỗ trợ / Cập nhật (Nếu có)
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
             links_text_list.append("⚠️ <i>Chưa có link nhóm nào được cấu hình trên hệ thống. Vui lòng liên hệ Admin!</i>")
        else:
            for grp in target_groups:
                # 1. Thử Unban (Lỗi thì bỏ qua vì khách có thể đang là Admin hoặc chưa từng bị Ban)
                try:
                    await bot.unban_chat_member(chat_id=int(grp["id"]), user_id=int(user_id))
                except Exception as unban_err:
                    print(f"ℹ️ Bỏ qua lỗi Unban tại {grp['name']}: {unban_err}")

                # 2. Tạo link độc lập
                try:
                    invite = await bot.create_chat_invite_link(chat_id=int(grp["id"]), member_limit=1)
                    item = msg_link_item.replace("{g_name}", grp["name"]).replace("{link}", invite.invite_link)
                    links_text_list.append(item)
                except Exception as e:
                    print(f"❌ Lỗi tạo link nhóm {grp['name']}: {e}")
                    links_text_list.append(f"👉 <b>{grp['name']}:</b> Lỗi bot chưa có quyền tạo link!")

        links_compiled = "\n".join(links_text_list)
        
        # --- ĐOẠN CODE FIX LỖI NGOẶC KÉP TRÊN SHEET ---
        raw_delivery_template = db.get_config("MSG_DELIVERY_TEMPLATE", (
            "🎉 <b>THANH TOÁN THÀNH CÔNG!</b>\n"
            "────────────────────\n"
            "🎁 Gói: <b>{plan}</b>\n"
            "{expiry_text}\n\n"
            "🔗 <b>LINK THAM GIA NHÓM CỦA BẠN:</b>\n"
            "{links}\n"
            "────────────────────\n"
            "⚠️ <i>Lưu ý: Mỗi link dưới đây chỉ nhấp được 1 lần cho 1 tài khoản. Tuyệt đối không chia sẻ cho người khác nhé!</i>"
        ))
        
        # Xử lý: Xoá dấu ngoặc kép dư thừa ở đầu/cuối và đổi \n thành xuống dòng thực tế
        delivery_template = raw_delivery_template.strip().strip('"').replace("\\n", "\n")
        
        final_msg = delivery_template.replace("{plan}", str(plan_name))
        final_msg = final_msg.replace("{expiry_text}", str(expiry_text))
        final_msg = final_msg.replace("{links}", str(links_compiled))

        # Thử gửi bằng HTML, nếu Google Sheets bị lỗi cú pháp HTML thì chuyển sang gửi Text thô
        try:
            await bot.send_message(chat_id=user_id, text=final_msg, parse_mode="HTML", disable_web_page_preview=True)
            print(f"✅ Đã giao hàng thành công đơn {target_code} cho user {user_id}")
        except Exception as html_err:
            print(f"⚠️ Lỗi cú pháp HTML từ Google Sheets, tự động chuyển sang gửi Text thô: {html_err}")
            await bot.send_message(chat_id=user_id, text=final_msg, parse_mode=None, disable_web_page_preview=True)
            print(f"✅ Đã giao hàng (Text) thành công đơn {target_code} cho user {user_id}")

    except Exception as e:
        print(f"❌ Lỗi giao hàng: {e}")

# =====================================================
# 2. HÀM TỰ ĐỘNG CHECK TRẠNG THÁI (AUTO LOOP)
# =====================================================
async def auto_check_loop(order_code, user_id):
    str_code = str(order_code).strip()
    print(f"🕵️ Bắt đầu Auto-check đơn: {str_code}")
    
    for i in range(40): 
        if str_code in cancelled_orders:
            print(f"🛑 Đã dừng theo dõi đơn {str_code} vì khách bấm nút Hủy.")
            try: cancelled_orders.remove(str_code)
            except: pass
            return

        await asyncio.sleep(15)
        status = payos_manager.get_payment_status(str_code)
        
        if status == "PAID":
            print(f"💰 Đơn {str_code} đã thanh toán! Đang gọi hàm giao hàng...")
            await process_successful_payment(str_code)
            return

    print(f"⏰ Đơn {str_code} đã hết thời gian chờ 10 phút.")
    msg_timeout = db.get_config("MSG_TIMEOUT_QR", "⏳ Mã QR thanh toán của bạn đã hết hạn (Quá 10 phút). Nếu bạn vẫn muốn mua, vui lòng tạo đơn mới nhé!").replace("\\n", "\n")
    try:
        await bot.send_message(chat_id=user_id, text=msg_timeout, parse_mode="HTML")
    except: pass