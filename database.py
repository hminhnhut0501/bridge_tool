import os
import time
import gspread
import json
import re
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

load_dotenv()

def normalize_key(value):
    return re.sub(r"[\u200b-\u200d\ufeff]", "", str(value or "")).strip()

class Database:
    def __init__(self):
        self.scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        self.client = None
        self.sh = None
        self.users_sheet = None
        self.config_sheet = None
        self.menu_sheet = None # Thêm tab Menu
        
        self.cache_config = {}
        self.pages_cache = {} # Thêm RAM Cache cho giao diện
        self.last_reload_time = 0 

    def connect(self):
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
            
            # Kết nối tab MenuBuilder
            try:
                self.menu_sheet = self.sh.worksheet("MenuBuilder")
            except:
                self.menu_sheet = next(
                    (sheet for sheet in self.sh.worksheets() if normalize_key(sheet.title).lower() == "menubuilder"),
                    None,
                )
                if not self.menu_sheet:
                    print("⚠️ Chưa tìm thấy tab MenuBuilder, Bot sẽ chạy giao diện cũ.")

            print("✅ Kết nối Google Sheets thành công!")
            self.reload_config(force=True)
            
        except Exception as e:
            print(f"❌ Lỗi kết nối Google Sheets: {e}")

    def reload_config(self, force=False):
        current_time = time.time()
        if not force and (current_time - self.last_reload_time < 60): return

        try:
            # 1. Tải Config
            all_rows = self.config_sheet.get_all_values()
            temp_cache = {}
            for row in all_rows:
                if len(row) >= 2:
                    key = normalize_key(row[0]).upper()
                    if key: temp_cache[key] = str(row[1]).strip()
            self.cache_config = temp_cache
            
            # 2. TẢI GIAO DIỆN ĐỘNG TỪ MENU BUILDER VÀO RAM
            if self.menu_sheet:
                menu_rows = self.menu_sheet.get_all_values()
                temp_pages = {}
                for row in menu_rows[1:]: # Bỏ qua tiêu đề
                    if len(row) >= 4:
                        pid = normalize_key(row[0])
                        if pid:
                            temp_pages[pid] = {
                                'img': str(row[1]).strip(),
                                'text': str(row[2]).strip(),
                                'layout': str(row[3]).strip()
                            }
                            temp_pages[pid.lower()] = temp_pages[pid]
                self.pages_cache = temp_pages
                print(f"🎨 Đã nạp thành công {len(self.pages_cache)} trang giao diện động!")

            self.last_reload_time = current_time
        except Exception as e:
            print(f"❌ Lỗi tải Dữ liệu: {e}")

    def get_config(self, key, default=""):
        if not self.cache_config: self.reload_config(force=True)
        return self.cache_config.get(normalize_key(key).upper(), str(default))

    def get_page(self, page_id):
        normalized = normalize_key(page_id)
        return self.pages_cache.get(normalized) or self.pages_cache.get(normalized.lower())

db = Database()
