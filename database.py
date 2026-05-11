import os
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
        
        # Biến Dictionary lưu Cache trên RAM (Tốc độ phản hồi tức thời)
        self.config_cache = {}

    def connect(self):
        """Kết nối tới Google Sheets và nạp Cache ngay lập tức"""
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
            
            # Ép tải dữ liệu vào RAM ngay lần đầu khởi chạy
            self.load_cache()
            
        except Exception as e:
            print(f"❌ Lỗi kết nối Google Sheets: {e}")

    def load_cache(self):
        """Tải dữ liệu từ Sheet vào RAM (Chỉ chạy 1 lần lúc khởi động hoặc khi Admin gọi lệnh)"""
        try:
            all_rows = self.config_sheet.get_all_values()
            temp_cache = {}
            
            print(f"🔎 Bot đang nạp {len(all_rows)} dòng từ tab Config vào RAM...")
            
            for row in all_rows:
                if len(row) >= 2:
                    key = str(row[0]).strip().upper()
                    value = str(row[1]).strip()
                    if key:
                        temp_cache[key] = value
            
            self.config_cache = temp_cache
            
            kt_msg = "CÓ" if "MSG_START" in self.config_cache else "KHÔNG"
            print(f"⚡ Đã nạp xong {len(self.config_cache)} cấu hình siêu tốc! (Tìm thấy MSG_START: {kt_msg})")
            
        except Exception as e:
            print(f"❌ Lỗi nạp Cache từ Sheet: {e}")

    def get_config(self, key, default=""):
        """Đọc giá trị TỪ RAM (Tuyệt đối KHÔNG kết nối Google Sheets ở đây để chống nghẽn Bot)"""
        if not self.config_cache:
            # Chỉ nạp lại khi bị lỗi rỗng RAM
            print("⚠️ Cache rỗng, đang nạp lại khẩn cấp...")
            self.load_cache()
        
        search_key = str(key).strip().upper()
        return self.config_cache.get(search_key, str(default))

# Khởi tạo đối tượng
db = Database()