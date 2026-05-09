import os
import hmac
import hashlib
import requests
from dotenv import load_dotenv

load_dotenv()

PAYOS_CLIENT_ID = os.getenv("PAYOS_CLIENT_ID")
PAYOS_API_KEY = os.getenv("PAYOS_API_KEY")
PAYOS_CHECKSUM_KEY = os.getenv("PAYOS_CHECKSUM_KEY")

class PayOSManager:
    def __init__(self):
        self.api_url = "https://api-merchant.payos.vn/v2/payment-requests"
        self.headers = {
            "x-client-id": PAYOS_CLIENT_ID,
            "x-api-key": PAYOS_API_KEY,
            "Content-Type": "application/json"
        }

    def get_payment_status(self, order_code: str):
        url = f"{self.api_url}/{order_code}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            data = response.json()
            if data.get("code") == "00":
                return data["data"]["status"] 
            return "ERROR"
        except Exception as e:
            print(f"⚠️ Lỗi kết nối PayOS: {e}")
            return "ERROR"

    def create_payment_link(self, order_code: int, amount: int, description: str):
        return_url = "https://t.me/hangcuprivebot" 
        cancel_url = "https://t.me/hangcuprivebot"
        sign_string = f"amount={amount}&cancelUrl={cancel_url}&description={description}&orderCode={order_code}&returnUrl={return_url}"
        
        signature = hmac.new(
            PAYOS_CHECKSUM_KEY.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        payload = {
            "orderCode": order_code,
            "amount": amount,
            "description": description,
            "returnUrl": return_url,
            "cancelUrl": cancel_url,
            "signature": signature
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers)
            res_data = response.json()
            if res_data.get("code") == "00":
                # TRẢ VỀ TOÀN BỘ DATA ĐỂ LẤY STK ẢO
                return res_data["data"]
            else:
                print(f"❌ Lỗi PayOS: {res_data.get('desc')}")
                return None
        except Exception as e:
            print(f"❌ Lỗi kết nối: {e}")
            return None

payos_manager = PayOSManager()