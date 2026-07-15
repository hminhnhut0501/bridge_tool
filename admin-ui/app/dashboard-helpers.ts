import type { ActivityEvent, KickAuditRow, Order, SupportEvent } from "@/lib/api";
import type { OrderPeriod } from "./dashboard-types";

const VI_TIME_ZONE = "Asia/Ho_Chi_Minh";

function groupedNumber(value: number) {
  return new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(value || 0);
}

function decimalMoney(value: number, maximumFractionDigits = 2) {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits,
  }).format(value || 0);
}

export function formatDisplayCurrency(value: number, currency: string, options?: { maximumFractionDigits?: number }) {
  const normalized = normalizeRevenueCurrency(currency);
  const amount = Number(value || 0);
  const fractionDigits = options?.maximumFractionDigits ?? (normalized === "USDT" || normalized === "CRYPTO" ? 6 : 2);
  if (normalized === "USD") return `${decimalMoney(amount, fractionDigits)} USD`;
  if (normalized === "USDT" || normalized === "CRYPTO") return `${decimalMoney(amount, fractionDigits)} ${normalized}`;
  return money(amount);
}

function parseLooseDateParts(value: string) {
  const text = value.trim();
  const hasTimezone = /[zZ]$|[+-]\d{2}:?\d{2}$/.test(text);
  if (hasTimezone) {
    const direct = new Date(text);
    if (!Number.isNaN(direct.getTime())) return direct;
  }

  const isoLike = text.match(/^(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?$/);
  if (isoLike) {
    const [, y, m, d, hh = "00", mm = "00", ss = "00"] = isoLike;
    return new Date(Date.UTC(Number(y), Number(m) - 1, Number(d), Number(hh) - 7, Number(mm), Number(ss)));
  }

  const dmyTime = text.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:[ T](\d{2}):(\d{2})(?::(\d{2}))?)?$/);
  if (dmyTime) {
    const [, d, m, y, hh = "00", mm = "00", ss = "00"] = dmyTime;
    return new Date(Date.UTC(Number(y), Number(m) - 1, Number(d), Number(hh) - 7, Number(mm), Number(ss)));
  }

  const timeFirst = text.match(/^(\d{2}):(\d{2})(?::(\d{2}))?\s+(\d{2})\/(\d{2})\/(\d{4})$/);
  if (timeFirst) {
    const [, hh, mm, ss = "00", d, m, y] = timeFirst;
    return new Date(Date.UTC(Number(y), Number(m) - 1, Number(d), Number(hh) - 7, Number(mm), Number(ss)));
  }

  const dateOnly = text.match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
  if (dateOnly) {
    const [, d, m, y] = dateOnly;
    return new Date(Date.UTC(Number(y), Number(m) - 1, Number(d), -7, 0, 0));
  }

  const timestamp = Number(text);
  if (Number.isFinite(timestamp)) return new Date(timestamp);
  const direct = new Date(text);
  if (!Number.isNaN(direct.getTime())) return direct;
  return null;
}

export function parseSafeDate(value: string | number | Date | null | undefined) {
  if (value === null || value === undefined) return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : new Date(value.getTime());
  if (typeof value === "number") return Number.isFinite(value) ? new Date(value) : null;
  const text = String(value).trim();
  if (!text || text === "null" || text === "undefined") return null;
  return parseLooseDateParts(text);
}

export function safeDateMillis(value: string | number | Date | null | undefined) {
  return parseSafeDate(value)?.getTime() ?? null;
}

function formatDateKey(value: Date) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: VI_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(value);
  const map = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return `${map.year || "0000"}-${map.month || "00"}-${map.day || "00"}`;
}

function formatDateTimeParts(value: Date) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: VI_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).formatToParts(value);
  const map = Object.fromEntries(parts.map((part) => [part.type, part.value]));
  return {
    year: map.year || "0000",
    month: map.month || "00",
    day: map.day || "00",
    hour: map.hour || "00",
    minute: map.minute || "00",
    second: map.second || "00",
  };
}

export function money(value: number) {
  return groupedNumber(value) + "đ";
}

export function displayText(value: unknown) {
  if (value === null || value === undefined) return "";
  const text = String(value).trim();
  return text === "undefined" || text === "null" ? "" : text;
}

export function stripPlanToken(value: string) {
  return displayText(value).replace(/\s*\[PT:[^\]]+\]\s*$/i, "").trim();
}

export function isLifetimeText(value: string | null | undefined) {
  const text = displayText(value).toLowerCase();
  return ["trọn đời", "tron doi", "lifetime", "long life"].some((part) => text.includes(part)) || /\blife\b/i.test(text);
}

export function isLifetimeAllAccessText(value: string | null | undefined) {
  const text = displayText(value).toLowerCase();
  if (!isLifetimeText(text)) return false;
  return text.includes("all access") || text.includes("svip");
}

export function inferOrderProvider(order: Order) {
  return String(order.payment_provider || "MANUAL").toUpperCase();
}

export function inferOrderCurrency(order: Order) {
  const explicit = String(order.payment_currency || "").toUpperCase();
  const provider = inferOrderProvider(order);
  if (explicit === "USD") return "USD";
  if (explicit === "VND" || !explicit) return "VND";
  if (explicit.includes("USDT") || explicit.includes("TRC20") || explicit.includes("CRYPTO")) return "USDT";
  if (provider === "PAYPAL") return "USD";
  if (provider === "TRON_USDT") return "USDT";
  if (provider === "PAYOS" || provider === "BINANCE_PAY") return "VND";
  return explicit || "VND";
}

export function orderCouponCode(order: Order) {
  return displayText(order.coupon_code || "");
}

export function orderPlanKind(order: Order) {
  if (isLifetimeText(order.plan_name)) return "Trọn đời";
  return displayText(stripPlanToken(String(order.plan_name || ""))) || "-";
}

export function isOrderActive(order: Order) {
  if (!order.expire_at || isLifetimeText(order.plan_name)) return true;
  const expireMillis = safeDateMillis(order.expire_at);
  return expireMillis === null ? true : expireMillis >= Date.now();
}

export function daysUntil(value: string | null | undefined) {
  if (!value) return -9999;
  const millis = safeDateMillis(value);
  if (millis === null) return -9999;
  return Math.ceil((millis - Date.now()) / 86400000);
}

export function groupNamesForOrder(order: Order) {
  const groups = String(order.plan_name || "")
    .split(/[,|/]/)
    .map((item) => stripPlanToken(item).trim())
    .filter(Boolean);
  return groups.length ? groups : [orderPlanKind(order)];
}

export function orderNoteText(order: Order) {
  const note = displayText(order.note || "");
  if (note) return note;
  const metadata = order.metadata && typeof order.metadata === "object" ? order.metadata as Record<string, unknown> : null;
  return displayText(metadata?.note);
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
  return formatDisplayCurrency(value, currency);
}

export function orderAmountValue(order: Order, value: number | string | null | undefined = order.amount) {
  const numeric = Number(value || 0);
  const currency = normalizeRevenueCurrency(inferOrderCurrency(order));
  if ((currency === "USD" || currency === "USDT" || currency === "CRYPTO") && Number.isInteger(numeric) && Math.abs(numeric) >= 100) {
    return numeric / 100;
  }
  return numeric;
}

export function providerRevenueFormat(provider: string, value: number, currency = "VND") {
  return `${provider}: ${formatDisplayCurrency(value, currency)}`;
}

export function dateText(value: string | null | undefined) {
  if (!value) return "-";
  const date = parseSafeDate(value);
  if (!date) return displayText(value) || "-";
  return new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: VI_TIME_ZONE,
  }).format(date);
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
  const date = parseSafeDate(value);
  if (!date) return "";
  const parts = formatDateTimeParts(date);
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

export function orderExpireValue(value: string | null | undefined) {
  return dateTimeInputValue(value);
}

export function isTodayDate(value: string | null | undefined) {
  if (!value) return false;
  const date = parseSafeDate(value);
  if (!date) return false;
  return formatDateKey(date) === formatDateKey(new Date());
}

export function dateMinusDaysText(value: string | null | undefined, days: number) {
  if (!value) return "-";
  const date = parseSafeDate(value);
  if (!date) return "-";
  return dateText(new Date(date.getTime() - days * 86400000).toISOString());
}

export function dayKey(value: string | null | undefined) {
  return value ? value.slice(0, 10) : "UNKNOWN";
}

export function isoDayKey(value: string | null | undefined) {
  return dayKey(value);
}

export function isWithinPeriod(value: string | null | undefined, period: OrderPeriod) {
  if (!value) return false;
  const date = parseSafeDate(value);
  const now = new Date();
  if (!date) return false;
  if (period === "all") return true;
  const dateKey = formatDateKey(date);
  const nowKey = formatDateKey(now);
  if (period === "today") return dateKey === nowKey;
  if (period === "7d") return now.getTime() - date.getTime() <= 7 * 86400000;
  if (period === "month") return dateKey.slice(0, 7) === nowKey.slice(0, 7);
  if (period === "year") return dateKey.slice(0, 4) === nowKey.slice(0, 4);
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
    auto_payment_redirect: "Auto payment chuyển hỗ trợ",
    support_inbox_disabled_redirect: "Auto payment chuyển hỗ trợ",
    admin_reply_sent: "Admin đã trả lời",
    admin_reply_failed: "Trả lời lỗi",
    delivery_success: "Đơn auto-paid",
    delivery_failed: "Đơn auto-paid lỗi",
    support_ticket_created: "Tin nhắn riêng mới",
    manual_activation_link_generated: "Kích hoạt đơn",
    manual_activation_link_failed: "Kích hoạt đơn lỗi",
    activation_link_cleanup_done: "Dọn link kích hoạt",
    activation_link_cleanup_failed: "Dọn link kích hoạt lỗi",
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

export function activityLogDetailLabel(type: string, detail: string, title = "") {
  const text = displayText(detail);
  const lower = text.toLowerCase();
  if (!text) return displayText(title) || "-";
  if (type === "manual_activation_link_generated" || lower.includes("manual activation link generated")) {
    const statusMatch = text.match(/Trạng thái:\s*([^•]+)•/i) || text.match(/status:\s*([^•]+)•/i);
    const planMatch = text.match(/(?:Gói|Plan):\s*([^•]+)•/i);
    const orderMatch = text.match(/(?:Đơn|Order):\s*([^•]+)•/i);
    const groups = Array.from(text.matchAll(/'group_name':\s*'([^']+)'.*?'invite_link':\s*'([^']+)'/g)).map((match) => `${match[1]}: ${match[2]}`);
    const summary = [statusMatch?.[1]?.trim(), planMatch?.[1]?.trim(), orderMatch?.[1]?.trim()].filter(Boolean).join(" • ");
    return [summary || displayText(title) || "Kích hoạt đơn", ...groups].filter(Boolean).join("\n");
  }
  if (lower.includes("support_inbox_disabled_redirect")) return "Auto payment chuyển sang hỗ trợ";
  if (lower.includes("auto payment") && lower.includes("redirect")) return "Auto payment chuyển sang hỗ trợ";
  return text;
}

export function friendlyDetailText(value: string | null | undefined) {
  const text = displayText(value);
  if (!text) return "-";
  const lower = text.toLowerCase();
  if (lower.includes("không map được group")) return "Không map được group";
  if (lower.includes("không mapp được group")) return "Không map được group";
  if (lower.includes("support inbox disabled redirect")) return "Bot đang chuyển sang hỗ trợ";
  if (lower.includes("manual activation link generated")) return "Kích hoạt đơn";
  if (lower.includes("manual order created")) return "Tạo đơn thủ công";
  return text;
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
  if (status === "PAID" && active) return "PAID · Active";
  if (status === "PAID" && !active) {
    return isLifetimeText(order.plan_name) ? "PAID · Trọn đời" : "PAID · Hết hạn";
  }
  if (status === "PENDING") {
    const expireMillis = safeDateMillis(order.expire_at);
    return expireMillis !== null && expireMillis < Date.now()
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

export function orderMoney(order: Order, value: number | string | null | undefined = order.amount) {
  return formatDisplayCurrency(orderAmountValue(order, value), inferOrderCurrency(order));
}
