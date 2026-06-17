import type { ActivityEvent, KickAuditRow, Order, SupportEvent } from "@/lib/api";
import type { OrderPeriod } from "./dashboard-types";

export function money(value: number) {
  return new Intl.NumberFormat("vi-VN").format(value || 0) + "đ";
}

export function displayText(value: unknown) {
  if (value === null || value === undefined) return "";
  const text = String(value).trim();
  return text === "undefined" || text === "null" ? "" : text;
}

export function isLifetimeText(value: string | null | undefined) {
  const text = displayText(value).toLowerCase();
  return ["life", "lifetime", "svip", "trọn đời", "tron doi", "long life"].some((part) => text.includes(part));
}

export function inferOrderProvider(order: Order) {
  return String(order.payment_provider || "MANUAL").toUpperCase();
}

export function inferOrderCurrency(order: Order) {
  const explicit = String(order.payment_currency || "").toUpperCase();
  const provider = inferOrderProvider(order);
  if (provider === "PAYPAL") return "USD";
  if (provider === "NOWPAYMENTS" || provider === "TRON_USDT") return "USDT";
  if (provider === "PAYOS" || provider === "BINANCE_PAY") return "VND";
  if (explicit === "USD") return "USD";
  if (explicit === "VND" || !explicit) return "VND";
  if (explicit.includes("USDT") || explicit.includes("TRC20") || explicit.includes("CRYPTO")) return "USDT";
  return explicit || "VND";
}

export function orderCouponCode(order: Order) {
  return displayText(order.coupon_code || "");
}

export function orderPlanKind(order: Order) {
  if (isLifetimeText(order.plan_name)) return "Trọn đời";
  return String(order.plan_name || "-");
}

export function isOrderActive(order: Order) {
  if (!order.expire_at || isLifetimeText(order.plan_name)) return true;
  return new Date(order.expire_at).getTime() >= Date.now();
}

export function daysUntil(value: string | null | undefined) {
  if (!value) return -9999;
  return Math.ceil((new Date(value).getTime() - Date.now()) / 86400000);
}

export function groupNamesForOrder(order: Order) {
  const groups = String(order.plan_name || "")
    .split(/[,|/]/)
    .map((item) => item.trim())
    .filter(Boolean);
  return groups.length ? groups : [orderPlanKind(order)];
}

export function uniqueValues(values: string[]) {
  return Array.from(new Set(values.map((item) => displayText(item)).filter(Boolean)));
}

export function payloadText(payload: Record<string, unknown>, key: string) {
  return displayText(payload?.[key]);
}

export function describeActivityEvent(event: ActivityEvent) {
  return event.event_name || "activity";
}

export function describeSupportEvent(event: SupportEvent) {
  return event.event_type || "support";
}

export function normalizeRevenueCurrency(value: string | null | undefined) {
  const currency = String(value || "VND").toUpperCase();
  if (currency === "VNĐ") return "VND";
  if (currency === "USDT_TRC20" || currency === "TRON_USDT") return "USDT";
  if (currency === "CRYPTO") return "CRYPTO";
  return currency;
}

export function formatRevenueCurrency(currency: string, value: number) {
  const normalized = normalizeRevenueCurrency(currency);
  if (normalized === "USD") return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value || 0);
  if (normalized === "USDT" || normalized === "CRYPTO") return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value || 0)} ${normalized}`;
  return money(value || 0);
}

export function providerRevenueFormat(provider: string, value: number) {
  return `${provider}: ${money(value || 0)}`;
}

export function dateText(value: string | null | undefined) {
  if (!value) return "-";
  return new Date(value).toLocaleString("vi-VN");
}

export function dateTextShort(value: string | null | undefined) {
  if (!value) return "-";
  return new Date(value).toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  }) + " " + new Date(value).toLocaleTimeString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function dateTimeInputValue(value: string | null | undefined) {
  if (!value) return "";
  const date = new Date(value);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

export function orderExpireValue(value: string | null | undefined) {
  return dateTimeInputValue(value);
}

export function isTodayDate(value: string | null | undefined) {
  if (!value) return false;
  const date = new Date(value);
  const now = new Date();
  return date.toDateString() === now.toDateString();
}

export function dateMinusDaysText(value: string | null | undefined, days: number) {
  if (!value) return "-";
  const date = new Date(value);
  date.setDate(date.getDate() - days);
  return dateText(date.toISOString());
}

export function dayKey(value: string | null | undefined) {
  return value ? value.slice(0, 10) : "UNKNOWN";
}

export function isoDayKey(value: string | null | undefined) {
  return dayKey(value);
}

export function isWithinPeriod(value: string | null | undefined, period: OrderPeriod) {
  if (!value) return false;
  const date = new Date(value);
  const now = new Date();
  if (period === "all") return true;
  if (period === "today") return date.toDateString() === now.toDateString();
  if (period === "7d") return now.getTime() - date.getTime() <= 7 * 86400000;
  if (period === "month") return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
  if (period === "year") return date.getFullYear() === now.getFullYear();
  return true;
}

export function statusClass(status: string) {
  return `status ${String(status || "").toLowerCase()}`;
}

export function kickAuditStatusClass(status: string) {
  return statusClass(status);
}

export function kickAuditReason(item: KickAuditRow) {
  return item.latest_error || item.retained_reason || item.status_label || item.status;
}

export function supportEventLabel(type: string) {
  return type;
}

export function channelPostStatusLabel(status: string) {
  return String(status || "-");
}

export function channelPostStatusClass(status: string) {
  return statusClass(status);
}

export function hiddenRequirementLabel(value: string | null | undefined) {
  return displayText(value) || "-";
}

export function hiddenScopeLabel(value: string | null | undefined) {
  return displayText(value) || "-";
}

export function hiddenSlug(value: string) {
  return displayText(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
}

export function hiddenCodeSeed(value: string) {
  return hiddenSlug(value).toUpperCase();
}

export function hiddenValidityText(code: { valid_from?: string | null; valid_until?: string | null }) {
  return [code.valid_from ? `Từ ${dateText(code.valid_from)}` : "", code.valid_until ? `Đến ${dateText(code.valid_until)}` : ""].filter(Boolean).join(" • ") || "-";
}

export function orderMoney(order: Order, value = order.amount) {
  const currency = inferOrderCurrency(order);
  if (currency === "USD") return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value || 0);
  if (currency === "USDT" || currency.includes("TRC20") || currency.includes("CRYPTO")) return `${new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value || 0)} ${currency.replace("_TRC20", "")}`;
  return money(value || 0);
}
