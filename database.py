import os
import time
import re

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional dependency for test/runtime bootstrap
    def load_dotenv(*args, **kwargs):
        return False

from supabase_store import supabase_store
from bot_links import normalize_bot_link_template
from config_aliases import canonical_config_key, canonicalize_config_rows, config_lookup_keys, config_write_items, normalize_config_key as normalize_config_key_alias

load_dotenv()


def normalize_key(value):
    return normalize_config_key_alias(value)

class Database:
    CONFIG_CACHE_TTL = 60
    PAGE_CACHE_TTL = 300
    SALE_CACHE_TTL = 300

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
        self.last_config_reload_time = 0
        self.last_pages_reload_time = 0
        self.last_sales_reload_time = 0
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
            self.last_config_reload_time = 0
            self.last_pages_reload_time = 0
            self.last_sales_reload_time = 0
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
            self.last_config_reload_time = 0
            self.last_pages_reload_time = 0
            self.last_sales_reload_time = 0
            raise

    def reload_config(self, force=False):
        try:
            if self.backend == "supabase" and supabase_store.enabled:
                self.reload_config_cache(force=force)
                self.reload_pages_cache(force=force)
                self.reload_sales_cache(force=force)
                return

            raise RuntimeError("Google Sheets runtime has been removed. Supabase is the only supported backend.")
        except Exception as e:
            print(f"❌ Lỗi tải Dữ liệu: {e}")
            if self.backend == "supabase" and supabase_store.enabled:
                raise

    def _maybe_refresh(self, last_reload_time, ttl, force):
        current_time = time.time()
        if force:
            return True, current_time
        if current_time - last_reload_time < ttl:
            return False, last_reload_time
        return True, current_time

    def reload_config_cache(self, force=False):
        should_refresh, timestamp = self._maybe_refresh(self.last_config_reload_time, self.CONFIG_CACHE_TTL, force)
        if not should_refresh:
            return
        temp_cache = {}
        for row in canonicalize_config_rows(supabase_store.list_config()):
            key = normalize_key(row.get("key")).upper()
            if key:
                value = str(row.get("value") or "").strip()
                if key == "MANUAL_ORDER_LINK_TEMPLATE":
                    value = self._normalize_manual_order_link_template(value)
                temp_cache[key] = value
        self.cache_config = temp_cache
        self.last_config_reload_time = timestamp

    def reload_pages_cache(self, force=False):
        should_refresh, timestamp = self._maybe_refresh(self.last_pages_reload_time, self.PAGE_CACHE_TTL, force)
        if not should_refresh:
            return
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
        self.last_pages_reload_time = timestamp
        print(f"🎨 Đã nạp thành công {len(self.pages_cache)} trang giao diện động từ Supabase!")

    def reload_sales_cache(self, force=False):
        should_refresh, timestamp = self._maybe_refresh(self.last_sales_reload_time, self.SALE_CACHE_TTL, force)
        if not should_refresh:
            return
        self.sales_cache = self.load_sales()
        self.last_sales_reload_time = timestamp

    def get_config(self, key, default=""):
        current_time = time.time()
        if not self.cache_config:
            self.reload_config_cache(force=True)
        elif current_time - self.last_config_reload_time >= self.CONFIG_CACHE_TTL:
            self.reload_config_cache(force=False)
        normalized_key = canonical_config_key(key)
        value = str(default)
        for candidate in config_lookup_keys(normalized_key):
            candidate_value = self.cache_config.get(candidate)
            if candidate_value is not None:
                value = candidate_value
                break
        if normalized_key == "MANUAL_ORDER_LINK_TEMPLATE":
            return self._normalize_manual_order_link_template(value)
        if normalized_key == "LICENSE_LINK_TEMPLATE":
            return self._normalize_license_link_template(value)
        if normalized_key in {"LICENSE_PLAN_MAPPING", "LICENSE_PLAN_MAPPING_JSON"}:
            return str(value).strip()
        return value

    def set_config(self, key, value):
        normalized_key = canonical_config_key(key)
        if not normalized_key:
            raise ValueError("Config key không hợp lệ")
        if normalized_key == "MANUAL_ORDER_LINK_TEMPLATE":
            normalized_value = self._normalize_manual_order_link_template(value)
        elif normalized_key == "LICENSE_LINK_TEMPLATE":
            normalized_value = self._normalize_license_link_template(value)
        elif normalized_key in {"LICENSE_PLAN_MAPPING", "LICENSE_PLAN_MAPPING_JSON"}:
            normalized_value = str(value).strip()
        else:
            normalized_value = str(value)
        if self.backend == "supabase" and supabase_store.enabled:
            rows = supabase_store.set_configs(config_write_items(normalized_key, normalized_value))
            for row in rows or []:
                row_key = normalize_key(row.get("key")).upper()
                if row_key:
                    self.cache_config[row_key] = str(row.get("value") or "")
            try:
                from helpers import recompute_bot_runtime_state

                recompute_bot_runtime_state()
            except Exception:
                pass
            return rows

        raise RuntimeError("Google Sheets runtime has been removed. Use Supabase config storage.")

    def _normalize_manual_order_link_template(self, value):
        return normalize_bot_link_template(value, default_payload="act_{code}")

    def _normalize_license_link_template(self, value):
        return normalize_bot_link_template(value, default_payload="lic_{code}")

    def get_page(self, page_id):
        current_time = time.time()
        if not self.pages_cache:
            self.reload_pages_cache(force=True)
        elif current_time - self.last_pages_reload_time >= self.PAGE_CACHE_TTL:
            self.reload_pages_cache(force=False)
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
