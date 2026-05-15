# Render Free + Vercel Free + Supabase Free Setup

## 1. Supabase

1. Tạo project Supabase Free.
2. Vào SQL Editor, chạy toàn bộ file `supabase/schema.sql`.
3. Lấy các giá trị:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`

Không đưa `SUPABASE_SERVICE_ROLE_KEY` vào frontend hoặc Vercel.

## 2. Migrate dữ liệu từ Google Sheets

Chạy sau khi đã cấu hình env:

```bash
SUPABASE_URL="..." \
SUPABASE_SERVICE_ROLE_KEY="..." \
SPREADSHEET_ID="..." \
GOOGLE_SHEETS_CREDS_JSON='...' \
python3 scripts/migrate_sheets_to_supabase.py
```

Nếu bạn vẫn dùng file `google-key.json` local thì có thể bỏ `GOOGLE_SHEETS_CREDS_JSON`.

Script hiện migrate:

- `Config` -> `bot_config`
- `MenuBuilder` -> `menu_pages`
- `Users` -> `orders`
- `Coupons` -> `coupons` nếu sheet tồn tại

## 3. Render backend

Deploy repo này lên Render bằng `render.yaml`, hoặc tạo Web Service thủ công:

```bash
pip install -r requirements.txt
uvicorn web_backend:app --host 0.0.0.0 --port $PORT
```

Env vars cần có trên Render:

```text
BOT_TOKEN=
WEBHOOK_URL=https://your-render-app.onrender.com/webhook
TELEGRAM_WEBHOOK_SECRET=
ADMIN_SECRET=
ADMIN_ALLOWED_ORIGINS=https://your-admin.vercel.app
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SPREADSHEET_ID=
GOOGLE_SHEETS_CREDS_JSON=
```

Trong giai đoạn chuyển đổi, backend vẫn cần Google Sheets env vì bot hiện tại còn nhiều module đọc sheet trực tiếp. Supabase được dùng cho admin API và dữ liệu đã migrate.

Kiểm tra backend:

```bash
curl https://your-render-app.onrender.com/health
```

## 4. Vercel admin UI

Deploy thư mục `admin-ui` lên Vercel.

Env var trên Vercel:

```text
NEXT_PUBLIC_ADMIN_API_URL=https://your-render-app.onrender.com
```

Sau khi mở admin UI, nhập `ADMIN_SECRET` giống trên Render. Secret được lưu trong localStorage của trình duyệt admin.

## 5. Thứ tự chuyển đổi an toàn

1. Deploy Supabase schema.
2. Chạy migrate dữ liệu.
3. Deploy Render backend và kiểm tra `/health`.
4. Deploy Vercel admin UI.
5. Dùng admin UI kiểm tra orders/users/config.
6. Refactor dần các module bot từ `db.users_sheet...` sang `supabase_store`.
7. Khi bot đã đọc/ghi Supabase hoàn toàn, bỏ Google Sheets khỏi env.

## 6. File mới quan trọng

- `supabase/schema.sql`: schema Postgres và RLS policy cho service role.
- `supabase_store.py`: client Supabase server-side.
- `scripts/migrate_sheets_to_supabase.py`: migrate dữ liệu từ Sheets sang Supabase.
- `web_backend.py`: FastAPI webhook + admin API cho Render.
- `render.yaml`: blueprint deploy Render Free.
- `admin-ui/`: Next.js admin dashboard cho Vercel.
