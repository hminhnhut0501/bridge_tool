import os
import time
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.client = None
        self.sh = None
        self.users_sheet = None
        self.config_sheet = None
        
        self.cache_config = {}
        self.last_reload_time = 0 

    def connect(self):
        """Kết nối tới Google Sheets"""
        try:
            print("⏳ Đang kết nối tới Google Sheets...")
            creds_json = os.getenv("GOOGLE_SHEETS_CREDS_JSON")
            if creds_json:
                creds_dict = json.loads(creds_json)
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, self.scope)
            else:
                creds = ServiceAccountCredentials.from_json_keyfile_name("google-key.json", self.scope)
            
            self.client = gspread.authorize(creds)
            self.sh = self.client.open_by_key(os.getenv("SPREADSHEET_ID"))
            self.users_sheet = self.sh.worksheet("Users")
            self.config_sheet = self.sh.worksheet("Config")
            print("✅ Kết nối Google Sheets thành công!")
            
            # Ép tải dữ liệu ngay lần đầu chạy
            self.reload_config(force=True)
            
        except Exception as e:
            print(f"❌ Lỗi kết nối Google Sheets: {e}")

    def reload_config(self, force=False):
        """Tải dữ liệu an toàn, có cơ chế chống nghẽn (Throttle)"""
        current_time = time.time()
        
        # 1. Nếu không ép buộc, 60s mới cho tải lại 1 lần
        if not force and (current_time - self.last_reload_time < 60):
            return
            
        # 2. TỐI ƯU HÓA: Kể cả khi file mod_general ép tải lại (force=True),
        # ta vẫn chặn không cho tải nếu khoảng cách giữa 2 lần chưa quá 10 giây.
        # Điều này giúp Bot không bị sập nếu có 100 người bấm /start cùng lúc.
        if force and self.cache_config and (current_time - self.last_reload_time < 10):
            return

        try:
            # Quét TỪ DÒNG SỐ 1, không bỏ sót bất kỳ ô nào
            all_rows = self.config_sheet.get_all_values()
            temp_cache = {}
            
            print(f"🔎 Bot đang đọc {len(all_rows)} dòng từ tab Config vào RAM...")
            
            for row in all_rows:
                if len(row) >= 2:
                    key = str(row[0]).strip().upper()
                    value = str(row[1]).strip()
                    if key:
                        temp_cache[key] = value
            
            self.cache_config = temp_cache
            self.last_reload_time = current_time
            
            kt_msg = "CÓ" if "MSG_START" in self.cache_config else "KHÔNG"
            print(f"⚡ Đã tải xong {len(self.cache_config)} cấu hình! (Tìm thấy MSG_START: {kt_msg})")
            
        except Exception as e:
            print(f"❌ Lỗi tải Config: {e}")

    def get_config(self, key, default=""):
        """Lấy giá trị siêu tốc từ bộ nhớ RAM"""
        # Nếu bộ nhớ rỗng, bắt buộc tải lại
        if not self.cache_config:
            self.reload_config(force=True)
        
        search_key = str(key).strip().upper()
        val = self.cache_config.get(search_key, str(default))
            
        return val

# Khởi tạo đối tượng chung
db = Database()