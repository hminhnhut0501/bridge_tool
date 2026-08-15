# Plan Name Normalization

Canonical families:

```text
Combo + thời hạn tùy chỉnh / Combo Trọn Đời
Prime + thời hạn tùy chỉnh / Prime Trọn Đời
Boy + thời hạn tùy chỉnh / Boy Trọn Đời
Real + thời hạn tùy chỉnh / Real Trọn Đời
Asia + thời hạn tùy chỉnh / Asia Trọn Đời
Pink: review separately as hidden/special group
```

`canonical_duration` giữ dạng `DAYS:N`, `MONTHS:N`, `LIFETIME` hoặc `REVIEW`.
Không được giả định mọi gói trả phí là 30 ngày.

The migration script is intentionally dry-run only. It never rewrites
Supabase directly because `plan_name` is currently used by legacy mapping
logic. Review its report and back up orders/tasks before implementing the
actual PATCH migration.
