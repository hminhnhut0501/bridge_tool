import os
import time
import re
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
        self.backend = "supabase"

    def connect(self):
        self.backend = "supabase"
        self.client = None
        self.sh = None
        self.users_sheet = None
        self.config_sheet = None
        self.menu_sheet = None
        self.sale_sheet = None
        if not supabase_store.enabled:
            self.cache_config = {}
            self.pages_cache = {}
            self.sales_cache = []
            raise RuntimeError("Supabase runtime is required. Google Sheets runtime has been removed.")
        try:
            print("⏳ Đang kết nối tới Supabase...")
            supabase_store.connect()
            print("✅ Kết nối Supabase thành công!")
            self.reload_config(force=True)
        except Exception as e:
            print(f"❌ Lỗi kết nối Supabase: {e}")
            self.cache_config = {}
            self.pages_cache = {}
            self.sales_cache = []
            raise

    def reload_config(self, force=False):
        current_time = time.time()
        if not force and (current_time - self.last_reload_time < 60): return

        try:
            if self.backend == "supabase" and supabase_store.enabled:
                temp_cache = {}
                for row in supabase_store.list_config():
                    key = normalize_key(row.get("key")).upper()
                    if key:
                        value = str(row.get("value") or "").strip()
                        if key == "MANUAL_ORDER_LINK_TEMPLATE":
                            value = self._normalize_manual_order_link_template(value)
                        temp_cache[key] = value
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

            raise RuntimeError("Google Sheets runtime has been removed. Supabase is the only supported backend.")
        except Exception as e:
            print(f"❌ Lỗi tải Dữ liệu: {e}")
            if self.backend == "supabase" and supabase_store.enabled:
                raise

    def get_config(self, key, default=""):
        current_time = time.time()
        if not self.cache_config:
            self.reload_config(force=True)
        elif current_time - self.last_reload_time >= 60:
            self.reload_config(force=False)
        normalized_key = normalize_key(key).upper()
        value = self.cache_config.get(normalized_key, str(default))
        if normalized_key == "MANUAL_ORDER_LINK_TEMPLATE":
            return self._normalize_manual_order_link_template(value)
        return value

    def set_config(self, key, value):
        normalized_key = normalize_key(key).upper()
        if not normalized_key:
            raise ValueError("Config key không hợp lệ")
        normalized_value = self._normalize_manual_order_link_template(value) if normalized_key == "MANUAL_ORDER_LINK_TEMPLATE" else str(value)
        if self.backend == "supabase" and supabase_store.enabled:
            supabase_store.set_config(normalized_key, normalized_value)
            self.cache_config[normalized_key] = str(normalized_value)
            try:
                from helpers import recompute_bot_runtime_state

                recompute_bot_runtime_state()
            except Exception:
                pass
            return

        raise RuntimeError("Google Sheets runtime has been removed. Use Supabase config storage.")

    def _normalize_manual_order_link_template(self, value):
        text = str(value or "").strip()
        if not text:
            return "t.me/hangcuprivebot?start=act_{code}"
        if "start=act_{code}" in text:
            return text
        if "start={code}" in text:
            return text.replace("start={code}", "start=act_{code}")
        return text

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

        return []

db = Database()
