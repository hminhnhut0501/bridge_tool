import type { ConfigRow, Order } from "@/lib/api";

export type GroupMode = "none" | "day" | "month";

export function getConfigValue(config: ConfigRow[], key: string, fallback = "") {
  return config.find((item) => item.key === key)?.value ?? fallback;
}

export function groupConfigKeys(groupNo: string) {
  return [`BTN_G${groupNo}`, `BTN_G${groupNo}_EN`, `ID_G${groupNo}`, `PRICE_G${groupNo}_1M`, `PRICE_G${groupNo}_LIFE`, `PRICE_G${groupNo}_1M_USD`, `PRICE_G${groupNo}_LIFE_USD`, `DESC_G${groupNo}`, `DESC_G${groupNo}_EN`, `IMG_G${groupNo}`];
}

export function isGroupConfigured(config: ConfigRow[], groupNo: number) {
  return Boolean(getConfigValue(config, `BTN_G${groupNo}`) && getConfigValue(config, `ID_G${groupNo}`));
}

export function hasAnyGroupConfig(config: ConfigRow[], groupNo: number) {
  return groupConfigKeys(String(groupNo)).some((key) => Boolean(getConfigValue(config, key)));
}

export function dayKey(value: string | null | undefined) {
  if (!value) return "Không rõ ngày";
  return new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium" }).format(new Date(value));
}

export function monthKey(value: string | null | undefined) {
  if (!value) return "Không rõ tháng";
  return new Intl.DateTimeFormat("vi-VN", { month: "2-digit", year: "numeric" }).format(new Date(value));
}

export function uniquePaidCustomers(orders: Order[]) {
  return new Set(orders.filter((item) => item.status === "PAID").map((item) => item.telegram_user_id)).size;
}

export function orderStats(orders: Order[]) {
  const paidOrders = orders.filter((item) => item.status === "PAID");
  const revenue = paidOrders.reduce((sum, item) => sum + (item.amount || 0), 0);
  const discount = paidOrders.reduce((sum, item) => sum + (item.coupon_discount_amount || 0), 0);
  return {
    total: orders.length,
    paid: paidOrders.length,
    pending: orders.filter((item) => item.status === "PENDING").length,
    cancelled: orders.filter((item) => item.status === "CANCELLED").length,
    expired: orders.filter((item) => item.status === "EXPIRED").length,
    revenue,
    discount,
    averageOrder: paidOrders.length ? Math.round(revenue / paidOrders.length) : 0,
    conversion: orders.length ? Math.round((paidOrders.length / orders.length) * 100) : 0,
    customers: uniquePaidCustomers(orders),
  };
}

export function groupOrders(orders: Order[], mode: GroupMode) {
  if (mode === "none") return [];
  const groups = new Map<string, Order[]>();
  for (const order of orders) {
    const key = mode === "day" ? dayKey(order.created_at) : monthKey(order.created_at);
    groups.set(key, [...(groups.get(key) || []), order]);
  }
  return Array.from(groups.entries()).map(([label, items]) => ({ label, items, stats: orderStats(items) }));
}
