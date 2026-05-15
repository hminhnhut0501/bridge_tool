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

export async function updateOrderStatus(secret: string, orderId: string, status: string) {
  return request<{ data: Order[] }>(`/admin-api/orders/${encodeURIComponent(orderId)}`, secret, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}
