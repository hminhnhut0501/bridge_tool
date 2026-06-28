import type { ActivityEvent, KickAuditRow, Order, SupportEvent } from "@/lib/api";
import type { OrderPeriod } from "./dashboard-types";

function groupedNumber(value: number) {
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(value || 0);
}

export function money(value: number) {
  return groupedNumber(value) + "đ";
}

export function displayText(value: unknown) {
  if (value === null || value === undefined) return "";
  const text = String(value).trim();
  return text === "undefined" || text === "null" ? "" : text;
}

export function isLifetimeText(value: string | null | undefined) {
  const text = displayText(value).toLowerCase();
  return ["trọn đời", "tron doi", "lifetime", "long life"].some((part) => text.includes(part)) || /\blife\b/i.test(text);
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
  if (normalized === "USD") return `${groupedNumber(value)} USD`;
  if (normalized === "USDT" || normalized === "CRYPTO") return `${groupedNumber(value)} ${normalized}`;
  return money(value || 0);
}

export function providerRevenueFormat(provider: string, value: number) {
  return `${provider}: ${groupedNumber(value)}đ`;
}

export function dateText(value: string | null | undefined) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(new Date(value));
}

export function dateTextShort(value: string | null | undefined) {
  if (!value) return "-";
  return dateText(value);
}

export function dateTimePreviewText(value: string | null | undefined, fallback = "-") {
  if (!value) return fallback;
  return dateText(value.includes("T") ? `${value}:00` : value);
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

export function tooltipLabel(label: string, code?: string | null) {
  const display = displayText(label) || "-";
  const raw = displayText(code);
  return raw && raw !== display ? `${display} (${raw})` : display;
}

export function kickAuditStatusClass(status: string) {
  return statusClass(status);
}

export function kickAuditReason(item: KickAuditRow) {
  return item.latest_error || item.retained_reason || item.status_label || item.status;
}

export function supportEventLabel(type: string) {
  const labels: Record<string, string> = {
    support_joined: "Vừa vào group hỗ trợ",
    support_left: "Rời group hỗ trợ",
    member_muted: "Đã tắt tiếng",
    member_unmuted: "Đã bật tiếng",
    member_kicked: "Đã xóa khỏi group",
    member_kick_closed: "Đã đóng quyền vào lại",
    expired_notice_sent: "Đã gửi thông báo hết hạn",
    renewal_reminder_sent: "Đã nhắc gia hạn",
    vip_joined: "Vừa vào group VIP",
    vip_left: "Rời group VIP",
    vip_muted: "Đã tắt tiếng VIP",
    vip_unmuted: "Đã bật tiếng VIP",
    vip_kicked: "Đã xóa khỏi group VIP",
    admin_reply_sent: "Admin đã trả lời",
    admin_reply_failed: "Trả lời lỗi",
  };
  return labels[type] || type;
}

export function activityEventLabel(type: string) {
  const labels: Record<string, string> = {
    message: "Tin nhắn",
    text: "Tin nhắn",
    command: "Lệnh",
    callback_query: "Bấm nút",
    callback: "Bấm nút",
    inline_query: "Tìm kiếm nội dung",
    start: "Bắt đầu",
    start_source: "Nguồn vào bot",
    start_activation: "Kích hoạt đơn",
    start_activation_legacy: "Kích hoạt đơn cũ",
    join: "Tham gia",
    leave: "Rời đi",
  };
  return labels[type] || type || "Sự kiện";
}

export function activityEventBadgeTone(type: string) {
  const normalized = String(type || "").trim().toLowerCase();
  if (normalized.includes("error") || normalized.includes("fail") || normalized.includes("kick") || normalized.includes("blocked")) return "bad";
  if (normalized.includes("paid") || normalized.includes("activated") || normalized.includes("joined") || normalized.includes("success")) return "good";
  if (normalized.includes("start") || normalized.includes("command") || normalized.includes("message") || normalized.includes("callback")) return "user";
  return "warning";
}

export function activityEventDetailLabel(eventType: string, title: string, detail: string) {
  if (eventType === "callback_query" || eventType === "callback") return detail || title || "Bấm nút";
  if (eventType === "command") return detail || title || "Lệnh bot";
  return title || detail || "Hoạt động";
}

export function logEntryTypeLabel(type: string) {
  return activityEventLabel(type) !== type ? activityEventLabel(type) : supportEventLabel(type);
}

export function groupDisplayLabel(name: string | null | undefined, id: string | null | undefined) {
  const cleanName = displayText(name);
  const cleanId = displayText(id);
  if (cleanName && cleanId) return cleanName;
  return cleanName || cleanId || "-";
}

export function groupDebugText(name: string | null | undefined, id: string | null | undefined) {
  const cleanName = displayText(name);
  const cleanId = displayText(id);
  if (cleanName && cleanId) return `${cleanName} • ${cleanId}`;
  return cleanName || cleanId || "-";
}

export function auditStatusLabel(status: string | null | undefined) {
  const value = String(status || "").toUpperCase();
  const labels: Record<string, string> = {
    ACTIVE_RETAINED: "Vẫn còn trong group vì còn gói active khác",
    ACTIVE: "Đang hoạt động bình thường",
    EXPIRED: "Đã hết hạn",
    KICKED: "Đã kick khỏi group",
    MUTED: "Đã tắt tiếng",
    UNMUTED: "Đã mở tắt tiếng",
    CLOSED: "Đã đóng quyền vào lại",
    PENDING: "Đang chờ xử lý",
    ERROR: "Đang có lỗi",
  };
  return labels[value] || displayText(status) || "-";
}

export function orderStatusLabel(status: string | null | undefined) {
  const value = String(status || "").toUpperCase();
  const labels: Record<string, string> = {
    PENDING: "Đang chờ thanh toán",
    PAID: "Đã thanh toán",
    EXPIRED: "Đã hết hạn",
    CANCELLED: "Đã hủy",
    REFUNDED: "Đã hoàn tiền",
  };
  return labels[value] || displayText(status) || "-";
}

export function orderLifecycleLabel(order: Order) {
  const status = String(order.status || "").toUpperCase();
  const active = isOrderActive(order);
  if (status === "PAID" && active) return "Đang active";
  if (status === "PAID" && !active) {
    return isLifetimeText(order.plan_name) ? "Trọn đời" : "VIP đã hết hạn";
  }
  if (status === "PENDING") {
    return order.expire_at && new Date(order.expire_at).getTime() < Date.now()
      ? "Chưa thanh toán / quá hạn"
      : "Đang chờ thanh toán";
  }
  if (status === "EXPIRED") return "Hết hạn / chờ kick";
  return orderStatusLabel(order.status);
}

export function channelPostStatusLabel(status: string) {
  const value = String(status || "").toLowerCase();
  const labels: Record<string, string> = {
    draft: "Bản nháp",
    queued: "Đang chờ gửi",
    queue: "Đang chờ gửi",
    scheduled: "Đã lên lịch",
    sent: "Đã gửi",
    failed: "Gửi lỗi",
    deleted: "Đã xóa",
    delete_scheduled: "Đã lên lịch xóa",
    delete_failed: "Xóa lỗi",
  };
  return labels[value] || displayText(status) || "-";
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
  if (currency === "USD") return `${groupedNumber(value)} USD`;
  if (currency === "USDT" || currency.includes("TRC20") || currency.includes("CRYPTO")) return `${groupedNumber(value)} ${currency.replace("_TRC20", "")}`;
  return money(value || 0);
}
