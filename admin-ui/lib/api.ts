export type Order = {
  order_id: string;
  telegram_user_id: string;
  full_name: string | null;
  plan_name: string;
  amount: number;
  status: string;
  paid_at: string | null;
  expire_at: string | null;
  created_at: string;
};

export type UserRow = {
  telegram_user_id: string;
  full_name: string | null;
  status: string;
  plan_name: string;
  expire_at: string | null;
  created_at: string;
};

export type ConfigRow = {
  key: string;
  value: string;
  updated_at: string;
};

export type MenuPage = {
  page_id: string;
  image_url: string | null;
  body: string;
  layout: string;
  updated_at: string;
};

export type SaleRule = {
  sale_id: string;
  price_key: string;
  discount_percent: number | null;
  sale_price: number | null;
  slot_limit: number | null;
  used_count: number;
  enabled: boolean;
  starts_at: string | null;
  ends_at: string | null;
};

export type Coupon = {
  code: string;
  plan_name: string | null;
  status: string;
  max_uses: number | null;
  used_count: number;
  expires_at: string | null;
  raw_data: Record<string, string>;
};

export type WebhookInfo = {
  url: string;
  has_custom_certificate: boolean;
  pending_update_count: number;
  last_error_date?: number;
  last_error_message?: string;
  max_connections?: number;
  allowed_updates?: string[];
};

const baseUrl = process.env.NEXT_PUBLIC_ADMIN_API_URL || "http://localhost:8000";

async function request<T>(path: string, secret: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${baseUrl}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Admin-Secret": secret,
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Request failed: ${res.status}`);
  }

  return res.json();
}

export async function getOrders(secret: string) {
  return request<{ data: Order[] }>("/admin-api/orders", secret);
}

export async function getUsers(secret: string) {
  return request<{ data: UserRow[] }>("/admin-api/users", secret);
}

export async function getConfig(secret: string) {
  return request<{ data: ConfigRow[] }>("/admin-api/config", secret);
}

export async function updateConfig(secret: string, key: string, value: string) {
  return request<{ data: ConfigRow[] }>(`/admin-api/config/${encodeURIComponent(key)}`, secret, {
    method: "PATCH",
    body: JSON.stringify({ value }),
  });
}

export async function deleteConfig(secret: string, key: string) {
  return request<{ data: ConfigRow[] }>(`/admin-api/config/${encodeURIComponent(key)}`, secret, {
    method: "DELETE",
  });
}

export async function updateOrderStatus(secret: string, orderId: string, status: string) {
  return request<{ data: Order[] }>(`/admin-api/orders/${encodeURIComponent(orderId)}`, secret, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export async function getMenuPages(secret: string) {
  return request<{ data: MenuPage[] }>("/admin-api/menu-pages", secret);
}

export async function updateMenuPage(secret: string, pageId: string, payload: Partial<MenuPage>) {
  return request<{ data: MenuPage[] }>(`/admin-api/menu-pages/${encodeURIComponent(pageId)}`, secret, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export async function deleteMenuPage(secret: string, pageId: string) {
  return request<{ data: MenuPage[] }>(`/admin-api/menu-pages/${encodeURIComponent(pageId)}`, secret, {
    method: "DELETE",
  });
}

export async function getSaleRules(secret: string) {
  return request<{ data: SaleRule[] }>("/admin-api/sale-rules", secret);
}

export async function upsertSaleRule(secret: string, payload: Record<string, string>) {
  return request<{ data: SaleRule[] }>("/admin-api/sale-rules", secret, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteSaleRule(secret: string, saleId: string) {
  return request<{ data: SaleRule[] }>(`/admin-api/sale-rules/${encodeURIComponent(saleId)}`, secret, {
    method: "DELETE",
  });
}

export async function getCoupons(secret: string) {
  return request<{ data: Coupon[] }>("/admin-api/coupons", secret);
}

export async function createCoupon(secret: string, payload: Record<string, string>) {
  return request<{ data: Coupon[] }>("/admin-api/coupons", secret, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteCoupon(secret: string, code: string) {
  return request<{ data: Coupon[] }>(`/admin-api/coupons/${encodeURIComponent(code)}`, secret, {
    method: "DELETE",
  });
}

export async function getWebhookInfo(secret: string) {
  return request<{ data: WebhookInfo }>("/admin-api/webhook-info", secret);
}

export async function resetWebhook(secret: string) {
  return request<{ data: WebhookInfo }>("/admin-api/webhook-reset", secret, {
    method: "POST",
  });
}
