"use client";

import {
  Activity,
  BadgePercent,
  BarChart3,
  CheckCircle2,
  ClipboardList,
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
  Users,
  XCircle,
} from "lucide-react";
import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import {
  ActivityEvent,
  ConfigRow,
  BlacklistEntry,
  Coupon,
  ManualOrderResult,
  MenuPage,
  Order,
  SaleRule,
  SupportEvent,
  UserRow,
  WebhookInfo,
  checkSupportGroup,
  createCoupon,
  createCoupons,
  createManualOrder,
  deleteConfig,
  deleteBlacklist,
  deleteCoupon,
  deleteMenuPage,
  deleteSaleRule,
  getConfig,
  getActivityEvents,
  getBlacklist,
  getCoupons,
  getMenuPages,
  getOrders,
  getSaleRules,
  getSupportEvents,
  getUsers,
  getWebhookInfo,
  resetWebhook,
  updateConfig,
  updateConfigs,
  updateMenuPage,
  updateOrder,
  updateOrderStatus,
  upsertBlacklist,
  upsertSaleRule,
  type SupportGroupCheck,
} from "@/lib/api";

type Tab = "overview" | "analytics" | "setup" | "orders" | "customers" | "activityLog" | "renewals" | "supportGroup" | "content" | "coupons" | "security" | "sales" | "system";
type ContentSubTab = "bot" | "plans" | "currency" | "buttons" | "commands" | "alerts" | "messages" | "saleContent" | "admin" | "menu";
type OrderPeriod = "all" | "today" | "7d" | "month" | "year";
type GroupMode = "none" | "day" | "month";
type CustomerStatusFilter = "all" | "active" | "expired" | "paid" | "coupon";
type LogDirectionFilter = "all" | "user" | "bot";
type RenewalSubTab = "soon" | "today" | "reminded" | "expiredNotice" | "kicked";
type SupportSubTab = "all" | "joined" | "left" | "muted" | "kicked";
type CouponTab = "unsent" | "sent" | "used" | "expired";

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

const DEFAULT_GROUP_COUNT = 20;

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
    key: "BOT_TIMEZONE",
    label: "Timezone bot",
    placeholder: "Asia/Ho_Chi_Minh",
    help: "Dùng cho scheduler nhắc hạn, hết hạn và dashboard theo ngày.",
  },
  {
    key: "GROUP_COUNT",
    label: "Số group tối đa",
    placeholder: "20",
    help: "Số lượng G1, G2... dashboard và bot sẽ quét. Tăng nếu bạn bán hơn 20 nhóm.",
  },
];

const RENEWAL_FIELDS: ConfigField[] = [
  {
    key: "REMINDER_ENABLED",
    label: "Bật nhắc gia hạn",
    placeholder: "ON",
    help: "Bật ON để scheduler gửi tin nhắc trước khi hết hạn.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "REMINDER_DAYS",
    label: "Nhắc trước khi hết hạn",
    placeholder: "3",
    help: "Số ngày trước khi hết hạn bot sẽ nhắc khách gia hạn.",
  },
  {
    key: "EXPIRED_NOTICE_ENABLED",
    label: "Bật tin báo hết hạn",
    placeholder: "ON",
    help: "Bật ON để bot gửi tin báo khi gói vừa hết hạn.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
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
    key: "EARLY_RENEW",
    label: "Gia hạn sớm legacy",
    placeholder: "ON",
    help: "Key tương thích cũ. Nếu không dùng, đặt giống Ưu đãi gia hạn sớm.",
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
  {
    key: "EARLY_RENEW_DAYS",
    label: "Số ngày được gia hạn sớm",
    placeholder: "3",
    help: "Số ngày trước khi hết hạn sẽ hiện offer gia hạn sớm. Để cùng REMINDER_DAYS nếu muốn đồng bộ.",
  },
  {
    key: "RENEWAL_DISCOUNT_PERCENT",
    label: "Giảm giá gia hạn legacy",
    placeholder: "10",
    help: "Key tương thích cũ. Nếu không dùng, đặt giống Giảm giá gia hạn sớm.",
  },
  {
    key: "MSG_REMINDER",
    label: "Tin nhắc sắp hết hạn",
    placeholder: "Gói {plan} sẽ hết hạn sau {days} ngày.",
    help: "Dùng biến {plan}, {days}, {date}.",
    kind: "textarea",
  },
  {
    key: "MSG_EXPIRED",
    label: "Tin gói hết hạn",
    placeholder: "Gói {plan} của bạn đã hết hạn.",
    help: "Dùng biến {plan}, {date}, {grace_days}.",
    kind: "textarea",
  },
  {
    key: "BTN_EARLY_RENEW",
    label: "Nút gia hạn sớm",
    placeholder: "🔥 Gia hạn sớm -{percent}%",
    help: "Text nút ưu đãi gia hạn sớm.",
  },
  {
    key: "BTN_RENEW_FULL",
    label: "Nút gia hạn SVIP",
    placeholder: "🌟 Gia hạn / Lên Trọn Đời",
    help: "Text nút gia hạn cho gói SVIP/full.",
  },
  {
    key: "BTN_RENEW_GROUP",
    label: "Nút gia hạn group",
    placeholder: "🔄 Gia hạn / Mở rộng gói",
    help: "Text nút gia hạn cho gói group lẻ.",
  },
  {
    key: "MSG_EARLY_RENEW_OFFER",
    label: "Block ưu đãi gia hạn sớm",
    placeholder: "🔥 <b>ƯU ĐÃI GIA HẠN SỚM</b>\\nGói hiện tại: <b>{plan}</b>\\nGiá gốc: <s>{old_price}</s>\\nGiá gia hạn sớm: <b>{renew_price}</b> (-{discount_percent}%)",
    help: "Dùng biến {plan}, {old_price}, {renew_price}, {discount_percent}, {date}, {countdown}.",
    kind: "textarea",
  },
];

const SECURITY_FIELDS: ConfigField[] = [
  {
    key: "BLACKLIST_ENABLED",
    label: "Bật blacklist",
    placeholder: "ON",
    help: "Bật ON để bot chặn các Telegram ID trong danh sách blacklist.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "BLACKLIST_NOTIFY_USER",
    label: "Thông báo khi bị chặn",
    placeholder: "ON",
    help: "Nếu bật, bot gửi tin nhắn chặn trong private chat. Callback luôn hiện alert ngắn.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "MSG_BLACKLIST_BLOCKED",
    label: "Tin nhắn bị blacklist",
    placeholder: "⛔ Tài khoản của bạn đang bị chặn sử dụng bot.",
    help: "Tin gửi khi user nằm trong blacklist.",
    kind: "textarea",
  },
  {
    key: "SELLER_BIO_LINK_BLOCK_ENABLED",
    label: "Tự chặn bio có link",
    placeholder: "OFF",
    help: "Bot sẽ đọc bio theo khả năng Telegram cho phép. Nếu bio chứa pattern bên dưới, user sẽ được thêm vào blacklist.",
    kind: "select",
    options: [
      { label: "Tắt", value: "OFF" },
      { label: "Bật", value: "ON" },
    ],
  },
  {
    key: "SELLER_BIO_LINK_PATTERNS",
    label: "Pattern link bio cần chặn",
    placeholder: "http://,https://,t.me/,telegram.me/,linktr.ee",
    help: "Cách nhau bằng dấu phẩy. Nên để cụ thể để tránh chặn nhầm.",
  },
  {
    key: "BIO_LINK_CHECK_TTL_SECONDS",
    label: "Chu kỳ kiểm tra bio",
    placeholder: "86400",
    help: "Số giây cache kiểm tra bio mỗi user. 86400 = 1 ngày.",
  },
  {
    key: "COUPON_MENU_ENABLED",
    label: "Hiện nút nhập coupon trong menu",
    placeholder: "OFF",
    help: "OFF sẽ ẩn các nút Menu Builder có action coupon_enter, coupon_code, redeem_code.",
    kind: "select",
    options: [
      { label: "Ẩn", value: "OFF" },
      { label: "Hiện", value: "ON" },
    ],
  },
  {
    key: "COUPON_COMMAND_ENABLED",
    label: "Hiện lệnh /coupon",
    placeholder: "OFF",
    help: "OFF sẽ không đưa /coupon vào danh sách lệnh Telegram và bỏ qua lệnh này từ khách.",
    kind: "select",
    options: [
      { label: "Ẩn", value: "OFF" },
      { label: "Hiện", value: "ON" },
    ],
  },
  {
    key: "COUPON_AUTO_REDEEM_ENABLED",
    label: "Tự nhận diện mã coupon",
    placeholder: "ON",
    help: "Bật ON để khách chỉ cần nhắn mã bắt đầu bằng prefix, không cần bấm menu nhập mã.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "COUPON_AUTO_REDEEM_PREFIXES",
    label: "Prefix tự nhận diện coupon",
    placeholder: "HANGCU_",
    help: "Nhiều prefix thì cách nhau bằng dấu phẩy. Ví dụ: HANGCU_,VIP_",
  },
  {
    key: "COUPON_ABUSE_ENABLED",
    label: "Chống dò coupon",
    placeholder: "ON",
    help: "Giới hạn số lần nhập coupon theo cửa sổ thời gian.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "COUPON_MAX_ATTEMPTS",
    label: "Số lần nhập tối đa",
    placeholder: "5",
    help: "Vượt số lần này trong cửa sổ thời gian sẽ bị khóa tạm.",
  },
  {
    key: "COUPON_WINDOW_SECONDS",
    label: "Cửa sổ tính lượt nhập",
    placeholder: "600",
    help: "600 giây = 10 phút.",
  },
  {
    key: "COUPON_LOCK_MINUTES",
    label: "Thời gian khóa nhập coupon",
    placeholder: "30",
    help: "Số phút chặn nhập coupon khi vượt giới hạn.",
  },
  {
    key: "COUPON_ABUSE_NOTIFY_USER",
    label: "Báo khách khi bị khóa coupon",
    placeholder: "ON",
    help: "Bật để gửi tin nhắn khi user bị giới hạn nhập coupon.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "MSG_COUPON_RATE_LIMITED",
    label: "Tin giới hạn coupon",
    placeholder: "⛔ Bạn nhập mã quá nhiều lần. Vui lòng thử lại sau {minutes} phút.",
    help: "Dùng biến {minutes}.",
    kind: "textarea",
  },
  {
    key: "COUPON_ABUSE_AUTO_BLACKLIST",
    label: "Tự blacklist khi dò coupon",
    placeholder: "OFF",
    help: "Chỉ bật nếu muốn tự đưa user vượt giới hạn vào blacklist.",
    kind: "select",
    options: [
      { label: "Tắt", value: "OFF" },
      { label: "Bật", value: "ON" },
    ],
  },
];

const SYSTEM_FIELDS: ConfigField[] = [
  {
    key: "SCHEDULER_INITIAL_DELAY_SECONDS",
    label: "Delay scheduler khi boot",
    placeholder: "10",
    help: "Số giây chờ trước vòng quét hạn đầu tiên sau khi backend khởi động.",
  },
  {
    key: "SCHEDULER_INTERVAL_SECONDS",
    label: "Chu kỳ quét hạn",
    placeholder: "60",
    help: "Số giây giữa các vòng quét hạn/gia hạn. Backend giới hạn tối đa 60 giây để kick kịp thời.",
  },
  {
    key: "SCHEDULER_ORDER_LIMIT",
    label: "Số đơn PAID quét mỗi vòng",
    placeholder: "5000",
    help: "Tăng nếu dữ liệu lớn để scheduler vẫn thấy cả đơn cũ hết hạn và đơn gia hạn/trọn đời mới.",
  },
  {
    key: "MAINTENANCE_INITIAL_DELAY_SECONDS",
    label: "Delay maintenance khi boot",
    placeholder: "300",
    help: "Số giây chờ trước vòng dọn dẹp đầu tiên.",
  },
  {
    key: "MAINTENANCE_INTERVAL_SECONDS",
    label: "Chu kỳ maintenance",
    placeholder: "43200",
    help: "Số giây giữa các vòng dọn dẹp. 43200 = 12 tiếng.",
  },
  {
    key: "PENDING_ORDER_MAX_AGE_SECONDS",
    label: "Tuổi tối đa đơn pending",
    placeholder: "2592000",
    help: "Đơn pending quá số giây này sẽ bị huỷ/dọn. 2592000 = 30 ngày.",
  },
  {
    key: "SHEET_DELETE_DELAY_SECONDS",
    label: "Delay xoá dòng Sheet",
    placeholder: "2",
    help: "Chỉ dùng khi chạy Google Sheet fallback.",
  },
  {
    key: "SHEET_APPEND_DELAY_SECONDS",
    label: "Delay ghi dòng Sheet",
    placeholder: "1",
    help: "Chỉ dùng khi chạy Google Sheet fallback.",
  },
  {
    key: "COUPON_CLEANUP_INITIAL_DELAY_SECONDS",
    label: "Delay cleanup coupon khi boot",
    placeholder: "30",
    help: "Số giây chờ trước worker cleanup coupon.",
  },
  {
    key: "COUPON_CLEANUP_INTERVAL_HOURS",
    label: "Chu kỳ cleanup coupon",
    placeholder: "12",
    help: "Số giờ giữa các lần cleanup coupon khi dùng Sheet fallback.",
  },
  {
    key: "COUPON_CLEANUP_AFTER_DAYS",
    label: "Số ngày giữ coupon đã dùng",
    placeholder: "7",
    help: "Dùng cho cleanup coupon ở Sheet fallback.",
  },
  {
    key: "ANALYTICS_DAILY_RETENTION_DAYS",
    label: "Số ngày giữ analytics ngày",
    placeholder: "120",
    help: "Giới hạn dữ liệu analytics daily giữ lại.",
  },
];

const COMMAND_FIELDS: ConfigField[] = [
  { key: "BOT_COMMAND_DESC_START", label: "Mô tả /start", placeholder: "Trang chủ / Mua gói", help: "Mô tả lệnh Telegram." },
  { key: "BOT_COMMAND_DESC_ME", label: "Mô tả /me", placeholder: "Kiểm tra gói & Hạn dùng", help: "Mô tả lệnh Telegram." },
  { key: "BOT_COMMAND_DESC_COUPON", label: "Mô tả /coupon", placeholder: "Nhập mã giảm giá / mã kích hoạt", help: "Chỉ hiện khi bật lệnh /coupon." },
  { key: "BOT_COMMAND_DESC_SUPPORT", label: "Mô tả /support", placeholder: "Liên hệ hỗ trợ Admin", help: "Mô tả lệnh Telegram." },
  { key: "BOT_COMMAND_DESC_POLICY", label: "Mô tả /policy", placeholder: "Đọc quy định nhóm", help: "Mô tả lệnh Telegram." },
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
    key: "SUPPORT_GROUP_MUTE_ENABLED",
    label: "Mute khi hết hạn",
    placeholder: "ON",
    help: "Bật ON để user hết hạn bị mute trong các group trả phí trước khi kick.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
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
    placeholder: "Mã: {code}\\nThời hạn: {duration_label}\\nChọn group bạn muốn kích hoạt bên dưới.",
    help: "Dùng khi coupon kích hoạt cho phép khách tự chọn group lẻ. Dùng biến {code}, {days}, {duration_label}.",
    kind: "textarea",
  },
  {
    key: "COUPON_ACTIVATION_PLAN_TEMPLATE",
    label: "Tên gói coupon kích hoạt",
    placeholder: "VIP {duration_label} - {group}",
    help: "Tên lưu vào đơn và hiển thị khi kích hoạt coupon chọn group. Dùng {duration_label}, {days}, {group}.",
  },
  {
    key: "COUPON_ACTIVATION_BUTTON_TEMPLATE",
    label: "Nút chọn group coupon",
    placeholder: "{plan_name}",
    help: "Text nút chọn group sau khi nhập coupon. Dùng {plan_name}, {duration_label}, {days}, {group}.",
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
  {
    key: "MSG_RELOAD_DONE",
    label: "Tin admin reload xong",
    placeholder: "🔄 Đã nạp lại toàn bộ dữ liệu & Giao diện từ Sheet!",
    help: "Tin trả về khi admin dùng /reload.",
  },
  {
    key: "MSG_ADMIN_ONLY",
    label: "Tin lệnh chỉ admin",
    placeholder: "⚠️ Lệnh này chỉ dành cho Admin.",
    help: "Dùng khi user thường gọi lệnh admin.",
  },
  {
    key: "MSG_CHECK_EXPIRY_STARTED",
    label: "Tin bắt đầu quét hạn",
    placeholder: "⏳ Đang quét hạn dùng ngay bây giờ...",
    help: "Tin trả về khi admin chạy /check_expiry.",
  },
  {
    key: "MSG_CHECK_EXPIRY_DONE",
    label: "Tin quét hạn xong",
    placeholder: "✅ Đã chạy xong một vòng quét hạn dùng.",
    help: "Tin trả về khi /check_expiry hoàn tất.",
  },
  {
    key: "MSG_EARLY_RENEW_STATUS",
    label: "Tin trạng thái early renew",
    placeholder: "EARLY_RENEW hiện đang: <b>{status}</b>\\nDùng: /early_renew on hoặc /early_renew off",
    help: "Dùng biến {status}.",
    kind: "textarea",
  },
  {
    key: "MSG_EARLY_RENEW_ON",
    label: "Tin bật early renew",
    placeholder: "✅ Đã bật EARLY_RENEW. Tin nhắc gia hạn sẽ kèm ưu đãi nếu đủ điều kiện.",
    help: "Tin trả về khi admin bật /early_renew.",
  },
  {
    key: "MSG_EARLY_RENEW_OFF",
    label: "Tin tắt early renew",
    placeholder: "✅ Đã tắt EARLY_RENEW. Tin nhắc gia hạn sẽ dùng nội dung và nút gia hạn thường.",
    help: "Tin trả về khi admin tắt /early_renew.",
  },
  {
    key: "MSG_EARLY_RENEW_USAGE",
    label: "Tin cú pháp early renew",
    placeholder: "Cú pháp: /early_renew on hoặc /early_renew off",
    help: "Tin trả về khi sai cú pháp /early_renew.",
  },
  {
    key: "MSG_COUPON_NO_SELECTABLE_GROUPS",
    label: "Tin coupon thiếu group chọn",
    placeholder: "❌ Mã hợp lệ nhưng chưa có group lẻ nào được cấu hình để khách chọn.",
    help: "Dùng khi coupon chọn group nhưng dashboard chưa cấu hình group.",
  },
  {
    key: "MSG_COUPON_PLAN_NOT_CONFIGURED",
    label: "Tin coupon thiếu group cấp link",
    placeholder: "❌ Mã hợp lệ nhưng gói này chưa cấu hình nhóm nhận link.",
    help: "Dùng khi coupon hợp lệ nhưng không tạo được link vì thiếu group.",
  },
  {
    key: "MSG_COUPON_PRIVATE_ONLY",
    label: "Tin coupon chỉ private",
    placeholder: "Vui lòng nhắn riêng với bot để nhập mã, tránh lộ mã trong group.",
    help: "Tin gửi khi khách nhập coupon trong group.",
  },
  {
    key: "MSG_COUPON_INVALID_FORMAT",
    label: "Tin format coupon sai",
    placeholder: "Mã không hợp lệ. Vui lòng nhập lại mã bạn nhận được.",
    help: "Tin gửi khi mã quá ngắn hoặc rỗng.",
  },
  {
    key: "TXT_SVIP_DESCRIPTION",
    label: "Mô tả trang SVIP",
    placeholder: "🔥 <b>ĐẶC QUYỀN SVIP+ TRỌN BỘ</b> 🔥\\n\\n👇 <i>Chọn gói đăng ký bên dưới:</i>",
    help: "Nội dung trang gói SVIP fallback nếu chưa dùng Menu Builder.",
    kind: "textarea",
  },
  {
    key: "IMG_SVIP_PAGE",
    label: "Ảnh trang SVIP",
    placeholder: "File ID Telegram hoặc URL ảnh",
    help: "Ảnh cover trang SVIP fallback.",
  },
  {
    key: "IMG_POLICY",
    label: "Ảnh trang policy",
    placeholder: "File ID Telegram hoặc URL ảnh",
    help: "Ảnh fallback cho trang policy.",
  },
  {
    key: "IMG_SUPPORT",
    label: "Ảnh trang support",
    placeholder: "File ID Telegram hoặc URL ảnh",
    help: "Ảnh fallback cho trang support.",
  },
  {
    key: "IMG_ME",
    label: "Ảnh trang /me",
    placeholder: "File ID Telegram hoặc URL ảnh",
    help: "Ảnh fallback cho trang tài khoản /me.",
  },
];

const BUTTON_FIELDS: ConfigField[] = [
  { key: "BTN_BACK", label: "Nút quay lại", placeholder: "🔙 Quay lại Menu", help: "Dùng ở hầu hết trang bot." },
  { key: "BTN_CHECK_PAYMENT", label: "Nút đã chuyển khoản", placeholder: "🔄 Đã chuyển khoản", help: "Nút dưới QR để khách check thủ công." },
  { key: "BTN_CANCEL_ORDER", label: "Nút hủy đơn", placeholder: "❌ Hủy", help: "Nút dưới QR để hủy đơn pending." },
  { key: "BTN_VIEW_QR", label: "Nút xem QR", placeholder: "🖼 Xem QR", help: "Dùng khi Telegram không gửi được ảnh QR." },
  { key: "BTN_BUY_1M", label: "Nút mua nhóm 30 ngày", placeholder: "💎 VIP 30 NGÀY", help: "Nút trên trang chi tiết nhóm." },
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
  { key: "ALERT_POLICY_UNAVAILABLE", label: "Không mở được policy", placeholder: "Không thể mở trang quy định lúc này.", help: "Alert khi trang policy lỗi." },
  { key: "ALERT_SUPPORT_UNAVAILABLE", label: "Không mở được support", placeholder: "Không thể mở trang hỗ trợ lúc này.", help: "Alert khi trang support lỗi." },
  { key: "ALERT_COUPON_MENU_DISABLED", label: "Coupon menu đang ẩn", placeholder: "Chức năng nhập mã trên menu đang được ẩn.", help: "Khi khách bấm nút coupon đã ẩn." },
  { key: "ALERT_COUPON_PRIVATE_ONLY", label: "Coupon chỉ private", placeholder: "Vui lòng nhắn riêng với bot để nhập mã.", help: "Alert khi bấm coupon trong group." },
  { key: "ALERT_COUPON_SELECTION_INVALID", label: "Coupon chọn group lỗi", placeholder: "Lựa chọn coupon không hợp lệ.", help: "Callback chọn group coupon sai format." },
  { key: "ALERT_COUPON_NOT_GROUP_SELECT", label: "Không phải coupon chọn group", placeholder: "Mã này không phải coupon chọn group.", help: "Callback chọn group không hợp lệ." },
  { key: "ALERT_COUPON_GROUP_OUT_OF_SCOPE", label: "Group ngoài phạm vi coupon", placeholder: "Group này không nằm trong phạm vi coupon.", help: "Khi coupon không áp dụng cho group đã chọn." },
  { key: "ALERT_RENEW_CODE_INVALID", label: "Mã gia hạn không hợp lệ", placeholder: "Mã gia hạn không hợp lệ.", help: "Khi callback gia hạn sai format." },
  { key: "ALERT_RENEW_OFFER_INVALID", label: "Offer gia hạn không hợp lệ", placeholder: "Ưu đãi gia hạn không còn hợp lệ.", help: "Khi offer không còn dữ liệu." },
  { key: "ALERT_RENEW_NOT_OWNER", label: "Offer không thuộc user", placeholder: "Ưu đãi này không thuộc tài khoản của bạn.", help: "Khi user bấm offer của người khác." },
  { key: "ALERT_RENEW_EXPIRED", label: "Offer gia hạn hết hạn", placeholder: "Ưu đãi gia hạn sớm đã hết hạn hoặc không còn hợp lệ.", help: "Khi offer không đủ điều kiện." },
  { key: "ALERT_DISCOUNT_INVALID", label: "Mã giảm giá lỗi", placeholder: "Mã giảm giá không hợp lệ.", help: "Callback coupon giảm giá sai format." },
  { key: "ALERT_DISCOUNT_NOT_APPLICABLE", label: "Coupon không áp dụng", placeholder: "Mã này không áp dụng cho gói đã chọn.", help: "Khi coupon không match gói." },
  { key: "ALERT_DISCOUNT_PLAN_INVALID", label: "Gói coupon không hợp lệ", placeholder: "Gói áp dụng không hợp lệ.", help: "Khi plan key không đọc được." },
  { key: "ALERT_DISCOUNT_ZERO_AMOUNT", label: "Coupon về 0đ", placeholder: "Mã giảm giá làm đơn về 0đ. Hãy dùng coupon kích hoạt thay vì coupon giảm giá.", help: "Chặn coupon giảm giá làm đơn còn 0đ." },
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
    placeholder: "🔥 Mua SVIP Trọn Đời => buy_full_life\\n💎 Mua SVIP 30 Ngày => buy_full_1m",
    help: "Mỗi dòng là một nút. Dùng cú pháp Text => callback.",
    kind: "textarea",
  },
];

const PLAN_FIELDS: ConfigField[] = [
  { key: "PLAN_FULL_1M", label: "Tên gói SVIP 30 ngày", placeholder: "SVIP+ 30 Ngày", help: "Tên gói hiển thị khi khách mua SVIP 30 ngày." },
  { key: "PLAN_FULL_LIFE", label: "Tên gói SVIP trọn đời", placeholder: "SVIP+ TRỌN ĐỜI", help: "Tên gói hiển thị khi khách mua SVIP trọn đời." },
  { key: "PRICE_SVIP_30D", label: "Giá SVIP 30 ngày", placeholder: "99000", help: "Nhập số tiền VND, không cần dấu chấm." },
  { key: "PRICE_SVIP_LIFE", label: "Giá SVIP trọn đời", placeholder: "499000", help: "Nhập số tiền VND, không cần dấu chấm." },
  { key: "BTN_BUY_SVIP_30D", label: "Nút mua SVIP 30 ngày", placeholder: "MUA 30 NGÀY", help: "Text nút trong bot." },
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
  Duration_Label: "",
  Plan_Name_Template: "",
  Button_Template: "",
  Discount_Percent: "10",
  Applies_To: "ALL",
  Max_Uses: "1",
  Enabled: "ON",
};

const EMPTY_MANUAL_ORDER_FORM = {
  telegram_user_id: "",
  full_name: "",
  plan_key: "FULL_1M",
  plan_name: "",
  amount: "0",
  duration_days: "30",
  expire_at: "",
  coupon_code: "",
};

const DEFAULT_LIFETIME_DAYS = "36500";

const ORDER_PAGE_SIZE = 25;
const CUSTOMER_PAGE_SIZE = 25;
const LOG_PAGE_SIZE = 80;
const RENEWAL_PAGE_SIZE = 25;
const SUPPORT_PAGE_SIZE = 25;
const COUPON_PAGE_SIZE = 20;

function randomHangcuCode() {
  const alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
  const suffix = Array.from({ length: 8 }, () => alphabet[Math.floor(Math.random() * alphabet.length)]).join("");
  return `HANGCU_${suffix}`;
}

function isLifetimeCouponPlan(planName: string) {
  const key = String(planName || "").trim().toUpperCase().replace(/\s+/g, "");
  return key === "FULL_LIFE" || key === "SVIP_LIFE" || key === "SELECT_GROUP_LIFE" || key.endsWith("_LIFE");
}

function isCouponSent(coupon: Coupon) {
  const raw = coupon.raw_data || {};
  const status = String(raw.Sent_Status || raw.Sent || raw.Is_Sent || "").trim().toUpperCase();
  return status === "SENT" || status === "YES" || status === "TRUE" || status === "1" || status === "ON";
}

function couponSentAt(coupon: Coupon) {
  const raw = coupon.raw_data || {};
  return String(raw.Sent_At || raw.sent_at || "").trim() || null;
}

function couponLastUserName(coupon: Coupon) {
  const raw = coupon.raw_data || {};
  return String(
    coupon.last_redeemed_full_name ||
    coupon.last_redeemed_username ||
    raw.Last_Redeemed_Full_Name ||
    raw.Last_Redeemed_Username ||
    coupon.last_redeemed_by ||
    raw.Last_Used_By ||
    raw.Last_Redeemed_By ||
    "",
  ).trim() || "-";
}

function couponLastUserDetail(coupon: Coupon) {
  const raw = coupon.raw_data || {};
  const parts = [
    coupon.last_redeemed_by || raw.Last_Used_By || raw.Last_Redeemed_By ? `ID ${coupon.last_redeemed_by || raw.Last_Used_By || raw.Last_Redeemed_By}` : "",
    coupon.last_redeemed_order_id ? `Đơn ${coupon.last_redeemed_order_id}` : "",
  ].filter(Boolean);
  return parts.join(" • ") || "-";
}

function couponLastUsedAt(coupon: Coupon) {
  const raw = coupon.raw_data || {};
  return coupon.last_redeemed_at || String(raw.Last_Used_At || raw.Last_Redeemed_At || "").trim() || couponSentAt(coupon);
}

function couponIsExpired(coupon: Coupon) {
  if (String(coupon.status || "").toUpperCase() !== "ACTIVE") return true;
  if (!coupon.expires_at) return false;
  const expire = new Date(coupon.expires_at);
  return !Number.isNaN(expire.getTime()) && expire.getTime() <= Date.now();
}

function couponIsUsed(coupon: Coupon) {
  return (coupon.redemption_count || coupon.used_count || 0) > 0;
}

function couponTabOf(coupon: Coupon): CouponTab {
  if (couponIsExpired(coupon)) return "expired";
  if (couponIsUsed(coupon)) return "used";
  if (isCouponSent(coupon)) return "sent";
  return "unsent";
}

function orderCouponCode(order: Order) {
  return order.coupon_code || (Number(order.amount || 0) === 0 && order.sale_id ? order.sale_id : "");
}

function stripHtml(value: string) {
  return String(value || "")
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/p>/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .trim();
}

function isLifetimeText(value: string | null | undefined) {
  const text = String(value || "").toLowerCase();
  return text.includes("trọn đời") || text.includes("tron doi") || text.includes("lifetime");
}

function isOrderActive(order: Order) {
  if (order.status !== "PAID") return false;
  if (isLifetimeText(order.plan_name)) return true;
  if (!order.expire_at) return false;
  const expire = new Date(order.expire_at);
  return !Number.isNaN(expire.getTime()) && expire.getTime() > Date.now();
}

function orderPlanKind(order: Order) {
  const plan = String(order.plan_name || "").toLowerCase();
  if (isLifetimeText(plan)) return "Trọn đời";
  if (plan.includes("1 ngày") || plan.includes("1 day")) return "1 ngày";
  if (plan.includes("30")) return "30 ngày";
  return "Khác";
}

function orderExpireValue(value: string | null | undefined) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hour}:${minute}`;
}

function groupNamesForOrder(order: Order) {
  const plan = String(order.plan_name || "");
  if (!plan) return [];
  const lowerPlan = plan.toLowerCase();
  if (lowerPlan.includes("full") || lowerPlan.includes("svip")) return ["Full nhóm"];
  const afterDash = plan.includes(" - ") ? plan.split(" - ").slice(1).join(" - ").trim() : "";
  return afterDash ? [afterDash] : [];
}

function uniqueValues(values: string[]) {
  return Array.from(new Set(values.filter(Boolean)));
}

function payloadText(payload: Record<string, unknown>, key: string) {
  const value = payload?.[key];
  return value === null || value === undefined ? "" : String(value);
}

function describeActivityEvent(event: ActivityEvent) {
  const payload = event.payload || {};
  const eventType = payloadText(payload, "event_type") || event.event_name;
  if (eventType === "message") {
    const command = payloadText(payload, "command");
    return command ? `User gửi lệnh /${command}` : "User gửi tin nhắn cho bot";
  }
  if (eventType === "callback") {
    const callback = payloadText(payload, "callback_data");
    return callback ? `User bấm nút: ${callback}` : "User bấm nút trong bot";
  }
  return eventType || "Tương tác user";
}

function describeSupportEvent(event: SupportEvent) {
  return supportEventLabel(event.event_type);
}

function money(value: number) {
  return new Intl.NumberFormat("vi-VN").format(value || 0) + "đ";
}

function dateText(value: string | null | undefined) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("vi-VN", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function datePlusDaysText(value: string | null | undefined, days: number) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  date.setDate(date.getDate() + days);
  return dateText(date.toISOString());
}

function dateMinusDaysText(value: string | null | undefined, days: number) {
  return datePlusDaysText(value, -days);
}

function normalizeChatId(value: string | number | null | undefined) {
  const raw = String(value ?? "").trim();
  if (!raw) return "";
  return raw.endsWith(".0") ? raw.slice(0, -2) : raw;
}

function dateOnly(value: string | null | undefined) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function isTodayDate(value: string | null | undefined) {
  return Boolean(value && dateOnly(value) === dateOnly(new Date().toISOString()));
}

function daysUntil(value: string | null | undefined) {
  if (!value) return 999999;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 999999;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(date);
  target.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / 86400000);
}

function dayKey(value: string | null | undefined) {
  if (!value) return "Không rõ ngày";
  return new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium" }).format(new Date(value));
}

function isoDayKey(value: string | null | undefined) {
  if (!value) return "UNKNOWN";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "UNKNOWN";
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
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

function supportEventLabel(type: string) {
  const labels: Record<string, string> = {
    support_joined: "Vừa join support",
    support_left: "Rời support",
    renewal_reminder_sent: "Đã nhắc gia hạn",
    expired_notice_sent: "Đã báo hết hạn",
    member_muted: "Đã mute",
    member_unmuted: "Đã mở mute",
    member_kicked: "Đã kick",
  };
  return labels[type] || type;
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
  const [blacklist, setBlacklist] = useState<BlacklistEntry[]>([]);
  const [supportEvents, setSupportEvents] = useState<SupportEvent[]>([]);
  const [activityEvents, setActivityEvents] = useState<ActivityEvent[]>([]);
  const [supportCheck, setSupportCheck] = useState<SupportGroupCheck | null>(null);
  const [webhook, setWebhook] = useState<WebhookInfo | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState("");
  const [query, setQuery] = useState("");
  const [orderStatus, setOrderStatus] = useState("ALL");
  const [orderPeriod, setOrderPeriod] = useState<OrderPeriod>("month");
  const [orderGroupMode, setOrderGroupMode] = useState<GroupMode>("day");
  const [orderPage, setOrderPage] = useState(1);
  const [customerPage, setCustomerPage] = useState(1);
  const [customerStatus, setCustomerStatus] = useState<CustomerStatusFilter>("all");
  const [customerGroup, setCustomerGroup] = useState("ALL");
  const [customerPlanKind, setCustomerPlanKind] = useState("ALL");
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [customerModalOpen, setCustomerModalOpen] = useState(false);
  const [logDirection, setLogDirection] = useState<LogDirectionFilter>("all");
  const [logType, setLogType] = useState("ALL");
  const [logDate, setLogDate] = useState("ALL");
  const [logPage, setLogPage] = useState(1);
  const [renewalTab, setRenewalTab] = useState<RenewalSubTab>("soon");
  const [renewalPage, setRenewalPage] = useState(1);
  const [renewalSettingsOpen, setRenewalSettingsOpen] = useState(false);
  const [supportTab, setSupportTab] = useState<SupportSubTab>("all");
  const [supportPage, setSupportPage] = useState(1);
  const [supportSettingsOpen, setSupportSettingsOpen] = useState(false);
  const [securitySettingsOpen, setSecuritySettingsOpen] = useState(false);
  const [systemSettingsOpen, setSystemSettingsOpen] = useState(false);
  const [groupNo, setGroupNo] = useState("1");
  const [groupName, setGroupName] = useState("");
  const [groupId, setGroupId] = useState("");
  const [groupPrice1m, setGroupPrice1m] = useState("");
  const [groupPriceLife, setGroupPriceLife] = useState("");
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [menuForm, setMenuForm] = useState({ page_id: "main_menu", image_url: "", body: "", layout: "" });
  const [saleForm, setSaleForm] = useState({ sale_id: "", price_key: "PRICE_SVIP_30D", discount_percent: "", sale_price: "", slot_limit: "", enabled: "ON", start_at: "", end_at: "" });
  const [couponForm, setCouponForm] = useState({ ...EMPTY_COUPON_FORM });
  const [couponBatchCount, setCouponBatchCount] = useState("10");
  const [couponTab, setCouponTab] = useState<CouponTab>("unsent");
  const [couponPage, setCouponPage] = useState(1);
  const [couponModalOpen, setCouponModalOpen] = useState(false);
  const [manualOrderForm, setManualOrderForm] = useState({ ...EMPTY_MANUAL_ORDER_FORM });
  const [manualOrderResult, setManualOrderResult] = useState<ManualOrderResult | null>(null);
  const [manualOrderModalOpen, setManualOrderModalOpen] = useState(false);
  const [blacklistForm, setBlacklistForm] = useState({ telegram_user_id: "", username: "", full_name: "", reason: "" });

  useEffect(() => {
    const stored = window.localStorage.getItem("prive_admin_secret") || "";
    setSavedSecret(stored);
    setSecret(stored);
  }, []);

  useEffect(() => {
    const nextValues: Record<string, string> = {};
    [...ADMIN_FIELDS, ...SUPPORT_FIELDS, ...CURRENCY_FIELDS, ...BOT_FIELDS, ...RENEWAL_FIELDS, ...SECURITY_FIELDS, ...SYSTEM_FIELDS, ...COMMAND_FIELDS, ...MESSAGE_FIELDS, ...BUTTON_FIELDS, ...ALERT_FIELDS, ...SALE_CONTENT_FIELDS, ...PLAN_FIELDS].forEach((field) => {
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
      const [ordersRes, usersRes, configRes, menuRes, salesRes, couponsRes, blacklistRes, supportEventsRes, activityEventsRes, webhookRes] = await Promise.all([
        getOrders(activeSecret),
        getUsers(activeSecret),
        getConfig(activeSecret),
        getMenuPages(activeSecret),
        getSaleRules(activeSecret),
        getCoupons(activeSecret),
        getBlacklist(activeSecret),
        getSupportEvents(activeSecret),
        getActivityEvents(activeSecret),
        getWebhookInfo(activeSecret),
      ]);
      setOrders(ordersRes.data);
      setUsers(usersRes.data);
      setConfig(configRes.data);
      setMenuPages(menuRes.data);
      setSaleRules(salesRes.data);
      setCoupons(couponsRes.data);
      setBlacklist(blacklistRes.data);
      setSupportEvents(supportEventsRes.data);
      setActivityEvents(activityEventsRes.data);
      setWebhook(webhookRes.data);
      setOrderPage(1);
      setCouponPage(1);
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
      await updateConfigs(savedSecret, fields.map((field) => ({ key: field.key, value: fieldValues[field.key] || "" })));
      await loadAll();
    });
  }

  function resetGroupForm(nextGroupNo?: string) {
    const used = new Set(config.filter((item) => /^BTN_G\d+$/.test(item.key)).map((item) => item.key.replace("BTN_G", "")));
    const firstEmpty = Array.from({ length: maxGroups }, (_, idx) => String(idx + 1)).find((item) => !used.has(item)) || "1";
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
      await updateConfigs(savedSecret, [
        { key: `BTN_G${groupNo}`, value: groupName },
        { key: `ID_G${groupNo}`, value: groupId },
        { key: `PRICE_G${groupNo}_1M`, value: groupPrice1m },
        { key: `PRICE_G${groupNo}_LIFE`, value: groupPriceLife },
      ]);
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

  async function runSupportGroupCheck() {
    await runAction("support-check", async () => {
      const res = await checkSupportGroup(savedSecret);
      setSupportCheck(res.data);
      if (res.data.get_chat.ok && res.data.bot_member.ok && res.data.invite_link.ok) {
        showNotice("ok", "Group hỗ trợ tạo link OK.");
      } else {
        showNotice("error", "Group hỗ trợ chưa tạo được link. Xem chi tiết trong tab.");
      }
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

  function normalizeCouponPayload(source: typeof EMPTY_COUPON_FORM, codeOverride?: string) {
    const payload = { ...source, Code: (codeOverride || source.Code || randomHangcuCode()).trim().toUpperCase() };
    if (payload.Code.length > 32) {
      throw new Error("Mã coupon nên tối đa 32 ký tự để nút Telegram hoạt động ổn định.");
    }
    if (payload.Coupon_Type === "DISCOUNT") {
      const percent = Number(payload.Discount_Percent || 0);
      if (!Number.isFinite(percent) || percent <= 0 || percent >= 100) {
        throw new Error("Coupon giảm giá cần phần trăm từ 1 đến 99. Muốn miễn phí hãy dùng loại Kích hoạt miễn phí.");
      }
      return payload;
    }

    if (isLifetimeCouponPlan(payload.Plan_Name)) {
      payload.Duration_Days = getConfigValue(config, "COUPON_LIFETIME_DAYS", DEFAULT_LIFETIME_DAYS) || DEFAULT_LIFETIME_DAYS;
      return payload;
    }

    const days = Number(payload.Duration_Days || 0);
    if (!Number.isFinite(days) || days <= 0) {
      throw new Error("Coupon kích hoạt theo ngày cần số ngày sử dụng lớn hơn 0.");
    }
    return payload;
  }

  async function saveCoupon() {
    await runAction("coupon", async () => {
      const payload = normalizeCouponPayload(couponForm);
      await createCoupon(savedSecret, payload);
      setCouponForm({ ...EMPTY_COUPON_FORM });
      setCouponModalOpen(false);
      await loadAll();
    });
  }

  function resetCouponForm() {
    setCouponForm({ ...EMPTY_COUPON_FORM });
  }

  function openNewCouponModal() {
    resetCouponForm();
    setCouponModalOpen(true);
  }

  function editCoupon(item: Coupon) {
    setCouponForm({
      ...EMPTY_COUPON_FORM,
      Code: item.code,
      Coupon_Type: String(item.raw_data?.Coupon_Type || "ACTIVATION"),
      Plan_Name: String(item.raw_data?.Plan_Name || item.plan_name || "SELECT_GROUP_1M"),
      Duration_Days: String(item.raw_data?.Duration_Days || "30"),
      Duration_Label: String(item.raw_data?.Duration_Label || item.raw_data?.Activation_Label || ""),
      Plan_Name_Template: String(item.raw_data?.Plan_Name_Template || item.raw_data?.Activation_Plan_Template || ""),
      Button_Template: String(item.raw_data?.Button_Template || item.raw_data?.Activation_Button_Template || ""),
      Discount_Percent: String(item.raw_data?.Discount_Percent || "10"),
      Applies_To: String(item.raw_data?.Applies_To || "ALL"),
      Max_Uses: String(item.max_uses || 1),
      Enabled: item.status === "ACTIVE" ? "ON" : "OFF",
    });
    setCouponModalOpen(true);
  }

  function generateCouponCode() {
    setCouponForm({ ...couponForm, Code: randomHangcuCode() });
  }

  async function generateManyCoupons() {
    const count = Number(couponBatchCount || 0);
    if (!Number.isInteger(count) || count < 2 || count > 200) {
      showNotice("error", "Số lượng gen nhiều nên từ 2 đến 200 mã mỗi lần.");
      return;
    }
    await runAction("coupon-bulk", async () => {
      const existing = new Set(coupons.map((item) => item.code.toUpperCase()));
      const generated = new Set<string>();
      while (generated.size < count) {
        const code = randomHangcuCode();
        if (!existing.has(code) && !generated.has(code)) generated.add(code);
      }
      const items = Array.from(generated).map((code) => normalizeCouponPayload({ ...couponForm, Code: "" }, code));
      await createCoupons(savedSecret, items);
      setCouponForm({ ...EMPTY_COUPON_FORM });
      setCouponModalOpen(false);
      await loadAll();
    });
  }

  function toggleCouponPlan(planKey: string) {
    const current = couponForm.Applies_To === "ALL" ? [] : couponForm.Applies_To.split(",").filter(Boolean);
    const next = current.includes(planKey) ? current.filter((item) => item !== planKey) : [...current, planKey];
    setCouponForm({ ...couponForm, Applies_To: next.length ? next.join(",") : "ALL" });
  }

  const couponsByTab = useMemo(() => {
    const buckets: Record<CouponTab, Coupon[]> = { unsent: [], sent: [], used: [], expired: [] };
    for (const coupon of coupons) {
      buckets[couponTabOf(coupon)].push(coupon);
    }
    const sortForTab = (list: Coupon[], tabKey: CouponTab) => {
      return [...list].sort((a, b) => {
        if (tabKey === "used") {
          return new Date(couponLastUsedAt(b) || b.created_at || "").getTime() - new Date(couponLastUsedAt(a) || a.created_at || "").getTime();
        }
        if (tabKey === "expired") {
          return new Date(b.expires_at || b.created_at || "").getTime() - new Date(a.expires_at || a.created_at || "").getTime();
        }
        return new Date(b.created_at || "").getTime() - new Date(a.created_at || "").getTime();
      });
    };
    return {
      unsent: sortForTab(buckets.unsent, "unsent"),
      sent: sortForTab(buckets.sent, "sent"),
      used: sortForTab(buckets.used, "used"),
      expired: sortForTab(buckets.expired, "expired"),
    };
  }, [coupons]);
  const couponTabCounts = useMemo(() => ({
    unsent: couponsByTab.unsent.length,
    sent: couponsByTab.sent.length,
    used: couponsByTab.used.length,
    expired: couponsByTab.expired.length,
  }), [couponsByTab]);
  const visibleCoupons = useMemo(() => couponsByTab[couponTab] || [], [couponTab, couponsByTab]);
  const totalCouponPages = Math.max(1, Math.ceil(visibleCoupons.length / COUPON_PAGE_SIZE));
  const pagedCoupons = useMemo(() => {
    const safePage = Math.min(couponPage, totalCouponPages);
    const start = (safePage - 1) * COUPON_PAGE_SIZE;
    return visibleCoupons.slice(start, start + COUPON_PAGE_SIZE);
  }, [visibleCoupons, couponPage, totalCouponPages]);

  async function removeCoupon(code = couponForm.Code) {
    if (!code || !window.confirm(`Xoá coupon "${code}"? Lịch sử đã dùng vẫn được giữ riêng trong hệ thống.`)) return;
    await runAction(`coupon-delete-${code}`, async () => {
      await deleteCoupon(savedSecret, code);
      resetCouponForm();
      setCouponModalOpen(false);
      await loadAll();
    });
  }

  async function toggleCouponSent(coupon: Coupon, sent: boolean) {
    await runAction(`coupon-sent-${coupon.code}`, async () => {
      await createCoupon(savedSecret, {
        ...(coupon.raw_data || {}),
        Code: coupon.code,
        Sent_Status: sent ? "SENT" : "",
        Sent_At: sent ? new Date().toISOString() : "",
      });
      await loadAll();
    });
  }

  async function copyCouponAndMarkSent(coupon: Coupon) {
    setSaving(`coupon-copy-${coupon.code}`);
    setNotice(null);
    try {
      await navigator.clipboard.writeText(coupon.code);
      if (!isCouponSent(coupon)) {
        await createCoupon(savedSecret, {
          ...(coupon.raw_data || {}),
          Code: coupon.code,
          Sent_Status: "SENT",
          Sent_At: new Date().toISOString(),
        });
        await loadAll();
      }
      showNotice("ok", `Đã copy ${coupon.code} và đánh dấu đã gửi.`);
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "Không copy được mã coupon.");
    } finally {
      setSaving("");
    }
  }

  async function saveBlacklistEntry() {
    await runAction("blacklist", async () => {
      const telegramId = blacklistForm.telegram_user_id.trim();
      if (!telegramId) {
        throw new Error("Cần nhập Telegram ID để chặn.");
      }
      await upsertBlacklist(savedSecret, {
        ...blacklistForm,
        telegram_user_id: telegramId,
        source: "dashboard",
        reason: blacklistForm.reason || "Chặn thủ công từ dashboard",
      });
      setBlacklistForm({ telegram_user_id: "", username: "", full_name: "", reason: "" });
      await loadAll();
    });
  }

  async function removeBlacklistEntry(telegramUserId = blacklistForm.telegram_user_id) {
    if (!telegramUserId || !window.confirm(`Gỡ Telegram ID "${telegramUserId}" khỏi blacklist?`)) return;
    await runAction(`blacklist-delete-${telegramUserId}`, async () => {
      await deleteBlacklist(savedSecret, telegramUserId);
      setBlacklistForm({ telegram_user_id: "", username: "", full_name: "", reason: "" });
      await loadAll();
    });
  }

  async function changeOrderStatus(orderId: string, status: string) {
    await runAction(`order-${orderId}`, async () => {
      await updateOrderStatus(savedSecret, orderId, status);
      await loadAll();
    });
  }

  async function changeOrderExpire(orderId: string, expireAt: string) {
    if (!expireAt) {
      showNotice("error", "Vui lòng chọn ngày giờ hết hạn.");
      return;
    }
    await runAction(`order-expire-${orderId}`, async () => {
      await updateOrder(savedSecret, orderId, { expire_at: expireAt, status: "PAID", expired_notice_at: null });
      await loadAll();
    });
  }

  async function changeOrderPlan(orderId: string, planName: string) {
    const nextPlanName = planName.trim();
    if (!nextPlanName) {
      showNotice("error", "Tên gói không được để trống.");
      return;
    }
    await runAction(`order-plan-${orderId}`, async () => {
      await updateOrder(savedSecret, orderId, { plan_name: nextPlanName });
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

  const maxGroups = useMemo(() => Math.max(Number(getConfigValue(config, "GROUP_COUNT", String(DEFAULT_GROUP_COUNT))) || DEFAULT_GROUP_COUNT, 1), [config]);
  const configuredGroups = useMemo(() => Array.from({ length: maxGroups }, (_, idx) => idx + 1).filter((item) => isGroupConfigured(config, item)), [config, maxGroups]);
  const visibleGroups = useMemo(() => Array.from({ length: maxGroups }, (_, idx) => idx + 1).filter((item) => hasAnyGroupConfig(config, item)), [config, maxGroups]);
  const groupSelectOptions = useMemo(() => {
    const selected = Number(groupNo);
    const values = new Set(visibleGroups);
    if (selected >= 1 && selected <= maxGroups) values.add(selected);
    return Array.from(values).sort((a, b) => a - b);
  }, [groupNo, visibleGroups, maxGroups]);
  const planKeyOptions = useMemo(() => [
    ...PLAN_KEY_OPTIONS,
    ...SELECTABLE_GROUP_COUPON_OPTIONS,
    ...configuredGroups.flatMap((item) => [`G${item}_1M`, `G${item}_LIFE`]),
  ], [configuredGroups]);
  const discountPlanKeyOptions = useMemo(() => [
    ...PLAN_KEY_OPTIONS,
    ...configuredGroups.flatMap((item) => [`G${item}_1M`, `G${item}_LIFE`]),
  ], [configuredGroups]);
  const manualPlanKeyOptions = useMemo(() => [
    ...discountPlanKeyOptions,
    "CUSTOM",
  ], [discountPlanKeyOptions]);
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
      const text = `${order.order_id} ${order.full_name || ""} ${order.telegram_user_id} ${order.plan_name} ${orderCouponCode(order)}`.toLowerCase();
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
  const customerSummaries = useMemo(() => {
    const grouped = new Map<string, { id: string; name: string; orders: Order[] }>();
    for (const order of orders) {
      const id = String(order.telegram_user_id || "").trim();
      if (!id) continue;
      const current = grouped.get(id) || { id, name: order.full_name || "-", orders: [] };
      if (order.full_name) current.name = order.full_name;
      current.orders.push(order);
      grouped.set(id, current);
    }
    return Array.from(grouped.values()).map((customer) => {
      const paidOrders = customer.orders.filter((item) => item.status === "PAID");
      const activeOrders = customer.orders.filter((item) => isOrderActive(item));
      const latestExpire = paidOrders
        .map((item) => item.expire_at)
        .filter(Boolean)
        .sort((a, b) => new Date(b || "").getTime() - new Date(a || "").getTime())[0] || "";
      const coupons = uniqueValues(customer.orders.map(orderCouponCode));
      const groups = uniqueValues(customer.orders.flatMap(groupNamesForOrder));
      const plans = uniqueValues(customer.orders.map((item) => item.plan_name));
      const revenue = paidOrders.reduce((sum, item) => sum + (item.amount || 0), 0);
      const lastOrderAt = customer.orders.map((item) => item.created_at).sort((a, b) => new Date(b).getTime() - new Date(a).getTime())[0] || "";
      return {
        ...customer,
        paidOrders,
        activeOrders,
        latestExpire,
        coupons,
        groups,
        plans,
        revenue,
        lastOrderAt,
        status: activeOrders.length ? "active" : paidOrders.length ? "expired" : "no_paid",
      };
    }).sort((a, b) => new Date(b.lastOrderAt || "").getTime() - new Date(a.lastOrderAt || "").getTime());
  }, [orders]);
  const customerNameById = useMemo(() => new Map(customerSummaries.map((item) => [item.id, item.name] as const)), [customerSummaries]);
  const customerGroupOptions = useMemo(() => uniqueValues(customerSummaries.flatMap((item) => item.groups)).sort(), [customerSummaries]);
  const filteredCustomers = useMemo(() => {
    const q = query.toLowerCase();
    return customerSummaries.filter((customer) => {
      const text = `${customer.id} ${customer.name} ${customer.plans.join(" ")} ${customer.groups.join(" ")} ${customer.coupons.join(" ")}`.toLowerCase();
      if (q && !text.includes(q)) return false;
      if (customerStatus === "active" && !customer.activeOrders.length) return false;
      if (customerStatus === "expired" && customer.activeOrders.length) return false;
      if (customerStatus === "paid" && !customer.paidOrders.length) return false;
      if (customerStatus === "coupon" && !customer.coupons.length) return false;
      if (customerGroup !== "ALL" && !customer.groups.includes(customerGroup)) return false;
      if (customerPlanKind !== "ALL" && !customer.orders.some((order) => orderPlanKind(order) === customerPlanKind)) return false;
      return true;
    });
  }, [customerSummaries, query, customerStatus, customerGroup, customerPlanKind]);
  const totalCustomerPages = Math.max(1, Math.ceil(filteredCustomers.length / CUSTOMER_PAGE_SIZE));
  const pagedCustomers = useMemo(() => {
    const safePage = Math.min(customerPage, totalCustomerPages);
    const start = (safePage - 1) * CUSTOMER_PAGE_SIZE;
    return filteredCustomers.slice(start, start + CUSTOMER_PAGE_SIZE);
  }, [filteredCustomers, customerPage, totalCustomerPages]);
  const selectedCustomer = useMemo(() => {
    return customerSummaries.find((item) => item.id === selectedCustomerId) || null;
  }, [customerSummaries, selectedCustomerId]);
  const paidMemberOrders = useMemo(() => orders.filter((item) => item.status === "PAID" && item.expire_at), [orders]);
  const reminderNoticeDays = useMemo(() => Number(getConfigValue(config, "REMINDER_DAYS", "3")) || 3, [config]);
  const expiringToday = useMemo(() => paidMemberOrders.filter((item) => daysUntil(item.expire_at) === 0), [paidMemberOrders]);
  const expiringSoon = useMemo(() => {
    return paidMemberOrders.filter((item) => {
      const days = daysUntil(item.expire_at);
      return days >= 0 && days <= reminderNoticeDays;
    });
  }, [paidMemberOrders, reminderNoticeDays]);
  const remindedToday = useMemo(() => paidMemberOrders.filter((item) => item.last_reminder_date && isTodayDate(item.last_reminder_date)), [paidMemberOrders]);
  const supportTodayEvents = useMemo(() => supportEvents.filter((item) => isTodayDate(item.created_at)), [supportEvents]);
  const supportGroupId = useMemo(() => normalizeChatId(getConfigValue(config, "SUPPORT_GROUP_ID")), [config]);
  const supportGroupEvents = useMemo(() => {
    if (!supportGroupId) return [];
    return supportEvents.filter((item) => normalizeChatId(item.chat_id) === supportGroupId);
  }, [supportEvents, supportGroupId]);
  const supportGroupTodayEvents = useMemo(() => supportGroupEvents.filter((item) => isTodayDate(item.created_at)), [supportGroupEvents]);
  const supportKickedToday = useMemo(() => supportTodayEvents.filter((item) => item.event_type === "member_kicked"), [supportTodayEvents]);
  const renewalReminderEvents = useMemo(() => supportEvents.filter((item) => item.event_type === "renewal_reminder_sent"), [supportEvents]);
  const expiredNoticeEvents = useMemo(() => supportEvents.filter((item) => item.event_type === "expired_notice_sent"), [supportEvents]);
  const uniqueKickedEvents = useMemo(() => {
    const map = new Map<string, SupportEvent>();
    for (const item of supportEvents.filter((event) => event.event_type === "member_kicked")) {
      const key = [item.telegram_user_id || "", item.order_id || "", item.chat_id || ""].join("|");
      const current = map.get(key);
      if (!current || new Date(item.created_at).getTime() > new Date(current.created_at).getTime()) {
        map.set(key, item);
      }
    }
    return Array.from(map.values()).sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }, [supportEvents]);
  const latestReminderByOrder = useMemo(() => {
    const map = new Map<string, SupportEvent>();
    for (const event of renewalReminderEvents) {
      const orderId = event.order_id || "";
      if (!orderId) continue;
      const current = map.get(orderId);
      if (!current || new Date(event.created_at).getTime() > new Date(current.created_at).getTime()) {
        map.set(orderId, event);
      }
    }
    return map;
  }, [renewalReminderEvents]);
  function renewalCustomerName(item: Order | SupportEvent) {
    const telegramId = "telegram_user_id" in item ? String(item.telegram_user_id || "").trim() : "";
    const fromOrder = "full_name" in item ? String(item.full_name || "").trim() : "";
    return fromOrder || customerNameById.get(telegramId) || telegramId || "-";
  }
  const renewalRows = useMemo(() => {
    const rows: Record<RenewalSubTab, ReactNode[][]> = {
      soon: expiringSoon.map((item) => {
        const reminderEvent = latestReminderByOrder.get(item.order_id);
        return [
          renewalCustomerName(item),
          item.telegram_user_id,
          item.plan_name,
          dateText(item.expire_at),
          `${daysUntil(item.expire_at)} ngày`,
          dateMinusDaysText(item.expire_at, reminderNoticeDays),
          reminderEvent ? dateText(reminderEvent.created_at) : item.last_reminder_date || "-",
        ];
      }),
      today: expiringToday.map((item) => [
        renewalCustomerName(item),
        item.telegram_user_id,
        item.plan_name,
        dateText(item.expire_at),
        item.status,
        item.expired_notice_at ? dateText(item.expired_notice_at) : "-",
      ]),
      reminded: renewalReminderEvents.map((item) => [
        renewalCustomerName(item),
        item.telegram_user_id || "-",
        item.plan_name || "-",
        item.order_id || "-",
        dateText(item.created_at),
        item.raw_data?.expire_at ? dateText(String(item.raw_data.expire_at)) : "-",
      ]),
      expiredNotice: expiredNoticeEvents.map((item) => [
        renewalCustomerName(item),
        item.telegram_user_id || "-",
        item.plan_name || "-",
        item.order_id || "-",
        dateText(item.created_at),
        item.raw_data?.expire_at ? dateText(String(item.raw_data.expire_at)) : "-",
      ]),
      kicked: uniqueKickedEvents.map((item) => [
        renewalCustomerName(item),
        item.telegram_user_id || "-",
        item.plan_name || "-",
        item.order_id || "-",
        item.chat_title || item.chat_id || "-",
        dateText(item.created_at),
      ]),
    };
    return rows;
  }, [expiringSoon, expiringToday, renewalReminderEvents, expiredNoticeEvents, uniqueKickedEvents, latestReminderByOrder, reminderNoticeDays]);
  const renewalHeaders: Record<RenewalSubTab, string[]> = {
    soon: ["Khách", "Telegram ID", "Gói", "Hết hạn lúc", "Còn lại", "Bắt đầu nhắc từ", "Nhắc gần nhất"],
    today: ["Khách", "Telegram ID", "Gói", "Hết hạn lúc", "Trạng thái", "Báo hết hạn lúc"],
    reminded: ["Khách", "Telegram ID", "Gói", "Đơn", "Giờ nhắc", "Hạn dùng"],
    expiredNotice: ["Khách", "Telegram ID", "Gói", "Đơn", "Giờ báo hết hạn", "Hạn dùng"],
    kicked: ["Khách", "Telegram ID", "Gói", "Đơn", "Group", "Giờ kick"],
  };
  const currentRenewalRows = renewalRows[renewalTab] || [];
  const totalRenewalPages = Math.max(1, Math.ceil(currentRenewalRows.length / RENEWAL_PAGE_SIZE));
  const pagedRenewalRows = useMemo(() => {
    const safePage = Math.min(renewalPage, totalRenewalPages);
    const start = (safePage - 1) * RENEWAL_PAGE_SIZE;
    return currentRenewalRows.slice(start, start + RENEWAL_PAGE_SIZE);
  }, [currentRenewalRows, renewalPage, totalRenewalPages]);
  const supportEventRows = useMemo(() => {
    const filtered = supportGroupEvents.filter((item) => {
      if (supportTab === "joined") return item.event_type === "support_joined";
      if (supportTab === "left") return item.event_type === "support_left";
      if (supportTab === "muted") return item.event_type === "member_muted";
      if (supportTab === "kicked") return item.event_type === "member_kicked";
      return true;
    });
    return filtered.map((item) => [
      supportEventLabel(item.event_type),
      item.full_name || item.username || "-",
      item.telegram_user_id || "-",
      item.chat_title || item.chat_id || "-",
      dateText(item.created_at),
      [item.raw_data?.old_status, item.raw_data?.new_status].filter(Boolean).join(" → ") || (item.raw_data?.reason ? String(item.raw_data.reason) : "-"),
    ]);
  }, [supportGroupEvents, supportTab]);
  const supportEventHeaders = useMemo(() => {
    return ["Loại", "Khách", "Telegram ID", "Group", "Giờ", "Chi tiết"];
  }, [supportTab]);
  const totalSupportPages = Math.max(1, Math.ceil(supportEventRows.length / SUPPORT_PAGE_SIZE));
  const pagedSupportRows = useMemo(() => {
    const safePage = Math.min(supportPage, totalSupportPages);
    const start = (safePage - 1) * SUPPORT_PAGE_SIZE;
    return supportEventRows.slice(start, start + SUPPORT_PAGE_SIZE);
  }, [supportEventRows, supportPage, totalSupportPages]);
  const logEntries = useMemo(() => {
    const userEvents = activityEvents.map((event) => {
      const payload = event.payload || {};
      return {
        id: `a-${event.id}`,
        direction: "user" as const,
        type: payloadText(payload, "event_type") || event.event_name || "event",
        userId: event.telegram_user_id || payloadText(payload, "user_id"),
        username: payloadText(payload, "username"),
        fullName: payloadText(payload, "full_name"),
        title: describeActivityEvent(event),
        detail: payloadText(payload, "callback_data") || payloadText(payload, "command") || payloadText(payload, "chat_type"),
        createdAt: event.created_at,
      };
    });
    const botEvents = supportEvents.map((event) => ({
      id: `s-${event.id}`,
      direction: "bot" as const,
      type: event.event_type,
      userId: event.telegram_user_id || "",
      username: event.username || "",
      fullName: event.full_name || "",
      title: describeSupportEvent(event),
      detail: [event.plan_name, event.chat_title, event.order_id].filter(Boolean).join(" • "),
      createdAt: event.created_at,
    }));
    return [...userEvents, ...botEvents].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }, [activityEvents, supportEvents]);
  const logTypeOptions = useMemo(() => uniqueValues(logEntries.map((item) => item.type)).sort(), [logEntries]);
  const logDateOptions = useMemo(() => uniqueValues(logEntries.map((item) => isoDayKey(item.createdAt))).sort((a, b) => {
    if (a === "UNKNOWN") return 1;
    if (b === "UNKNOWN") return -1;
    return b.localeCompare(a);
  }), [logEntries]);
  const filteredLogEntries = useMemo(() => {
    const q = query.toLowerCase();
    return logEntries.filter((entry) => {
      if (logDirection !== "all" && entry.direction !== logDirection) return false;
      if (logType !== "ALL" && entry.type !== logType) return false;
      if (logDate !== "ALL" && isoDayKey(entry.createdAt) !== logDate) return false;
      const text = `${entry.type} ${entry.userId} ${entry.username} ${entry.fullName} ${entry.title} ${entry.detail}`.toLowerCase();
      return !q || text.includes(q);
    });
  }, [logEntries, logDirection, logType, logDate, query]);
  const totalLogPages = Math.max(1, Math.ceil(filteredLogEntries.length / LOG_PAGE_SIZE));
  const pagedLogEntries = useMemo(() => {
    const safePage = Math.min(logPage, totalLogPages);
    const start = (safePage - 1) * LOG_PAGE_SIZE;
    return filteredLogEntries.slice(start, start + LOG_PAGE_SIZE);
  }, [filteredLogEntries, logPage, totalLogPages]);
  const lifetimeCouponSelected = couponForm.Coupon_Type === "ACTIVATION" && isLifetimeCouponPlan(couponForm.Plan_Name);
  const lifetimeCouponDays = getConfigValue(config, "COUPON_LIFETIME_DAYS", DEFAULT_LIFETIME_DAYS) || DEFAULT_LIFETIME_DAYS;

  useEffect(() => {
    setOrderPage(1);
  }, [query, orderStatus, orderPeriod, orderGroupMode]);

  useEffect(() => {
    setCustomerPage(1);
  }, [query, customerStatus, customerGroup, customerPlanKind]);

  useEffect(() => {
    setLogPage(1);
  }, [query, logDirection, logType, logDate]);

  useEffect(() => {
    setRenewalPage(1);
  }, [renewalTab]);

  useEffect(() => {
    setSupportPage(1);
  }, [supportTab]);

  useEffect(() => {
    setCouponPage(1);
  }, [couponTab]);

  useEffect(() => {
    if (selectedCustomerId && !customerSummaries.some((item) => item.id === selectedCustomerId)) {
      setSelectedCustomerId("");
      setCustomerModalOpen(false);
    }
  }, [customerSummaries, selectedCustomerId]);

  function planOptionLabel(value: string) {
    if (value === "FULL_1M") return "SVIP chung - 30 ngày";
    if (value === "FULL_LIFE") return "SVIP chung - trọn đời";
    if (value === "SELECT_GROUP_1M") return "Khách tự chọn group lẻ - 30 ngày";
    if (value === "SELECT_GROUP_LIFE") return "Khách tự chọn group lẻ - trọn đời";
    const match = value.match(/^G(\d+)_(1M|LIFE)$/);
    if (!match) return value;
    const name = getConfigValue(config, `BTN_G${match[1]}`) || `Nhóm G${match[1]}`;
    return `${name} - ${match[2] === "1M" ? "30 ngày" : "trọn đời"}`;
  }

  function priceOptionLabel(value: string) {
    if (value === "PRICE_SVIP_30D") return "Giá SVIP chung - 30 ngày";
    if (value === "PRICE_SVIP_LIFE") return "Giá SVIP chung - trọn đời";
    const match = value.match(/^PRICE_G(\d+)_(1M|LIFE)$/);
    if (!match) return value;
    const name = getConfigValue(config, `BTN_G${match[1]}`) || `Nhóm G${match[1]}`;
    return `${name} - ${match[2] === "1M" ? "giá 30 ngày" : "giá trọn đời"}`;
  }

  function manualPlanNameFromKey(value: string) {
    if (value === "FULL_1M") return getConfigValue(config, "PLAN_FULL_1M", "SVIP+ 30 Ngày") || "SVIP+ 30 Ngày";
    if (value === "FULL_LIFE") return getConfigValue(config, "PLAN_FULL_LIFE", "SVIP+ Trọn Đời") || "SVIP+ Trọn Đời";
    const match = value.match(/^G(\d+)_(1M|LIFE)$/);
    if (!match) return "";
    const prefixKey = match[2] === "1M" ? "PLAN_G_1M" : "PLAN_G_LIFE";
    const fallbackPrefix = match[2] === "1M" ? "VIP 30 Ngày" : "VIP Trọn Đời";
    const prefix = getConfigValue(config, prefixKey, fallbackPrefix) || fallbackPrefix;
    const groupName = getConfigValue(config, `BTN_G${match[1]}`) || `G${match[1]}`;
    return `${prefix} - ${groupName}`;
  }

  function manualPriceFromKey(value: string) {
    if (value === "FULL_1M") return getConfigValue(config, "PRICE_SVIP_30D", "0");
    if (value === "FULL_LIFE") return getConfigValue(config, "PRICE_SVIP_LIFE", "0");
    const match = value.match(/^G(\d+)_(1M|LIFE)$/);
    if (!match) return "";
    return getConfigValue(config, `PRICE_G${match[1]}_${match[2]}`, "0");
  }

  function changeManualPlanKey(value: string) {
    const lifetime = isLifetimeCouponPlan(value);
    setManualOrderForm({
      ...manualOrderForm,
      plan_key: value,
      plan_name: value === "CUSTOM" ? manualOrderForm.plan_name : manualPlanNameFromKey(value),
      amount: manualPriceFromKey(value) || manualOrderForm.amount,
      duration_days: lifetime ? lifetimeCouponDays : manualOrderForm.duration_days || "30",
    });
  }

  async function saveManualOrder() {
    const planName = manualOrderForm.plan_key === "CUSTOM" ? manualOrderForm.plan_name.trim() : manualPlanNameFromKey(manualOrderForm.plan_key);
    await runAction("manual-order", async () => {
      const res = await createManualOrder(savedSecret, {
        telegram_user_id: manualOrderForm.telegram_user_id.trim(),
        full_name: manualOrderForm.full_name.trim(),
        plan_name: planName,
        amount: manualOrderForm.amount,
        duration_days: manualOrderForm.duration_days,
        expire_at: manualOrderForm.expire_at,
        coupon_code: manualOrderForm.coupon_code.trim(),
        sale_id: "MANUAL",
      });
      setManualOrderResult(res.data);
      setManualOrderForm({ ...EMPTY_MANUAL_ORDER_FORM, plan_name: manualPlanNameFromKey("FULL_1M"), amount: manualPriceFromKey("FULL_1M") || "0" });
      await loadAll();
    });
  }

  async function copyManualLinks() {
    if (!manualOrderResult) return;
    const text = [
      `Đơn thủ công: ${manualOrderResult.order_id}`,
      `Telegram ID: ${manualOrderResult.telegram_user_id}`,
      `Gói: ${manualOrderResult.plan_name}`,
      `Hạn sử dụng: ${manualOrderResult.expire_at}`,
      "",
      stripHtml(manualOrderResult.links_text),
      manualOrderResult.support_text,
    ].filter(Boolean).join("\n");
    await navigator.clipboard.writeText(text);
    showNotice("ok", "Đã copy link đơn thủ công.");
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
          <button className={tab === "customers" ? "active" : ""} onClick={() => setTab("customers")}><Users size={18} /> Khách hàng</button>
          <button className={tab === "activityLog" ? "active" : ""} onClick={() => setTab("activityLog")}><ClipboardList size={18} /> Nhật ký</button>
          <button className={tab === "renewals" ? "active" : ""} onClick={() => setTab("renewals")}><RefreshCw size={18} /> Gia hạn</button>
          <button className={tab === "supportGroup" ? "active" : ""} onClick={() => setTab("supportGroup")}><ShieldCheck size={18} /> Group hỗ trợ</button>
          <button className={tab === "content" ? "active" : ""} onClick={() => setTab("content")}><FileText size={18} /> Nội dung bot</button>
          <button className={tab === "coupons" ? "active" : ""} onClick={() => setTab("coupons")}><Ticket size={18} /> Coupon</button>
          <button className={tab === "security" ? "active" : ""} onClick={() => setTab("security")}><ShieldCheck size={18} /> Bảo mật</button>
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
                <label className="field"><span>Giá 30 ngày</span><input value={groupPrice1m} onChange={(event) => setGroupPrice1m(event.target.value)} placeholder={getConfigValue(config, `PRICE_G${groupNo}_1M`) || "VD: 99000"} /></label>
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
              <PanelHead
                title="Thêm đơn thủ công"
                subtitle="Dùng khi cần cấp quyền ngoài cổng thanh toán. Mở popup để nhập thông tin, tạo order PAID và gen link."
                action={<button className="btn" onClick={() => { setManualOrderResult(null); setManualOrderModalOpen(true); }}><Plus size={18} /> Mở form tạo đơn</button>}
              />
              <div className="hint compact">Form tạo đơn thủ công được đưa vào popup để tab Đơn hàng chỉ tập trung vào danh sách và bộ lọc.</div>
            </section>
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

        {tab === "customers" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Khách trong bộ lọc" value={String(filteredCustomers.length)} />
              <Metric label="Đang còn hạn" value={String(customerSummaries.filter((item) => item.activeOrders.length).length)} />
              <Metric label="Có dùng coupon" value={String(customerSummaries.filter((item) => item.coupons.length).length)} />
              <Metric label="Doanh thu khách lọc" value={money(filteredCustomers.reduce((sum, item) => sum + item.revenue, 0))} />
            </div>
            <section className="panel">
              <PanelHead title="Khách hàng" subtitle="Danh sách ưu tiên khách mới nhất. Bấm Xem chi tiết để mở popup quản lý đơn, hạn dùng và trạng thái." />
              <div className="toolbar orders-toolbar">
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm tên khách, Telegram ID, gói, group, coupon..." />
                <select value={customerStatus} onChange={(event) => setCustomerStatus(event.target.value as CustomerStatusFilter)}>
                  <option value="all">Tất cả khách</option>
                  <option value="active">Đang còn hạn</option>
                  <option value="expired">Không còn gói active</option>
                  <option value="paid">Đã mua/kích hoạt thành công</option>
                  <option value="coupon">Có dùng coupon</option>
                </select>
                <select value={customerGroup} onChange={(event) => setCustomerGroup(event.target.value)}>
                  <option value="ALL">Tất cả group</option>
                  {customerGroupOptions.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
                <select value={customerPlanKind} onChange={(event) => setCustomerPlanKind(event.target.value)}>
                  <option value="ALL">Tất cả gói</option>
                  <option value="1 ngày">1 ngày</option>
                  <option value="30 ngày">30 ngày</option>
                  <option value="Trọn đời">Trọn đời</option>
                  <option value="Khác">Khác</option>
                </select>
              </div>
              <SimpleTable
                headers={["Khách", "Trạng thái", "PAID", "Gói / Group", "Hạn gần nhất", "Tổng tiền"]}
                rows={pagedCustomers.map((customer) => [
                  <><strong>{customer.name}</strong><div className="muted">{customer.id}</div></>,
                  <span className={customer.activeOrders.length ? "status paid" : customer.paidOrders.length ? "status expired" : "status pending"}>{customer.activeOrders.length ? "Đang còn hạn" : customer.paidOrders.length ? "Hết hạn / chờ kick" : "Chưa PAID"}</span>,
                  String(customer.paidOrders.length),
                  <><strong>{customer.plans[0] || "-"}</strong><div className="muted">{customer.groups.slice(0, 2).join(", ") || "Chưa rõ group"}</div></>,
                  dateText(customer.latestExpire),
                  money(customer.revenue),
                ])}
                actions={(idx) => (
                  <button className="btn secondary" onClick={() => {
                    const customer = pagedCustomers[idx];
                    setSelectedCustomerId(customer.id);
                    setCustomerModalOpen(true);
                  }}>Chi tiết</button>
                )}
              />
              <Pagination page={customerPage} totalPages={totalCustomerPages} totalItems={filteredCustomers.length} onPage={setCustomerPage} label="khách" />
            </section>
          </div>
        ) : null}

        {tab === "activityLog" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Tổng event" value={String(filteredLogEntries.length)} />
              <Metric label="User → Bot" value={String(logEntries.filter((item) => item.direction === "user").length)} />
              <Metric label="Bot → User" value={String(logEntries.filter((item) => item.direction === "bot").length)} />
              <Metric label="Hôm nay" value={String(logEntries.filter((item) => isTodayDate(item.createdAt)).length)} />
            </div>
            <section className="panel">
              <PanelHead title="Nhật ký tương tác" subtitle="Tổng hợp user đã nhắn/bấm gì với bot và các hành động bot đã gửi hoặc xử lý cho user." />
              <div className="toolbar orders-toolbar">
                <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm tên, Telegram ID, event, callback, gói, đơn..." />
                <select value={logDirection} onChange={(event) => setLogDirection(event.target.value as LogDirectionFilter)}>
                  <option value="all">Tất cả hướng</option>
                  <option value="user">User → Bot</option>
                  <option value="bot">Bot → User</option>
                </select>
                <select value={logType} onChange={(event) => setLogType(event.target.value)}>
                  <option value="ALL">Tất cả loại event</option>
                  {logTypeOptions.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
                <select value={logDate} onChange={(event) => setLogDate(event.target.value)}>
                  <option value="ALL">Tất cả ngày</option>
                  {logDateOptions.map((item) => <option key={item} value={item}>{item === "UNKNOWN" ? "Không rõ ngày" : dayKey(item)}</option>)}
                </select>
              </div>
              <SimpleTable
                headers={["Thời điểm", "Hướng", "Khách", "Loại", "Nội dung", "Chi tiết"]}
                rows={pagedLogEntries.map((item) => [
                  dateText(item.createdAt),
                  item.direction === "user" ? "User → Bot" : "Bot → User",
                  <><strong>{item.fullName || item.username || "-"}</strong><div className="muted">{item.userId || "-"}</div></>,
                  item.type,
                  item.title,
                  item.detail || "-",
                ])}
              />
              <Pagination page={logPage} totalPages={totalLogPages} totalItems={filteredLogEntries.length} onPage={setLogPage} label="event" />
            </section>
          </div>
        ) : null}

        {tab === "renewals" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Hết hạn hôm nay" value={String(expiringToday.length)} />
              <Metric label="Sắp hết hạn" value={String(expiringSoon.length)} />
              <Metric label="Đã nhắc hôm nay" value={String(renewalReminderEvents.filter((item) => isTodayDate(item.created_at)).length || remindedToday.length)} />
              <Metric label="Đã kick hôm nay" value={String(supportKickedToday.length)} />
            </div>
            <section className="panel">
              <PanelHead
                title="Quản lý gia hạn"
                subtitle="Theo dõi hạn dùng, lịch nhắc, báo hết hạn và lịch sử kick theo từng tab để danh sách không bị quá dài."
                action={<button className="btn" onClick={() => setRenewalSettingsOpen(true)}><Settings size={16} /> Cài đặt</button>}
              />
              <div className="subtabs">
                <button className={renewalTab === "soon" ? "active" : ""} onClick={() => setRenewalTab("soon")}>Sắp hết hạn ({expiringSoon.length})</button>
                <button className={renewalTab === "today" ? "active" : ""} onClick={() => setRenewalTab("today")}>Hết hạn hôm nay ({expiringToday.length})</button>
                <button className={renewalTab === "reminded" ? "active" : ""} onClick={() => setRenewalTab("reminded")}>Đã nhắc ({renewalReminderEvents.length})</button>
                <button className={renewalTab === "expiredNotice" ? "active" : ""} onClick={() => setRenewalTab("expiredNotice")}>Báo hết hạn ({expiredNoticeEvents.length})</button>
                <button className={renewalTab === "kicked" ? "active" : ""} onClick={() => setRenewalTab("kicked")}>Đã kick ({uniqueKickedEvents.length})</button>
              </div>
              <SimpleTable headers={renewalHeaders[renewalTab]} rows={pagedRenewalRows} />
              <Pagination page={renewalPage} totalPages={totalRenewalPages} totalItems={currentRenewalRows.length} onPage={setRenewalPage} label="dòng" />
            </section>
          </div>
        ) : null}

        {tab === "supportGroup" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Join hôm nay" value={String(supportGroupTodayEvents.filter((item) => item.event_type === "support_joined").length)} />
              <Metric label="Rời hôm nay" value={String(supportGroupTodayEvents.filter((item) => item.event_type === "support_left").length)} />
              <Metric label="Mute hôm nay" value={String(supportGroupTodayEvents.filter((item) => item.event_type === "member_muted").length)} />
              <Metric label="Kick hôm nay" value={String(supportGroupTodayEvents.filter((item) => item.event_type === "member_kicked").length)} />
              <Metric label="Sự kiện group hỗ trợ" value={String(supportGroupEvents.length)} />
              <Metric label="Group hỗ trợ" value={supportCheck?.group_name || getConfigValue(config, "SUPPORT_GROUP_NAME", "Nhóm hỗ trợ")} />
            </div>
            <section className="panel">
              <PanelHead
                title="Group hỗ trợ"
                subtitle="Chỉ hiển thị sự kiện của group hỗ trợ theo SUPPORT_GROUP_ID. Không trộn dữ liệu VIP."
                action={
                  <div className="panel-actions">
                    <button className="btn secondary" onClick={() => setSupportSettingsOpen(true)}><Settings size={16} /> Cài đặt</button>
                    <button className="btn" onClick={runSupportGroupCheck} disabled={saving === "support-check"}>{saving === "support-check" ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />} Kiểm tra</button>
                  </div>
                }
              />
              {supportCheck ? (
                <SimpleTable
                  headers={["Hạng mục", "Trạng thái", "Chi tiết"]}
                  rows={[
                    ["Cấu hình", supportCheck.enabled ? "ON" : "OFF", `${supportCheck.group_name || "-"} / ${supportCheck.group_id || "chưa có ID"}`],
                    ["Telegram getChat", supportCheck.get_chat.ok ? "OK" : "Lỗi", supportCheck.get_chat.message || "-"],
                    ["Bot trong group", supportCheck.bot_member.ok ? "OK" : "Lỗi", supportCheck.bot_member.message || "-"],
                    ["Tạo link mời", supportCheck.invite_link.ok ? "OK" : "Lỗi", supportCheck.invite_link.message || "-"],
                  ]}
                />
              ) : (
                <div className="muted">Bấm kiểm tra sau khi lưu Support group ID.</div>
              )}
            </section>
            <section className="panel">
              <PanelHead
                title="Sự kiện support"
                subtitle="Theo tab để dễ lọc, chỉ hiển thị dữ liệu support group và không lẫn thông tin VIP."
              />
              <div className="subtabs">
                <button className={supportTab === "all" ? "active" : ""} onClick={() => setSupportTab("all")}>Tất cả ({supportGroupEvents.length})</button>
                <button className={supportTab === "joined" ? "active" : ""} onClick={() => setSupportTab("joined")}>Join ({supportGroupEvents.filter((item) => item.event_type === "support_joined").length})</button>
                <button className={supportTab === "left" ? "active" : ""} onClick={() => setSupportTab("left")}>Left ({supportGroupEvents.filter((item) => item.event_type === "support_left").length})</button>
                <button className={supportTab === "muted" ? "active" : ""} onClick={() => setSupportTab("muted")}>Đã mute ({supportGroupEvents.filter((item) => item.event_type === "member_muted").length})</button>
                <button className={supportTab === "kicked" ? "active" : ""} onClick={() => setSupportTab("kicked")}>Đã kick ({supportGroupEvents.filter((item) => item.event_type === "member_kicked").length})</button>
              </div>
              <SimpleTable headers={supportEventHeaders} rows={pagedSupportRows} />
              <Pagination page={supportPage} totalPages={totalSupportPages} totalItems={supportEventRows.length} onPage={setSupportPage} label="sự kiện" />
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
                <button className={contentTab === "currency" ? "active" : ""} onClick={() => setContentTab("currency")}>Tiền tệ</button>
                <button className={contentTab === "buttons" ? "active" : ""} onClick={() => setContentTab("buttons")}>Nút bấm</button>
                <button className={contentTab === "commands" ? "active" : ""} onClick={() => setContentTab("commands")}>Lệnh bot</button>
                <button className={contentTab === "alerts" ? "active" : ""} onClick={() => setContentTab("alerts")}>Cảnh báo</button>
                <button className={contentTab === "messages" ? "active" : ""} onClick={() => setContentTab("messages")}>Tin nhắn</button>
                <button className={contentTab === "saleContent" ? "active" : ""} onClick={() => setContentTab("saleContent")}>Flash sale</button>
                <button className={contentTab === "admin" ? "active" : ""} onClick={() => setContentTab("admin")}>Admin ID</button>
                <button className={contentTab === "menu" ? "active" : ""} onClick={() => setContentTab("menu")}>Menu Builder</button>
              </div>
            </section>
            {contentTab === "bot" ? <ConfigEditor title="Cài đặt bot" subtitle="Bảo trì, nhắc hạn, QR 5 phút và tần suất check thanh toán." fields={BOT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(BOT_FIELDS)} /> : null}
            {contentTab === "plans" ? <ConfigEditor title="Tên gói và giá SVIP" subtitle="Các gói chung không thuộc nhóm riêng. Nhóm riêng nằm ở Setup nhóm." fields={PLAN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(PLAN_FIELDS)} /> : null}
            {contentTab === "currency" ? <ConfigEditor title="Tiền tệ hiển thị" subtitle="Chỉ đổi cách hiển thị trong bot/UI. Số tiền QR PayOS vẫn giữ nguyên VND." fields={CURRENCY_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(CURRENCY_FIELDS)} /> : null}
            {contentTab === "buttons" ? <ConfigEditor title="Nút bấm trong bot" subtitle="Text các nút Telegram mặc định: thanh toán, quay lại, gia hạn, mua gói." fields={BUTTON_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(BUTTON_FIELDS)} /> : null}
            {contentTab === "commands" ? <ConfigEditor title="Lệnh Telegram" subtitle="Mô tả các lệnh hiển thị trong menu command của Telegram." fields={COMMAND_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(COMMAND_FIELDS)} /> : null}
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
                  <label className="field"><span>Tên trang</span><input value={menuForm.page_id} onChange={(event) => setMenuForm({ ...menuForm, page_id: event.target.value })} placeholder="VD: main_menu, support_page" /><small>Dùng đúng page_id bạn muốn bot hiển thị.</small></label>
                  <label className="field"><span>Ảnh cover</span><input value={menuForm.image_url} onChange={(event) => setMenuForm({ ...menuForm, image_url: event.target.value })} placeholder="File ID Telegram hoặc URL ảnh" /></label>
                  <label className="field wide"><span>Nội dung trang</span><textarea value={menuForm.body} onChange={(event) => setMenuForm({ ...menuForm, body: event.target.value })} placeholder="Nhập nội dung HTML. Có thể dùng {PRICE_SVIP_30D}, {SALE_LABEL_PRICE_SVIP_30D}..." /></label>
                  <label className="field wide"><span>Nút bấm</span><textarea value={menuForm.layout} onChange={(event) => setMenuForm({ ...menuForm, layout: event.target.value })} placeholder={"Mỗi dòng là một hàng nút. Ví dụ:\\nMua SVIP => buy_full_1m | Hỗ trợ => nav:support_page"} /><small>Có thể dùng biến như {"{BTN_BUY_SVIP_30D}"}.</small></label>
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
              subtitle="Danh sách coupon được tách theo trạng thái. Bấm mã để copy và đánh dấu đã gửi, bấm dòng để chỉnh sửa trong popup."
              action={
                <div className="panel-actions">
                  <button className="btn" onClick={openNewCouponModal}><Plus size={16} /> Thêm coupon</button>
                </div>
              }
            />
            <div className="grid">
              <Metric label="Chưa gửi" value={String(couponTabCounts.unsent)} />
              <Metric label="Đã gửi" value={String(couponTabCounts.sent)} />
              <Metric label="Đã sử dụng" value={String(couponTabCounts.used)} />
              <Metric label="Đã hết hạn" value={String(couponTabCounts.expired)} />
            </div>
            <div className="subtabs">
              <button className={couponTab === "unsent" ? "active" : ""} onClick={() => setCouponTab("unsent")}>Chưa gửi ({couponTabCounts.unsent})</button>
              <button className={couponTab === "sent" ? "active" : ""} onClick={() => setCouponTab("sent")}>Đã gửi ({couponTabCounts.sent})</button>
              <button className={couponTab === "used" ? "active" : ""} onClick={() => setCouponTab("used")}>Đã sử dụng ({couponTabCounts.used})</button>
              <button className={couponTab === "expired" ? "active" : ""} onClick={() => setCouponTab("expired")}>Đã hết hạn ({couponTabCounts.expired})</button>
            </div>
            <SimpleTable
              headers={["Mã", "Loại", "Áp dụng / Gói", "Giảm", "Trạng thái", "Đã gửi", "Đã dùng", "Người dùng gần nhất"]}
              rows={pagedCoupons.map((item) => [
                <button
                  className="coupon-code-copy"
                  disabled={saving === `coupon-copy-${item.code}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    copyCouponAndMarkSent(item);
                  }}
                  title="Copy mã và đánh dấu đã gửi"
                >
                  {item.code}
                </button>,
                String(item.raw_data?.Coupon_Type || "") === "DISCOUNT" ? "Giảm giá" : "Kích hoạt",
                String(item.raw_data?.Coupon_Type || "") === "DISCOUNT" ? appliesLabel(String(item.raw_data?.Applies_To || "")) : planOptionLabel(String(item.raw_data?.Plan_Name || item.plan_name || "-")),
                String(item.raw_data?.Coupon_Type || "") === "DISCOUNT" ? `${String(item.raw_data?.Discount_Percent || 0)}%` : "-",
                <><strong>{couponIsExpired(item) ? "Hết hạn" : item.status}</strong><div className="muted">HSD: {dateText(item.expires_at)}</div></>,
                isCouponSent(item) ? <><strong>Đã gửi</strong><div className="muted">{dateText(couponSentAt(item))}</div></> : "Chưa gửi",
                <><strong>{item.used_count}</strong><div className="muted">Tối đa {item.max_uses || "-"}</div></>,
                <><strong>{couponLastUserName(item)}</strong><div className="muted">{couponLastUserDetail(item)}{item.last_redeemed_at ? ` • ${dateText(item.last_redeemed_at)}` : ""}</div></>,
              ])}
              onRow={(idx) => {
                editCoupon(pagedCoupons[idx]);
              }}
              actions={(idx) => (
                <div className="coupon-row-actions">
                  <label className="sent-toggle" title="Đánh dấu đã gửi coupon">
                    <input
                      type="checkbox"
                      checked={isCouponSent(pagedCoupons[idx])}
                      disabled={saving === `coupon-sent-${pagedCoupons[idx].code}`}
                      onChange={(event) => {
                        event.stopPropagation();
                        toggleCouponSent(pagedCoupons[idx], event.target.checked);
                      }}
                      onClick={(event) => event.stopPropagation()}
                    />
                    <span>Gửi</span>
                  </label>
                  <button className="icon-danger" onClick={(event) => { event.stopPropagation(); removeCoupon(pagedCoupons[idx].code); }} title="Xoá coupon">
                    <Trash2 size={16} />
                  </button>
                </div>
              )}
            />
            <Pagination page={couponPage} totalPages={totalCouponPages} totalItems={visibleCoupons.length} onPage={setCouponPage} label="coupon" />
          </section>
        ) : null}

        {tab === "security" ? (
          <div className="stack">
            <section className="panel">
              <PanelHead
                title="Bảo mật bot và coupon"
                subtitle="Chặn seller, ẩn menu nhập mã và chống dò coupon. Mặc định khách chỉ cần nhắn mã bắt đầu bằng HANGCU_."
                action={
                  <div className="panel-actions">
                    <button className="btn secondary" onClick={() => setSecuritySettingsOpen(true)}><Settings size={16} /> Cài đặt</button>
                    <button className="btn danger" onClick={() => removeBlacklistEntry()} disabled={!blacklistForm.telegram_user_id}><Trash2 size={16} /> Gỡ chặn</button>
                    <button className="btn" onClick={saveBlacklistEntry}><ShieldCheck size={16} /> Lưu blacklist</button>
                  </div>
                }
              />
              <div className="hint compact">Cấu hình bảo mật được tách vào popup để phần blacklist luôn gọn và dễ thao tác.</div>
              <div className="form-grid">
                <label className="field"><span>Telegram ID</span><input value={blacklistForm.telegram_user_id} onChange={(event) => setBlacklistForm({ ...blacklistForm, telegram_user_id: event.target.value.trim() })} placeholder="VD: 123456789" /></label>
                <label className="field"><span>Username</span><input value={blacklistForm.username} onChange={(event) => setBlacklistForm({ ...blacklistForm, username: event.target.value })} placeholder="@username nếu có" /></label>
                <label className="field"><span>Tên hiển thị</span><input value={blacklistForm.full_name} onChange={(event) => setBlacklistForm({ ...blacklistForm, full_name: event.target.value })} placeholder="Tên user" /></label>
                <label className="field"><span>Lý do</span><input value={blacklistForm.reason} onChange={(event) => setBlacklistForm({ ...blacklistForm, reason: event.target.value })} placeholder="VD: Seller gắn link bio" /></label>
              </div>
              <SimpleTable
                headers={["Telegram ID", "Username", "Tên", "Nguồn", "Lý do", "Trạng thái"]}
                rows={blacklist.map((item) => [
                  item.telegram_user_id,
                  item.username || "-",
                  item.full_name || "-",
                  item.source || "-",
                  item.reason || "-",
                  item.is_active ? "Đang chặn" : "Tắt",
                ])}
                onRow={(idx) => {
                  const item = blacklist[idx];
                  setBlacklistForm({
                    telegram_user_id: item.telegram_user_id,
                    username: item.username || "",
                    full_name: item.full_name || "",
                    reason: item.reason || "",
                  });
                }}
                actions={(idx) => (
                  <button className="icon-danger" onClick={(event) => { event.stopPropagation(); removeBlacklistEntry(blacklist[idx].telegram_user_id); }} title="Gỡ blacklist">
                    <Trash2 size={16} />
                  </button>
                )}
              />
            </section>
          </div>
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
              <PanelHead
                title="Cài đặt hệ thống"
                subtitle="Các chu kỳ worker, cleanup và retention đang chạy trên backend Render."
                action={
                  <div className="panel-actions">
                    <button className="btn secondary" onClick={() => setSystemSettingsOpen(true)}><Settings size={16} /> Cài đặt</button>
                    <button className="btn" onClick={handleWebhookReset}><RefreshCw size={16} /> Reset webhook</button>
                  </div>
                }
              />
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

        {couponModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title={couponForm.Code ? `Coupon ${couponForm.Code}` : "Thêm coupon"}
                subtitle="Tạo mã giảm giá, mã kích hoạt hoặc gen nhiều mã cùng điều kiện trong popup này."
                action={<button className="icon-danger" onClick={() => setCouponModalOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="modal-content">
                <div className="panel-actions modal-toolbar">
                  <button className="btn secondary" onClick={generateCouponCode}><RefreshCw size={16} /> Gen mã HANGCU_</button>
                  <input className="mini-input" value={couponBatchCount} onChange={(event) => setCouponBatchCount(event.target.value)} inputMode="numeric" title="Số lượng mã cần gen cùng điều kiện" />
                  <button className="btn secondary" onClick={generateManyCoupons}><RefreshCw size={16} /> Gen nhiều cùng điều kiện</button>
                </div>
                <div className="form-grid">
                  <label className="field"><span>Mã coupon</span><input value={couponForm.Code} onChange={(event) => setCouponForm({ ...couponForm, Code: event.target.value.toUpperCase() })} placeholder="VD: VIP2026" /></label>
                  <label className="field"><span>Loại coupon</span><select value={couponForm.Coupon_Type} onChange={(event) => setCouponForm({ ...couponForm, Coupon_Type: event.target.value })}><option value="DISCOUNT">Giảm giá khi mua QR</option><option value="ACTIVATION">Kích hoạt miễn phí</option></select><small>Giảm giá: khách nhập mã rồi chọn gói để tạo QR đã trừ tiền. Kích hoạt: nhập mã là cấp link ngay.</small></label>
                  {couponForm.Coupon_Type === "DISCOUNT" ? (
                    <label className="field"><span>Phần trăm giảm</span><input value={couponForm.Discount_Percent} onChange={(event) => setCouponForm({ ...couponForm, Discount_Percent: event.target.value })} placeholder="VD: 15" /><small>Nhập 1-99. Nếu muốn miễn phí 100%, dùng loại Kích hoạt miễn phí.</small></label>
                  ) : (
                    <>
                      <label className="field"><span>Gói cấp cho khách</span><select value={couponForm.Plan_Name} onChange={(event) => {
                        const nextPlan = event.target.value;
                        setCouponForm({
                          ...couponForm,
                          Plan_Name: nextPlan,
                          Duration_Days: isLifetimeCouponPlan(nextPlan) ? lifetimeCouponDays : couponForm.Duration_Days,
                        });
                      }}>{planKeyOptions.map((item) => <option key={item} value={item}>{planOptionLabel(item)}</option>)}</select><small>Chọn một gói cố định, hoặc để khách tự chọn group lẻ sau khi nhập mã.</small></label>
                      <label className="field"><span>Số ngày sử dụng</span><input value={lifetimeCouponSelected ? lifetimeCouponDays : couponForm.Duration_Days} onChange={(event) => setCouponForm({ ...couponForm, Duration_Days: event.target.value })} placeholder="VD: 30" disabled={lifetimeCouponSelected} /><small>{lifetimeCouponSelected ? "Gói trọn đời tự dùng số ngày trọn đời, không cần nhập 0." : "Dùng cho coupon kích hoạt theo ngày."}</small></label>
                      <label className="field"><span>Nhãn thời hạn</span><input value={couponForm.Duration_Label} onChange={(event) => setCouponForm({ ...couponForm, Duration_Label: event.target.value })} placeholder="VD: 30 ngày, dùng thử, trọn đời" /><small>{lifetimeCouponSelected ? "Để trống thì bot tự hiện “trọn đời”." : "Để trống thì bot tự dùng “N ngày”."}</small></label>
                      <label className="field"><span>Mẫu tên gói</span><input value={couponForm.Plan_Name_Template} onChange={(event) => setCouponForm({ ...couponForm, Plan_Name_Template: event.target.value })} placeholder="VIP {duration_label} - {group}" /><small>Lưu vào đơn và hiện trong tin thành công. Dùng {"{duration_label}"}, {"{days}"}, {"{group}"}.</small></label>
                      <label className="field"><span>Mẫu nút chọn group</span><input value={couponForm.Button_Template} onChange={(event) => setCouponForm({ ...couponForm, Button_Template: event.target.value })} placeholder="{plan_name}" /><small>Dùng khi khách tự chọn group. Dùng {"{plan_name}"}, {"{duration_label}"}, {"{group}"}.</small></label>
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
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setCouponModalOpen(false)}>Đóng</button>
                <button className="btn danger" onClick={() => removeCoupon()} disabled={!couponForm.Code}><Trash2 size={16} /> Xoá coupon</button>
                <button className="btn" onClick={saveCoupon}><Gift size={16} /> Lưu coupon</button>
              </div>
            </section>
          </div>
        ) : null}

        {renewalSettingsOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title="Cài đặt gia hạn"
                subtitle="Bật/tắt nhắc gia hạn, báo hết hạn và nội dung tin nhắn liên quan đến hạn thành viên."
                action={<button className="icon-danger" onClick={() => setRenewalSettingsOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="form-grid two">
                {RENEWAL_FIELDS.map((field) => (
                  <label className={field.kind === "textarea" ? "field wide" : "field"} key={field.key}>
                    <span>{field.label}</span>
                    {field.kind === "textarea" ? (
                      <textarea value={fieldValues[field.key] || ""} onChange={(event) => setFieldValues({ ...fieldValues, [field.key]: event.target.value })} placeholder={field.placeholder} />
                    ) : field.kind === "select" ? (
                      <select value={fieldValues[field.key] || field.placeholder} onChange={(event) => setFieldValues({ ...fieldValues, [field.key]: event.target.value })}>
                        {(field.options || []).map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                      </select>
                    ) : (
                      <input value={fieldValues[field.key] || ""} onChange={(event) => setFieldValues({ ...fieldValues, [field.key]: event.target.value })} placeholder={field.placeholder} />
                    )}
                    <small>{field.help}</small>
                  </label>
                ))}
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setRenewalSettingsOpen(false)}>Đóng</button>
                <button className="btn" onClick={async () => { await saveFields(RENEWAL_FIELDS); setRenewalSettingsOpen(false); }}><Save size={16} /> Lưu cài đặt</button>
              </div>
            </section>
          </div>
        ) : null}

        {supportSettingsOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title="Cài đặt group hỗ trợ"
                subtitle="Quản lý link join support, bật/tắt mute khi hết hạn và số ngày giữ mute trước khi kick."
                action={<button className="icon-danger" onClick={() => setSupportSettingsOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="form-grid two">
                {SUPPORT_FIELDS.map((field) => (
                  <label className={field.kind === "textarea" ? "field wide" : "field"} key={field.key}>
                    <span>{field.label}</span>
                    {field.kind === "textarea" ? (
                      <textarea value={fieldValues[field.key] || ""} onChange={(event) => setFieldValues({ ...fieldValues, [field.key]: event.target.value })} placeholder={field.placeholder} />
                    ) : field.kind === "select" ? (
                      <select value={fieldValues[field.key] || field.placeholder} onChange={(event) => setFieldValues({ ...fieldValues, [field.key]: event.target.value })}>
                        {(field.options || []).map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                      </select>
                    ) : (
                      <input value={fieldValues[field.key] || ""} onChange={(event) => setFieldValues({ ...fieldValues, [field.key]: event.target.value })} placeholder={field.placeholder} />
                    )}
                    <small>{field.help}</small>
                  </label>
                ))}
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setSupportSettingsOpen(false)}>Đóng</button>
                <button className="btn" onClick={async () => { await saveFields(SUPPORT_FIELDS); setSupportSettingsOpen(false); }}><Save size={16} /> Lưu cài đặt</button>
              </div>
            </section>
          </div>
        ) : null}

        {securitySettingsOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title="Bảo mật bot và coupon"
                subtitle="Chặn seller, ẩn menu nhập mã và chống dò coupon. Mặc định khách chỉ cần nhắn mã bắt đầu bằng HANGCU_."
                action={<button className="icon-danger" onClick={() => setSecuritySettingsOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="form-grid two">
                {SECURITY_FIELDS.map((field) => (
                  <label className={field.kind === "textarea" ? "field wide" : "field"} key={field.key}>
                    <span>{field.label}</span>
                    {field.kind === "textarea" ? (
                      <textarea value={fieldValues[field.key] || ""} onChange={(event) => setFieldValues({ ...fieldValues, [field.key]: event.target.value })} placeholder={field.placeholder} />
                    ) : field.kind === "select" ? (
                      <select value={fieldValues[field.key] || field.placeholder} onChange={(event) => setFieldValues({ ...fieldValues, [field.key]: event.target.value })}>
                        {(field.options || []).map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                      </select>
                    ) : (
                      <input value={fieldValues[field.key] || ""} onChange={(event) => setFieldValues({ ...fieldValues, [field.key]: event.target.value })} placeholder={field.placeholder} />
                    )}
                    <small>{field.help}</small>
                  </label>
                ))}
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setSecuritySettingsOpen(false)}>Đóng</button>
                <button className="btn" onClick={async () => { await saveFields(SECURITY_FIELDS); setSecuritySettingsOpen(false); }}><Save size={16} /> Lưu cài đặt</button>
              </div>
            </section>
          </div>
        ) : null}

        {systemSettingsOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title="Cài đặt hệ thống"
                subtitle="Các chu kỳ worker, cleanup và retention đang chạy trên backend Render."
                action={<button className="icon-danger" onClick={() => setSystemSettingsOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="form-grid two">
                {SYSTEM_FIELDS.map((field) => (
                  <label className={field.kind === "textarea" ? "field wide" : "field"} key={field.key}>
                    <span>{field.label}</span>
                    {field.kind === "textarea" ? (
                      <textarea value={fieldValues[field.key] || ""} onChange={(event) => setFieldValues({ ...fieldValues, [field.key]: event.target.value })} placeholder={field.placeholder} />
                    ) : field.kind === "select" ? (
                      <select value={fieldValues[field.key] || field.placeholder} onChange={(event) => setFieldValues({ ...fieldValues, [field.key]: event.target.value })}>
                        {(field.options || []).map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                      </select>
                    ) : (
                      <input value={fieldValues[field.key] || ""} onChange={(event) => setFieldValues({ ...fieldValues, [field.key]: event.target.value })} placeholder={field.placeholder} />
                    )}
                    <small>{field.help}</small>
                  </label>
                ))}
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setSystemSettingsOpen(false)}>Đóng</button>
                <button className="btn" onClick={async () => { await saveFields(SYSTEM_FIELDS); setSystemSettingsOpen(false); }}><Save size={16} /> Lưu cài đặt</button>
              </div>
            </section>
          </div>
        ) : null}

        {manualOrderModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title="Tạo đơn thủ công"
                subtitle="Nhập thông tin khách, tạo order PAID và gen link join group."
                action={<button className="icon-danger" onClick={() => setManualOrderModalOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="form-grid">
                <label className="field">
                  <span>Telegram ID</span>
                  <input value={manualOrderForm.telegram_user_id} onChange={(event) => setManualOrderForm({ ...manualOrderForm, telegram_user_id: event.target.value })} placeholder="VD: 7344961485" />
                  <small>ID số của khách. Không dùng username @.</small>
                </label>
                <label className="field">
                  <span>Tên khách</span>
                  <input value={manualOrderForm.full_name} onChange={(event) => setManualOrderForm({ ...manualOrderForm, full_name: event.target.value })} placeholder="Tên hiển thị để dễ quản lý" />
                </label>
                <label className="field">
                  <span>Gói cấp cho khách</span>
                  <select value={manualOrderForm.plan_key} onChange={(event) => changeManualPlanKey(event.target.value)}>
                    {manualPlanKeyOptions.map((item) => <option key={item} value={item}>{item === "CUSTOM" ? "Tự nhập tên gói" : planOptionLabel(item)}</option>)}
                  </select>
                </label>
                <label className="field wide">
                  <span>Tên gói lưu vào đơn</span>
                  <input value={manualOrderForm.plan_key === "CUSTOM" ? manualOrderForm.plan_name : manualPlanNameFromKey(manualOrderForm.plan_key)} onChange={(event) => setManualOrderForm({ ...manualOrderForm, plan_name: event.target.value, plan_key: "CUSTOM" })} placeholder="VD: VIP 30 Ngày - Hang Cú Prime" />
                  <small>Với gói tự nhập, nên chứa đúng tên group đang cấu hình trong Setup nhóm.</small>
                </label>
                <label className="field">
                  <span>Số tiền</span>
                  <input value={manualOrderForm.amount} onChange={(event) => setManualOrderForm({ ...manualOrderForm, amount: event.target.value })} placeholder="0" inputMode="numeric" />
                </label>
                <label className="field">
                  <span>Số ngày sử dụng</span>
                  <input value={manualOrderForm.duration_days} onChange={(event) => setManualOrderForm({ ...manualOrderForm, duration_days: event.target.value })} placeholder="30" inputMode="numeric" />
                  <small>Chỉ dùng khi ngày hết hạn trống.</small>
                </label>
                <label className="field">
                  <span>Ngày hết hạn cụ thể</span>
                  <input type="datetime-local" value={manualOrderForm.expire_at} onChange={(event) => setManualOrderForm({ ...manualOrderForm, expire_at: event.target.value })} />
                </label>
                <label className="field">
                  <span>Coupon / ghi chú mã</span>
                  <input value={manualOrderForm.coupon_code} onChange={(event) => setManualOrderForm({ ...manualOrderForm, coupon_code: event.target.value.toUpperCase() })} placeholder="VD: MANUAL_ADMIN" />
                </label>
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setManualOrderModalOpen(false)}>Đóng</button>
                <button className="btn" onClick={saveManualOrder} disabled={saving === "manual-order"}>{saving === "manual-order" ? <Loader2 size={18} className="spin" /> : <Plus size={18} />} Tạo đơn & gen link</button>
              </div>
              {manualOrderResult ? (
                <div className="form-grid two">
                  <label className="field wide">
                    <span>Link đã tạo</span>
                    <textarea readOnly value={[
                      `Order: ${manualOrderResult.order_id}`,
                      `Gói: ${manualOrderResult.plan_name}`,
                      `Hết hạn: ${manualOrderResult.expire_at}`,
                      "",
                      stripHtml(manualOrderResult.links_text),
                      manualOrderResult.support_text,
                    ].filter(Boolean).join("\n")} />
                  </label>
                  <div className="field wide">
                    <button className="btn secondary" onClick={copyManualLinks}>Copy toàn bộ link</button>
                    {manualOrderResult.support_error ? <small className="danger-text">Group hỗ trợ chưa tạo được link: {manualOrderResult.support_error}</small> : <small>Đơn đã được ghi PAID và link chỉ dùng được 1 người.</small>}
                  </div>
                </div>
              ) : null}
            </section>
          </div>
        ) : null}

        {customerModalOpen && selectedCustomer ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel customer-modal">
              <PanelHead
                title={selectedCustomer.name}
                subtitle={`Telegram ID: ${selectedCustomer.id}`}
                action={<button className="icon-danger" onClick={() => setCustomerModalOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="customer-detail modal-content">
                <div className="customer-head">
                  <span className={selectedCustomer.activeOrders.length ? "status paid" : "status expired"}>{selectedCustomer.activeOrders.length ? "Đang còn hạn" : "Hết hạn / chờ kick"}</span>
                </div>
                <div className="customer-facts">
                  <div><span>Đơn PAID</span><strong>{selectedCustomer.paidOrders.length}</strong></div>
                  <div><span>Gói active</span><strong>{selectedCustomer.activeOrders.length}</strong></div>
                  <div><span>Hạn gần nhất</span><strong>{dateText(selectedCustomer.latestExpire)}</strong></div>
                  <div><span>Tổng tiền</span><strong>{money(selectedCustomer.revenue)}</strong></div>
                </div>
                <div className="customer-tags">
                  {selectedCustomer.groups.map((item) => <span key={`g-${item}`}>{item}</span>)}
                  {selectedCustomer.coupons.map((item) => <span key={`c-${item}`}>Coupon: {item}</span>)}
                </div>
                <CustomerOrdersTable orders={selectedCustomer.orders} saving={saving} onExpireChange={changeOrderExpire} onPlanChange={changeOrderPlan} onStatusChange={changeOrderStatus} />
              </div>
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

function CustomerOrdersTable({ orders, saving, onExpireChange, onPlanChange, onStatusChange }: { orders: Order[]; saving: string; onExpireChange: (orderId: string, expireAt: string) => void; onPlanChange: (orderId: string, planName: string) => void; onStatusChange: (orderId: string, status: string) => void }) {
  const sorted = [...orders].sort((a, b) => new Date(b.created_at || "").getTime() - new Date(a.created_at || "").getTime());
  return (
    <div className="table-wrap">
      <table>
        <thead><tr><th>Đơn</th><th>Gói / Group</th><th>Coupon</th><th>Hạn dùng</th><th>Trạng thái</th><th>Cập nhật</th></tr></thead>
        <tbody>
          {sorted.map((order) => (
            <tr key={order.order_id}>
              <td><strong>{order.order_id}</strong><div className="muted">{dateText(order.created_at)}</div></td>
              <td>
                <div className="plan-editor">
                  <input defaultValue={order.plan_name} id={`plan-${order.order_id}`} />
                  <button className="btn secondary" disabled={saving === `order-plan-${order.order_id}`} onClick={() => {
                    const input = document.getElementById(`plan-${order.order_id}`) as HTMLInputElement | null;
                    onPlanChange(order.order_id, input?.value || "");
                  }}>Lưu tên gói</button>
                </div>
                <div className="muted">{groupNamesForOrder(order).join(", ") || orderPlanKind(order)}</div>
              </td>
              <td>{orderCouponCode(order) ? <><strong>{orderCouponCode(order)}</strong><div className="muted">{Number(order.amount || 0) === 0 ? "Kích hoạt miễn phí" : money(order.coupon_discount_amount || 0)}</div></> : "-"}</td>
              <td>{dateText(order.expire_at)}<div className="muted">{isOrderActive(order) ? "Còn hạn" : "Không active"}</div></td>
              <td>
                <select value={order.status} disabled={saving === `order-${order.order_id}`} onChange={(event) => onStatusChange(order.order_id, event.target.value)}>
                  <option value="PENDING">PENDING</option>
                  <option value="PAID">PAID</option>
                  <option value="CANCELLED">CANCELLED</option>
                  <option value="EXPIRED">EXPIRED</option>
                </select>
              </td>
              <td>
                <div className="expire-editor">
                  <input type="datetime-local" defaultValue={orderExpireValue(order.expire_at)} id={`expire-${order.order_id}`} />
                  <button className="btn secondary" disabled={saving === `order-expire-${order.order_id}`} onClick={() => {
                    const input = document.getElementById(`expire-${order.order_id}`) as HTMLInputElement | null;
                    onExpireChange(order.order_id, input?.value || "");
                  }}>Lưu hạn</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
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
              <td>{orderCouponCode(order) ? <><strong>{orderCouponCode(order)}</strong><div className="muted">{Number(order.amount || 0) === 0 ? "Kích hoạt miễn phí" : `-${order.coupon_discount_percent || 0}% / ${money(order.coupon_discount_amount || 0)}`}</div></> : "-"}</td>
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

function Pagination({ page, totalPages, totalItems, onPage, label = "đơn" }: { page: number; totalPages: number; totalItems: number; onPage: (page: number) => void; label?: string }) {
  const safePage = Math.min(page, totalPages);
  return (
    <div className="pagination">
      <span>{totalItems} {label} • Trang {safePage}/{totalPages}</span>
      <div>
        <button className="btn secondary" disabled={safePage <= 1} onClick={() => onPage(safePage - 1)}>Trước</button>
        <button className="btn secondary" disabled={safePage >= totalPages} onClick={() => onPage(safePage + 1)}>Sau</button>
      </div>
    </div>
  );
}

function SimpleTable({ headers, rows, onRow, actions }: { headers: string[]; rows: ReactNode[][]; onRow?: (index: number) => void; actions?: (index: number) => ReactNode }) {
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
