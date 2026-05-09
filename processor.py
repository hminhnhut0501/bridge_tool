import asyncio
from datetime import datetime, timedelta
from database import db
from bot_instance import bot 
from payment import payos_manager

# Tập hợp chứa các ID đơn hàng bị khách bấm Hủy để dừng vòng lặp check
# Biến này sẽ được import và sử dụng trong bot_handlers.py
cancelled_orders = set()

# ======================================================
# 1. HÀM XỬ LÝ GIAO HÀNG KHI THANH TOÁN THÀNH CÔNG
# ======================================================
async def process_successful_payment(order_code: str):
    """
    Hàm xử lý cập nhật đơn hàng và gửi link khi nhận được tiền.
    Hỗ trợ phân loại gói FULL hoặc gói lẻ G1, G2, G3, G4.
    Gửi kèm link nhóm bảo hành và tính hạn sử dụng chuẩn.
    """
    try:
        target_code = str(order_code).strip()
        print(f"🔄 Đang bắt đầu xử lý giao hàng cho đơn: {target_code}")
        
        # 1. Lấy dữ liệu từ Sheets
        users_data = db.users_sheet.get_all_values()
        row_index = -1
        user_id = None
        plan_name = None 
        
        # Duyệt ngược từ dưới lên để lấy đơn hàng mới nhất tránh trùng lặp
        for i in range(len(users_data) - 1, 0, -1):
            row = users_data[i]
            if str(row[0]).strip() == target_code:
                # Nếu đơn này đã được xử lý (PAID) thì bỏ qua
                if row[5] == "PAID":
                    print(f"ℹ️ Đơn {target_code} đã được xử lý xong trước đó.")
                    return 

                row_index = i + 1
                user_id = row[1]
                plan_name = str(row[3]) # Tên gói hiển thị (Ví dụ: Lẻ Nhóm 1 (1 Tháng))
                break
        
        if row_index == -1 or user_id is None:
            print(f"⚠️ Không tìm thấy đơn {target_code} trên Sheets.")
            return

        # 2. Tính toán hạn sử dụng (Expire Date) theo tiếng Việt
        now = datetime.now()
        now_str = now.strftime("%d/%m/%Y %H:%M:%S")
        
        if "1 Tháng" in str(plan_name):
            expire_dt = now + timedelta(days=30)
            expire_date_str = expire_dt.strftime("%d/%m/%Y %H:%M:%S")
        else:
            expire_date_str = "Vĩnh viễn"
        
        # 3. Cập nhật trạng thái và thời gian lên Sheets (Cột F, G, H)
        db.users_sheet.update(f"F{row_index}", [["PAID"]])
        db.users_sheet.update(f"G{row_index}", [[now_str]])
        db.users_sheet.update(f"H{row_index}", [[expire_date_str]])

        # 4. Chuẩn bị nội dung tin nhắn giao hàng
        warranty_link = db.get_config("WARRANTY_LINK", "https://t.me/admin")
        links_text = f"🎉 <b>BÙM! CHUYỂN KHOẢN THÀNH CÔNG!</b>\n\n"
        links_text += f"Chào mừng bạn chính thức trở thành <b>Hội Viên VIP</b> của Prive+ 👑\n\n"
        links_text += f"📦 Gói kích hoạt: <b>{plan_name}</b>\n"
        links_text += f"📅 Thời hạn: <b>{expire_date_str}</b>\n"
        links_text += f"────────────────────\n"
        links_text += f"👇 <b>HÃY NHẤN VÀO LINK BÊN DƯỚI ĐỂ VÀO NHÓM NGAY:</b>\n\n"

        # 5. Logic cấp link dựa trên loại gói
        if "Trọn bộ" in str(plan_name):
            for i in range(1, 5):
                g_id = db.get_config(f"GROUP_{i}_ID")
                g_title = db.get_config(f"BTN_G{i}", f"Nhóm {i}")
                if g_id:
                    try:
                        invite = await bot.create_chat_invite_link(chat_id=int(g_id), member_limit=1)
                        links_text += f"• {g_title}: <a href='{invite.invite_link}'>Tham gia ngay</a>\n"
                    except Exception:
                        links_text += f"• {g_title}: <i>Lỗi tạo link mời</i>\n"
        else:
            for i in range(1, 5):
                g_title_config = db.get_config(f"BTN_G{i}")
                if g_title_config and g_title_config in str(plan_name):
                    g_id = db.get_config(f"GROUP_{i}_ID")
                    if g_id:
                        try:
                            invite = await bot.create_chat_invite_link(chat_id=int(g_id), member_limit=1)
                            links_text += f"• {g_title_config}: <a href='{invite.invite_link}'>Tham gia ngay</a>\n"
                        except Exception:
                            links_text += f"• {g_title_config}: <i>Lỗi tạo link mời</i>\n"
                    break

        links_text += f"\n────────────────────\n"
        links_text += f"🤝 <b>Group bảo hành/ hổ trợ :</b> 👉 {warranty_link}\n\n"
        links_text += f"⚠️ <i>Bảo mật: Link mời này là duy nhất và được mã hoá riêng cho bạn. Tuyệt đối không chia sẻ nhé! Chúc bạn trải nghiệm tuyệt vời!</i>"

        # Gửi tin nhắn đến khách hàng
        await bot.send_message(chat_id=user_id, text=links_text, parse_mode="HTML", disable_web_page_preview=True)
        print(f"✅ Đã giao hàng thành công đơn {target_code} cho user {user_id}")

    except Exception as e:
        print(f"❌ Lỗi giao hàng: {e}")

# ======================================================
# 2. HÀM TỰ ĐỘNG CHECK TRẠNG THÁI (AUTO LOOP)
# ======================================================
async def auto_check_loop(order_code, user_id):
    """
    Vòng lặp tự động check trạng thái thanh toán từ PayOS.
    Mỗi 15 giây kiểm tra một lần, tối đa trong 10 phút (40 lần).
    """
    str_code = str(order_code).strip()
    print(f"🕵️ Bắt đầu Auto-check đơn: {str_code}")
    
    for i in range(40): 
        # Kiểm tra nếu đơn bị hủy bởi người dùng
        if str_code in cancelled_orders:
            print(f"🛑 Đã dừng theo dõi đơn {str_code} vì khách bấm nút Hủy.")
            try: cancelled_orders.remove(str_code)
            except: pass
            return

        await asyncio.sleep(15)
        
        status = payos_manager.get_payment_status(str_code)
        print(f"🔍 Check {str_code} (Lần {i+1}/40): {status}")
        
        if status == "PAID":
            await process_successful_payment(str_code)
            return
        if status == "CANCELLED":
            return