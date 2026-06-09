import os
import time
import gspread
import json
import re
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
from supabase_store import supabase_store

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
        self.sale_sheet = None
        
        self.cache_config = {}
        self.pages_cache = {} # Thêm RAM Cache cho giao diện
        self.sales_cache = []
        self.last_reload_time = 0 
        self.backend = "sheets"

    def connect(self):
        if supabase_store.enabled:
            try:
                print("⏳ Đang kết nối tới Supabase...")
                supabase_store.connect()
                self.backend = "supabase"
                self.users_sheet = None
                self.config_sheet = None
                self.menu_sheet = None
                self.sale_sheet = None
                print("✅ Kết nối Supabase thành công!")
                self.reload_config(force=True)
                return
            except Exception as e:
                print(f"❌ Lỗi kết nối Supabase: {e}")

        self.connect_google()

    def connect_google(self):
        try:
            print("⏳ Đang kết nối tới Google Sheets...")
            self.backend = "sheets"
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

            try:
                self.sale_sheet = self.sh.worksheet("Sale")
            except:
                self.sale_sheet = next(
                    (sheet for sheet in self.sh.worksheets() if normalize_key(sheet.title).lower() in ["sale", "sales"]),
                    None,
                )
                if not self.sale_sheet:
                    print("ℹ️ Chưa tìm thấy tab Sale, Bot sẽ dùng giá gốc.")

            print("✅ Kết nối Google Sheets thành công!")
            self.reload_config(force=True)
            
        except Exception as e:
            print(f"❌ Lỗi kết nối Google Sheets: {e}")

    def reload_config(self, force=False):
        current_time = time.time()
        if not force and (current_time - self.last_reload_time < 60): return

        try:
            if self.backend == "supabase" and supabase_store.enabled:
                temp_cache = {}
                for row in supabase_store.list_config():
                    key = normalize_key(row.get("key")).upper()
                    if key:
                        temp_cache[key] = str(row.get("value") or "").strip()
                self.cache_config = temp_cache

                temp_pages = {}
                for row in supabase_store.list_menu_pages():
                    pid = normalize_key(row.get("page_id"))
                    if pid:
                        temp_pages[pid] = {
                            "img": str(row.get("image_url") or "").strip(),
                            "text": str(row.get("body") or "").strip(),
                            "layout": str(row.get("layout") or "").strip(),
                        }
                        temp_pages[pid.lower()] = temp_pages[pid]
                self.pages_cache = temp_pages
                print(f"🎨 Đã nạp thành công {len(self.pages_cache)} trang giao diện động từ Supabase!")

                self.sales_cache = self.load_sales()
                self.last_reload_time = current_time
                return

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

            # 3. TẢI CẤU HÌNH SALE
            self.sales_cache = self.load_sales()

            self.last_reload_time = current_time
        except Exception as e:
            print(f"❌ Lỗi tải Dữ liệu: {e}")

    def get_config(self, key, default=""):
        if not self.cache_config: self.reload_config(force=True)
        return self.cache_config.get(normalize_key(key).upper(), str(default))

    def set_config(self, key, value):
        normalized_key = normalize_key(key).upper()
        if not normalized_key:
            raise ValueError("Config key không hợp lệ")
        if self.backend == "supabase" and supabase_store.enabled:
            supabase_store.set_config(normalized_key, value)
            self.cache_config[normalized_key] = str(value)
            try:
                from helpers import recompute_bot_runtime_state

                recompute_bot_runtime_state()
            except Exception:
                pass
            return

        if not self.config_sheet:
            self.connect()

        rows = self.config_sheet.get_all_values()
        for idx, row in enumerate(rows, start=1):
            if row and normalize_key(row[0]).upper() == normalized_key:
                self.config_sheet.update_cell(idx, 2, str(value))
                self.cache_config[normalized_key] = str(value)
                return

        self.config_sheet.append_row([normalized_key, str(value)])
        self.cache_config[normalized_key] = str(value)
        try:
            from helpers import recompute_bot_runtime_state

            recompute_bot_runtime_state()
        except Exception:
            pass

    def get_page(self, page_id):
        normalized = normalize_key(page_id)
        return self.pages_cache.get(normalized) or self.pages_cache.get(normalized.lower())

    def load_sales(self):
        if self.backend == "supabase" and supabase_store.enabled:
            sales = []
            try:
                for row in supabase_store.list_sale_rules():
                    raw = dict(row.get("raw_data") or {})
                    raw.setdefault("sale_id", row.get("sale_id") or "")
                    raw.setdefault("price_key", row.get("price_key") or "")
                    raw.setdefault("discount_percent", row.get("discount_percent") or "")
                    raw.setdefault("sale_price", row.get("sale_price") or "")
                    raw.setdefault("start_at", row.get("starts_at") or "")
                    raw.setdefault("end_at", row.get("ends_at") or "")
                    raw.setdefault("slot_limit", row.get("slot_limit") or "")
                    raw.setdefault("enabled", "ON" if row.get("enabled", True) else "OFF")
                    sales.append({normalize_key(k).lower().replace(" ", "_"): str(v or "") for k, v in raw.items()})
                print(f"🏷 Đã nạp {len(sales)} dòng cấu hình Sale từ Supabase.")
                return sales
            except Exception as e:
                print(f"❌ Lỗi tải sale_rules từ Supabase: {e}")
                return []

        if not self.sale_sheet:
            return []

        try:
            rows = self.sale_sheet.get_all_values()
            if len(rows) < 2:
                return []

            headers = [normalize_key(h).lower().replace(" ", "_") for h in rows[0]]
            sales = []
            for row in rows[1:]:
                if not any(str(cell).strip() for cell in row):
                    continue
                item = {}
                for idx, header in enumerate(headers):
                    if header:
                        item[header] = str(row[idx]).strip() if idx < len(row) else ""
                sales.append(item)

            print(f"🏷 Đã nạp {len(sales)} dòng cấu hình Sale.")
            return sales
        except Exception as e:
            print(f"❌ Lỗi tải tab Sale: {e}")
            return []

db = Database()
