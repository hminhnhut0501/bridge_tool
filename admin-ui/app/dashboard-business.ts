import type { ConfigRow, Order } from "@/lib/api";
import { inferOrderCurrency, normalizeRevenueCurrency, orderAmountValue } from "./dashboard-helpers";

export type GroupMode = "none" | "day" | "month";

const CONFIG_KEY_ALIASES: Record<string, string> = {
  PLAN_FULL_1M: "PLAN_ALL_ACCESS_30D",
  PLAN_FULL_LIFE: "PLAN_ALL_ACCESS_LIFE",
  PLAN_UPSELL_FULL: "PLAN_UPSELL_ALL_ACCESS",
  PRICE_SVIP_30D: "PRICE_ALL_ACCESS_30D",
  PRICE_SVIP_LIFE: "PRICE_ALL_ACCESS_LIFE",
  PRICE_SVIP_30D_USD: "PRICE_ALL_ACCESS_30D_USD",
  PRICE_SVIP_LIFE_USD: "PRICE_ALL_ACCESS_LIFE_USD",
  BTN_VIEW_SVIP_PAGE: "BTN_VIEW_ALL_ACCESS_PAGE",
  BTN_UPGRADE_SVIP: "BTN_UPGRADE_ALL_ACCESS",
  BTN_BUY_SVIP_LIFE: "BTN_BUY_ALL_ACCESS_LIFE",
  BTN_BUY_SVIP_30D: "BTN_BUY_ALL_ACCESS_30D",
  TXT_SVIP_DESCRIPTION: "TXT_ALL_ACCESS_DESCRIPTION",
  IMG_SVIP_PAGE: "IMG_ALL_ACCESS_PAGE",
  PLAN_G_1M: "PLAN_COLLECTION_30D",
  PLAN_G_LIFE: "PLAN_COLLECTION_LIFE",
  PLAN_UPSELL_G: "PLAN_UPSELL_COLLECTION",
  BTN_BUY_1M: "BTN_BUY_COLLECTION_30D",
  BTN_BUY_LIFE: "BTN_BUY_COLLECTION_LIFE",
};

export function canonicalConfigKey(key: string) {
  const raw = String(key || "").trim().toUpperCase();
  if (!raw) return "";
  if (CONFIG_KEY_ALIASES[raw]) return CONFIG_KEY_ALIASES[raw];
  const priceMatch = raw.match(/^PRICE_G(\d+)_(1M|LIFE)(?:_(USD))?$/);
  if (priceMatch) {
    return `PRICE_COLLECTION_G${priceMatch[1]}_${priceMatch[2] === "1M" ? "30D" : "LIFE"}${priceMatch[3] ? "_USD" : ""}`;
  }
  const groupMatch = raw.match(/^(BTN|ID|DESC)_G(\d+)(_EN)?$/);
  if (groupMatch) {
    const prefix = groupMatch[1];
    const suffix = groupMatch[3] || "";
    return `${prefix}_COLLECTION_G${groupMatch[2]}${suffix}`;
  }
  return raw;
}

function configKeyCandidates(key: string) {
  const canonical = canonicalConfigKey(key);
  const requested = String(key || "").trim().toUpperCase();
  const candidates = new Set<string>();
  if (canonical) candidates.add(canonical);
  if (requested) candidates.add(requested);
  Object.entries(CONFIG_KEY_ALIASES).forEach(([legacy, modern]) => {
    if (modern === canonical) candidates.add(legacy);
  });
  if (canonical.startsWith("PRICE_COLLECTION_G")) {
    const match = canonical.match(/^PRICE_COLLECTION_G(\d+)_(30D|LIFE)(?:_(USD))?$/);
    if (match) candidates.add(`PRICE_G${match[1]}_${match[2] === "30D" ? "1M" : "LIFE"}${match[3] ? "_USD" : ""}`);
  }
  const groupMatch = canonical.match(/^(BTN|ID|DESC)_COLLECTION_G(\d+)(_EN)?$/);
  if (groupMatch) {
    candidates.add(`${groupMatch[1]}_G${groupMatch[2]}${groupMatch[3] || ""}`);
  }
  return Array.from(candidates);
}

export function getConfigValue(config: ConfigRow[], key: string, fallback = "") {
  for (const candidate of configKeyCandidates(key)) {
    const found = config.find((item) => item.key === candidate);
    if (found) return found.value ?? fallback;
  }
  return fallback;
}

export function groupConfigKeys(groupNo: string) {
  return [`BTN_G${groupNo}`, `BTN_G${groupNo}_EN`, `BTN_G${groupNo}_ALIASES`, `ID_G${groupNo}`, `PRICE_G${groupNo}_1M`, `PRICE_G${groupNo}_LIFE`, `PRICE_G${groupNo}_1M_USD`, `PRICE_G${groupNo}_LIFE_USD`, `DESC_G${groupNo}`, `DESC_G${groupNo}_EN`, `IMG_G${groupNo}`];
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
  const revenue = paidOrders.reduce((sum, item) => sum + orderAmountValue(item), 0);
  const discount = paidOrders.reduce((sum, item) => sum + orderAmountValue(item, item.coupon_discount_amount), 0);
  const revenueByCurrency = paidOrders.reduce((sum, item) => {
    const currency = normalizeRevenueCurrency(inferOrderCurrency(item));
    sum[currency] = (sum[currency] || 0) + orderAmountValue(item);
    return sum;
  }, {} as Record<string, number>);
  const discountByCurrency = paidOrders.reduce((sum, item) => {
    const currency = normalizeRevenueCurrency(inferOrderCurrency(item));
    sum[currency] = (sum[currency] || 0) + orderAmountValue(item, item.coupon_discount_amount);
    return sum;
  }, {} as Record<string, number>);
  const averageByCurrency = paidOrders.reduce((sum, item) => {
    const currency = normalizeRevenueCurrency(inferOrderCurrency(item));
    if (!sum[currency]) sum[currency] = [];
    sum[currency].push(orderAmountValue(item));
    return sum;
  }, {} as Record<string, number[]>);
  return {
    total: orders.length,
    paid: paidOrders.length,
    pending: orders.filter((item) => item.status === "PENDING").length,
    cancelled: orders.filter((item) => item.status === "CANCELLED").length,
    expired: orders.filter((item) => item.status === "EXPIRED").length,
    revenue,
    discount,
    averageOrder: paidOrders.length ? Math.round(revenue / paidOrders.length) : 0,
    revenueByCurrency,
    discountByCurrency,
    averageByCurrency: Object.fromEntries(Object.entries(averageByCurrency).map(([currency, values]) => [currency, values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0])),
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
