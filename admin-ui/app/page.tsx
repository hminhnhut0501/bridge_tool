"use client";

import {
  Activity,
  BadgePercent,
  BarChart3,
  CheckCircle2,
  FileText,
  Gift,
  Loader2,
  Plus,
  RefreshCw,
  Save,
  Settings,
  ShieldCheck,
  ShoppingCart,
  Ticket,
  Trash2,
  XCircle,
} from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import {
  ConfigRow,
  Coupon,
  MenuPage,
  Order,
  SaleRule,
  UserRow,
  WebhookInfo,
  createCoupon,
  deleteConfig,
  deleteCoupon,
  deleteMenuPage,
  deleteSaleRule,
  getConfig,
  getCoupons,
  getMenuPages,
  getOrders,
  getSaleRules,
  getUsers,
  getWebhookInfo,
  resetWebhook,
  updateConfig,
  updateMenuPage,
  updateOrderStatus,
  upsertSaleRule,
} from "@/lib/api";

type Tab = "overview" | "analytics" | "setup" | "orders" | "content" | "coupons" | "sales" | "system";
type ContentSubTab = "bot" | "plans" | "support" | "currency" | "buttons" | "alerts" | "messages" | "saleContent" | "admin" | "menu";
type OrderPeriod = "all" | "today" | "7d" | "month" | "year";
type GroupMode = "none" | "day" | "month";

type Notice = {
  type: "ok" | "error";
  text: string;
};

type ConfigField = {
  key: string;
  label: string;
  placeholder: string;
  help: string;
  kind?: "input" | "textarea" | "select";
  options?: { label: string; value: string }[];
};

const GROUP_COUNT = 20;

const BOT_FIELDS: ConfigField[] = [
  {
    key: "QR_TTL_SECONDS",
    label: "Thời hạn mã QR",
    placeholder: "300",
    help: "Số giây QR còn hiệu lực. 300 giây = 5 phút. Hết hạn bot sẽ xoá QR và nhắc tạo đơn mới.",
  },
  {
    key: "PAYMENT_CHECK_INTERVAL_SECONDS",
    label: "Tần suất tự kiểm tra thanh toán",
    placeholder: "10",
    help: "Bot sẽ check PayOS mỗi N giây trong thời hạn QR. Khuyến nghị 10-15 giây.",
  },
  {
    key: "MAINTENANCE_MODE",
    label: "Chế độ bảo trì",
    placeholder: "OFF",
    help: "Bật ON để chỉ admin dùng bot, khách sẽ thấy thông báo bảo trì.",
    kind: "select",
    options: [
      { label: "Tắt", value: "OFF" },
      { label: "Bật", value: "ON" },
    ],
  },
  {
    key: "MSG_MAINTENANCE",
    label: "Thông báo bảo trì",
    placeholder: "Hệ thống đang bảo trì, vui lòng quay lại sau.",
    help: "Tin nhắn gửi cho khách khi bot đang bảo trì.",
    kind: "textarea",
  },
  {
    key: "REMINDER_DAYS",
    label: "Nhắc trước khi hết hạn",
    placeholder: "3",
    help: "Số ngày trước khi hết hạn bot sẽ nhắc khách gia hạn.",
  },
  {
    key: "EARLY_RENEW_ENABLED",
    label: "Ưu đãi gia hạn sớm",
    placeholder: "ON",
    help: "Bật/tắt nút gia hạn sớm trong tin nhắc hết hạn.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "EARLY_RENEW_DISCOUNT_PERCENT",
    label: "Giảm giá gia hạn sớm",
    placeholder: "10",
    help: "Phần trăm giảm khi khách gia hạn sớm.",
  },
];

const ADMIN_FIELDS: ConfigField[] = [
  {
    key: "ADMIN_IDS",
    label: "Telegram Admin ID",
    placeholder: "887869657",
    help: "Nhập một hoặc nhiều Telegram ID admin, cách nhau bằng dấu phẩy. Admin được bỏ qua bảo trì/spam và dùng lệnh quản trị.",
  },
];

const SUPPORT_FIELDS: ConfigField[] = [
  {
    key: "SUPPORT_GROUP_ENABLED",
    label: "Bật nhóm support",
    placeholder: "OFF",
    help: "Bật ON để gửi nút join nhóm hỗ trợ kèm link tham gia sau thanh toán/coupon.",
    kind: "select",
    options: [
      { label: "Tắt", value: "OFF" },
      { label: "Bật", value: "ON" },
    ],
  },
  {
    key: "SUPPORT_GROUP_ID",
    label: "Support group ID",
    placeholder: "-1001234567890",
    help: "ID nhóm support. Nhóm này không bị kick khi gói hết hạn.",
  },
  {
    key: "SUPPORT_GROUP_NAME",
    label: "Tên nhóm support",
    placeholder: "Nhóm hỗ trợ Privé+",
    help: "Tên hiển thị trong log/lỗi.",
  },
  {
    key: "SUPPORT_GROUP_BUTTON_TEXT",
    label: "Text nút join support",
    placeholder: "💬 Join nhóm hỗ trợ",
    help: "Nút URL riêng, mỗi link chỉ dùng được 1 lần.",
  },
  {
    key: "SUPPORT_GROUP_GRACE_DAYS",
    label: "Số ngày mute trước khi kick",
    placeholder: "14",
    help: "Gói ngày/coupon hết hạn sẽ bị mute, sau N ngày không gia hạn mới bị kick khỏi nhóm trả phí.",
  },
];

const CURRENCY_FIELDS: ConfigField[] = [
  {
    key: "DISPLAY_CURRENCY_STYLE",
    label: "Kiểu hiển thị tiền",
    placeholder: "VND_LOWER",
    help: "Chỉ ảnh hưởng text UI bot. QR PayOS vẫn luôn dùng VND integer.",
    kind: "select",
    options: [
      { label: "3.000đ", value: "VND_LOWER" },
      { label: "3.000 VNĐ", value: "VND_TEXT" },
      { label: "3K", value: "COMPACT_K" },
      { label: "3.000 + hậu tố tuỳ chỉnh", value: "CUSTOM_SUFFIX" },
    ],
  },
  {
    key: "DISPLAY_CURRENCY_SUFFIX",
    label: "Hậu tố tiền tuỳ chỉnh",
    placeholder: "🐟",
    help: "Dùng khi chọn kiểu hậu tố tuỳ chỉnh. Ví dụ: 🐟, coin, điểm.",
  },
  {
    key: "DISPLAY_CURRENCY_COMPACT_DECIMALS",
    label: "Số lẻ khi hiển thị K",
    placeholder: "0",
    help: "Ví dụ 1 sẽ hiển thị 3.5K nếu giá là 3500.",
  },
];

const MESSAGE_FIELDS: ConfigField[] = [
  {
    key: "MSG_BILL_TEMPLATE",
    label: "Nội dung bill QR",
    placeholder: "Mã Đơn: {desc}\\nSố tiền: {amount}\\nNgân hàng: {bank}",
    help: "Dùng biến {plan}, {amount}, {bank}, {name}, {stk}, {desc}.",
    kind: "textarea",
  },
  {
    key: "MSG_TIMEOUT_QR",
    label: "Tin khi QR hết hạn",
    placeholder: "⏳ Mã QR đã hết hạn sau {minutes} phút. Vui lòng tạo đơn mới để thanh toán.",
    help: "Dùng biến {minutes}. Bot gửi tin này sau khi hết thời gian tự check.",
    kind: "textarea",
  },
  {
    key: "MSG_DELIVERY",
    label: "Tin gửi link sau thanh toán",
    placeholder: "Thanh toán thành công!\\nGói: {plan}\\nHạn dùng: {date}\\n{links}",
    help: "Dùng biến {plan}, {date}, {links}. Tin QR sẽ được xóa trước khi gửi link.",
    kind: "textarea",
  },
  {
    key: "MSG_COUPON_SUCCESS",
    label: "Tin kích hoạt coupon thành công",
    placeholder: "Mã: {code}\\nGói: {plan}\\nHạn: {expire}\\n{links}",
    help: "Dùng biến {code}, {plan}, {expire}, {links}.",
    kind: "textarea",
  },
  {
    key: "MSG_COUPON_PROMPT",
    label: "Tin yêu cầu nhập coupon",
    placeholder: "<b>Nhập mã giảm giá / mã kích hoạt</b>\\n\\nGửi mã bạn nhận được vào đây.",
    help: "Tin bot gửi khi khách bấm nhập coupon.",
    kind: "textarea",
  },
  {
    key: "MSG_COUPON_DISCOUNT_OPTIONS",
    label: "Tin coupon giảm giá hợp lệ",
    placeholder: "Mã: {code}\\nGiảm: {percent}%\\nChọn gói muốn mua bên dưới.",
    help: "Dùng biến {code}, {percent}.",
    kind: "textarea",
  },
  {
    key: "MSG_COUPON_GROUP_OPTIONS",
    label: "Tin coupon chọn group",
    placeholder: "Mã: {code}\\nThời hạn: {days} ngày\\nChọn group bạn muốn kích hoạt bên dưới.",
    help: "Dùng khi coupon kích hoạt cho phép khách tự chọn group lẻ. Dùng biến {code}, {days}.",
    kind: "textarea",
  },
  {
    key: "MSG_WAIT_QR",
    label: "Tin đang tạo QR",
    placeholder: "⏳ Đang tạo mã QR...",
    help: "Tin tạm khi bot gọi PayOS.",
  },
  {
    key: "MSG_QR_ERROR",
    label: "Tin lỗi tạo QR",
    placeholder: "❌ Lỗi cổng thanh toán!",
    help: "Tin gửi khi PayOS không tạo được đơn.",
  },
  {
    key: "MSG_EXPIRED",
    label: "Tin gói hết hạn",
    placeholder: "Gói {plan} của bạn đã hết hạn.",
    help: "Dùng biến {plan}, {date}.",
    kind: "textarea",
  },
  {
    key: "MSG_REMINDER",
    label: "Tin nhắc sắp hết hạn",
    placeholder: "Gói {plan} sẽ hết hạn sau {days} ngày.",
    help: "Dùng biến {plan}, {days}, {date}.",
    kind: "textarea",
  },
  {
    key: "MSG_ME_TITLE",
    label: "Tiêu đề /me",
    placeholder: "👤 <b>GÓI DỊCH VỤ CỦA BẠN:</b>\\n\\n",
    help: "Phần đầu trang tài khoản.",
    kind: "textarea",
  },
  {
    key: "MSG_ME_EMPTY",
    label: "Tin /me khi chưa có gói",
    placeholder: "❌ Bạn chưa có gói VIP nào.",
    help: "Hiện khi khách chưa có đơn PAID.",
  },
  {
    key: "MSG_ME_ITEM",
    label: "Mẫu từng gói trong /me",
    placeholder: "🎁 Gói: <b>{plan}</b>\\n📅 Hạn: <code>{date}</code>\\n\\n",
    help: "Dùng biến {plan}, {date}.",
    kind: "textarea",
  },
  {
    key: "MSG_POLICY",
    label: "Nội dung quy định fallback",
    placeholder: "Chính sách đang cập nhật...",
    help: "Dùng khi chưa có menu page policy_page.",
    kind: "textarea",
  },
  {
    key: "MSG_SUPPORT",
    label: "Nội dung hỗ trợ fallback",
    placeholder: "Hỗ trợ đang cập nhật...",
    help: "Dùng khi chưa có menu page support_page.",
    kind: "textarea",
  },
  {
    key: "MSG_UPDATING",
    label: "Tin đang cập nhật",
    placeholder: "🌟 <b>ĐANG CẬP NHẬT DỮ LIỆU...</b>",
    help: "Fallback khi nội dung trang trống.",
    kind: "textarea",
  },
];

const BUTTON_FIELDS: ConfigField[] = [
  { key: "BTN_BACK", label: "Nút quay lại", placeholder: "🔙 Quay lại Menu", help: "Dùng ở hầu hết trang bot." },
  { key: "BTN_CHECK_PAYMENT", label: "Nút đã chuyển khoản", placeholder: "🔄 Đã chuyển khoản", help: "Nút dưới QR để khách check thủ công." },
  { key: "BTN_CANCEL_ORDER", label: "Nút hủy đơn", placeholder: "❌ Hủy", help: "Nút dưới QR để hủy đơn pending." },
  { key: "BTN_VIEW_QR", label: "Nút xem QR", placeholder: "🖼 Xem QR", help: "Dùng khi Telegram không gửi được ảnh QR." },
  { key: "BTN_BUY_1M", label: "Nút mua nhóm 1 tháng", placeholder: "💎 VIP 1 THÁNG", help: "Nút trên trang chi tiết nhóm." },
  { key: "BTN_BUY_LIFE", label: "Nút mua nhóm trọn đời", placeholder: "👑 VIP TRỌN ĐỜI", help: "Nút trên trang chi tiết nhóm." },
  { key: "BTN_VIEW_SVIP_PAGE", label: "Nút xem SVIP", placeholder: "🌟 XEM GÓI SVIP+", help: "Nút từ nhóm riêng sang trang SVIP." },
  { key: "BTN_RENEW", label: "Nút gia hạn", placeholder: "🔄 Gia hạn ngay", help: "Nút khi gói hết hạn." },
  { key: "BTN_EARLY_RENEW", label: "Nút gia hạn sớm", placeholder: "🔥 Gia hạn sớm -{discount_percent}%", help: "Nút ưu đãi gia hạn sớm." },
  { key: "BTN_RENEW_FULL", label: "Nút gia hạn/lên trọn đời", placeholder: "🌟 Gia hạn / Lên Trọn Đời", help: "Nút trong tin nhắc gia hạn." },
  { key: "BTN_RENEW_GROUP", label: "Nút mở rộng gói", placeholder: "🔄 Gia hạn / Mở rộng gói", help: "Nút trong tin nhắc gia hạn." },
];

const ALERT_FIELDS: ConfigField[] = [
  { key: "ALERT_SPAM", label: "Cảnh báo spam chung", placeholder: "⏳ Vui lòng thao tác chậm lại!", help: "Khi khách bấm quá nhanh." },
  { key: "ALERT_SPAM_QR", label: "Cảnh báo spam tạo QR", placeholder: "⏳ Thao tác quá nhanh! Vui lòng chờ 15s.", help: "Khi khách tạo QR liên tục." },
  { key: "ALERT_MAINTENANCE", label: "Cảnh báo bảo trì", placeholder: "🛠 Bot đang bảo trì, vui lòng quay lại sau...", help: "Alert khi khách bấm nút lúc bảo trì." },
  { key: "ALERT_QR_EXPIRED", label: "Cảnh báo QR hết hạn", placeholder: "⏳ Mã QR đã hết hạn. Vui lòng tạo đơn mới.", help: "Khi khách bấm check QR quá hạn." },
  { key: "ALERT_PAID_SUCCESS", label: "Cảnh báo đã nhận tiền", placeholder: "✅ Giao dịch thành công!", help: "Khi PayOS trả PAID." },
  { key: "ALERT_NOT_PAID", label: "Cảnh báo chưa nhận tiền", placeholder: "⏳ Hệ thống chưa nhận được tiền!", help: "Khi khách bấm đã chuyển khoản nhưng PayOS chưa PAID." },
  { key: "ALERT_CANCELLED", label: "Cảnh báo hủy đơn", placeholder: "🚫 Đã hủy đơn.", help: "Khi khách bấm hủy QR." },
  { key: "ALERT_EARLY_RENEW_OFF", label: "Cảnh báo gia hạn sớm tắt", placeholder: "Ưu đãi gia hạn sớm đang tắt. Vui lòng gia hạn theo giá thường.", help: "Khi khách bấm offer đã tắt." },
];

const SALE_CONTENT_FIELDS: ConfigField[] = [
  {
    key: "SALE_ANNOUNCE_ENABLED",
    label: "Thông báo flash sale khi /start",
    placeholder: "ON",
    help: "Bật/tắt màn hình thông báo flash sale trước menu chính.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  { key: "IMG_SALE_BANNER", label: "Ảnh banner flash sale", placeholder: "File ID Telegram hoặc URL ảnh", help: "Ảnh gửi kèm thông báo sale." },
  {
    key: "MSG_SALE_ANNOUNCE",
    label: "Nội dung thông báo flash sale",
    placeholder: "🔥 <b>FLASH SALE PRIVÉ+ ĐANG MỞ</b>\\n\\n{sale_lines}\\n\\nSale kết thúc sau: {countdown}",
    help: "Dùng biến {sale_lines}, {countdown}, {slots}.",
    kind: "textarea",
  },
  {
    key: "SALE_LINE_TEMPLATE",
    label: "Mẫu từng dòng sale",
    placeholder: "🔥 <b>{price_key}</b>\\nGiá gốc: <s>{old_price}</s>\\nGiá sale: <b>{sale_price}</b> (-{discount_percent}%)",
    help: "Dùng biến {price_key}, {old_price}, {sale_price}, {discount_percent}, {countdown}, {slots}.",
    kind: "textarea",
  },
  {
    key: "SALE_ANNOUNCE_BUTTONS",
    label: "Nút dưới thông báo flash sale",
    placeholder: "🔥 Mua SVIP Trọn Đời => buy_full_life\\n💎 Mua SVIP 1 Tháng => buy_full_1m",
    help: "Mỗi dòng là một nút. Dùng cú pháp Text => callback.",
    kind: "textarea",
  },
];

const PLAN_FIELDS: ConfigField[] = [
  { key: "PLAN_FULL_1M", label: "Tên gói SVIP 1 tháng", placeholder: "SVIP+ 1 THÁNG", help: "Tên gói hiển thị khi khách mua SVIP 1 tháng." },
  { key: "PLAN_FULL_LIFE", label: "Tên gói SVIP trọn đời", placeholder: "SVIP+ TRỌN ĐỜI", help: "Tên gói hiển thị khi khách mua SVIP trọn đời." },
  { key: "PRICE_SVIP_30D", label: "Giá SVIP 1 tháng", placeholder: "99000", help: "Nhập số tiền VND, không cần dấu chấm." },
  { key: "PRICE_SVIP_LIFE", label: "Giá SVIP trọn đời", placeholder: "499000", help: "Nhập số tiền VND, không cần dấu chấm." },
  { key: "BTN_BUY_SVIP_30D", label: "Nút mua SVIP 1 tháng", placeholder: "MUA 1 THÁNG", help: "Text nút trong bot." },
  { key: "BTN_BUY_SVIP_LIFE", label: "Nút mua SVIP trọn đời", placeholder: "MUA TRỌN ĐỜI", help: "Text nút trong bot." },
];

const PRICE_KEY_OPTIONS = [
  "PRICE_SVIP_30D",
  "PRICE_SVIP_LIFE",
];

const PLAN_KEY_OPTIONS = [
  "FULL_1M",
  "FULL_LIFE",
];

const SELECTABLE_GROUP_COUPON_OPTIONS = [
  "SELECT_GROUP_1M",
  "SELECT_GROUP_LIFE",
];

const EMPTY_COUPON_FORM = {
  Code: "",
  Coupon_Type: "DISCOUNT",
  Plan_Name: "SELECT_GROUP_1M",
  Duration_Days: "30",
  Discount_Percent: "10",
  Applies_To: "ALL",
  Max_Uses: "1",
  Enabled: "ON",
};

const ORDER_PAGE_SIZE = 25;

function money(value: number) {
  return new Intl.NumberFormat("vi-VN").format(value || 0) + "đ";
}

function dateText(value: string | null | undefined) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("vi-VN", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function dayKey(value: string | null | undefined) {
  if (!value) return "Không rõ ngày";
  return new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium" }).format(new Date(value));
}

function monthKey(value: string | null | undefined) {
  if (!value) return "Không rõ tháng";
  return new Intl.DateTimeFormat("vi-VN", { month: "2-digit", year: "numeric" }).format(new Date(value));
}

function isWithinPeriod(value: string | null | undefined, period: OrderPeriod) {
  if (period === "all") return true;
  if (!value) return false;

  const date = new Date(value);
  const now = new Date();
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);

  if (period === "today") return date >= start;
  if (period === "7d") {
    const sevenDaysAgo = new Date(start);
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 6);
    return date >= sevenDaysAgo;
  }
  if (period === "month") {
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    return date >= monthStart;
  }
  if (period === "year") {
    const yearStart = new Date(now.getFullYear(), 0, 1);
    return date >= yearStart;
  }
  return true;
}

function uniquePaidCustomers(orders: Order[]) {
  return new Set(orders.filter((item) => item.status === "PAID").map((item) => item.telegram_user_id)).size;
}

function orderStats(orders: Order[]) {
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

function groupOrders(orders: Order[], mode: GroupMode) {
  if (mode === "none") return [];
  const groups = new Map<string, Order[]>();
  for (const order of orders) {
    const key = mode === "day" ? dayKey(order.created_at) : monthKey(order.created_at);
    groups.set(key, [...(groups.get(key) || []), order]);
  }
  return Array.from(groups.entries()).map(([label, items]) => ({ label, items, stats: orderStats(items) }));
}

function statusClass(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === "paid") return "status paid";
  if (normalized === "expired" || normalized === "cancelled") return "status expired";
  return "status pending";
}

function getConfigValue(config: ConfigRow[], key: string, fallback = "") {
  return config.find((item) => item.key === key)?.value ?? fallback;
}

function isGroupConfigured(config: ConfigRow[], groupNo: number) {
  return Boolean(getConfigValue(config, `BTN_G${groupNo}`) && getConfigValue(config, `ID_G${groupNo}`));
}

function hasAnyGroupConfig(config: ConfigRow[], groupNo: number) {
  return groupConfigKeys(String(groupNo)).some((key) => Boolean(getConfigValue(config, key)));
}

function groupConfigKeys(groupNo: string) {
  return [`BTN_G${groupNo}`, `ID_G${groupNo}`, `PRICE_G${groupNo}_1M`, `PRICE_G${groupNo}_LIFE`, `DESC_G${groupNo}`, `IMG_G${groupNo}`];
}

export default function Home() {
  const [secret, setSecret] = useState("");
  const [savedSecret, setSavedSecret] = useState("");
  const [tab, setTab] = useState<Tab>("overview");
  const [contentTab, setContentTab] = useState<ContentSubTab>("bot");
  const [orders, setOrders] = useState<Order[]>([]);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [config, setConfig] = useState<ConfigRow[]>([]);
  const [menuPages, setMenuPages] = useState<MenuPage[]>([]);
  const [saleRules, setSaleRules] = useState<SaleRule[]>([]);
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [webhook, setWebhook] = useState<WebhookInfo | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState("");
  const [query, setQuery] = useState("");
  const [orderStatus, setOrderStatus] = useState("ALL");
  const [orderPeriod, setOrderPeriod] = useState<OrderPeriod>("month");
  const [orderGroupMode, setOrderGroupMode] = useState<GroupMode>("day");
  const [orderPage, setOrderPage] = useState(1);
  const [groupNo, setGroupNo] = useState("1");
  const [groupName, setGroupName] = useState("");
  const [groupId, setGroupId] = useState("");
  const [groupPrice1m, setGroupPrice1m] = useState("");
  const [groupPriceLife, setGroupPriceLife] = useState("");
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [menuForm, setMenuForm] = useState({ page_id: "main_menu", image_url: "", body: "", layout: "" });
  const [saleForm, setSaleForm] = useState({ sale_id: "", price_key: "PRICE_SVIP_30D", discount_percent: "", sale_price: "", slot_limit: "", enabled: "ON", start_at: "", end_at: "" });
  const [couponForm, setCouponForm] = useState({ ...EMPTY_COUPON_FORM });

  useEffect(() => {
    const stored = window.localStorage.getItem("prive_admin_secret") || "";
    setSavedSecret(stored);
    setSecret(stored);
  }, []);

  useEffect(() => {
    const nextValues: Record<string, string> = {};
    [...ADMIN_FIELDS, ...SUPPORT_FIELDS, ...CURRENCY_FIELDS, ...BOT_FIELDS, ...MESSAGE_FIELDS, ...BUTTON_FIELDS, ...ALERT_FIELDS, ...SALE_CONTENT_FIELDS, ...PLAN_FIELDS].forEach((field) => {
      nextValues[field.key] = getConfigValue(config, field.key);
    });
    setFieldValues(nextValues);
  }, [config]);

  useEffect(() => {
    if (savedSecret) {
      loadAll(savedSecret);
    }
  }, [savedSecret]);

  function showNotice(type: Notice["type"], text: string) {
    setNotice({ type, text });
    window.setTimeout(() => setNotice(null), 3500);
  }

  async function runAction(label: string, action: () => Promise<void>) {
    setSaving(label);
    setNotice(null);
    try {
      await action();
      showNotice("ok", "Đã xử lý thành công.");
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "Không lưu được thay đổi.");
    } finally {
      setSaving("");
    }
  }

  async function loadAll(activeSecret = savedSecret) {
    if (!activeSecret) return;
    setLoading(true);
    setNotice(null);
    try {
      const [ordersRes, usersRes, configRes, menuRes, salesRes, couponsRes, webhookRes] = await Promise.all([
        getOrders(activeSecret),
        getUsers(activeSecret),
        getConfig(activeSecret),
        getMenuPages(activeSecret),
        getSaleRules(activeSecret),
        getCoupons(activeSecret),
        getWebhookInfo(activeSecret),
      ]);
      setOrders(ordersRes.data);
      setUsers(usersRes.data);
      setConfig(configRes.data);
      setMenuPages(menuRes.data);
      setSaleRules(salesRes.data);
      setCoupons(couponsRes.data);
      setWebhook(webhookRes.data);
      setOrderPage(1);
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "Không tải được dữ liệu.");
    } finally {
      setLoading(false);
    }
  }

  function login() {
    window.localStorage.setItem("prive_admin_secret", secret);
    setSavedSecret(secret);
  }

  function logout() {
    window.localStorage.removeItem("prive_admin_secret");
    setSavedSecret("");
    setSecret("");
  }

  async function saveFields(fields: ConfigField[]) {
    await runAction("fields", async () => {
      for (const field of fields) {
        await updateConfig(savedSecret, field.key, fieldValues[field.key] || "");
      }
      await loadAll();
    });
  }

  function resetGroupForm(nextGroupNo?: string) {
    const used = new Set(config.filter((item) => item.key.startsWith("BTN_G")).map((item) => item.key.replace("BTN_G", "")));
    const firstEmpty = Array.from({ length: GROUP_COUNT }, (_, idx) => String(idx + 1)).find((item) => !used.has(item)) || "1";
    setGroupNo(nextGroupNo || firstEmpty);
    setGroupName("");
    setGroupId("");
    setGroupPrice1m("");
    setGroupPriceLife("");
  }

  function fillGroupForm(nextGroupNo: string) {
    setGroupNo(nextGroupNo);
    setGroupName(getConfigValue(config, `BTN_G${nextGroupNo}`));
    setGroupId(getConfigValue(config, `ID_G${nextGroupNo}`));
    setGroupPrice1m(getConfigValue(config, `PRICE_G${nextGroupNo}_1M`));
    setGroupPriceLife(getConfigValue(config, `PRICE_G${nextGroupNo}_LIFE`));
  }

  async function saveGroupConfig() {
    await runAction("group", async () => {
      await updateConfig(savedSecret, `BTN_G${groupNo}`, groupName);
      await updateConfig(savedSecret, `ID_G${groupNo}`, groupId);
      await updateConfig(savedSecret, `PRICE_G${groupNo}_1M`, groupPrice1m);
      await updateConfig(savedSecret, `PRICE_G${groupNo}_LIFE`, groupPriceLife);
      setGroupName("");
      setGroupId("");
      setGroupPrice1m("");
      setGroupPriceLife("");
      await loadAll();
    });
  }

  async function removeGroupConfig() {
    if (!window.confirm(`Xoá toàn bộ cấu hình G${groupNo}? Coupon đang trỏ tới G${groupNo}_1M/G${groupNo}_LIFE sẽ không cấp được link.`)) return;
    await runAction("group-delete", async () => {
      for (const key of groupConfigKeys(groupNo)) {
        await deleteConfig(savedSecret, key);
      }
      resetGroupForm(groupNo);
      await loadAll();
    });
  }

  async function saveMenuPage() {
    await runAction("menu", async () => {
      await updateMenuPage(savedSecret, menuForm.page_id, menuForm);
      await loadAll();
    });
  }

  function resetMenuForm() {
    setMenuForm({ page_id: "", image_url: "", body: "", layout: "" });
  }

  async function removeMenuPage(pageId = menuForm.page_id) {
    if (!pageId || !window.confirm(`Xoá trang menu "${pageId}"?`)) return;
    await runAction(`menu-delete-${pageId}`, async () => {
      await deleteMenuPage(savedSecret, pageId);
      resetMenuForm();
      await loadAll();
    });
  }

  async function saveSaleRule() {
    await runAction("sale", async () => {
      await upsertSaleRule(savedSecret, saleForm);
      await loadAll();
    });
  }

  function resetSaleForm() {
    setSaleForm({ sale_id: "", price_key: "PRICE_SVIP_30D", discount_percent: "", sale_price: "", slot_limit: "", enabled: "ON", start_at: "", end_at: "" });
  }

  async function removeSaleRule(saleId = saleForm.sale_id) {
    if (!saleId || !window.confirm(`Xoá sale "${saleId}"?`)) return;
    await runAction(`sale-delete-${saleId}`, async () => {
      await deleteSaleRule(savedSecret, saleId);
      resetSaleForm();
      await loadAll();
    });
  }

  async function saveCoupon() {
    await runAction("coupon", async () => {
      const payload = { ...couponForm };
      if (!payload.Code) {
        const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
        const suffix = Array.from({ length: 8 }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join("");
        payload.Code = `HANGCU_${suffix}`;
      }
      if (payload.Code.length > 32) {
        throw new Error("Mã coupon nên tối đa 32 ký tự để nút Telegram hoạt động ổn định.");
      }
      if (payload.Coupon_Type === "DISCOUNT") {
        const percent = Number(payload.Discount_Percent || 0);
        if (!Number.isFinite(percent) || percent <= 0 || percent >= 100) {
          throw new Error("Coupon giảm giá cần phần trăm từ 1 đến 99. Muốn miễn phí hãy dùng loại Kích hoạt miễn phí.");
        }
      } else {
        const days = Number(payload.Duration_Days || 0);
        if (!Number.isFinite(days) || days <= 0) {
          throw new Error("Coupon kích hoạt cần số ngày sử dụng lớn hơn 0.");
        }
      }
      await createCoupon(savedSecret, payload);
      setCouponForm({ ...EMPTY_COUPON_FORM });
      await loadAll();
    });
  }

  function resetCouponForm() {
    setCouponForm({ ...EMPTY_COUPON_FORM });
  }

  function generateCouponCode() {
    const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
    const suffix = Array.from({ length: 8 }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join("");
    setCouponForm({ ...couponForm, Code: `HANGCU_${suffix}` });
  }

  function toggleCouponPlan(planKey: string) {
    const current = couponForm.Applies_To === "ALL" ? [] : couponForm.Applies_To.split(",").filter(Boolean);
    const next = current.includes(planKey) ? current.filter((item) => item !== planKey) : [...current, planKey];
    setCouponForm({ ...couponForm, Applies_To: next.length ? next.join(",") : "ALL" });
  }

  const usedCoupons = useMemo(() => coupons.filter((item) => item.max_uses && item.used_count >= item.max_uses), [coupons]);
  const [showUsedCoupons, setShowUsedCoupons] = useState(true);
  const visibleCoupons = useMemo(() => showUsedCoupons ? coupons : coupons.filter((item) => !(item.max_uses && item.used_count >= item.max_uses)), [coupons, showUsedCoupons]);

  async function removeCoupon(code = couponForm.Code) {
    if (!code || !window.confirm(`Xoá coupon "${code}"? Lịch sử đã dùng vẫn được giữ riêng trong hệ thống.`)) return;
    await runAction(`coupon-delete-${code}`, async () => {
      await deleteCoupon(savedSecret, code);
      resetCouponForm();
      await loadAll();
    });
  }

  async function removeUsedCoupons() {
    if (!usedCoupons.length) {
      showNotice("ok", "Không có coupon đã dùng hết để xoá.");
      return;
    }
    if (!window.confirm(`Xoá ${usedCoupons.length} coupon đã dùng hết? Lịch sử redemption vẫn được giữ riêng.`)) return;
    await runAction("coupon-delete-used", async () => {
      for (const coupon of usedCoupons) {
        await deleteCoupon(savedSecret, coupon.code);
      }
      resetCouponForm();
      await loadAll();
    });
  }

  async function changeOrderStatus(orderId: string, status: string) {
    await runAction(`order-${orderId}`, async () => {
      await updateOrderStatus(savedSecret, orderId, status);
      await loadAll();
    });
  }

  async function handleWebhookReset() {
    await runAction("webhook", async () => {
      const res = await resetWebhook(savedSecret);
      setWebhook(res.data);
    });
  }

  const metrics = useMemo(() => {
    const paid = orders.filter((item) => item.status === "PAID").length;
    const pending = orders.filter((item) => item.status === "PENDING").length;
    const revenue = orders.filter((item) => item.status === "PAID").reduce((sum, item) => sum + (item.amount || 0), 0);
    return { paid, pending, revenue, users: users.length, coupons: coupons.length, menu: menuPages.length };
  }, [orders, users, coupons, menuPages]);
  const todayStats = useMemo(() => orderStats(orders.filter((item) => isWithinPeriod(item.created_at, "today"))), [orders]);
  const monthStats = useMemo(() => orderStats(orders.filter((item) => isWithinPeriod(item.created_at, "month"))), [orders]);
  const yearStats = useMemo(() => orderStats(orders.filter((item) => isWithinPeriod(item.created_at, "year"))), [orders]);

  const configuredGroups = useMemo(() => Array.from({ length: GROUP_COUNT }, (_, idx) => idx + 1).filter((item) => isGroupConfigured(config, item)), [config]);
  const visibleGroups = useMemo(() => Array.from({ length: GROUP_COUNT }, (_, idx) => idx + 1).filter((item) => hasAnyGroupConfig(config, item)), [config]);
  const groupSelectOptions = useMemo(() => {
    const selected = Number(groupNo);
    const values = new Set(visibleGroups);
    if (selected >= 1 && selected <= GROUP_COUNT) values.add(selected);
    return Array.from(values).sort((a, b) => a - b);
  }, [groupNo, visibleGroups]);
  const planKeyOptions = useMemo(() => [
    ...PLAN_KEY_OPTIONS,
    ...SELECTABLE_GROUP_COUPON_OPTIONS,
    ...configuredGroups.flatMap((item) => [`G${item}_1M`, `G${item}_LIFE`]),
  ], [configuredGroups]);
  const discountPlanKeyOptions = useMemo(() => [
    ...PLAN_KEY_OPTIONS,
    ...configuredGroups.flatMap((item) => [`G${item}_1M`, `G${item}_LIFE`]),
  ], [configuredGroups]);
  const priceKeyOptions = useMemo(() => [
    ...PRICE_KEY_OPTIONS,
    ...configuredGroups.flatMap((item) => [`PRICE_G${item}_1M`, `PRICE_G${item}_LIFE`]),
  ], [configuredGroups]);
  const missingCore = useMemo(() => {
    const items = [];
    if (!webhook?.url) items.push("Webhook Telegram chưa hoạt động");
    if (configuredGroups.length === 0) items.push("Chưa cấu hình nhóm nhận link");
    if (!getConfigValue(config, "MSG_DELIVERY")) items.push("Chưa có tin gửi link sau thanh toán");
    return items;
  }, [config, configuredGroups.length, webhook]);

  const filteredOrders = useMemo(() => {
    return orders.filter((order) => {
      const text = `${order.order_id} ${order.full_name || ""} ${order.telegram_user_id} ${order.plan_name} ${order.coupon_code || ""}`.toLowerCase();
      const matchQuery = !query || text.includes(query.toLowerCase());
      const matchStatus = orderStatus === "ALL" || order.status === orderStatus;
      const matchPeriod = isWithinPeriod(order.created_at, orderPeriod);
      return matchQuery && matchStatus && matchPeriod;
    });
  }, [orders, query, orderStatus, orderPeriod]);
  const filteredOrderStats = useMemo(() => orderStats(filteredOrders), [filteredOrders]);
  const groupedFilteredOrders = useMemo(() => groupOrders(filteredOrders, orderGroupMode), [filteredOrders, orderGroupMode]);
  const totalOrderPages = Math.max(1, Math.ceil(filteredOrders.length / ORDER_PAGE_SIZE));
  const pagedOrders = useMemo(() => {
    const safePage = Math.min(orderPage, totalOrderPages);
    const start = (safePage - 1) * ORDER_PAGE_SIZE;
    return filteredOrders.slice(start, start + ORDER_PAGE_SIZE);
  }, [filteredOrders, orderPage, totalOrderPages]);

  useEffect(() => {
    setOrderPage(1);
  }, [query, orderStatus, orderPeriod, orderGroupMode]);

  function planOptionLabel(value: string) {
    if (value === "FULL_1M") return "SVIP chung - 1 tháng";
    if (value === "FULL_LIFE") return "SVIP chung - trọn đời";
    if (value === "SELECT_GROUP_1M") return "Khách tự chọn group lẻ - 1 tháng";
    if (value === "SELECT_GROUP_LIFE") return "Khách tự chọn group lẻ - trọn đời";
    const match = value.match(/^G(\d+)_(1M|LIFE)$/);
    if (!match) return value;
    const name = getConfigValue(config, `BTN_G${match[1]}`) || `Nhóm G${match[1]}`;
    return `${name} - ${match[2] === "1M" ? "1 tháng" : "trọn đời"}`;
  }

  function priceOptionLabel(value: string) {
    if (value === "PRICE_SVIP_30D") return "Giá SVIP chung - 1 tháng";
    if (value === "PRICE_SVIP_LIFE") return "Giá SVIP chung - trọn đời";
    const match = value.match(/^PRICE_G(\d+)_(1M|LIFE)$/);
    if (!match) return value;
    const name = getConfigValue(config, `BTN_G${match[1]}`) || `Nhóm G${match[1]}`;
    return `${name} - ${match[2] === "1M" ? "giá 1 tháng" : "giá trọn đời"}`;
  }

  function appliesLabel(value: string | undefined) {
    if (!value || value === "ALL") return "Tất cả gói";
    const labels = value.split(",").filter(Boolean).map((item) => planOptionLabel(item));
    if (labels.length <= 2) return labels.join(", ");
    return `${labels.slice(0, 2).join(", ")} +${labels.length - 2} gói`;
  }

  if (!savedSecret) {
    return (
      <main className="login-page">
        <section className="login-panel stack">
          <div>
            <h1>Prive Admin</h1>
            <p className="muted">Nhập mật khẩu admin đã đặt trong Render.</p>
          </div>
          <label className="field">
            <span>Mật khẩu admin</span>
            <input type="password" value={secret} onChange={(event) => setSecret(event.target.value)} placeholder="Dán ADMIN_SECRET tại đây" />
          </label>
          <button className="btn" onClick={login}>Đăng nhập</button>
        </section>
      </main>
    );
  }

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">Prive Admin</div>
        <div className="side-status">
          <span className={webhook?.url ? "dot ok" : "dot bad"} />
          {webhook?.url ? "Webhook đang bật" : "Webhook cần kiểm tra"}
        </div>
        <nav className="nav">
          <button className={tab === "overview" ? "active" : ""} onClick={() => setTab("overview")}><Activity size={18} /> Tổng quan</button>
          <button className={tab === "analytics" ? "active" : ""} onClick={() => setTab("analytics")}><BarChart3 size={18} /> Thống kê</button>
          <button className={tab === "setup" ? "active" : ""} onClick={() => setTab("setup")}><ShieldCheck size={18} /> Setup nhóm</button>
          <button className={tab === "orders" ? "active" : ""} onClick={() => setTab("orders")}><ShoppingCart size={18} /> Đơn hàng</button>
          <button className={tab === "content" ? "active" : ""} onClick={() => setTab("content")}><FileText size={18} /> Nội dung bot</button>
          <button className={tab === "coupons" ? "active" : ""} onClick={() => setTab("coupons")}><Ticket size={18} /> Coupon</button>
          <button className={tab === "sales" ? "active" : ""} onClick={() => setTab("sales")}><BadgePercent size={18} /> Sale</button>
          <button className={tab === "system" ? "active" : ""} onClick={() => setTab("system")}><Settings size={18} /> Hệ thống</button>
        </nav>
      </aside>

      <section className="main">
        <div className="topbar">
          <div>
            <h1 className="title">Quản lý bot Privé+</h1>
            <div className="muted">Dashboard vận hành: nhóm nhận link, đơn hàng, coupon, sale và nội dung bot.</div>
          </div>
          <div className="actions">
            <button className="btn secondary" onClick={() => loadAll()} disabled={loading}>
              {loading ? <Loader2 size={17} className="spin" /> : <RefreshCw size={17} />} Tải lại
            </button>
            <button className="btn ghost" onClick={logout}>Đăng xuất</button>
          </div>
        </div>

        {notice ? <div className={notice.type === "ok" ? "toast ok" : "toast error-toast"}>{notice.type === "ok" ? <CheckCircle2 size={18} /> : <XCircle size={18} />}{notice.text}</div> : null}

        {missingCore.length ? (
          <div className="warning">
            <strong>Cần hoàn tất cấu hình</strong>
            <span>{missingCore.join(" • ")}</span>
          </div>
        ) : null}

        {tab === "overview" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Doanh thu đã thanh toán" value={money(metrics.revenue)} />
              <Metric label="Đơn đang chờ" value={String(metrics.pending)} />
              <Metric label="Khách gần đây" value={String(metrics.users)} />
              <Metric label="Nhóm đang bán" value={String(configuredGroups.length)} />
            </div>
            <div className="grid">
              <Metric label="Doanh thu hôm nay" value={money(todayStats.revenue)} />
              <Metric label="Đơn PAID hôm nay" value={String(todayStats.paid)} />
              <Metric label="Doanh thu tháng này" value={money(monthStats.revenue)} />
              <Metric label="Tỉ lệ thanh toán tháng" value={`${monthStats.conversion}%`} />
            </div>
            <section className="panel">
              <PanelHead title="Trạng thái vận hành" subtitle="Kiểm tra nhanh các phần cần có trước khi bán." />
              <div className="status-grid">
                <HealthItem ok={Boolean(webhook?.url)} title="Telegram webhook" detail={webhook?.url || "Chưa set webhook"} />
                <HealthItem ok={configuredGroups.length > 0} title="Nhóm nhận link" detail={configuredGroups.length ? `Đã có ${configuredGroups.length} nhóm` : "Vào Setup nhóm để cấu hình"} />
                <HealthItem ok={metrics.menu > 0} title="Menu bot" detail={`${metrics.menu} trang menu`} />
                <HealthItem ok={metrics.coupons >= 0} title="Coupon" detail={`${metrics.coupons} mã trong hệ thống`} />
              </div>
            </section>
            <section className="panel">
              <PanelHead title="Đơn hàng mới nhất" subtitle="5 đơn gần nhất." />
              <OrdersTable orders={orders.slice(0, 5)} onStatusChange={changeOrderStatus} saving={saving} />
            </section>
          </div>
        ) : null}

        {tab === "analytics" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Hôm nay" value={money(todayStats.revenue)} />
              <Metric label="Tháng này" value={money(monthStats.revenue)} />
              <Metric label="Năm nay" value={money(yearStats.revenue)} />
              <Metric label="Khách đã trả tiền" value={String(yearStats.customers)} />
            </div>
            <div className="grid">
              <Metric label="Đơn PAID tháng" value={String(monthStats.paid)} />
              <Metric label="Đơn chờ tháng" value={String(monthStats.pending)} />
              <Metric label="AOV tháng" value={money(monthStats.averageOrder)} />
              <Metric label="Coupon giảm tháng" value={money(monthStats.discount)} />
            </div>
            <section className="panel">
              <PanelHead title="Theo dõi tăng trưởng" subtitle="Doanh thu, tỉ lệ thanh toán, khách trả tiền và giảm giá coupon theo từng ngày trong tháng." />
              <SummaryTable groups={groupOrders(orders.filter((item) => isWithinPeriod(item.created_at, "month")), "day")} />
            </section>
            <section className="panel">
              <PanelHead title="Tổng hợp theo tháng" subtitle="Dữ liệu năm hiện tại, không xoá đơn cũ." />
              <SummaryTable groups={groupOrders(orders.filter((item) => isWithinPeriod(item.created_at, "year")), "month")} />
            </section>
          </div>
        ) : null}

        {tab === "setup" ? (
          <div className="stack">
            <section className="panel">
              <PanelHead
                title="Setup nhóm nhận link"
                subtitle="Không cần nhớ key. Chọn G1, G2... rồi nhập tên nhóm và Telegram group ID."
                action={
                  <div className="panel-actions">
                    <button className="btn secondary" onClick={() => resetGroupForm()}><Plus size={16} /> Thêm nhóm mới</button>
                    <button className="btn danger" onClick={removeGroupConfig} disabled={saving === "group-delete"}><Trash2 size={16} /> Xoá nhóm</button>
                    <button className="btn" onClick={saveGroupConfig} disabled={saving === "group"}><Save size={16} /> Lưu nhóm</button>
                  </div>
                }
              />
              <div className="form-grid">
                <label className="field">
                  <span>Nhóm cần cấu hình</span>
                  <select value={groupNo} onChange={(event) => fillGroupForm(event.target.value)}>
                    {groupSelectOptions.map((item) => (
                      <option key={item} value={item}>
                        G{item}{visibleGroups.includes(item) ? "" : " - nhóm mới"}
                      </option>
                    ))}
                  </select>
                  <small>Coupon và sale sẽ hiện tên nhóm này trong dropdown, không cần nhớ mã kỹ thuật.</small>
                </label>
                <label className="field"><span>Tên nhóm hiển thị</span><input value={groupName} onChange={(event) => setGroupName(event.target.value)} placeholder={getConfigValue(config, `BTN_G${groupNo}`) || "VD: Nhóm 1 Privé+"} /></label>
                <label className="field"><span>Telegram group ID</span><input value={groupId} onChange={(event) => setGroupId(event.target.value)} placeholder={getConfigValue(config, `ID_G${groupNo}`) || "VD: -1001234567890"} /></label>
                <label className="field"><span>Giá 1 tháng</span><input value={groupPrice1m} onChange={(event) => setGroupPrice1m(event.target.value)} placeholder={getConfigValue(config, `PRICE_G${groupNo}_1M`) || "VD: 99000"} /></label>
                <label className="field"><span>Giá trọn đời</span><input value={groupPriceLife} onChange={(event) => setGroupPriceLife(event.target.value)} placeholder={getConfigValue(config, `PRICE_G${groupNo}_LIFE`) || "VD: 299000"} /></label>
              </div>
              <div className="hint">
                Muốn lấy group ID: thêm bot vào group, cho bot quyền tạo invite link, rồi dùng group id dạng <code>-100...</code>. Sau khi lưu, nhóm này sẽ xuất hiện bằng tên rõ ràng trong Coupon và Sale.
              </div>
            </section>
            <section className="panel">
              <PanelHead title="Danh sách nhóm" subtitle="Chỉ hiện những nhóm bạn đã thêm. Bấm Thêm nhóm mới để tạo G tiếp theo." />
              <div className="group-list">
                {visibleGroups.length ? visibleGroups.map((item) => {
                  const name = getConfigValue(config, `BTN_G${item}`);
                  const id = getConfigValue(config, `ID_G${item}`);
                  return (
                    <button className={name && id ? "group-row ok" : "group-row"} key={item} onClick={() => fillGroupForm(String(item))}>
                      <span>G{item}</span>
                      <strong>{name || "Chưa đặt tên"}</strong>
                      <em>{id || "Chưa có group ID"}</em>
                    </button>
                  );
                }) : <div className="empty-card">Chưa có nhóm nào. Bấm <strong>Thêm nhóm mới</strong>, nhập tên nhóm và Telegram group ID rồi lưu.</div>}
              </div>
            </section>
          </div>
        ) : null}

        {tab === "orders" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Doanh thu bộ lọc" value={money(filteredOrderStats.revenue)} />
              <Metric label="Đơn PAID" value={String(filteredOrderStats.paid)} />
              <Metric label="Đang chờ" value={String(filteredOrderStats.pending)} />
              <Metric label="Tỉ lệ thanh toán" value={`${filteredOrderStats.conversion}%`} />
            </div>
            <section className="panel">
              <PanelHead title="Đơn hàng" subtitle="Đơn được giữ lại lâu dài. Dùng bộ lọc, nhóm và phân trang để xem nhẹ hơn." />
              <div className="toolbar orders-toolbar">
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm mã đơn, tên khách, Telegram ID, tên gói, coupon..." />
                <select value={orderStatus} onChange={(event) => setOrderStatus(event.target.value)}>
                  <option value="ALL">Tất cả trạng thái</option>
                  <option value="PENDING">Đang chờ</option>
                  <option value="PAID">Đã thanh toán</option>
                  <option value="CANCELLED">Đã hủy</option>
                  <option value="EXPIRED">Hết hạn</option>
                </select>
                <select value={orderPeriod} onChange={(event) => setOrderPeriod(event.target.value as OrderPeriod)}>
                  <option value="today">Hôm nay</option>
                  <option value="7d">7 ngày gần đây</option>
                  <option value="month">Tháng này</option>
                  <option value="year">Năm nay</option>
                  <option value="all">Tất cả</option>
                </select>
                <select value={orderGroupMode} onChange={(event) => setOrderGroupMode(event.target.value as GroupMode)}>
                  <option value="day">Nhóm theo ngày</option>
                  <option value="month">Nhóm theo tháng</option>
                  <option value="none">Không nhóm</option>
                </select>
              </div>
              {orderGroupMode !== "none" ? <SummaryTable groups={groupedFilteredOrders} /> : null}
              <OrdersTable orders={pagedOrders} onStatusChange={changeOrderStatus} saving={saving} />
              <Pagination page={orderPage} totalPages={totalOrderPages} totalItems={filteredOrders.length} onPage={setOrderPage} />
            </section>
          </div>
        ) : null}

        {tab === "content" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="Nội dung Bot" subtitle="Tách từng nhóm cấu hình để dễ sửa. Bấm từng tab con bên dưới." />
              <div className="subtabs">
                <button className={contentTab === "bot" ? "active" : ""} onClick={() => setContentTab("bot")}>Cài đặt bot</button>
                <button className={contentTab === "plans" ? "active" : ""} onClick={() => setContentTab("plans")}>Gói & giá</button>
                <button className={contentTab === "support" ? "active" : ""} onClick={() => setContentTab("support")}>Support group</button>
                <button className={contentTab === "currency" ? "active" : ""} onClick={() => setContentTab("currency")}>Tiền tệ</button>
                <button className={contentTab === "buttons" ? "active" : ""} onClick={() => setContentTab("buttons")}>Nút bấm</button>
                <button className={contentTab === "alerts" ? "active" : ""} onClick={() => setContentTab("alerts")}>Cảnh báo</button>
                <button className={contentTab === "messages" ? "active" : ""} onClick={() => setContentTab("messages")}>Tin nhắn</button>
                <button className={contentTab === "saleContent" ? "active" : ""} onClick={() => setContentTab("saleContent")}>Flash sale</button>
                <button className={contentTab === "admin" ? "active" : ""} onClick={() => setContentTab("admin")}>Admin ID</button>
                <button className={contentTab === "menu" ? "active" : ""} onClick={() => setContentTab("menu")}>Menu Builder</button>
              </div>
            </section>
            {contentTab === "bot" ? <ConfigEditor title="Cài đặt bot" subtitle="Bảo trì, nhắc hạn, QR 5 phút và tần suất check thanh toán." fields={BOT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(BOT_FIELDS)} /> : null}
            {contentTab === "plans" ? <ConfigEditor title="Tên gói và giá SVIP" subtitle="Các gói chung không thuộc nhóm riêng. Nhóm riêng nằm ở Setup nhóm." fields={PLAN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(PLAN_FIELDS)} /> : null}
            {contentTab === "support" ? <ConfigEditor title="Support group" subtitle="Cấu hình nhóm hỗ trợ riêng. Link join chỉ dùng 1 lần; group này không bị kick khi hết hạn." fields={SUPPORT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(SUPPORT_FIELDS)} /> : null}
            {contentTab === "currency" ? <ConfigEditor title="Tiền tệ hiển thị" subtitle="Chỉ đổi cách hiển thị trong bot/UI. Số tiền QR PayOS vẫn giữ nguyên VND." fields={CURRENCY_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(CURRENCY_FIELDS)} /> : null}
            {contentTab === "buttons" ? <ConfigEditor title="Nút bấm trong bot" subtitle="Text các nút Telegram mặc định: thanh toán, quay lại, gia hạn, mua gói." fields={BUTTON_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(BUTTON_FIELDS)} /> : null}
            {contentTab === "alerts" ? <ConfigEditor title="Cảnh báo nhanh" subtitle="Các alert ngắn khi khách bấm nút, spam, hủy đơn, check QR." fields={ALERT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(ALERT_FIELDS)} /> : null}
            {contentTab === "messages" ? <ConfigEditor title="Tin nhắn tự động" subtitle="Các mẫu tin bot gửi cho khách. Placeholder được ghi rõ dưới từng ô." fields={MESSAGE_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(MESSAGE_FIELDS)} /> : null}
            {contentTab === "saleContent" ? <ConfigEditor title="Nội dung flash sale" subtitle="Bật/tắt thông báo sale, chỉnh banner, mẫu tin và nút dưới thông báo sale." fields={SALE_CONTENT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(SALE_CONTENT_FIELDS)} /> : null}
            {contentTab === "admin" ? <ConfigEditor title="Setup Admin ID" subtitle="Quản lý Telegram ID có quyền admin. Nhiều ID thì cách nhau bằng dấu phẩy." fields={ADMIN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(ADMIN_FIELDS)} /> : null}
            {contentTab === "menu" ? (
              <section className="panel">
                <PanelHead
                  title="Menu Builder"
                  subtitle="Soạn nội dung trang bot và layout nút bấm."
                  action={
                    <div className="panel-actions">
                      <button className="btn secondary" onClick={resetMenuForm}><Plus size={16} /> Thêm trang</button>
                      <button className="btn danger" onClick={() => removeMenuPage()} disabled={!menuForm.page_id}><Trash2 size={16} /> Xoá trang</button>
                      <button className="btn" onClick={saveMenuPage}><Save size={16} /> Lưu menu</button>
                    </div>
                  }
                />
                <div className="form-grid two">
                  <label className="field"><span>Tên trang</span><input value={menuForm.page_id} onChange={(event) => setMenuForm({ ...menuForm, page_id: event.target.value })} placeholder="VD: main_menu, support_page, policy_page" /></label>
                  <label className="field"><span>Ảnh cover</span><input value={menuForm.image_url} onChange={(event) => setMenuForm({ ...menuForm, image_url: event.target.value })} placeholder="File ID Telegram hoặc URL ảnh" /></label>
                  <label className="field wide"><span>Nội dung trang</span><textarea value={menuForm.body} onChange={(event) => setMenuForm({ ...menuForm, body: event.target.value })} placeholder="Nhập nội dung HTML. Có thể dùng {PRICE_SVIP_30D}, {SALE_LABEL_PRICE_SVIP_30D}..." /></label>
                  <label className="field wide"><span>Nút bấm</span><textarea value={menuForm.layout} onChange={(event) => setMenuForm({ ...menuForm, layout: event.target.value })} placeholder={"Mỗi dòng là một hàng nút. Ví dụ:\\nMua SVIP => buy_full_1m | Hỗ trợ => nav:support_page"} /></label>
                </div>
                <SimpleTable
                  headers={["Trang", "Nội dung", "Nút"]}
                  rows={menuPages.map((item) => [item.page_id, item.body, item.layout])}
                  onRow={(idx) => {
                    const item = menuPages[idx];
                    setMenuForm({ page_id: item.page_id, image_url: item.image_url || "", body: item.body || "", layout: item.layout || "" });
                  }}
                  actions={(idx) => (
                    <button className="icon-danger" onClick={(event) => { event.stopPropagation(); removeMenuPage(menuPages[idx].page_id); }} title="Xoá trang">
                      <Trash2 size={16} />
                    </button>
                  )}
                />
              </section>
            ) : null}
          </div>
        ) : null}

        {tab === "coupons" ? (
          <section className="panel">
            <PanelHead
              title="Coupon"
              subtitle="Tạo mã giảm giá hoặc mã kích hoạt. Chọn dòng bên dưới để sửa, hoặc bấm Thêm mới để tạo mã khác."
              action={
                <div className="panel-actions">
                  <button className="btn secondary" onClick={resetCouponForm}><Plus size={16} /> Thêm mới</button>
                  <button className="btn secondary" onClick={generateCouponCode}><RefreshCw size={16} /> Gen mã HANGCU_</button>
                  <button className="btn secondary" onClick={() => setShowUsedCoupons(!showUsedCoupons)}>{showUsedCoupons ? "Ẩn đã dùng" : "Hiện đã dùng"}</button>
                  <button className="btn danger" onClick={removeUsedCoupons} disabled={!usedCoupons.length}><Trash2 size={16} /> Xoá đã dùng</button>
                  <button className="btn danger" onClick={() => removeCoupon()} disabled={!couponForm.Code}><Trash2 size={16} /> Xoá coupon</button>
                  <button className="btn" onClick={saveCoupon}><Gift size={16} /> Lưu coupon</button>
                </div>
              }
            />
            <div className="form-grid">
              <label className="field"><span>Mã coupon</span><input value={couponForm.Code} onChange={(event) => setCouponForm({ ...couponForm, Code: event.target.value.toUpperCase() })} placeholder="VD: VIP2026" /></label>
              <label className="field"><span>Loại coupon</span><select value={couponForm.Coupon_Type} onChange={(event) => setCouponForm({ ...couponForm, Coupon_Type: event.target.value })}><option value="DISCOUNT">Giảm giá khi mua QR</option><option value="ACTIVATION">Kích hoạt miễn phí</option></select><small>Giảm giá: khách nhập mã rồi chọn gói để tạo QR đã trừ tiền. Kích hoạt: nhập mã là cấp link ngay.</small></label>
              {couponForm.Coupon_Type === "DISCOUNT" ? (
                <label className="field"><span>Phần trăm giảm</span><input value={couponForm.Discount_Percent} onChange={(event) => setCouponForm({ ...couponForm, Discount_Percent: event.target.value })} placeholder="VD: 15" /><small>Nhập 1-99. Nếu muốn miễn phí 100%, dùng loại Kích hoạt miễn phí.</small></label>
              ) : (
                <>
                  <label className="field"><span>Gói cấp cho khách</span><select value={couponForm.Plan_Name} onChange={(event) => setCouponForm({ ...couponForm, Plan_Name: event.target.value })}>{planKeyOptions.map((item) => <option key={item} value={item}>{planOptionLabel(item)}</option>)}</select><small>Chọn một gói cố định, hoặc để khách tự chọn group lẻ sau khi nhập mã.</small></label>
                  <label className="field"><span>Số ngày sử dụng</span><input value={couponForm.Duration_Days} onChange={(event) => setCouponForm({ ...couponForm, Duration_Days: event.target.value })} placeholder="VD: 30" /></label>
                </>
              )}
              <label className="field"><span>Số lượt dùng tối đa</span><input value={couponForm.Max_Uses} onChange={(event) => setCouponForm({ ...couponForm, Max_Uses: event.target.value })} placeholder="VD: 1" /></label>
              <label className="field"><span>Trạng thái</span><select value={couponForm.Enabled} onChange={(event) => setCouponForm({ ...couponForm, Enabled: event.target.value })}><option value="ON">Bật</option><option value="OFF">Tắt</option></select></label>
            </div>
            {couponForm.Coupon_Type === "DISCOUNT" ? (
              <div className="coupon-scope">
                <div className="coupon-scope-head">
                  <strong>Gói được áp dụng</strong>
                  <button className={couponForm.Applies_To === "ALL" ? "scope-pill active" : "scope-pill"} onClick={() => setCouponForm({ ...couponForm, Applies_To: "ALL" })}>Tất cả gói</button>
                </div>
                <div className="check-grid">
                  {discountPlanKeyOptions.map((item) => {
                    const selected = couponForm.Applies_To === "ALL" || couponForm.Applies_To.split(",").includes(item);
                    return (
                      <label className={selected ? "check-card active" : "check-card"} key={item}>
                        <input type="checkbox" checked={selected} onChange={() => toggleCouponPlan(item)} />
                        <span>{planOptionLabel(item)}</span>
                      </label>
                    );
                  })}
                </div>
              </div>
            ) : null}
            <SimpleTable
              headers={["Mã", "Loại", "Áp dụng / Gói", "Giảm", "Trạng thái", "Đã dùng", "Tối đa"]}
              rows={visibleCoupons.map((item) => [
                item.code,
                item.raw_data?.Coupon_Type === "DISCOUNT" ? "Giảm giá" : "Kích hoạt",
                item.raw_data?.Coupon_Type === "DISCOUNT" ? appliesLabel(item.raw_data?.Applies_To) : planOptionLabel(item.raw_data?.Plan_Name || item.plan_name || "-"),
                item.raw_data?.Coupon_Type === "DISCOUNT" ? `${item.raw_data?.Discount_Percent || 0}%` : "-",
                item.status,
                String(item.used_count),
                String(item.max_uses || "-"),
              ])}
              onRow={(idx) => {
                const item = visibleCoupons[idx];
                setCouponForm({
                  ...EMPTY_COUPON_FORM,
                  Code: item.code,
                  Coupon_Type: item.raw_data?.Coupon_Type || "ACTIVATION",
                  Plan_Name: item.raw_data?.Plan_Name || item.plan_name || "SELECT_GROUP_1M",
                  Duration_Days: item.raw_data?.Duration_Days || "30",
                  Discount_Percent: item.raw_data?.Discount_Percent || "10",
                  Applies_To: item.raw_data?.Applies_To || "ALL",
                  Max_Uses: String(item.max_uses || 1),
                  Enabled: item.status === "ACTIVE" ? "ON" : "OFF",
                });
              }}
              actions={(idx) => (
                <button className="icon-danger" onClick={(event) => { event.stopPropagation(); removeCoupon(visibleCoupons[idx].code); }} title="Xoá coupon">
                  <Trash2 size={16} />
                </button>
              )}
            />
          </section>
        ) : null}

        {tab === "sales" ? (
          <section className="panel">
            <PanelHead
              title="Sale rules"
              subtitle="Tạo giảm giá theo gói. Chọn dòng bên dưới để sửa, hoặc bấm Thêm sale để tạo chương trình mới."
              action={
                <div className="panel-actions">
                  <button className="btn secondary" onClick={resetSaleForm}><Plus size={16} /> Thêm sale</button>
                  <button className="btn danger" onClick={() => removeSaleRule()} disabled={!saleForm.sale_id}><Trash2 size={16} /> Xoá sale</button>
                  <button className="btn" onClick={saveSaleRule}><Save size={16} /> Lưu sale</button>
                </div>
              }
            />
            <div className="form-grid">
              <label className="field"><span>Tên chương trình sale</span><input value={saleForm.sale_id} onChange={(event) => setSaleForm({ ...saleForm, sale_id: event.target.value })} placeholder="VD: FLASH-G1-THANG-5" /></label>
              <label className="field"><span>Gói áp dụng</span><select value={saleForm.price_key} onChange={(event) => setSaleForm({ ...saleForm, price_key: event.target.value })}>{priceKeyOptions.map((item) => <option key={item} value={item}>{priceOptionLabel(item)}</option>)}</select><small>Chỉ hiện nhóm đã setup, cộng với SVIP chung.</small></label>
              <label className="field"><span>Giảm theo phần trăm</span><input value={saleForm.discount_percent} onChange={(event) => setSaleForm({ ...saleForm, discount_percent: event.target.value })} placeholder="VD: 20" /></label>
              <label className="field"><span>Hoặc giá sale cố định</span><input value={saleForm.sale_price} onChange={(event) => setSaleForm({ ...saleForm, sale_price: event.target.value })} placeholder="VD: 79000" /></label>
              <label className="field"><span>Giới hạn slot</span><input value={saleForm.slot_limit} onChange={(event) => setSaleForm({ ...saleForm, slot_limit: event.target.value })} placeholder="Để trống hoặc 0 nếu không giới hạn" /></label>
              <label className="field"><span>Trạng thái</span><select value={saleForm.enabled} onChange={(event) => setSaleForm({ ...saleForm, enabled: event.target.value })}><option value="ON">Bật</option><option value="OFF">Tắt</option></select></label>
            </div>
            <SimpleTable
              headers={["Sale", "Gói", "Giảm %", "Giá sale", "Slot", "Bật"]}
              rows={saleRules.map((item) => [item.sale_id, item.price_key, String(item.discount_percent || "-"), String(item.sale_price || "-"), String(item.slot_limit || "-"), item.enabled ? "ON" : "OFF"])}
              onRow={(idx) => {
                const item = saleRules[idx];
                setSaleForm({ sale_id: item.sale_id, price_key: item.price_key, discount_percent: String(item.discount_percent || ""), sale_price: String(item.sale_price || ""), slot_limit: String(item.slot_limit || ""), enabled: item.enabled ? "ON" : "OFF", start_at: item.starts_at || "", end_at: item.ends_at || "" });
              }}
              actions={(idx) => (
                <button className="icon-danger" onClick={(event) => { event.stopPropagation(); removeSaleRule(saleRules[idx].sale_id); }} title="Xoá sale">
                  <Trash2 size={16} />
                </button>
              )}
            />
          </section>
        ) : null}

        {tab === "system" ? (
          <div className="stack">
            <section className="panel">
              <PanelHead title="Telegram webhook" subtitle="Nếu bot không phản hồi, kiểm tra và reset webhook tại đây." action={<button className="btn" onClick={handleWebhookReset}><RefreshCw size={16} /> Reset webhook</button>} />
              <div className="system-list">
                <Info label="Webhook URL" value={webhook?.url || "Chưa cấu hình"} />
                <Info label="Update đang chờ" value={String(webhook?.pending_update_count ?? 0)} />
                <Info label="Lỗi gần nhất" value={webhook?.last_error_message || "Không có"} />
              </div>
            </section>
            <section className="panel">
              <PanelHead title="Raw config" subtitle="Chỉ dùng khi cần kiểm tra sâu. Các form phía trên đã che key kỹ thuật." />
              <SimpleTable headers={["Tên kỹ thuật", "Giá trị"]} rows={config.map((item) => [item.key, item.value])} />
            </section>
          </div>
        ) : null}
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return <div className="card"><div className="muted">{label}</div><div className="metric">{value}</div></div>;
}

function PanelHead({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return <div className="panel-head"><div><strong>{title}</strong>{subtitle ? <div className="muted">{subtitle}</div> : null}</div>{action}</div>;
}

function HealthItem({ ok, title, detail }: { ok: boolean; title: string; detail: string }) {
  return <div className="health-item">{ok ? <CheckCircle2 className="good" size={20} /> : <XCircle className="bad" size={20} />}<div><strong>{title}</strong><span>{detail}</span></div></div>;
}

function Info({ label, value }: { label: string; value: string }) {
  return <div className="info-row"><span>{label}</span><strong>{value}</strong></div>;
}

function ConfigEditor({ title, subtitle, fields, values, setValues, onSave }: { title: string; subtitle: string; fields: ConfigField[]; values: Record<string, string>; setValues: (values: Record<string, string>) => void; onSave: () => void }) {
  return (
    <section className="panel">
      <PanelHead title={title} subtitle={subtitle} action={<button className="btn" onClick={onSave}><Save size={16} /> Lưu</button>} />
      <div className="form-grid two">
        {fields.map((field) => (
          <label className={field.kind === "textarea" ? "field wide" : "field"} key={field.key}>
            <span>{field.label}</span>
            {field.kind === "textarea" ? (
              <textarea value={values[field.key] || ""} onChange={(event) => setValues({ ...values, [field.key]: event.target.value })} placeholder={field.placeholder} />
            ) : field.kind === "select" ? (
              <select value={values[field.key] || field.placeholder} onChange={(event) => setValues({ ...values, [field.key]: event.target.value })}>
                {(field.options || []).map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
              </select>
            ) : (
              <input value={values[field.key] || ""} onChange={(event) => setValues({ ...values, [field.key]: event.target.value })} placeholder={field.placeholder} />
            )}
            <small>{field.help}</small>
          </label>
        ))}
      </div>
    </section>
  );
}

function OrdersTable({ orders, onStatusChange, saving }: { orders: Order[]; onStatusChange: (orderId: string, status: string) => void; saving: string }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Mã đơn</th><th>Khách</th><th>Gói</th><th>Tiền</th><th>Coupon</th><th>Trạng thái</th><th>Tạo lúc</th><th>Đổi trạng thái</th></tr></thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.order_id}>
              <td>{order.order_id}</td>
              <td><strong>{order.full_name || "-"}</strong><div className="muted">{order.telegram_user_id}</div></td>
              <td>{order.plan_name}</td>
              <td>{money(order.amount)}</td>
              <td>{order.coupon_code ? <><strong>{order.coupon_code}</strong><div className="muted">-{order.coupon_discount_percent || 0}% / {money(order.coupon_discount_amount || 0)}</div></> : "-"}</td>
              <td><span className={statusClass(order.status)}>{order.status}</span></td>
              <td>{dateText(order.created_at)}</td>
              <td>
                <select value={order.status} disabled={saving === `order-${order.order_id}`} onChange={(event) => onStatusChange(order.order_id, event.target.value)}>
                  <option value="PENDING">Đang chờ</option>
                  <option value="PAID">Đã thanh toán</option>
                  <option value="CANCELLED">Đã hủy</option>
                  <option value="EXPIRED">Hết hạn</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SummaryTable({ groups }: { groups: { label: string; items: Order[]; stats: ReturnType<typeof orderStats> }[] }) {
  return (
    <div className="table-wrap summary-wrap">
      <table>
        <thead><tr><th>Kỳ</th><th>Doanh thu</th><th>PAID</th><th>PENDING</th><th>Huỷ/Hết hạn</th><th>Khách trả tiền</th><th>AOV</th><th>Coupon giảm</th><th>Tỉ lệ thanh toán</th></tr></thead>
        <tbody>
          {groups.length ? groups.map((group) => (
            <tr key={group.label}>
              <td><strong>{group.label}</strong><div className="muted">{group.items.length} đơn</div></td>
              <td>{money(group.stats.revenue)}</td>
              <td>{group.stats.paid}</td>
              <td>{group.stats.pending}</td>
              <td>{group.stats.cancelled + group.stats.expired}</td>
              <td>{group.stats.customers}</td>
              <td>{money(group.stats.averageOrder)}</td>
              <td>{money(group.stats.discount)}</td>
              <td>{group.stats.conversion}%</td>
            </tr>
          )) : (
            <tr><td colSpan={9} className="empty-state">Chưa có dữ liệu trong kỳ này.</td></tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function Pagination({ page, totalPages, totalItems, onPage }: { page: number; totalPages: number; totalItems: number; onPage: (page: number) => void }) {
  const safePage = Math.min(page, totalPages);
  return (
    <div className="pagination">
      <span>{totalItems} đơn • Trang {safePage}/{totalPages}</span>
      <div>
        <button className="btn secondary" disabled={safePage <= 1} onClick={() => onPage(safePage - 1)}>Trước</button>
        <button className="btn secondary" disabled={safePage >= totalPages} onClick={() => onPage(safePage + 1)}>Sau</button>
      </div>
    </div>
  );
}

function SimpleTable({ headers, rows, onRow, actions }: { headers: string[]; rows: string[][]; onRow?: (index: number) => void; actions?: (index: number) => ReactNode }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{headers.map((item) => <th key={item}>{item}</th>)}{actions ? <th>Thao tác</th> : null}</tr></thead>
        <tbody>
          {rows.length ? rows.map((row, idx) => (
            <tr key={idx} onClick={() => onRow?.(idx)} className={onRow ? "clickable-row" : ""}>
              {row.map((cell, cellIdx) => <td key={cellIdx}>{cell}</td>)}
              {actions ? <td className="table-action">{actions(idx)}</td> : null}
            </tr>
          )) : (
            <tr>
              <td colSpan={headers.length + (actions ? 1 : 0)} className="empty-state">Chưa có dữ liệu. Bấm nút thêm mới để tạo.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
