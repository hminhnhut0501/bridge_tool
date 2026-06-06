"use client";

import {
  Activity,
  BadgePercent,
  BarChart3,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  Eye,
  FileText,
  Gift,
  Loader2,
  Megaphone,
  PauseCircle,
  Pencil,
  PlayCircle,
  Plus,
  RefreshCw,
  Save,
  Send,
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
  BroadcastCampaign,
  BroadcastRecipient,
  CampaignPreview,
  ChannelPost,
  ChannelPostEvent,
  ConfigRow,
  BlacklistEntry,
  Coupon,
  KickAuditRow,
  ManualOrderResult,
  MenuPage,
  Order,
  SaleRule,
  SupportEvent,
  UserRow,
  WebhookInfo,
  checkSupportGroup,
  cancelCampaign,
  channelPostAction,
  createChannelPost,
  createCampaign,
  createCoupon,
  createCoupons,
  createManualOrder,
  deleteConfig,
  deleteBlacklist,
  deleteCoupon,
  deleteHiddenCode,
  deleteHiddenGroup,
  deleteMenuPage,
  deleteSaleRule,
  getConfig,
  getActivityEvents,
  getBlacklist,
  getCampaignRecipients,
  getCampaigns,
  getChannelPostEvents,
  getChannelPosts,
  getCoupons,
  getHiddenCodes,
  getHiddenGroups,
  getHiddenRedemptions,
  getKickAudit,
  getMenuPages,
  getOrders,
  getSaleRules,
  getSupportEvents,
  getUsers,
  getWebhookInfo,
  kickAuditMember,
  pauseCampaign,
  previewCampaign,
  resetWebhook,
  startCampaign,
  updateChannelPost,
  updateConfigs,
  updateMenuPage,
  updateOrder,
  updateOrderStatus,
  upsertBlacklist,
  upsertHiddenCode,
  upsertHiddenGroup,
  type HiddenRedemption,
  upsertSaleRule,
  type HiddenCode,
  type HiddenGroup,
  type SupportGroupCheck,
} from "@/lib/api";

type Tab = "overview" | "analytics" | "setup" | "orders" | "customers" | "activityLog" | "campaigns" | "channelPosts" | "renewals" | "supportGroup" | "content" | "botVi" | "botEn" | "botTools" | "menuBuilder" | "coupons" | "security" | "sales" | "system";
type ContentSubTab = "bot" | "payment" | "currency" | "admin";
type BotUiSubTab = "plans" | "buttons" | "messages" | "saleContent" | "groups";
type BotToolsSubTab = "commandsVi" | "commandsEn" | "alertsVi" | "alertsEn";
type MenuLanguage = "vi" | "en";
type OrderPeriod = "all" | "today" | "7d" | "month" | "year";
type GroupMode = "none" | "day" | "month";
type CustomerStatusFilter = "all" | "active" | "expired" | "paid" | "coupon";
type LogDirectionFilter = "all" | "user" | "bot";
type RenewalSubTab = "soon" | "today" | "reminded" | "expiredNotice" | "kicked" | "audit";
type SupportSubTab = "all" | "joined" | "left" | "muted" | "kicked";
type CouponTab = "unsent" | "sent" | "used" | "expired";
type ChannelPostTab = "draft" | "queue" | "scheduled" | "sent" | "failed" | "deleted";
type HiddenSetupView = "groups" | "codes" | "activity";
type HiddenGroupFormState = {
  id: string;
  name: string;
  description: string;
  chat_id: string;
  price_1m_vnd: string;
  price_life_vnd: string;
  price_1m_usd: string;
  price_life_usd: string;
  duration_1m_days: string;
  lifetime_days: string;
  image_url: string;
  requirement_type: string;
  requirement_value: string;
  sort_order: string;
  is_active: boolean;
};
type HiddenCodeFormState = {
  code: string;
  name: string;
  description: string;
  scope_type: string;
  group_ids: string[];
  requirement_type: string;
  requirement_value: string;
  max_uses: string;
  used_count: string;
  valid_from: string;
  valid_until: string;
  is_active: boolean;
};

type Notice = {
  type: "ok" | "error";
  text: string;
};

type LoadScope = Tab | "all";
type LoadOptions = {
  silent?: boolean;
  resetPages?: boolean;
  scope?: LoadScope;
  mode?: "full" | "light";
};

const TAB_VALUES: Tab[] = ["overview", "analytics", "setup", "orders", "customers", "activityLog", "campaigns", "channelPosts", "renewals", "supportGroup", "content", "botVi", "botEn", "botTools", "menuBuilder", "coupons", "security", "sales", "system"];
const TAB_STORAGE_KEY = "prive_admin_tab";
const AUTO_REFRESH_SECONDS = 60;

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
    key: "BOT_SCHEDULE_ENABLED",
    label: "Bật lịch hoạt động tự động",
    placeholder: "OFF",
    help: "Bật ON để bot chỉ phục vụ khách trong các khung giờ đã đặt. Admin và tác vụ nền vẫn hoạt động ngoài giờ.",
    kind: "select",
    options: [
      { label: "Tắt", value: "OFF" },
      { label: "Bật", value: "ON" },
    ],
  },
  {
    key: "LANGUAGE_SWITCH_ENABLED",
    label: "Hiện nút đổi ngôn ngữ",
    placeholder: "ON",
    help: "Bật để hiện nút English/Tiếng Việt ở menu chính. Khi tắt, hệ thống cũng ẩn các nút set_lang: đã khai báo trong Menu Builder.",
    kind: "select",
    options: [
      { label: "Tắt", value: "OFF" },
      { label: "Bật", value: "ON" },
    ],
  },
  {
    key: "BOT_ACTIVE_HOURS",
    label: "Khung giờ bot hoạt động",
    placeholder: "08:00-23:00",
    help: "Giờ Việt Nam. Có thể nhập nhiều khung, cách nhau bằng dấu phẩy, ví dụ 08:00-12:00,13:30-23:00. Khung qua đêm dùng 20:00-02:00.",
  },
  {
    key: "MSG_MAINTENANCE",
    label: "Thông báo bảo trì",
    placeholder: "Hệ thống đang bảo trì, vui lòng quay lại sau.",
    help: "Tin nhắn gửi cho khách khi bot đang bảo trì.",
    kind: "textarea",
  },
  {
    key: "MSG_OUTSIDE_ACTIVE_HOURS",
    label: "Thông báo ngoài giờ hoạt động",
    placeholder: "🛠 <b>BOT ĐANG NGOÀI GIỜ HOẠT ĐỘNG</b>\\n\\nBot hiện ở chế độ bảo trì. Vui lòng quay lại trong khung giờ hoạt động.",
    help: "Tin nhắn gửi cho khách khi lịch tự động chuyển bot sang chế độ bảo trì.",
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

const PAYMENT_FIELDS: ConfigField[] = [
  {
    key: "PAYOS_PAYMENT_ENABLED",
    label: "Bật thanh toán PayOS",
    placeholder: "ON",
    help: "PayOS/VietQR dành cho thanh toán VND tại Việt Nam.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "PAYPAL_PAYMENT_ENABLED",
    label: "Bật thanh toán PayPal",
    placeholder: "OFF",
    help: "Chỉ hoạt động khi Render đã có PAYPAL_CLIENT_ID và PAYPAL_CLIENT_SECRET.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "NOWPAYMENTS_PAYMENT_ENABLED",
    label: "Bật thanh toán Crypto NOWPayments",
    placeholder: "OFF",
    help: "Chỉ hoạt động khi Render đã có NOWPAYMENTS_API_KEY và NOWPAYMENTS_IPN_SECRET.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "TRON_USDT_PAYMENT_ENABLED",
    label: "Bật USDT TRC20 tự quét",
    placeholder: "OFF",
    help: "Cổng tự build: bot hiển thị ví USDT TRC20 và tự quét TronGrid. Cần cấu hình ví nhận.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "PAYMENT_PROVIDERS_VI",
    label: "Các cổng cho tiếng Việt",
    placeholder: "PAYOS,PAYPAL,TRON_USDT",
    help: "Có thể dùng PAYOS,PAYPAL,TRON_USDT. PayPal/USDT dùng bảng giá USD riêng.",
  },
  {
    key: "PAYMENT_PROVIDERS_EN",
    label: "Các cổng cho tiếng Anh",
    placeholder: "PAYPAL,TRON_USDT",
    help: "Khuyến nghị dùng PAYPAL,TRON_USDT. PayOS chỉ nhận giá VNĐ.",
  },
  {
    key: "PAYPAL_BRAND_NAME",
    label: "Tên shop trên PayPal",
    placeholder: "Prive Bot",
    help: "Tên hiển thị trên trang thanh toán PayPal.",
  },
  {
    key: "NOWPAYMENTS_PRICE_CURRENCY",
    label: "Tiền tệ giá Crypto",
    placeholder: "USD",
    help: "Nên giữ USD để dùng bảng giá USD riêng, không quy đổi từ VNĐ.",
  },
  {
    key: "NOWPAYMENTS_PAY_CURRENCY",
    label: "Coin cố định",
    placeholder: "Để trống hoặc usdttrc20",
    help: "Để trống để khách tự chọn coin/network. Nhập usdttrc20 nếu muốn ép thanh toán USDT TRC20.",
  },
  {
    key: "NOWPAYMENTS_IPN_CALLBACK_URL",
    label: "NOWPayments IPN URL",
    placeholder: "https://prive-bot-backend.onrender.com/payment-webhooks/nowpayments",
    help: "URL callback để NOWPayments báo trạng thái. Có thể để trống nếu Render có PUBLIC_BASE_URL hoặc RENDER_EXTERNAL_URL.",
  },
  {
    key: "NOWPAYMENTS_TTL_SECONDS",
    label: "Thời gian chờ Crypto",
    placeholder: "3600",
    help: "Số giây bot giữ đơn crypto ở trạng thái chờ. Mặc định 3600 giây vì blockchain xác nhận chậm hơn VietQR.",
  },
  {
    key: "TRON_USDT_WALLET_ADDRESS",
    label: "Ví nhận USDT TRC20",
    placeholder: "T...",
    help: "Địa chỉ ví TRON nhận USDT TRC20. Không nhập seed/private key vào đây.",
  },
  {
    key: "TRON_USDT_UNIQUE_AMOUNT_ENABLED",
    label: "Tạo số USDT riêng cho từng đơn",
    placeholder: "ON",
    help: "Bật để bot thêm phần lẻ 0.000001-0.000999 vào số USDT, giúp phân biệt nhiều khách mua cùng giá.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "TRON_USDT_TTL_SECONDS",
    label: "Thời gian chờ USDT",
    placeholder: "7200",
    help: "Số giây bot giữ đơn USDT ở trạng thái chờ. Mặc định 2 giờ.",
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
    placeholder: "1800",
    help: "Số giây giữa các vòng quét hạn/gia hạn. Backend tối thiểu 1800 giây để nhẹ Render free.",
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
    key: "MSG_PAYPAL_BILL_TEMPLATE",
    label: "Nội dung bill PayPal",
    placeholder: "💳 <b>PAYPAL PAYMENT</b>\\n\\n🎁 Plan: <b>{plan}</b>\\n💵 Amount: <b>${paypal_amount} USD</b>\\n🧾 Order: <code>{desc}</code>",
    help: "Dùng biến {plan}, {amount}, {paypal_amount}, {desc}.",
    kind: "textarea",
  },
  {
    key: "MSG_NOWPAYMENTS_BILL_TEMPLATE",
    label: "Nội dung bill Crypto NOWPayments",
    placeholder: "₿ <b>THANH TOÁN CRYPTO</b>\\n\\n🎁 Gói: <b>{plan}</b>\\n💵 Số tiền: <b>{amount}</b>\\n🧾 Đơn: <code>{desc}</code>\\n\\nSau khi blockchain xác nhận xong, bot sẽ tự cấp quyền. Quá trình này có thể mất vài phút.",
    help: "Dùng biến {plan}, {amount}, {desc}. Đây là tin bot gửi kèm nút thanh toán Crypto.",
    kind: "textarea",
  },
  {
    key: "MSG_TRON_USDT_BILL_TEMPLATE",
    label: "Nội dung bill USDT TRC20",
    placeholder: "₮ <b>THANH TOÁN USDT TRC20</b>\\n\\n🎁 Gói: <b>{plan}</b>\\n💵 Số tiền: <code>{usdt_amount} USDT</code>\\n🌐 Network: <b>TRC20</b>\\n👛 Ví nhận:\\n<code>{wallet}</code>\\n🧾 Đơn: <code>{desc}</code>\\n\\nVui lòng chuyển đúng số USDT trên. Bot sẽ tự quét blockchain và cấp quyền sau khi giao dịch xác nhận.",
    help: "Dùng biến {plan}, {amount}, {usdt_amount}, {wallet}, {desc}.",
    kind: "textarea",
  },
  {
    key: "MSG_CHOOSE_PAYMENT_PROVIDER",
    label: "Tin chọn phương thức thanh toán",
    placeholder: "Chọn phương thức thanh toán. VietQR dùng VNĐ; PayPal và Crypto dùng giá USD riêng.",
    help: "Tin bot gửi khi một gói có nhiều phương thức thanh toán được bật.",
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
  { key: "BTN_PAYPAL_CHECKOUT", label: "Nút thanh toán PayPal", placeholder: "💳 Pay with PayPal", help: "Nút mở trang checkout PayPal." },
  { key: "BTN_NOWPAYMENTS_CHECKOUT", label: "Nút thanh toán Crypto", placeholder: "₿ Thanh toán Crypto", help: "Nút mở trang checkout NOWPayments." },
  { key: "BTN_TRONSCAN_ADDRESS", label: "Nút xem ví Tronscan", placeholder: "🔎 Xem ví trên Tronscan", help: "Nút dưới bill USDT TRC20." },
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
  { key: "PLAN_G_1M", label: "Tiền tố gói group lẻ 30 ngày", placeholder: "VIP 30 Ngày", help: "Ghép với tên group, ví dụ: VIP 30 Ngày - Hang Cú Prime." },
  { key: "PLAN_G_LIFE", label: "Tiền tố gói group lẻ trọn đời", placeholder: "VIP Trọn Đời", help: "Ghép với tên group, ví dụ: VIP Trọn Đời - Hang Cú Prime." },
  { key: "PRICE_SVIP_30D", label: "Giá SVIP 30 ngày", placeholder: "99000", help: "Nhập số tiền VND, không cần dấu chấm." },
  { key: "PRICE_SVIP_LIFE", label: "Giá SVIP trọn đời", placeholder: "499000", help: "Nhập số tiền VND, không cần dấu chấm." },
  { key: "PRICE_SVIP_30D_USD", label: "Giá USD SVIP 30 ngày", placeholder: "4.99", help: "Giá PayPal độc lập, không quy đổi từ VNĐ." },
  { key: "PRICE_SVIP_LIFE_USD", label: "Giá USD SVIP trọn đời", placeholder: "19.99", help: "Giá PayPal độc lập, không quy đổi từ VNĐ." },
  { key: "BTN_BUY_SVIP_30D", label: "Nút mua SVIP 30 ngày", placeholder: "MUA 30 NGÀY", help: "Text nút trong bot." },
  { key: "BTN_BUY_SVIP_LIFE", label: "Nút mua SVIP trọn đời", placeholder: "MUA TRỌN ĐỜI", help: "Text nút trong bot." },
];

function localizedFields(fields: ConfigField[], language: "EN"): ConfigField[] {
  return fields.map((field) => ({
    ...field,
    key: `${field.key}_${language}`,
    label: `${field.label} - tiếng Anh`,
    help: `Dữ liệu riêng cho Bot tiếng Anh. ${field.help}`,
  }));
}

const PLAN_DISPLAY_FIELDS = PLAN_FIELDS.filter((field) => !field.key.startsWith("PRICE_"));
const SVIP_PRICE_FIELDS = PLAN_FIELDS.filter((field) => field.key.startsWith("PRICE_"));
const PLAN_VI_FIELDS = PLAN_DISPLAY_FIELDS;
const PLAN_EN_FIELDS: ConfigField[] = localizedFields(PLAN_DISPLAY_FIELDS, "EN");
const BUTTON_EN_FIELDS = localizedFields(BUTTON_FIELDS, "EN");
const MESSAGE_EN_FIELDS = localizedFields(MESSAGE_FIELDS, "EN");
const COMMAND_EN_FIELDS = localizedFields(COMMAND_FIELDS, "EN");
const ALERT_EN_FIELDS = localizedFields(ALERT_FIELDS, "EN");
const SALE_CONTENT_EN_FIELDS = localizedFields(SALE_CONTENT_FIELDS.filter((field) => field.key !== "SALE_ANNOUNCE_ENABLED"), "EN");

const PRICE_KEY_OPTIONS = [
  "PRICE_SVIP_30D",
  "PRICE_SVIP_LIFE",
  "PRICE_SVIP_30D_USD",
  "PRICE_SVIP_LIFE_USD",
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

const EMPTY_CAMPAIGN_FORM = {
  title: "",
  target_segment: "ALL",
  plan_filter: "ALL",
  plan_match_scope: "ANY_PAID",
  message: "",
  delay_seconds: "5",
  batch_size: "20",
  parse_mode: "HTML",
};

const EMPTY_CHANNEL_POST_FORM = {
  id: "",
  status: "draft",
  target_chat_id: "",
  title: "",
  image_ref: "",
  content: "",
  buttons_text: "",
  parse_mode: "HTML",
  disable_web_page_preview: false,
  scheduled_at: "",
  delete_at: "",
  repeat_daily: false,
  sync_bot_schedule: false,
  notes: "",
};

const HIDDEN_REQUIREMENT_OPTIONS = [
  { value: "NONE", label: "Không yêu cầu thêm" },
  { value: "SVIP_ACTIVE", label: "Phải có SVIP active" },
  { value: "SVIP_LIFETIME", label: "Phải có SVIP lifetime" },
  { value: "PLAN_TOKEN_ACTIVE", label: "Phải có plan token active" },
  { value: "PLAN_TOKEN_LIFETIME", label: "Phải có plan token lifetime" },
];

const HIDDEN_SCOPE_OPTIONS = [
  { value: "SELECTED_GROUPS", label: "Chỉ hiện group được chọn" },
  { value: "ALL_ACTIVE_HIDDEN_GROUPS", label: "Hiện toàn bộ hidden group đang bật" },
];

const EMPTY_HIDDEN_GROUP_FORM: HiddenGroupFormState = {
  id: "",
  name: "",
  description: "",
  chat_id: "",
  price_1m_vnd: "0",
  price_life_vnd: "0",
  price_1m_usd: "0",
  price_life_usd: "0",
  duration_1m_days: "30",
  lifetime_days: "3650",
  image_url: "",
  requirement_type: "NONE",
  requirement_value: "",
  sort_order: "1",
  is_active: true,
};

const EMPTY_HIDDEN_CODE_FORM: HiddenCodeFormState = {
  code: "",
  name: "",
  description: "",
  scope_type: "SELECTED_GROUPS",
  group_ids: [],
  requirement_type: "SVIP_LIFETIME",
  requirement_value: "",
  max_uses: "0",
  used_count: "0",
  valid_from: "",
  valid_until: "",
  is_active: true,
};

const DEFAULT_LIFETIME_DAYS = "36500";

const ORDER_PAGE_SIZE = 25;
const CUSTOMER_PAGE_SIZE = 25;
const LOG_PAGE_SIZE = 80;
const RENEWAL_PAGE_SIZE = 25;
const SUPPORT_PAGE_SIZE = 25;
const COUPON_PAGE_SIZE = 20;
const CAMPAIGN_RECIPIENT_PAGE_SIZE = 20;
const CHANNEL_POST_PAGE_SIZE = 12;

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

function displayText(value: unknown) {
  const text = value === null || value === undefined ? "" : String(value).trim();
  return text === "-" ? "" : text;
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

function orderMoney(order: Order, value = order.amount) {
  if ((order.payment_currency || "VND").toUpperCase() === "USD") {
    return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value || 0);
  }
  return money(value || 0);
}

function ordersMoney(orders: Order[], field: "amount" | "coupon_discount_amount" = "amount") {
  const totals = orders.reduce((sum, order) => {
    const currency = (order.payment_currency || "VND").toUpperCase() === "USD" ? "USD" : "VND";
    sum[currency] += Number(order[field] || 0);
    return sum;
  }, { VND: 0, USD: 0 });
  const parts = [];
  if (totals.VND || !totals.USD) parts.push(money(totals.VND));
  if (totals.USD) parts.push(new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(totals.USD));
  return parts.join(" + ");
}

function ordersAverageMoney(orders: Order[]) {
  const paid = orders.filter((order) => order.status === "PAID");
  const byCurrency = {
    VND: paid.filter((order) => (order.payment_currency || "VND").toUpperCase() !== "USD"),
    USD: paid.filter((order) => (order.payment_currency || "VND").toUpperCase() === "USD"),
  };
  const parts = [];
  if (byCurrency.VND.length) parts.push(money(byCurrency.VND.reduce((sum, order) => sum + Number(order.amount || 0), 0) / byCurrency.VND.length));
  if (byCurrency.USD.length) {
    const average = byCurrency.USD.reduce((sum, order) => sum + Number(order.amount || 0), 0) / byCurrency.USD.length;
    parts.push(new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(average));
  }
  return parts.join(" + ") || money(0);
}

function dateText(value: string | null | undefined) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("vi-VN", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

function dateTimeInputValue(value: string | null | undefined) {
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

function datetimeLocalToIso(value: string) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}

function hiddenRequirementLabel(value: string | null | undefined) {
  return HIDDEN_REQUIREMENT_OPTIONS.find((item) => item.value === String(value || "").toUpperCase())?.label || "Không yêu cầu thêm";
}

function hiddenScopeLabel(value: string | null | undefined) {
  return HIDDEN_SCOPE_OPTIONS.find((item) => item.value === String(value || "").toUpperCase())?.label || "Chọn thủ công";
}

function hiddenRequirementNeedsValue(value: string | null | undefined) {
  return ["PLAN_TOKEN_ACTIVE", "PLAN_TOKEN_LIFETIME"].includes(String(value || "").toUpperCase());
}

function hiddenSlug(value: string) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/đ/g, "d")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .slice(0, 48);
}

function hiddenCodeSeed(value: string) {
  return hiddenSlug(value).replace(/_/g, "-").toUpperCase();
}

function hiddenValidityText(code: HiddenCode) {
  if (!code.valid_from && !code.valid_until) return "Không giới hạn thời gian";
  return `${dateText(code.valid_from) === "-" ? "Ngay" : dateText(code.valid_from)} → ${dateText(code.valid_until) === "-" ? "Vô hạn" : dateText(code.valid_until)}`;
}

function hiddenGroupToForm(item?: HiddenGroup, nextSort = 1): HiddenGroupFormState {
  return {
    id: item?.id || "",
    name: item?.name || "",
    description: item?.description || "",
    chat_id: item?.chat_id || "",
    price_1m_vnd: String(item?.price_1m_vnd ?? 0),
    price_life_vnd: String(item?.price_life_vnd ?? 0),
    price_1m_usd: String(item?.price_1m_usd ?? 0),
    price_life_usd: String(item?.price_life_usd ?? 0),
    duration_1m_days: String(item?.duration_1m_days ?? 30),
    lifetime_days: String(item?.lifetime_days ?? 3650),
    image_url: item?.image_url || "",
    requirement_type: item?.requirement_type || "NONE",
    requirement_value: item?.requirement_value || "",
    sort_order: String(item?.sort_order ?? nextSort),
    is_active: item?.is_active ?? true,
  };
}

function hiddenCodeToForm(item?: HiddenCode, defaultGroupIds: string[] = []): HiddenCodeFormState {
  return {
    code: item?.code || "",
    name: item?.name || "",
    description: item?.description || "",
    scope_type: item?.scope_type || "SELECTED_GROUPS",
    group_ids: item?.group_ids?.length ? [...item.group_ids] : [...defaultGroupIds],
    requirement_type: item?.requirement_type || "SVIP_LIFETIME",
    requirement_value: item?.requirement_value || "",
    max_uses: String(item?.max_uses ?? 0),
    used_count: String(item?.used_count ?? 0),
    valid_from: dateTimeInputValue(item?.valid_from),
    valid_until: dateTimeInputValue(item?.valid_until),
    is_active: item?.is_active ?? true,
  };
}

function channelPostTabFor(post: ChannelPost): ChannelPostTab {
  const status = String(post.status || "draft").toLowerCase();
  if (["queued", "pending", "sending"].includes(status)) return "queue";
  if (status === "scheduled") return "scheduled";
  if (["sent", "delete_scheduled", "deleting"].includes(status)) return "sent";
  if (["failed", "delete_failed"].includes(status)) return "failed";
  if (status === "deleted") return "deleted";
  return "draft";
}

function channelPostStatusLabel(status: string) {
  const labels: Record<string, string> = {
    draft: "Nháp",
    queued: "Chờ gửi",
    pending: "Chờ gửi",
    sending: "Đang gửi",
    scheduled: "Đã lên lịch",
    sent: "Đã đăng",
    delete_scheduled: "Chờ xóa",
    deleting: "Đang xóa",
    deleted: "Đã xóa",
    failed: "Lỗi gửi",
    delete_failed: "Lỗi xóa",
  };
  return labels[String(status || "").toLowerCase()] || status || "-";
}

function channelPostStatusClass(status: string) {
  const normalized = String(status || "").toLowerCase();
  if (["sent", "deleted"].includes(normalized)) return "status paid";
  if (["failed", "delete_failed"].includes(normalized)) return "status expired";
  return "status pending";
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
  if (["paid", "sent", "done", "running"].includes(normalized)) return "status paid";
  if (["expired", "cancelled", "failed"].includes(normalized)) return "status expired";
  return "status pending";
}

function kickAuditStatusClass(status: string) {
  if (["KICKED", "LEFT_NO_LOG", "ACTIVE_RETAINED"].includes(status)) return "status paid";
  if (["WAITING_KICK", "REJOINED", "CHECK_ERROR", "NO_GROUP", "INVALID_EXPIRE_AT"].includes(status)) return "status expired";
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
  return [`BTN_G${groupNo}`, `BTN_G${groupNo}_EN`, `ID_G${groupNo}`, `PRICE_G${groupNo}_1M`, `PRICE_G${groupNo}_LIFE`, `PRICE_G${groupNo}_1M_USD`, `PRICE_G${groupNo}_LIFE_USD`, `DESC_G${groupNo}`, `DESC_G${groupNo}_EN`, `IMG_G${groupNo}`];
}

export default function Home() {
  const [secret, setSecret] = useState("");
  const [savedSecret, setSavedSecret] = useState("");
  const [tab, setTab] = useState<Tab>("overview");
  const [contentTab, setContentTab] = useState<ContentSubTab>("bot");
  const [botViTab, setBotViTab] = useState<BotUiSubTab>("plans");
  const [botEnTab, setBotEnTab] = useState<BotUiSubTab>("plans");
  const [botToolsTab, setBotToolsTab] = useState<BotToolsSubTab>("commandsVi");
  const [menuLanguage, setMenuLanguage] = useState<MenuLanguage>("vi");
  const [orders, setOrders] = useState<Order[]>([]);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [config, setConfig] = useState<ConfigRow[]>([]);
  const [menuPages, setMenuPages] = useState<MenuPage[]>([]);
  const [saleRules, setSaleRules] = useState<SaleRule[]>([]);
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [hiddenGroups, setHiddenGroups] = useState<HiddenGroup[]>([]);
  const [hiddenCodes, setHiddenCodes] = useState<HiddenCode[]>([]);
  const [hiddenRedemptions, setHiddenRedemptions] = useState<HiddenRedemption[]>([]);
  const [blacklist, setBlacklist] = useState<BlacklistEntry[]>([]);
  const [supportEvents, setSupportEvents] = useState<SupportEvent[]>([]);
  const [kickAudit, setKickAudit] = useState<KickAuditRow[]>([]);
  const [activityEvents, setActivityEvents] = useState<ActivityEvent[]>([]);
  const [campaigns, setCampaigns] = useState<BroadcastCampaign[]>([]);
  const [campaignRecipients, setCampaignRecipients] = useState<BroadcastRecipient[]>([]);
  const [campaignPreview, setCampaignPreview] = useState<CampaignPreview | null>(null);
  const [channelPosts, setChannelPosts] = useState<ChannelPost[]>([]);
  const [channelEvents, setChannelEvents] = useState<ChannelPostEvent[]>([]);
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
  const [campaignForm, setCampaignForm] = useState({ ...EMPTY_CAMPAIGN_FORM });
  const [campaignModalOpen, setCampaignModalOpen] = useState(false);
  const [selectedCampaignId, setSelectedCampaignId] = useState("");
  const [campaignRecipientPage, setCampaignRecipientPage] = useState(1);
  const [channelPostForm, setChannelPostForm] = useState({ ...EMPTY_CHANNEL_POST_FORM });
  const [channelPostModalOpen, setChannelPostModalOpen] = useState(false);
  const [channelPostTab, setChannelPostTab] = useState<ChannelPostTab>("queue");
  const [channelPostPage, setChannelPostPage] = useState(1);
  const [selectedChannelPostId, setSelectedChannelPostId] = useState<number | null>(null);
  const [renewalTab, setRenewalTab] = useState<RenewalSubTab>("soon");
  const [renewalPage, setRenewalPage] = useState(1);
  const [renewalSettingsOpen, setRenewalSettingsOpen] = useState(false);
  const [supportTab, setSupportTab] = useState<SupportSubTab>("all");
  const [supportPage, setSupportPage] = useState(1);
  const [supportSettingsOpen, setSupportSettingsOpen] = useState(false);
  const [securitySettingsOpen, setSecuritySettingsOpen] = useState(false);
  const [systemSettingsOpen, setSystemSettingsOpen] = useState(false);
  const [svipPriceSettingsOpen, setSvipPriceSettingsOpen] = useState(false);
  const [groupModalOpen, setGroupModalOpen] = useState(false);
  const [groupNo, setGroupNo] = useState("1");
  const [groupName, setGroupName] = useState("");
  const [groupNameEn, setGroupNameEn] = useState("");
  const [groupId, setGroupId] = useState("");
  const [groupPrice1m, setGroupPrice1m] = useState("");
  const [groupPriceLife, setGroupPriceLife] = useState("");
  const [groupPrice1mUsd, setGroupPrice1mUsd] = useState("");
  const [groupPriceLifeUsd, setGroupPriceLifeUsd] = useState("");
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [menuForm, setMenuForm] = useState({ page_id: "main_menu", image_url: "", body: "", layout: "" });
  const [menuModalOpen, setMenuModalOpen] = useState(false);
  const [saleForm, setSaleForm] = useState({ sale_id: "", price_key: "PRICE_SVIP_30D", discount_percent: "", sale_price: "", slot_limit: "", enabled: "ON", start_at: "", end_at: "" });
  const [saleModalOpen, setSaleModalOpen] = useState(false);
  const [couponForm, setCouponForm] = useState({ ...EMPTY_COUPON_FORM });
  const [couponBatchCount, setCouponBatchCount] = useState("10");
  const [couponTab, setCouponTab] = useState<CouponTab>("unsent");
  const [couponPage, setCouponPage] = useState(1);
  const [couponModalOpen, setCouponModalOpen] = useState(false);
  const [hiddenSetupView, setHiddenSetupView] = useState<HiddenSetupView>("groups");
  const [hiddenGroupModalOpen, setHiddenGroupModalOpen] = useState(false);
  const [hiddenCodeModalOpen, setHiddenCodeModalOpen] = useState(false);
  const [hiddenGroupForm, setHiddenGroupForm] = useState<HiddenGroupFormState>({ ...EMPTY_HIDDEN_GROUP_FORM });
  const [hiddenCodeForm, setHiddenCodeForm] = useState<HiddenCodeFormState>({ ...EMPTY_HIDDEN_CODE_FORM });
  const [hiddenGroupQuery, setHiddenGroupQuery] = useState("");
  const [hiddenCodeQuery, setHiddenCodeQuery] = useState("");
  const [manualOrderForm, setManualOrderForm] = useState({ ...EMPTY_MANUAL_ORDER_FORM });
  const [manualOrderResult, setManualOrderResult] = useState<ManualOrderResult | null>(null);
  const [manualOrderModalOpen, setManualOrderModalOpen] = useState(false);
  const [blacklistForm, setBlacklistForm] = useState({ telegram_user_id: "", username: "", full_name: "", reason: "" });
  const [blacklistModalOpen, setBlacklistModalOpen] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem("prive_admin_secret") || "";
    setSavedSecret(stored);
    setSecret(stored);
    const queryTab = new URLSearchParams(window.location.search).get("tab") as Tab | null;
    const storedTab = window.localStorage.getItem(TAB_STORAGE_KEY) as Tab | null;
    const nextTab = queryTab && TAB_VALUES.includes(queryTab) ? queryTab : storedTab && TAB_VALUES.includes(storedTab) ? storedTab : null;
    if (nextTab) setTab(nextTab);
  }, []);

  useEffect(() => {
    const nextValues: Record<string, string> = {};
    config.forEach((item) => {
      nextValues[item.key] = item.value;
    });
    [...ADMIN_FIELDS, ...SUPPORT_FIELDS, ...CURRENCY_FIELDS, ...BOT_FIELDS, ...PAYMENT_FIELDS, ...RENEWAL_FIELDS, ...SECURITY_FIELDS, ...SYSTEM_FIELDS, ...COMMAND_FIELDS, ...COMMAND_EN_FIELDS, ...MESSAGE_FIELDS, ...MESSAGE_EN_FIELDS, ...BUTTON_FIELDS, ...BUTTON_EN_FIELDS, ...ALERT_FIELDS, ...ALERT_EN_FIELDS, ...SALE_CONTENT_FIELDS, ...SALE_CONTENT_EN_FIELDS, ...PLAN_FIELDS, ...PLAN_EN_FIELDS].forEach((field) => {
      if (!(field.key in nextValues)) nextValues[field.key] = "";
    });
    setFieldValues(nextValues);
  }, [config]);

  function ui(vi: string, _en: string) {
    void _en;
    return vi;
  }

  useEffect(() => {
    if (savedSecret) {
      loadAll(savedSecret, { scope: tab });
    }
  }, [savedSecret, tab]);

  useEffect(() => {
    if (!savedSecret) return;
    if (!["campaigns", "channelPosts"].includes(tab)) return;
    const interval = window.setInterval(() => {
      loadAll(savedSecret, { silent: true, resetPages: false, scope: tab, mode: "light" });
    }, AUTO_REFRESH_SECONDS * 1000);
    return () => window.clearInterval(interval);
  }, [savedSecret, tab]);

  useEffect(() => {
    if (!savedSecret || tab !== "campaigns") return;
    previewCampaign(savedSecret, campaignForm.target_segment, campaignForm.plan_filter, campaignForm.plan_match_scope)
      .then((res) => setCampaignPreview(res.data))
      .catch(() => setCampaignPreview(null));
  }, [savedSecret, tab, campaignForm.target_segment, campaignForm.plan_filter, campaignForm.plan_match_scope]);

  useEffect(() => {
    if (!savedSecret || !selectedCampaignId) {
      setCampaignRecipients([]);
      return;
    }
    getCampaignRecipients(savedSecret, selectedCampaignId)
      .then((res) => setCampaignRecipients(res.data))
      .catch(() => setCampaignRecipients([]));
  }, [savedSecret, selectedCampaignId, campaigns]);

  useEffect(() => {
    if (tab === "campaigns" && !selectedCampaignId && campaigns.length) {
      setSelectedCampaignId(campaigns[0].id);
    }
  }, [tab, selectedCampaignId, campaigns]);

  useEffect(() => {
    if (!savedSecret || !selectedChannelPostId) {
      setChannelEvents([]);
      return;
    }
    getChannelPostEvents(savedSecret, selectedChannelPostId)
      .then((res) => setChannelEvents(res.data))
      .catch(() => setChannelEvents([]));
  }, [savedSecret, selectedChannelPostId, channelPosts]);

  function selectTab(nextTab: Tab) {
    setTab(nextTab);
    window.localStorage.setItem(TAB_STORAGE_KEY, nextTab);
    const url = new URL(window.location.href);
    url.searchParams.set("tab", nextTab);
    window.history.replaceState(null, "", url.toString());
  }

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
      return true;
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "Không lưu được thay đổi.");
      return false;
    } finally {
      setSaving("");
    }
  }

  async function refreshCampaigns(activeSecret = savedSecret) {
    if (!activeSecret) return;
    const campaignsRes = await getCampaigns(activeSecret);
    setCampaigns(campaignsRes.data);
    if (selectedCampaignId) {
      const recipientsRes = await getCampaignRecipients(activeSecret, selectedCampaignId);
      setCampaignRecipients(recipientsRes.data);
    }
  }

  async function refreshChannelPosts(activeSecret = savedSecret) {
    if (!activeSecret) return;
    const postsRes = await getChannelPosts(activeSecret);
    setChannelPosts(postsRes.data);
    if (selectedChannelPostId) {
      const eventsRes = await getChannelPostEvents(activeSecret, selectedChannelPostId);
      setChannelEvents(eventsRes.data);
    }
  }

  function openNewChannelPostModal() {
    setChannelPostForm({ ...EMPTY_CHANNEL_POST_FORM });
    setSelectedChannelPostId(null);
    setChannelEvents([]);
    setChannelPostModalOpen(true);
  }

  function editChannelPost(post: ChannelPost) {
    setSelectedChannelPostId(post.id);
    setChannelPostForm({
      id: String(post.id),
      status: post.status || "draft",
      target_chat_id: post.target_chat_id || "",
      title: post.title || "",
      image_ref: post.image_ref || "",
      content: post.content || "",
      buttons_text: post.buttons_text || "",
      parse_mode: post.parse_mode || "HTML",
      disable_web_page_preview: Boolean(post.disable_web_page_preview),
      scheduled_at: dateTimeInputValue(post.scheduled_at),
      delete_at: dateTimeInputValue(post.delete_at),
      repeat_daily: Boolean(post.repeat_daily),
      sync_bot_schedule: Boolean(post.sync_bot_schedule),
      notes: post.notes || "",
    });
    setChannelPostModalOpen(true);
  }

  async function saveChannelPost(mode: "draft" | "send_now" | "schedule") {
    await runAction(`channel-post-${mode}`, async () => {
      const payload = {
        target_chat_id: channelPostForm.target_chat_id.trim(),
        title: channelPostForm.title,
        image_ref: channelPostForm.image_ref,
        content: channelPostForm.content,
        buttons_text: channelPostForm.buttons_text,
        parse_mode: channelPostForm.parse_mode,
        disable_web_page_preview: channelPostForm.disable_web_page_preview,
        notes: channelPostForm.notes,
        scheduled_at: mode === "schedule" ? datetimeLocalToIso(channelPostForm.scheduled_at) : null,
        delete_at: datetimeLocalToIso(channelPostForm.delete_at),
        repeat_daily: Boolean(channelPostForm.repeat_daily),
        sync_bot_schedule: Boolean(channelPostForm.sync_bot_schedule),
        status: mode === "schedule" ? "scheduled" : mode === "send_now" ? "queued" : channelPostForm.id ? channelPostForm.status || "draft" : "draft",
        created_by: "admin_cp",
      };
      if (!payload.target_chat_id || !payload.content.trim()) {
        throw new Error("Cần nhập channel/group nhận bài và nội dung bài đăng.");
      }
      if (mode === "schedule" && !payload.scheduled_at) {
        throw new Error("Cần chọn giờ đăng hợp lệ.");
      }
      if (payload.sync_bot_schedule && !payload.repeat_daily) {
        throw new Error("Muốn liên kết giờ bot hoạt động thì phải bật lặp lại mỗi ngày.");
      }
      if ((payload.repeat_daily || payload.sync_bot_schedule) && (!payload.scheduled_at || !payload.delete_at)) {
        throw new Error("Bài lặp ngày cần có cả giờ đăng và giờ xóa.");
      }
      if (channelPostForm.id) {
        await updateChannelPost(savedSecret, channelPostForm.id, payload);
        if (mode === "send_now") await channelPostAction(savedSecret, channelPostForm.id, "send_now");
      } else {
        const created = await createChannelPost(savedSecret, payload);
        if (mode === "send_now") await channelPostAction(savedSecret, created.data.id, "send_now");
      }
      setChannelPostModalOpen(false);
      await refreshChannelPosts();
    });
  }

  async function runChannelPostAction(post: ChannelPost, action: string, payload: Record<string, unknown> = {}) {
    await runAction(`channel-post-action-${action}-${post.id}`, async () => {
      await channelPostAction(savedSecret, post.id, action, payload);
      await refreshChannelPosts();
    });
  }

  async function saveCampaign() {
    await runAction("campaign-create", async () => {
      const created = await createCampaign(savedSecret, {
        ...campaignForm,
        delay_seconds: campaignForm.delay_seconds,
        batch_size: campaignForm.batch_size,
      });
      setCampaignForm({ ...EMPTY_CAMPAIGN_FORM });
      setCampaignModalOpen(false);
      setSelectedCampaignId(created.data.id);
      await refreshCampaigns();
    });
  }

  async function changeCampaignStatus(campaignId: string, action: "start" | "pause" | "cancel") {
    await runAction(`campaign-${action}-${campaignId}`, async () => {
      if (action === "start") await startCampaign(savedSecret, campaignId);
      if (action === "pause") await pauseCampaign(savedSecret, campaignId);
      if (action === "cancel") await cancelCampaign(savedSecret, campaignId);
      await refreshCampaigns();
    });
  }

  async function loadAll(activeSecret = savedSecret, options: LoadOptions = {}) {
    if (!activeSecret) return;
    const silent = Boolean(options.silent);
    const resetPages = options.resetPages ?? !silent;
    const scope = options.scope || tab;
    const mode = options.mode || "full";
    const light = mode === "light";
    const isAll = scope === "all";
    const shouldLoad = (...tabs: Tab[]) => isAll || tabs.includes(scope as Tab);
    if (!silent) {
      setLoading(true);
      setNotice(null);
    }
    try {
      const tasks: Promise<void>[] = [];
      const addTask = <T,>(enabled: boolean, promiseFactory: () => Promise<{ data: T }>, setter: (data: T) => void) => {
        if (enabled) tasks.push(promiseFactory().then((res) => setter(res.data)));
      };

      const needsOrders = !light && shouldLoad("overview", "analytics", "orders", "customers", "campaigns", "renewals");
      const needsUsers = !light && shouldLoad("overview", "analytics");
      const needsConfig = !light;
      const needsMenu = !light && shouldLoad("overview", "content", "botVi", "botEn", "menuBuilder");
      const needsSales = !light && shouldLoad("sales");
      const needsCoupons = !light && shouldLoad("overview", "coupons");
      const needsHidden = !light && shouldLoad("setup", "coupons");
      const needsBlacklist = !light && shouldLoad("security");
      const needsSupportEvents = !light && shouldLoad("activityLog", "renewals", "supportGroup");
      const needsKickAudit = !light && shouldLoad("renewals");
      const needsActivityEvents = !light && shouldLoad("activityLog", "analytics");
      const needsCampaigns = shouldLoad("campaigns");
      const needsChannelPosts = shouldLoad("channelPosts");
      const needsWebhook = !light;

      addTask(needsOrders, () => getOrders(activeSecret), setOrders);
      addTask(needsUsers, () => getUsers(activeSecret), setUsers);
      addTask(needsConfig, () => getConfig(activeSecret), setConfig);
      addTask(needsMenu, () => getMenuPages(activeSecret), setMenuPages);
      addTask(needsSales, () => getSaleRules(activeSecret), setSaleRules);
      addTask(needsCoupons, () => getCoupons(activeSecret), setCoupons);
      addTask(needsHidden, () => getHiddenGroups(activeSecret), setHiddenGroups);
      addTask(needsHidden, () => getHiddenCodes(activeSecret), setHiddenCodes);
      addTask(needsHidden, () => getHiddenRedemptions(activeSecret, 200), setHiddenRedemptions);
      addTask(needsBlacklist, () => getBlacklist(activeSecret), setBlacklist);
      addTask(needsSupportEvents, () => getSupportEvents(activeSecret), setSupportEvents);
      addTask(needsKickAudit, () => getKickAudit(activeSecret), setKickAudit);
      addTask(needsActivityEvents, () => getActivityEvents(activeSecret), setActivityEvents);
      addTask(needsCampaigns, () => getCampaigns(activeSecret), setCampaigns);
      addTask(needsChannelPosts, () => getChannelPosts(activeSecret), setChannelPosts);
      addTask(needsWebhook, () => getWebhookInfo(activeSecret), setWebhook);

      await Promise.all(tasks);
      if (resetPages) {
        setOrderPage(1);
        setCouponPage(1);
      }
    } catch (err) {
      if (!silent) showNotice("error", err instanceof Error ? err.message : "Không tải được dữ liệu.");
    } finally {
      if (!silent) setLoading(false);
    }
  }

  function openNewHiddenGroupModal() {
    setHiddenGroupForm(hiddenGroupToForm(undefined, hiddenGroups.length + 1));
    setHiddenGroupModalOpen(true);
  }

  function openEditHiddenGroupModal(item: HiddenGroup) {
    setHiddenGroupForm(hiddenGroupToForm(item, hiddenGroups.length + 1));
    setHiddenGroupModalOpen(true);
  }

  async function saveHiddenGroup() {
    if (!savedSecret) return;
    const id = hiddenGroupForm.id.trim() || hiddenSlug(hiddenGroupForm.name);
    const payload = {
      id,
      name: hiddenGroupForm.name.trim(),
      description: hiddenGroupForm.description.trim(),
      chat_id: hiddenGroupForm.chat_id.trim(),
      price_1m_vnd: Number(hiddenGroupForm.price_1m_vnd || 0),
      price_life_vnd: Number(hiddenGroupForm.price_life_vnd || 0),
      price_1m_usd: Number(hiddenGroupForm.price_1m_usd || 0),
      price_life_usd: Number(hiddenGroupForm.price_life_usd || 0),
      duration_1m_days: Number(hiddenGroupForm.duration_1m_days || 30),
      lifetime_days: Number(hiddenGroupForm.lifetime_days || 3650),
      image_url: hiddenGroupForm.image_url.trim(),
      requirement_type: hiddenGroupForm.requirement_type,
      requirement_value: hiddenRequirementNeedsValue(hiddenGroupForm.requirement_type) ? hiddenGroupForm.requirement_value.trim() : "",
      sort_order: Number(hiddenGroupForm.sort_order || hiddenGroups.length + 1),
      is_active: hiddenGroupForm.is_active,
    };
    if (!payload.id) {
      showNotice("error", "Cần nhập ID kỹ thuật hoặc tên để hệ thống tự tạo ID.");
      return;
    }
    if (!payload.name || !payload.chat_id) {
      showNotice("error", "Cần đủ tên hiển thị và Telegram group ID.");
      return;
    }
    if (hiddenRequirementNeedsValue(payload.requirement_type) && !payload.requirement_value) {
      showNotice("error", "Rule theo plan token cần nhập thêm requirement value.");
      return;
    }
    try {
      setSaving(`hidden-group-${payload.id || "new"}`);
      await upsertHiddenGroup(savedSecret, payload);
      setHiddenGroupModalOpen(false);
      await loadAll(savedSecret, { silent: true, resetPages: false });
      showNotice("ok", hiddenGroups.some((item) => item.id === payload.id) ? "Đã cập nhật Hidden Group." : "Đã tạo Hidden Group.");
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "Không lưu được Hidden Group.");
    } finally {
      setSaving("");
    }
  }

  async function removeHiddenGroupAction(hiddenGroupId: string) {
    if (!savedSecret || !window.confirm(`Xóa Hidden Group ${hiddenGroupId}?`)) return;
    try {
      setSaving(`hidden-group-delete-${hiddenGroupId}`);
      await deleteHiddenGroup(savedSecret, hiddenGroupId);
      await loadAll(savedSecret, { silent: true, resetPages: false });
      showNotice("ok", "Đã xóa Hidden Group.");
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "Không xóa được Hidden Group.");
    } finally {
      setSaving("");
    }
  }

  function openNewHiddenCodeModal() {
    const defaultGroupIds = hiddenGroups.filter((item) => item.is_active).slice(0, 1).map((item) => item.id);
    setHiddenCodeForm(hiddenCodeToForm(undefined, defaultGroupIds));
    setHiddenCodeModalOpen(true);
  }

  function openEditHiddenCodeModal(item: HiddenCode) {
    setHiddenCodeForm(hiddenCodeToForm(item));
    setHiddenCodeModalOpen(true);
  }

  function toggleHiddenCodeGroup(groupId: string) {
    const current = new Set(hiddenCodeForm.group_ids);
    if (current.has(groupId)) current.delete(groupId);
    else current.add(groupId);
    setHiddenCodeForm({ ...hiddenCodeForm, group_ids: Array.from(current) });
  }

  async function saveHiddenCode() {
    if (!savedSecret) return;
    const code = (hiddenCodeForm.code.trim() || hiddenCodeSeed(hiddenCodeForm.name)).toUpperCase();
    const validFrom = datetimeLocalToIso(hiddenCodeForm.valid_from);
    const validUntil = datetimeLocalToIso(hiddenCodeForm.valid_until);
    if (!code) {
      showNotice("error", "Cần nhập mã hidden code hoặc tên để hệ thống tự tạo mã.");
      return;
    }
    if (validFrom && validUntil && new Date(validUntil).getTime() < new Date(validFrom).getTime()) {
      showNotice("error", "Thời gian hết hạn phải sau thời gian bắt đầu.");
      return;
    }
    if (hiddenCodeForm.scope_type === "SELECTED_GROUPS" && !hiddenCodeForm.group_ids.length) {
      showNotice("error", "Hidden code kiểu chọn thủ công cần ít nhất 1 hidden group.");
      return;
    }
    if (hiddenRequirementNeedsValue(hiddenCodeForm.requirement_type) && !hiddenCodeForm.requirement_value.trim()) {
      showNotice("error", "Rule theo plan token cần nhập requirement value.");
      return;
    }
    const payload = {
      code,
      name: hiddenCodeForm.name.trim(),
      description: hiddenCodeForm.description.trim(),
      scope_type: hiddenCodeForm.scope_type,
      group_ids: hiddenCodeForm.scope_type === "ALL_ACTIVE_HIDDEN_GROUPS" ? [] : hiddenCodeForm.group_ids,
      requirement_type: hiddenCodeForm.requirement_type || "",
      requirement_value: hiddenRequirementNeedsValue(hiddenCodeForm.requirement_type) ? hiddenCodeForm.requirement_value.trim() : "",
      max_uses: Number(hiddenCodeForm.max_uses || 0),
      used_count: Number(hiddenCodeForm.used_count || 0),
      valid_from: validFrom,
      valid_until: validUntil,
      is_active: hiddenCodeForm.is_active,
    };
    try {
      setSaving(`hidden-code-${code}`);
      await upsertHiddenCode(savedSecret, payload);
      setHiddenCodeModalOpen(false);
      await loadAll(savedSecret, { silent: true, resetPages: false });
      showNotice("ok", hiddenCodes.some((item) => item.code === code) ? "Đã cập nhật Hidden Code." : "Đã tạo Hidden Code.");
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "Không lưu được Hidden Code.");
    } finally {
      setSaving("");
    }
  }

  async function removeHiddenCodeAction(code: string) {
    if (!savedSecret || !window.confirm(`Xóa Hidden Code ${code}?`)) return;
    try {
      setSaving(`hidden-code-delete-${code}`);
      await deleteHiddenCode(savedSecret, code);
      await loadAll(savedSecret, { silent: true, resetPages: false });
      showNotice("ok", "Đã xóa Hidden Code.");
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "Không xóa được Hidden Code.");
    } finally {
      setSaving("");
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

  async function saveFields(fields: ConfigField[], values = fieldValues) {
    return runAction("fields", async () => {
      const items = fields.map((field) => ({ key: field.key, value: values[field.key] || "" }));
      const res = await updateConfigs(savedSecret, items);
      const changedKeys = new Set(items.map((item) => item.key));
      setConfig((current) => [
        ...current.filter((item) => !changedKeys.has(item.key)),
        ...res.data,
      ]);
    });
  }

  function resetGroupForm(nextGroupNo?: string) {
    const used = new Set(config.filter((item) => /^BTN_G\d+$/.test(item.key)).map((item) => item.key.replace("BTN_G", "")));
    const firstEmpty = Array.from({ length: maxGroups }, (_, idx) => String(idx + 1)).find((item) => !used.has(item)) || "1";
    setGroupNo(nextGroupNo || firstEmpty);
    setGroupName("");
    setGroupNameEn("");
    setGroupId("");
    setGroupPrice1m("");
    setGroupPriceLife("");
    setGroupPrice1mUsd("");
    setGroupPriceLifeUsd("");
  }

  function openNewGroupModal() {
    resetGroupForm();
    setGroupModalOpen(true);
  }

  function fillGroupForm(nextGroupNo: string) {
    setGroupNo(nextGroupNo);
    setGroupName(getConfigValue(config, `BTN_G${nextGroupNo}`));
    setGroupNameEn(getConfigValue(config, `BTN_G${nextGroupNo}_EN`));
    setGroupId(getConfigValue(config, `ID_G${nextGroupNo}`));
    setGroupPrice1m(getConfigValue(config, `PRICE_G${nextGroupNo}_1M`));
    setGroupPriceLife(getConfigValue(config, `PRICE_G${nextGroupNo}_LIFE`));
    setGroupPrice1mUsd(getConfigValue(config, `PRICE_G${nextGroupNo}_1M_USD`));
    setGroupPriceLifeUsd(getConfigValue(config, `PRICE_G${nextGroupNo}_LIFE_USD`));
  }

  function openEditGroupModal(nextGroupNo: string) {
    fillGroupForm(nextGroupNo);
    setGroupModalOpen(true);
  }

  async function saveGroupConfig() {
    await runAction("group", async () => {
      await updateConfigs(savedSecret, [
        { key: `BTN_G${groupNo}`, value: groupName },
        { key: `BTN_G${groupNo}_EN`, value: groupNameEn },
        { key: `ID_G${groupNo}`, value: groupId },
        { key: `PRICE_G${groupNo}_1M`, value: groupPrice1m },
        { key: `PRICE_G${groupNo}_LIFE`, value: groupPriceLife },
        { key: `PRICE_G${groupNo}_1M_USD`, value: groupPrice1mUsd },
        { key: `PRICE_G${groupNo}_LIFE_USD`, value: groupPriceLifeUsd },
      ]);
      setGroupName("");
      setGroupNameEn("");
      setGroupId("");
      setGroupPrice1m("");
      setGroupPriceLife("");
      setGroupPrice1mUsd("");
      setGroupPriceLifeUsd("");
      setGroupModalOpen(false);
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
      setGroupModalOpen(false);
      await loadAll();
    });
  }

  async function saveMenuPage() {
    const pageId = menuForm.page_id.trim();
    if (!pageId) {
      showNotice("error", "Vui lòng nhập tên trang menu.");
      return;
    }
    if (menuLanguage === "en" && !pageId.endsWith("_en")) {
      showNotice("error", "Trang tiếng Anh bắt buộc có hậu tố _en, ví dụ main_menu_en.");
      return;
    }
    if (menuLanguage === "vi" && pageId.endsWith("_en")) {
      showNotice("error", "Trang tiếng Việt không được dùng hậu tố _en.");
      return;
    }
    await runAction("menu", async () => {
      await updateMenuPage(savedSecret, pageId, { ...menuForm, page_id: pageId });
      setMenuModalOpen(false);
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

  async function refreshKickAudit(live = false) {
    await runAction(live ? "kick-audit-live" : "kick-audit-refresh", async () => {
      const res = await getKickAudit(savedSecret, live);
      setKickAudit(res.data);
      if (live) showNotice("ok", "Đã kiểm tra live trạng thái kick trong group.");
    });
  }

  async function manualKickAudit(row: KickAuditRow) {
    if (!row.group_id || !window.confirm(`Kick lại ${row.customer_name || row.telegram_user_id} khỏi ${row.group_name || row.group_id}?`)) return;
    await runAction(`kick-audit-${row.audit_id}`, async () => {
      const res = await kickAuditMember(savedSecret, {
        telegram_user_id: row.telegram_user_id,
        order_id: row.order_id,
        group_id: row.group_id,
        plan_name: row.plan_name,
        customer_name: row.customer_name,
      });
      setKickAudit((current) => {
        const next = [...current];
        for (const updated of res.data) {
          const idx = next.findIndex((item) => item.audit_id === updated.audit_id);
          if (idx >= 0) next[idx] = updated;
        }
        return next;
      });
      await loadAll(savedSecret, { silent: true, resetPages: false });
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
      setMenuModalOpen(false);
      await loadAll();
    });
  }

  async function saveSaleRule() {
    await runAction("sale", async () => {
      await upsertSaleRule(savedSecret, saleForm);
      setSaleModalOpen(false);
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
      setSaleModalOpen(false);
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

  const filteredHiddenGroups = useMemo(() => {
    const keyword = hiddenGroupQuery.trim().toLowerCase();
    if (!keyword) return hiddenGroups;
    return hiddenGroups.filter((item) => [item.id, item.name, item.chat_id, item.description].some((value) => String(value || "").toLowerCase().includes(keyword)));
  }, [hiddenGroups, hiddenGroupQuery]);

  const filteredHiddenCodes = useMemo(() => {
    const keyword = hiddenCodeQuery.trim().toLowerCase();
    if (!keyword) return hiddenCodes;
    return hiddenCodes.filter((item) => [
      item.code,
      item.name,
      item.description,
      item.scope_type,
      item.requirement_type,
      item.group_ids.join(","),
    ].some((value) => String(value || "").toLowerCase().includes(keyword)));
  }, [hiddenCodes, hiddenCodeQuery]);

  const hiddenCodeUsageByGroup = useMemo(() => {
    const index = new Map<string, number>();
    for (const group of hiddenGroups) index.set(group.id, 0);
    const activeGroupIds = hiddenGroups.filter((item) => item.is_active).map((item) => item.id);
    for (const code of hiddenCodes) {
      const targets = code.scope_type === "ALL_ACTIVE_HIDDEN_GROUPS" ? activeGroupIds : code.group_ids;
      for (const groupId of targets) {
        index.set(groupId, (index.get(groupId) || 0) + 1);
      }
    }
    return index;
  }, [hiddenGroups, hiddenCodes]);

  async function copyHiddenCode(code: string) {
    setSaving(`hidden-code-copy-${code}`);
    try {
      await navigator.clipboard.writeText(code);
      showNotice("ok", `Đã copy mã ${code}.`);
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "Không copy được hidden code.");
    } finally {
      setSaving("");
    }
  }

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
      setBlacklistModalOpen(false);
      await loadAll();
    });
  }

  async function removeBlacklistEntry(telegramUserId = blacklistForm.telegram_user_id) {
    if (!telegramUserId || !window.confirm(`Gỡ Telegram ID "${telegramUserId}" khỏi blacklist?`)) return;
    await runAction(`blacklist-delete-${telegramUserId}`, async () => {
      await deleteBlacklist(savedSecret, telegramUserId);
      setBlacklistForm({ telegram_user_id: "", username: "", full_name: "", reason: "" });
      setBlacklistModalOpen(false);
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
    ...configuredGroups.flatMap((item) => [`PRICE_G${item}_1M`, `PRICE_G${item}_LIFE`, `PRICE_G${item}_1M_USD`, `PRICE_G${item}_LIFE_USD`]),
  ], [configuredGroups]);
  const groupViContentFields = useMemo<ConfigField[]>(() => configuredGroups.flatMap((item) => [
    { key: `DESC_G${item}`, label: `G${item} - Mô tả tiếng Việt`, placeholder: "Mô tả nội dung nhóm", help: "Nội dung trang chi tiết nhóm tiếng Việt.", kind: "textarea" as const },
  ]), [configuredGroups]);
  const groupEnContentFields = useMemo<ConfigField[]>(() => configuredGroups.flatMap((item) => [
    { key: `DESC_G${item}_EN`, label: `G${item} - Mô tả tiếng Anh`, placeholder: "English group description", help: "Nội dung trang chi tiết nhóm tiếng Anh.", kind: "textarea" as const },
  ]), [configuredGroups]);
  const visibleMenuPages = useMemo(
    () => menuPages.filter((item) => menuLanguage === "en" ? item.page_id.endsWith("_en") : !item.page_id.endsWith("_en")),
    [menuPages, menuLanguage],
  );
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
  const supportNameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const item of supportEvents) {
      const id = String(item.telegram_user_id || "").trim();
      const name = displayText(item.full_name) || displayText(item.username);
      if (id && name && !map.has(id)) map.set(id, name);
    }
    return map;
  }, [supportEvents]);
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
    const fromOrder = "full_name" in item ? displayText(item.full_name) : "";
    return fromOrder || customerNameById.get(telegramId) || telegramId || "-";
  }
  function supportCustomerName(item: SupportEvent) {
    const telegramId = String(item.telegram_user_id || "").trim();
    const raw = item.raw_data || {};
    return (
      displayText(item.full_name) ||
      displayText(item.username) ||
      displayText(raw.full_name) ||
      displayText(raw.Full_Name) ||
      supportNameById.get(telegramId) ||
      customerNameById.get(telegramId) ||
      telegramId ||
      "-"
    );
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
      audit: kickAudit.map((item) => [
        <><strong>{item.customer_name || "-"}</strong><div className="muted">{item.telegram_user_id || "-"}</div></>,
        <><strong>{item.plan_name || "-"}</strong><div className="muted">Đơn {item.order_id || "-"}</div></>,
        <><strong>{item.group_name || "-"}</strong><div className="muted">{item.group_id || "-"}</div></>,
        dateText(item.expire_at),
        <span key="status" className={kickAuditStatusClass(item.status)}>{item.status_label || item.status}</span>,
        item.latest_kick_at ? dateText(item.latest_kick_at) : item.latest_error ? <span className="muted">{item.latest_error}</span> : "-",
        item.live_checked ? `${item.live_status || "-"}${item.live_present === true ? " / còn trong group" : item.live_present === false ? " / đã rời" : ""}` : "Chưa kiểm tra live",
        item.needs_action && item.group_id ? (
          <button className="btn secondary" onClick={() => manualKickAudit(item)} disabled={saving === `kick-audit-${item.audit_id}`}>
            {saving === `kick-audit-${item.audit_id}` ? <Loader2 size={16} className="spin" /> : <XCircle size={16} />} Kick lại
          </button>
        ) : "-",
      ]),
    };
    return rows;
  }, [expiringSoon, expiringToday, renewalReminderEvents, expiredNoticeEvents, uniqueKickedEvents, kickAudit, latestReminderByOrder, reminderNoticeDays, saving]);
  const renewalHeaders: Record<RenewalSubTab, string[]> = {
    soon: ["Khách", "Telegram ID", "Gói", "Hết hạn lúc", "Còn lại", "Bắt đầu nhắc từ", "Nhắc gần nhất"],
    today: ["Khách", "Telegram ID", "Gói", "Hết hạn lúc", "Trạng thái", "Báo hết hạn lúc"],
    reminded: ["Khách", "Telegram ID", "Gói", "Đơn", "Giờ nhắc", "Hạn dùng"],
    expiredNotice: ["Khách", "Telegram ID", "Gói", "Đơn", "Giờ báo hết hạn", "Hạn dùng"],
    kicked: ["Khách", "Telegram ID", "Gói", "Đơn", "Group", "Giờ kick"],
    audit: ["Khách", "Gói / Đơn", "Group", "Hạn dùng", "Trạng thái", "Kick / lỗi gần nhất", "Live", "Thao tác"],
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
      supportCustomerName(item),
      item.telegram_user_id || "-",
      item.chat_title || item.chat_id || "-",
      dateText(item.created_at),
      [item.raw_data?.old_status, item.raw_data?.new_status].filter(Boolean).join(" → ") || (item.raw_data?.reason ? String(item.raw_data.reason) : "-"),
    ]);
  }, [supportGroupEvents, supportTab, customerNameById, supportNameById]);
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
    const privateActivityEvents = activityEvents.filter((event) => {
      const chatType = payloadText(event.payload || {}, "chat_type").toLowerCase();
      return chatType !== "group" && chatType !== "supergroup" && chatType !== "channel";
    });
    const userEvents = privateActivityEvents.map((event) => {
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
      fullName: supportCustomerName(event),
      title: describeSupportEvent(event),
      detail: [event.plan_name, event.chat_title, event.order_id].filter(Boolean).join(" • "),
      createdAt: event.created_at,
    }));
    return [...userEvents, ...botEvents].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }, [activityEvents, supportEvents, customerNameById, supportNameById]);
  const logTypeOptions = useMemo(() => uniqueValues(logEntries.map((item) => item.type)).sort(), [logEntries]);
  const logDateOptions = useMemo(() => uniqueValues(logEntries.map((item) => isoDayKey(item.createdAt))).sort((a, b) => {
    if (a === "UNKNOWN") return 1;
    if (b === "UNKNOWN") return -1;
    return b.localeCompare(a);
  }), [logEntries]);
  const campaignPlanOptions = useMemo(() => {
    return uniqueValues(orders.filter((item) => item.status === "PAID").map((item) => item.plan_name)).sort((a, b) => a.localeCompare(b));
  }, [orders]);
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
  const selectedCampaign = useMemo(() => campaigns.find((item) => item.id === selectedCampaignId) || campaigns[0] || null, [campaigns, selectedCampaignId]);
  const campaignRecipientCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const item of campaignRecipients) {
      counts[item.status] = (counts[item.status] || 0) + 1;
    }
    return counts;
  }, [campaignRecipients]);
  const totalCampaignRecipientPages = Math.max(1, Math.ceil(campaignRecipients.length / CAMPAIGN_RECIPIENT_PAGE_SIZE));
  const pagedCampaignRecipients = useMemo(() => {
    const safePage = Math.min(campaignRecipientPage, totalCampaignRecipientPages);
    const start = (safePage - 1) * CAMPAIGN_RECIPIENT_PAGE_SIZE;
    return campaignRecipients.slice(start, start + CAMPAIGN_RECIPIENT_PAGE_SIZE);
  }, [campaignRecipients, campaignRecipientPage, totalCampaignRecipientPages]);
  const channelPostCounts = useMemo(() => {
    const counts: Record<ChannelPostTab, number> = { draft: 0, queue: 0, scheduled: 0, sent: 0, failed: 0, deleted: 0 };
    for (const item of channelPosts) counts[channelPostTabFor(item)] += 1;
    return counts;
  }, [channelPosts]);
  const visibleChannelPosts = useMemo(() => {
    return channelPosts
      .filter((item) => channelPostTabFor(item) === channelPostTab)
      .sort((a, b) => new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime());
  }, [channelPosts, channelPostTab]);
  const totalChannelPostPages = Math.max(1, Math.ceil(visibleChannelPosts.length / CHANNEL_POST_PAGE_SIZE));
  const pagedChannelPosts = useMemo(() => {
    const safePage = Math.min(channelPostPage, totalChannelPostPages);
    const start = (safePage - 1) * CHANNEL_POST_PAGE_SIZE;
    return visibleChannelPosts.slice(start, start + CHANNEL_POST_PAGE_SIZE);
  }, [visibleChannelPosts, channelPostPage, totalChannelPostPages]);
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
    setChannelPostPage(1);
  }, [channelPostTab]);

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
    if (value === "PRICE_SVIP_30D_USD") return "Giá USD SVIP chung - 30 ngày";
    if (value === "PRICE_SVIP_LIFE_USD") return "Giá USD SVIP chung - trọn đời";
    const match = value.match(/^PRICE_G(\d+)_(1M|LIFE)(_USD)?$/);
    if (!match) return value;
    const name = getConfigValue(config, `BTN_G${match[1]}`) || `Nhóm G${match[1]}`;
    return `${name} - ${match[2] === "1M" ? "giá 30 ngày" : "giá trọn đời"}${match[3] ? " (USD)" : " (VNĐ)"}`;
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
          {webhook?.url ? ui("Webhook đang bật", "Webhook active") : ui("Webhook cần kiểm tra", "Check webhook")}
        </div>
        <nav className="nav">
          <button className={tab === "overview" ? "active" : ""} onClick={() => selectTab("overview")}><Activity size={18} /> {ui("Tổng quan", "Overview")}</button>
          <button className={tab === "analytics" ? "active" : ""} onClick={() => selectTab("analytics")}><BarChart3 size={18} /> {ui("Thống kê", "Analytics")}</button>
          <button className={tab === "setup" ? "active" : ""} onClick={() => selectTab("setup")}><ShieldCheck size={18} /> {ui("Nhóm & giá", "Groups & pricing")}</button>
          <button className={tab === "orders" ? "active" : ""} onClick={() => selectTab("orders")}><ShoppingCart size={18} /> {ui("Đơn hàng", "Orders")}</button>
          <button className={tab === "customers" ? "active" : ""} onClick={() => selectTab("customers")}><Users size={18} /> {ui("Khách hàng", "Customers")}</button>
          <button className={tab === "activityLog" ? "active" : ""} onClick={() => selectTab("activityLog")}><ClipboardList size={18} /> {ui("Nhật ký", "Activity log")}</button>
          <button className={tab === "campaigns" ? "active" : ""} onClick={() => selectTab("campaigns")}><Megaphone size={18} /> Campaign</button>
          <button className={tab === "channelPosts" ? "active" : ""} onClick={() => selectTab("channelPosts")}><Send size={18} /> Đăng channel</button>
          <button className={tab === "renewals" ? "active" : ""} onClick={() => selectTab("renewals")}><RefreshCw size={18} /> {ui("Gia hạn", "Renewals")}</button>
          <button className={tab === "supportGroup" ? "active" : ""} onClick={() => selectTab("supportGroup")}><ShieldCheck size={18} /> {ui("Group hỗ trợ", "Support group")}</button>
          <button className={tab === "content" ? "active" : ""} onClick={() => selectTab("content")}><Settings size={18} /> Cấu hình bot</button>
          <button className={tab === "botVi" ? "active" : ""} onClick={() => selectTab("botVi")}><FileText size={18} /> UI Bot tiếng Việt</button>
          <button className={tab === "botEn" ? "active" : ""} onClick={() => selectTab("botEn")}><FileText size={18} /> UI Bot tiếng Anh</button>
          <button className={tab === "botTools" ? "active" : ""} onClick={() => selectTab("botTools")}><ClipboardList size={18} /> Lệnh & cảnh báo</button>
          <button className={tab === "menuBuilder" ? "active" : ""} onClick={() => selectTab("menuBuilder")}><FileText size={18} /> Menu Builder</button>
          <button className={tab === "coupons" ? "active" : ""} onClick={() => selectTab("coupons")}><Ticket size={18} /> Coupon</button>
          <button className={tab === "security" ? "active" : ""} onClick={() => selectTab("security")}><ShieldCheck size={18} /> {ui("Bảo mật", "Security")}</button>
          <button className={tab === "sales" ? "active" : ""} onClick={() => selectTab("sales")}><BadgePercent size={18} /> Sale</button>
          <button className={tab === "system" ? "active" : ""} onClick={() => selectTab("system")}><Settings size={18} /> {ui("Hệ thống", "System")}</button>
        </nav>
      </aside>

      <section className="main">
        <div className="topbar">
          <div>
            <h1 className="title">{ui("Quản lý bot Privé+", "Privé+ Bot Admin")}</h1>
            <div className="muted">{ui("Dashboard vận hành: nhóm nhận link, đơn hàng, coupon, sale và nội dung bot.", "Operations dashboard for groups, orders, coupons, sales, and bot content.")}</div>
          </div>
          <div className="actions">
            <button className="btn secondary" onClick={() => loadAll()} disabled={loading}>
              {loading ? <Loader2 size={17} className="spin" /> : <RefreshCw size={17} />} {ui("Tải lại", "Reload")}
            </button>
            <button className="btn ghost" onClick={logout}>{ui("Đăng xuất", "Log out")}</button>
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
              <Metric label="Doanh thu đã thanh toán" value={ordersMoney(orders.filter((item) => item.status === "PAID"))} />
              <Metric label="Đơn đang chờ" value={String(metrics.pending)} />
              <Metric label="Khách gần đây" value={String(metrics.users)} />
              <Metric label="Nhóm đang bán" value={String(configuredGroups.length)} />
            </div>
            <div className="grid">
              <Metric label="Doanh thu hôm nay" value={ordersMoney(orders.filter((item) => item.status === "PAID" && isWithinPeriod(item.created_at, "today")))} />
              <Metric label="Đơn PAID hôm nay" value={String(todayStats.paid)} />
              <Metric label="Doanh thu tháng này" value={ordersMoney(orders.filter((item) => item.status === "PAID" && isWithinPeriod(item.created_at, "month")))} />
              <Metric label="Tỉ lệ thanh toán tháng" value={`${monthStats.conversion}%`} />
            </div>
            <section className="panel">
              <PanelHead title="Trạng thái vận hành" subtitle="Kiểm tra nhanh các phần cần có trước khi bán." />
              <div className="status-grid">
                <HealthItem ok={Boolean(webhook?.url)} title="Telegram webhook" detail={webhook?.url || "Chưa set webhook"} />
                <HealthItem ok={configuredGroups.length > 0} title="Nhóm nhận link" detail={configuredGroups.length ? `Đã có ${configuredGroups.length} nhóm` : "Vào Nhóm & giá để cấu hình"} />
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
              <Metric label="Hôm nay" value={ordersMoney(orders.filter((item) => item.status === "PAID" && isWithinPeriod(item.created_at, "today")))} />
              <Metric label="Tháng này" value={ordersMoney(orders.filter((item) => item.status === "PAID" && isWithinPeriod(item.created_at, "month")))} />
              <Metric label="Năm nay" value={ordersMoney(orders.filter((item) => item.status === "PAID" && isWithinPeriod(item.created_at, "year")))} />
              <Metric label="Khách đã trả tiền" value={String(yearStats.customers)} />
            </div>
            <div className="grid">
              <Metric label="Đơn PAID tháng" value={String(monthStats.paid)} />
              <Metric label="Đơn chờ tháng" value={String(monthStats.pending)} />
              <Metric label="AOV tháng" value={ordersAverageMoney(orders.filter((item) => isWithinPeriod(item.created_at, "month")))} />
              <Metric label="Coupon giảm tháng" value={ordersMoney(orders.filter((item) => item.status === "PAID" && isWithinPeriod(item.created_at, "month")), "coupon_discount_amount")} />
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
                title="Bảng giá SVIP chung"
                subtitle="Giá SVIP được quản lý tập trung tại đây. Bấm Cài đặt để chỉnh trong popup."
                action={<button className="btn secondary" onClick={() => setSvipPriceSettingsOpen(true)}><Settings size={16} /> Cài đặt giá SVIP</button>}
              />
              <div className="system-list">
                <Info label="SVIP 30 ngày VNĐ" value={money(Number(getConfigValue(config, "PRICE_SVIP_30D", "0") || 0))} />
                <Info label="SVIP trọn đời VNĐ" value={money(Number(getConfigValue(config, "PRICE_SVIP_LIFE", "0") || 0))} />
                <Info label="SVIP 30 ngày USD" value={getConfigValue(config, "PRICE_SVIP_30D_USD", "-") || "-"} />
                <Info label="SVIP trọn đời USD" value={getConfigValue(config, "PRICE_SVIP_LIFE_USD", "-") || "-"} />
              </div>
            </section>
            <section className="panel">
              <PanelHead
                title="Nhóm lẻ & bảng giá"
                subtitle="Bấm một nhóm để sửa trong popup. Không còn form dài nằm sẵn trên trang."
                action={<button className="btn" onClick={openNewGroupModal}><Plus size={16} /> Thêm nhóm mới</button>}
              />
              <div className="hint">
                Giá chỉ chỉnh tại màn hình này. UI Bot chỉ quản lý nội dung hiển thị, không còn trường giá trùng lặp.
              </div>
              <div className="group-list">
                {visibleGroups.length ? visibleGroups.map((item) => {
                  const name = getConfigValue(config, `BTN_G${item}`);
                  const id = getConfigValue(config, `ID_G${item}`);
                  return (
                    <button className={name && id ? "group-row ok" : "group-row"} key={item} onClick={() => openEditGroupModal(String(item))}>
                      <span>G{item}</span>
                      <strong>{name || "Chưa đặt tên"}</strong>
                      <em>{id || "Chưa có group ID"} • 30 ngày {getConfigValue(config, `PRICE_G${item}_1M`, "-")}đ • trọn đời {getConfigValue(config, `PRICE_G${item}_LIFE`, "-")}đ</em>
                    </button>
                  );
                }) : <div className="empty-card">Chưa có nhóm nào. Bấm <strong>Thêm nhóm mới</strong>, nhập tên nhóm và Telegram group ID rồi lưu.</div>}
              </div>
            </section>
            <section className="panel">
              <PanelHead
                title="Hidden access"
                subtitle="Quản lý nhóm extra ẩn, mã reveal và lịch sử người đã mở catalog."
                action={(
                  <div className="panel-actions">
                    {hiddenSetupView === "groups" ? <button className="btn" onClick={openNewHiddenGroupModal}><Plus size={16} /> Thêm Hidden Group</button> : null}
                    {hiddenSetupView === "codes" ? <button className="btn" onClick={openNewHiddenCodeModal}><Plus size={16} /> Thêm Hidden Code</button> : null}
                  </div>
                )}
              />
              <div className="status-grid">
                <Metric label="Hidden group" value={String(hiddenGroups.length)} />
                <Metric label="Đang bật" value={String(hiddenGroups.filter((item) => item.is_active).length)} />
                <Metric label="Hidden code" value={String(hiddenCodes.length)} />
                <Metric label="Lượt mở catalog" value={String(hiddenRedemptions.length)} />
              </div>
              <div className="subtabs hidden-subtabs">
                <button className={hiddenSetupView === "groups" ? "active" : ""} onClick={() => setHiddenSetupView("groups")}>Nhóm ẩn</button>
                <button className={hiddenSetupView === "codes" ? "active" : ""} onClick={() => setHiddenSetupView("codes")}>Mã reveal</button>
                <button className={hiddenSetupView === "activity" ? "active" : ""} onClick={() => setHiddenSetupView("activity")}>Lịch sử mở mã</button>
              </div>
              {hiddenSetupView === "groups" ? (
                <>
                  <div className="hint compact">
                    Mỗi hidden group là một entitlement riêng. ID nên ngắn gọn, ổn định như <code>prime_alpha</code> vì nó đi vào plan token và scheduler.
                  </div>
                  <div className="toolbar hidden-toolbar">
                    <input value={hiddenGroupQuery} onChange={(event) => setHiddenGroupQuery(event.target.value)} placeholder="Tìm theo ID, tên nhóm, chat ID..." />
                  </div>
                  <div className="group-list">
                    {filteredHiddenGroups.length ? filteredHiddenGroups.map((item) => (
                      <div className={item.is_active ? "group-row ok hidden-row" : "group-row hidden-row"} key={item.id}>
                        <span>{item.id}</span>
                        <div className="hidden-row-copy">
                          <strong>{item.name || "Chưa đặt tên"}</strong>
                          <em>{item.chat_id || "Chưa có group ID"} • {hiddenRequirementLabel(item.requirement_type)} • {hiddenCodeUsageByGroup.get(item.id) || 0} mã đang trỏ vào</em>
                          <div className="tag-list">
                            <span>{item.is_active ? "Đang bán" : "Tạm tắt"}</span>
                            <span>30 ngày {money(item.price_1m_vnd || 0)}</span>
                            <span>Trọn đời {money(item.price_life_vnd || 0)}</span>
                            <span>USD {Number(item.price_1m_usd || 0).toFixed(2)} / {Number(item.price_life_usd || 0).toFixed(2)}</span>
                            <span>{item.duration_1m_days}d / {item.lifetime_days}d</span>
                          </div>
                        </div>
                        <div className="coupon-row-actions">
                          <button className="btn secondary" onClick={() => openEditHiddenGroupModal(item)} disabled={saving === `hidden-group-${item.id}`}><Pencil size={16} /> Sửa</button>
                          <button className="btn danger" onClick={() => removeHiddenGroupAction(item.id)} disabled={saving === `hidden-group-delete-${item.id}`}><Trash2 size={16} /> Xóa</button>
                        </div>
                      </div>
                    )) : <div className="empty-card">Chưa có Hidden Group khớp bộ lọc.</div>}
                  </div>
                </>
              ) : null}
              {hiddenSetupView === "codes" ? (
                <>
                  <div className="hint compact">
                    Hidden code chỉ dùng để reveal catalog, không phải coupon. Bạn có thể giới hạn thời gian, số lượt và điều kiện như <code>SVIP_LIFETIME</code>.
                  </div>
                  <div className="toolbar hidden-toolbar">
                    <input value={hiddenCodeQuery} onChange={(event) => setHiddenCodeQuery(event.target.value)} placeholder="Tìm theo mã, tên, rule, group..." />
                  </div>
                  <div className="group-list">
                    {filteredHiddenCodes.length ? filteredHiddenCodes.map((item) => (
                      <div className={item.is_active ? "group-row ok hidden-row" : "group-row hidden-row"} key={item.code}>
                        <span>{item.code}</span>
                        <div className="hidden-row-copy">
                          <strong>{item.name || "Không tên"}</strong>
                          <em>{hiddenScopeLabel(item.scope_type)} • {hiddenRequirementLabel(item.requirement_type)} • used {item.used_count}/{item.max_uses || "∞"}</em>
                          <div className="tag-list">
                            <span>{item.is_active ? "Đang bật" : "Tạm tắt"}</span>
                            <span>{hiddenValidityText(item)}</span>
                            <span>{item.scope_type === "ALL_ACTIVE_HIDDEN_GROUPS" ? "Toàn bộ hidden group active" : `${item.group_ids.length} group cụ thể`}</span>
                            {(item.group_ids || []).slice(0, 4).map((groupId) => <span key={`${item.code}-${groupId}`}>{groupId}</span>)}
                            {item.group_ids.length > 4 ? <span>+{item.group_ids.length - 4} group</span> : null}
                          </div>
                        </div>
                        <div className="coupon-row-actions">
                          <button className="btn secondary" onClick={() => copyHiddenCode(item.code)} disabled={saving === `hidden-code-copy-${item.code}`}><Ticket size={16} /> Copy mã</button>
                          <button className="btn secondary" onClick={() => openEditHiddenCodeModal(item)} disabled={saving === `hidden-code-${item.code}`}><Pencil size={16} /> Sửa</button>
                          <button className="btn danger" onClick={() => removeHiddenCodeAction(item.code)} disabled={saving === `hidden-code-delete-${item.code}`}><Trash2 size={16} /> Xóa</button>
                        </div>
                      </div>
                    )) : <div className="empty-card">Chưa có Hidden Code khớp bộ lọc.</div>}
                  </div>
                </>
              ) : null}
              {hiddenSetupView === "activity" ? (
                <SimpleTable
                  headers={["Thời gian", "Mã", "Người dùng", "Nhóm đã reveal"]}
                  rows={hiddenRedemptions.map((item) => [
                    dateText(item.created_at),
                    <strong key={`code-${item.id || item.code}`}>{item.code}</strong>,
                    <><strong>{item.full_name || item.username || item.telegram_user_id}</strong><div className="muted">{item.telegram_user_id}{item.username ? ` • @${item.username}` : ""}</div></>,
                    item.revealed_group_ids?.length ? item.revealed_group_ids.join(", ") : "-",
                  ])}
                />
              ) : null}
            </section>
          </div>
        ) : null}

        {tab === "orders" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Doanh thu bộ lọc" value={ordersMoney(filteredOrders.filter((item) => item.status === "PAID"))} />
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
              <Metric label="Doanh thu khách lọc" value={ordersMoney(filteredCustomers.flatMap((item) => item.paidOrders))} />
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
                  <span key="status" className={customer.activeOrders.length ? "status paid" : customer.paidOrders.length ? "status expired" : "status pending"}>{customer.activeOrders.length ? "Đang còn hạn" : customer.paidOrders.length ? "Hết hạn / chờ kick" : "Chưa PAID"}</span>,
                  String(customer.paidOrders.length),
                  <><strong>{customer.plans[0] || "-"}</strong><div className="muted">{customer.groups.slice(0, 2).join(", ") || "Chưa rõ group"}</div></>,
                  dateText(customer.latestExpire),
                  ordersMoney(customer.paidOrders),
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

        {tab === "campaigns" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Campaign" value={String(campaigns.length)} />
              <Metric label="Đang chạy" value={String(campaigns.filter((item) => item.status === "RUNNING").length)} />
              <Metric label="Đã gửi" value={String(campaigns.reduce((sum, item) => sum + (item.sent_count || 0), 0))} />
              <Metric label="Preview nhận" value={String(campaignPreview?.total || 0)} />
            </div>
            <section className="panel">
              <PanelHead
                title="Tạo campaign"
                subtitle="Tạo campaign trong popup để tránh trang chính quá nhiều trường. Worker sẽ gửi từng user theo delay để tránh spam."
                action={<button className="btn" onClick={() => { setCampaignForm({ ...EMPTY_CAMPAIGN_FORM }); setCampaignModalOpen(true); }}><Plus size={16} /> Tạo campaign</button>}
              />
              <div className="campaign-preview">
                <strong>Preview: {campaignPreview?.total || 0} người</strong>
                <span>Active: {campaignPreview?.counts?.VIP_ACTIVE || 0}</span>
                <span>Hết hạn: {campaignPreview?.counts?.VIP_EXPIRED || 0}</span>
                <span>Chưa mua: {campaignPreview?.counts?.NO_PURCHASE || 0}</span>
              </div>
            </section>

            <section className="panel">
              <PanelHead title="Danh sách campaign" subtitle="Bấm tên campaign để xem danh sách người nhận và trạng thái từng người." />
              <SimpleTable
                headers={["Campaign", "Tệp", "Trạng thái", "Tiến trình", "Delay", "Thao tác"]}
                rows={campaigns.map((item) => [
                  <button key={`select-${item.id}`} className="link-button" onClick={() => { setSelectedCampaignId(item.id); setCampaignRecipientPage(1); }}><strong>{item.title}</strong><div className="muted">{dateText(item.created_at)}</div></button>,
                  <><strong>{item.target_segment}</strong><div className="muted">{String(item.raw_data?.plan_filter || "ALL")} • {String(item.raw_data?.plan_match_scope || "ANY_PAID")}</div></>,
                  <span key={`status-${item.id}`} className={statusClass(item.status)}>{item.status}</span>,
                  <><strong>{item.sent_count}/{item.total_recipients}</strong><div className="muted">Fail {item.failed_count} • Skip {item.skipped_count}</div></>,
                  `${item.delay_seconds}s`,
                  <div key={`actions-${item.id}`} className="coupon-row-actions">
                    {item.status !== "RUNNING" && item.status !== "DONE" && item.status !== "CANCELLED" ? <button className="btn small" onClick={() => changeCampaignStatus(item.id, "start")}><PlayCircle size={15} /> Gửi</button> : null}
                    {item.status === "RUNNING" ? <button className="btn secondary small" onClick={() => changeCampaignStatus(item.id, "pause")}><PauseCircle size={15} /> Tạm dừng</button> : null}
                    {item.status !== "DONE" && item.status !== "CANCELLED" ? <button className="btn danger small" onClick={() => changeCampaignStatus(item.id, "cancel")}>Huỷ</button> : null}
                  </div>,
                ])}
              />
            </section>

            <section className="panel">
              <PanelHead title={selectedCampaign ? `Người nhận: ${selectedCampaign.title}` : "Người nhận"} subtitle="Danh sách được snapshot lúc tạo campaign. Người đã SENT sẽ không bị gửi lại khi worker restart." />
              <div className="campaign-preview">
                <span>Pending: {campaignRecipientCounts.PENDING || 0}</span>
                <span>Sent: {campaignRecipientCounts.SENT || 0}</span>
                <span>Failed: {campaignRecipientCounts.FAILED || 0}</span>
                <span>Skipped: {campaignRecipientCounts.SKIPPED || 0}</span>
              </div>
              <SimpleTable
                headers={["Khách", "Telegram ID", "Nhóm", "Gói liên quan", "Trạng thái", "Gửi lúc", "Lỗi"]}
                rows={pagedCampaignRecipients.map((item) => [
                  <><strong>{item.full_name || item.username || "-"}</strong><div className="muted">{item.username ? `@${item.username}` : ""}</div></>,
                  item.telegram_user_id,
                  item.segment,
                  <><strong>{String(item.raw_data?.latest_plan_name || "-")}</strong><div className="muted">{Array.isArray(item.raw_data?.paid_plan_names) ? item.raw_data.paid_plan_names.join(", ") : ""}</div></>,
                  <span key={`r-${item.id}`} className={statusClass(item.status)}>{item.status}</span>,
                  dateText(item.sent_at || item.last_attempt_at),
                  item.error || "-",
                ])}
              />
              <Pagination page={campaignRecipientPage} totalPages={totalCampaignRecipientPages} totalItems={campaignRecipients.length} onPage={setCampaignRecipientPage} label="người nhận" />
            </section>
          </div>
        ) : null}

        {tab === "channelPosts" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Tổng bài" value={String(channelPosts.length)} />
              <Metric label="Chờ gửi" value={String(channelPostCounts.queue + channelPostCounts.scheduled)} />
              <Metric label="Đã đăng" value={String(channelPostCounts.sent)} />
              <Metric label="Có lỗi" value={String(channelPostCounts.failed)} />
            </div>
            <section className="panel">
              <PanelHead
                title="Đăng channel"
                subtitle="Soạn bài, gắn nút inline, hẹn giờ đăng hoặc hẹn giờ xóa bài khỏi Telegram. Bot phải là admin của channel/group nhận bài."
                action={<button className="btn" onClick={openNewChannelPostModal}><Plus size={16} /> Soạn bài mới</button>}
              />
              <div className="subtabs">
                <button className={channelPostTab === "draft" ? "active" : ""} onClick={() => setChannelPostTab("draft")}>Nháp ({channelPostCounts.draft})</button>
                <button className={channelPostTab === "queue" ? "active" : ""} onClick={() => setChannelPostTab("queue")}>Chờ gửi ({channelPostCounts.queue})</button>
                <button className={channelPostTab === "scheduled" ? "active" : ""} onClick={() => setChannelPostTab("scheduled")}>Đã lên lịch ({channelPostCounts.scheduled})</button>
                <button className={channelPostTab === "sent" ? "active" : ""} onClick={() => setChannelPostTab("sent")}>Đã đăng ({channelPostCounts.sent})</button>
                <button className={channelPostTab === "failed" ? "active" : ""} onClick={() => setChannelPostTab("failed")}>Lỗi ({channelPostCounts.failed})</button>
                <button className={channelPostTab === "deleted" ? "active" : ""} onClick={() => setChannelPostTab("deleted")}>Đã xóa ({channelPostCounts.deleted})</button>
              </div>
              <SimpleTable
                headers={["Bài đăng", "Channel/Group", "Trạng thái", "Lịch", "Telegram", "Lỗi"]}
                rows={pagedChannelPosts.map((item) => [
                  <button key={`cp-title-${item.id}`} className="link-button" onClick={() => editChannelPost(item)}><strong>{item.title || `Bài #${item.id}`}</strong><div className="muted">{String(item.content || "").slice(0, 90)}</div></button>,
                  item.target_chat_id,
                  <span key={`cp-status-${item.id}`} className={channelPostStatusClass(item.status)}>{channelPostStatusLabel(item.status)}</span>,
                  <><strong>Đăng: {dateText(item.scheduled_at || item.sent_at)}</strong><div className="muted">Xóa: {dateText(item.delete_at || item.deleted_at)}</div></>,
                  <><strong>{item.sent_message_id ? `Message ${item.sent_message_id}` : "-"}</strong><div className="muted">Thử {item.attempt_count || 0} • {dateText(item.updated_at)}{item.repeat_daily ? " • Lặp ngày" : ""}{item.sync_bot_schedule ? " • Gắn giờ bot" : ""}</div></>,
                  item.error ? <><strong>{item.error_code || "telegram_error"}</strong><div className="muted">{item.error}</div></> : "-",
                ])}
                onRow={(idx) => editChannelPost(pagedChannelPosts[idx])}
                actions={(idx) => {
                  const item = pagedChannelPosts[idx];
                  const status = String(item.status || "").toLowerCase();
                  return (
                    <div className="coupon-row-actions">
                      {["draft", "failed", "delete_failed"].includes(status) ? <button className="btn small" onClick={(event) => { event.stopPropagation(); runChannelPostAction(item, "send_now"); }}><Send size={15} /> Gửi</button> : null}
                      {status === "scheduled" ? <button className="btn secondary small" onClick={(event) => { event.stopPropagation(); runChannelPostAction(item, "cancel_schedule"); }}>Hủy lịch</button> : null}
                      {["sent", "delete_scheduled"].includes(status) ? <button className="btn danger small" onClick={(event) => { event.stopPropagation(); runChannelPostAction(item, "delete_now"); }}><Trash2 size={15} /> Xóa</button> : null}
                      {status === "delete_scheduled" ? <button className="btn secondary small" onClick={(event) => { event.stopPropagation(); runChannelPostAction(item, "cancel_delete"); }}>Hủy xóa</button> : null}
                    </div>
                  );
                }}
              />
              <Pagination page={channelPostPage} totalPages={totalChannelPostPages} totalItems={visibleChannelPosts.length} onPage={setChannelPostPage} label="bài đăng" />
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
              <Metric label="Cần kiểm tra kick" value={String(kickAudit.filter((item) => item.needs_action).length)} />
            </div>
            <section className="panel">
              <PanelHead
                title="Quản lý gia hạn"
                subtitle="Theo dõi hạn dùng, lịch nhắc, báo hết hạn và lịch sử kick theo từng tab để danh sách không bị quá dài."
                action={
                  <div className="panel-actions">
                    <button className="btn secondary" onClick={() => refreshKickAudit(true)} disabled={saving === "kick-audit-live"}>
                      {saving === "kick-audit-live" ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />} Kiểm tra live
                    </button>
                    <button className="btn" onClick={() => setRenewalSettingsOpen(true)}><Settings size={16} /> Cài đặt</button>
                  </div>
                }
              />
              <div className="subtabs">
                <button className={renewalTab === "soon" ? "active" : ""} onClick={() => { setRenewalTab("soon"); setRenewalPage(1); }}>Sắp hết hạn ({expiringSoon.length})</button>
                <button className={renewalTab === "today" ? "active" : ""} onClick={() => { setRenewalTab("today"); setRenewalPage(1); }}>Hết hạn hôm nay ({expiringToday.length})</button>
                <button className={renewalTab === "reminded" ? "active" : ""} onClick={() => { setRenewalTab("reminded"); setRenewalPage(1); }}>Đã nhắc ({renewalReminderEvents.length})</button>
                <button className={renewalTab === "expiredNotice" ? "active" : ""} onClick={() => { setRenewalTab("expiredNotice"); setRenewalPage(1); }}>Báo hết hạn ({expiredNoticeEvents.length})</button>
                <button className={renewalTab === "kicked" ? "active" : ""} onClick={() => { setRenewalTab("kicked"); setRenewalPage(1); }}>Đã kick ({uniqueKickedEvents.length})</button>
                <button className={renewalTab === "audit" ? "active" : ""} onClick={() => { setRenewalTab("audit"); setRenewalPage(1); }}>Cần kiểm tra kick ({kickAudit.filter((item) => item.needs_action).length}/{kickAudit.length})</button>
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
              <PanelHead title="Cấu hình vận hành Bot" subtitle="Chỉ chứa thiết lập hệ thống. Nội dung khách nhìn thấy, lệnh, cảnh báo và Menu Builder đã được tách thành menu riêng." />
              <div className="subtabs">
                <button className={contentTab === "bot" ? "active" : ""} onClick={() => setContentTab("bot")}>Cài đặt bot</button>
                <button className={contentTab === "payment" ? "active" : ""} onClick={() => setContentTab("payment")}>Thanh toán</button>
                <button className={contentTab === "currency" ? "active" : ""} onClick={() => setContentTab("currency")}>Tiền tệ</button>
                <button className={contentTab === "admin" ? "active" : ""} onClick={() => setContentTab("admin")}>Admin ID</button>
              </div>
            </section>
            {contentTab === "bot" ? <ConfigEditor title="Cài đặt bot" subtitle="Bảo trì thủ công, lịch hoạt động giờ Việt Nam, QR và tần suất kiểm tra thanh toán." fields={BOT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {contentTab === "payment" ? <ConfigEditor title="Phương thức thanh toán" subtitle="PayOS dùng giá VNĐ; PayPal và NOWPayments dùng giá USD riêng, không quy đổi tỷ giá. Credentials vẫn đặt an toàn trong Render Environment." fields={PAYMENT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {contentTab === "currency" ? <ConfigEditor title="Tiền tệ hiển thị" subtitle="Chỉ đổi cách hiển thị trong bot/UI. Số tiền QR PayOS vẫn giữ nguyên VND." fields={CURRENCY_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {contentTab === "admin" ? <ConfigEditor title="Setup Admin ID" subtitle="Quản lý Telegram ID có quyền admin. Nhiều ID thì cách nhau bằng dấu phẩy." fields={ADMIN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
          </div>
        ) : null}

        {tab === "botVi" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="UI Bot tiếng Việt" subtitle="Chỉ quản lý tên gói và nội dung khách Việt nhìn thấy. Giá được quản lý tập trung tại Nhóm & giá." />
              <div className="subtabs">
                <button className={botViTab === "plans" ? "active" : ""} onClick={() => setBotViTab("plans")}>Tên gói & nút mua</button>
                <button className={botViTab === "groups" ? "active" : ""} onClick={() => setBotViTab("groups")}>Mô tả group</button>
                <button className={botViTab === "buttons" ? "active" : ""} onClick={() => setBotViTab("buttons")}>Nút bấm</button>
                <button className={botViTab === "messages" ? "active" : ""} onClick={() => setBotViTab("messages")}>Tin nhắn</button>
                <button className={botViTab === "saleContent" ? "active" : ""} onClick={() => setBotViTab("saleContent")}>Flash sale</button>
              </div>
            </section>
            {botViTab === "plans" ? <ConfigEditor title="Tên gói và nút mua tiếng Việt" subtitle="Không chứa giá. Giá bán được quản lý tập trung tại Nhóm & giá." fields={PLAN_VI_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botViTab === "groups" ? <ConfigEditor title="Mô tả group lẻ tiếng Việt" subtitle="Chỉ chỉnh nội dung mô tả. Tên group và giá nằm tại Nhóm & giá." fields={groupViContentFields} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botViTab === "buttons" ? <ConfigEditor title="Nút bấm tiếng Việt" subtitle="Text nút Telegram dành cho khách Việt." fields={BUTTON_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botViTab === "messages" ? <ConfigEditor title="Tin nhắn tiếng Việt" subtitle="Các mẫu tin Bot gửi cho khách Việt." fields={MESSAGE_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botViTab === "saleContent" ? <ConfigEditor title="Flash sale tiếng Việt" subtitle="Nội dung flash sale dành cho khách Việt." fields={SALE_CONTENT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
          </div>
        ) : null}

        {tab === "botEn" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="UI Bot tiếng Anh" subtitle="Chỉ quản lý tên gói và nội dung tiếng Anh. Giá USD PayPal được quản lý tập trung tại Nhóm & giá." />
              <div className="subtabs">
                <button className={botEnTab === "plans" ? "active" : ""} onClick={() => setBotEnTab("plans")}>Tên gói & nút mua</button>
                <button className={botEnTab === "groups" ? "active" : ""} onClick={() => setBotEnTab("groups")}>Mô tả group</button>
                <button className={botEnTab === "buttons" ? "active" : ""} onClick={() => setBotEnTab("buttons")}>Nút bấm</button>
                <button className={botEnTab === "messages" ? "active" : ""} onClick={() => setBotEnTab("messages")}>Tin nhắn</button>
                <button className={botEnTab === "saleContent" ? "active" : ""} onClick={() => setBotEnTab("saleContent")}>Flash sale</button>
              </div>
            </section>
            {botEnTab === "plans" ? <ConfigEditor title="Tên gói và nút mua tiếng Anh" subtitle="Không chứa giá. Giá USD PayPal được quản lý tập trung tại Nhóm & giá." fields={PLAN_EN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botEnTab === "groups" ? <ConfigEditor title="Mô tả group lẻ tiếng Anh" subtitle="Chỉ chỉnh nội dung mô tả. Tên tiếng Anh và giá USD nằm tại Nhóm & giá." fields={groupEnContentFields} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botEnTab === "buttons" ? <ConfigEditor title="Nút bấm tiếng Anh" subtitle="Các key BTN_*_EN dành riêng cho khách tiếng Anh." fields={BUTTON_EN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botEnTab === "messages" ? <ConfigEditor title="Tin nhắn tiếng Anh" subtitle="Các key MSG_*_EN dành riêng cho khách tiếng Anh." fields={MESSAGE_EN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botEnTab === "saleContent" ? <ConfigEditor title="Flash sale tiếng Anh" subtitle="Nội dung sale tiếng Anh, dùng giá USD." fields={SALE_CONTENT_EN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
          </div>
        ) : null}

        {tab === "botTools" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="Lệnh & cảnh báo Bot" subtitle="Tách riêng khỏi nội dung UI để dễ kiểm soát các lệnh Telegram và alert ngắn." />
              <div className="subtabs">
                <button className={botToolsTab === "commandsVi" ? "active" : ""} onClick={() => setBotToolsTab("commandsVi")}>Lệnh tiếng Việt</button>
                <button className={botToolsTab === "commandsEn" ? "active" : ""} onClick={() => setBotToolsTab("commandsEn")}>Lệnh tiếng Anh</button>
                <button className={botToolsTab === "alertsVi" ? "active" : ""} onClick={() => setBotToolsTab("alertsVi")}>Cảnh báo tiếng Việt</button>
                <button className={botToolsTab === "alertsEn" ? "active" : ""} onClick={() => setBotToolsTab("alertsEn")}>Cảnh báo tiếng Anh</button>
              </div>
            </section>
            {botToolsTab === "commandsVi" ? <ConfigEditor title="Lệnh Telegram tiếng Việt" subtitle="Mô tả lệnh hiển thị cho khách Việt." fields={COMMAND_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botToolsTab === "commandsEn" ? <ConfigEditor title="Lệnh Telegram tiếng Anh" subtitle="Mô tả lệnh hiển thị cho khách tiếng Anh." fields={COMMAND_EN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botToolsTab === "alertsVi" ? <ConfigEditor title="Cảnh báo tiếng Việt" subtitle="Alert ngắn khi khách Việt thao tác." fields={ALERT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botToolsTab === "alertsEn" ? <ConfigEditor title="Cảnh báo tiếng Anh" subtitle="Alert ngắn khi khách tiếng Anh thao tác." fields={ALERT_EN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
          </div>
        ) : null}

        {tab === "menuBuilder" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="Menu Builder" subtitle="Trang tiếng Việt và tiếng Anh được tách riêng. Trang tiếng Anh dùng hậu tố _en." />
              <div className="subtabs">
                <button className={menuLanguage === "vi" ? "active" : ""} onClick={() => { setMenuLanguage("vi"); resetMenuForm(); }}>Trang tiếng Việt</button>
                <button className={menuLanguage === "en" ? "active" : ""} onClick={() => { setMenuLanguage("en"); resetMenuForm(); }}>Trang tiếng Anh</button>
              </div>
            </section>
              <section className="panel">
                <PanelHead
                  title={menuLanguage === "en" ? "Menu Builder tiếng Anh" : "Menu Builder tiếng Việt"}
                  subtitle={menuLanguage === "en" ? "Tên trang bắt buộc kết thúc bằng _en, ví dụ main_menu_en." : "Trang gốc tiếng Việt không dùng hậu tố _en."}
                  action={
                    <div className="panel-actions">
                      <button className="btn" onClick={() => { resetMenuForm(); setMenuModalOpen(true); }}><Plus size={16} /> Thêm trang</button>
                    </div>
                  }
                />
                <SimpleTable
                  headers={["Trang", "Nội dung", "Nút"]}
                  rows={visibleMenuPages.map((item) => [item.page_id, item.body, item.layout])}
                  onRow={(idx) => {
                    const item = visibleMenuPages[idx];
                    setMenuForm({ page_id: item.page_id, image_url: item.image_url || "", body: item.body || "", layout: item.layout || "" });
                    setMenuModalOpen(true);
                  }}
                  actions={(idx) => (
                    <button className="icon-danger" onClick={(event) => { event.stopPropagation(); removeMenuPage(visibleMenuPages[idx].page_id); }} title="Xoá trang">
                      <Trash2 size={16} />
                    </button>
                  )}
                />
              </section>
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
                  key="coupon-code"
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
                    <button className="btn" onClick={() => { setBlacklistForm({ telegram_user_id: "", username: "", full_name: "", reason: "" }); setBlacklistModalOpen(true); }}><Plus size={16} /> Thêm blacklist</button>
                  </div>
                }
              />
              <div className="hint compact">Cấu hình bảo mật được tách vào popup để phần blacklist luôn gọn và dễ thao tác.</div>
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
                  setBlacklistModalOpen(true);
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
                  <button className="btn" onClick={() => { resetSaleForm(); setSaleModalOpen(true); }}><Plus size={16} /> Thêm sale</button>
                </div>
              }
            />
            <SimpleTable
              headers={["Sale", "Gói", "Giảm %", "Giá sale", "Slot", "Bật"]}
              rows={saleRules.map((item) => [item.sale_id, item.price_key, String(item.discount_percent || "-"), String(item.sale_price || "-"), String(item.slot_limit || "-"), item.enabled ? "ON" : "OFF"])}
              onRow={(idx) => {
                const item = saleRules[idx];
                setSaleForm({ sale_id: item.sale_id, price_key: item.price_key, discount_percent: String(item.discount_percent || ""), sale_price: String(item.sale_price || ""), slot_limit: String(item.slot_limit || ""), enabled: item.enabled ? "ON" : "OFF", start_at: item.starts_at || "", end_at: item.ends_at || "" });
                setSaleModalOpen(true);
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

        {svipPriceSettingsOpen ? (
          <SettingsConfigModal title="Cài đặt giá SVIP chung" subtitle="Giá VNĐ dùng PayOS/VietQR, giá USD dùng PayPal. Đây là nơi duy nhất chỉnh giá SVIP." fields={SVIP_PRICE_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} onClose={() => setSvipPriceSettingsOpen(false)} />
        ) : null}

        {groupModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title={`Cấu hình nhóm G${groupNo}`}
                subtitle="Tên nhóm, group ID và giá bán được lưu tập trung tại đây."
                action={<button className="icon-danger" onClick={() => setGroupModalOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="form-grid">
                <label className="field">
                  <span>Nhóm cần cấu hình</span>
                  <select value={groupNo} onChange={(event) => fillGroupForm(event.target.value)}>
                    {groupSelectOptions.map((item) => (
                      <option key={item} value={item}>G{item}{visibleGroups.includes(item) ? "" : " - nhóm mới"}</option>
                    ))}
                  </select>
                  <small>Coupon và sale sẽ hiện tên nhóm này trong dropdown.</small>
                </label>
                <label className="field"><span>Tên nhóm tiếng Việt</span><input value={groupName} onChange={(event) => setGroupName(event.target.value)} placeholder={getConfigValue(config, `BTN_G${groupNo}`) || "VD: Hang Cú Prime"} /></label>
                <label className="field"><span>Tên nhóm tiếng Anh</span><input value={groupNameEn} onChange={(event) => setGroupNameEn(event.target.value)} placeholder={getConfigValue(config, `BTN_G${groupNo}_EN`) || "VD: Prime Group"} /></label>
                <label className="field"><span>Telegram group ID</span><input value={groupId} onChange={(event) => setGroupId(event.target.value)} placeholder={getConfigValue(config, `ID_G${groupNo}`) || "VD: -1001234567890"} /></label>
                <label className="field"><span>Giá VNĐ 30 ngày</span><input value={groupPrice1m} onChange={(event) => setGroupPrice1m(event.target.value)} placeholder={getConfigValue(config, `PRICE_G${groupNo}_1M`) || "VD: 99000"} /></label>
                <label className="field"><span>Giá VNĐ trọn đời</span><input value={groupPriceLife} onChange={(event) => setGroupPriceLife(event.target.value)} placeholder={getConfigValue(config, `PRICE_G${groupNo}_LIFE`) || "VD: 299000"} /></label>
                <label className="field"><span>Giá USD 30 ngày</span><input value={groupPrice1mUsd} onChange={(event) => setGroupPrice1mUsd(event.target.value)} placeholder="VD: 4.99" /></label>
                <label className="field"><span>Giá USD trọn đời</span><input value={groupPriceLifeUsd} onChange={(event) => setGroupPriceLifeUsd(event.target.value)} placeholder="VD: 14.99" /></label>
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setGroupModalOpen(false)}>Đóng</button>
                <button className="btn danger" onClick={removeGroupConfig} disabled={saving === "group-delete"}><Trash2 size={16} /> Xoá nhóm</button>
                <button className="btn" onClick={saveGroupConfig} disabled={saving === "group"}>{saving === "group" ? <Loader2 size={16} className="spin" /> : <Save size={16} />} Lưu nhóm</button>
              </div>
            </section>
          </div>
        ) : null}

        {hiddenGroupModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title={hiddenGroupForm.id ? `Hidden Group: ${hiddenGroupForm.id}` : "Tạo Hidden Group"}
                subtitle="Thiết lập group extra ẩn, giá, hạn và điều kiện mua. Không còn phải nhập JSON thủ công."
                action={<button className="icon-danger" onClick={() => setHiddenGroupModalOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="form-grid">
                <label className="field">
                  <span>ID kỹ thuật</span>
                  <input value={hiddenGroupForm.id} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, id: hiddenSlug(event.target.value) })} placeholder="VD: prime_alpha" />
                  <small>Dùng trong plan token dạng <code>HG:prime_alpha:1M</code>. Để trống thì hệ thống tự tạo từ tên.</small>
                </label>
                <label className="field">
                  <span>Tên hiển thị</span>
                  <input value={hiddenGroupForm.name} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, name: event.target.value })} placeholder="VD: Prime Alpha" />
                </label>
                <label className="field">
                  <span>Telegram group ID</span>
                  <input value={hiddenGroupForm.chat_id} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, chat_id: event.target.value })} placeholder="-1001234567890" />
                </label>
                <label className="field wide">
                  <span>Mô tả ngắn</span>
                  <textarea value={hiddenGroupForm.description} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, description: event.target.value })} placeholder="Mô tả nội bộ hoặc nội dung bot dùng để giới thiệu hidden group." />
                </label>
                <div className="hint compact wide">Giá duration nào để 0 thì bot sẽ không hiện nút mua duration đó. Nếu chỉ bán trọn đời, để giá 30 ngày VND/USD = 0 và chỉ nhập giá trọn đời.</div>
                <label className="field">
                  <span>Giá VNĐ 30 ngày</span>
                  <input value={hiddenGroupForm.price_1m_vnd} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, price_1m_vnd: event.target.value })} inputMode="numeric" placeholder="99000" />
                </label>
                <label className="field">
                  <span>Giá VNĐ trọn đời</span>
                  <input value={hiddenGroupForm.price_life_vnd} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, price_life_vnd: event.target.value })} inputMode="numeric" placeholder="299000" />
                </label>
                <label className="field">
                  <span>Giá USD 30 ngày</span>
                  <input value={hiddenGroupForm.price_1m_usd} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, price_1m_usd: event.target.value })} inputMode="decimal" placeholder="4.99" />
                </label>
                <label className="field">
                  <span>Giá USD trọn đời</span>
                  <input value={hiddenGroupForm.price_life_usd} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, price_life_usd: event.target.value })} inputMode="decimal" placeholder="14.99" />
                </label>
                <label className="field">
                  <span>Hạn 30 ngày (days)</span>
                  <input value={hiddenGroupForm.duration_1m_days} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, duration_1m_days: event.target.value })} inputMode="numeric" placeholder="30" />
                </label>
                <label className="field">
                  <span>Hạn trọn đời (days)</span>
                  <input value={hiddenGroupForm.lifetime_days} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, lifetime_days: event.target.value })} inputMode="numeric" placeholder="3650" />
                </label>
                <label className="field">
                  <span>Sort order</span>
                  <input value={hiddenGroupForm.sort_order} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, sort_order: event.target.value })} inputMode="numeric" placeholder="1" />
                </label>
                <label className="field">
                  <span>Ảnh / File ID</span>
                  <input value={hiddenGroupForm.image_url} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, image_url: event.target.value })} placeholder="URL hoặc Telegram file_id nếu có" />
                </label>
                <label className="field">
                  <span>Điều kiện mặc định</span>
                  <select value={hiddenGroupForm.requirement_type} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, requirement_type: event.target.value, requirement_value: hiddenRequirementNeedsValue(event.target.value) ? hiddenGroupForm.requirement_value : "" })}>
                    {HIDDEN_REQUIREMENT_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                  </select>
                </label>
                <label className="field">
                  <span>Requirement value</span>
                  <input value={hiddenGroupForm.requirement_value} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, requirement_value: event.target.value })} placeholder="VD: FULL_LIFE hoặc HG:prime_alpha:LIFE" disabled={!hiddenRequirementNeedsValue(hiddenGroupForm.requirement_type)} />
                </label>
                <label className="field">
                  <span>Trạng thái</span>
                  <select value={hiddenGroupForm.is_active ? "ON" : "OFF"} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, is_active: event.target.value === "ON" })}>
                    <option value="ON">Đang bật</option>
                    <option value="OFF">Tạm tắt</option>
                  </select>
                </label>
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setHiddenGroupModalOpen(false)}>Đóng</button>
                {hiddenGroupForm.id ? <button className="btn secondary" onClick={() => setHiddenGroupForm({ ...hiddenGroupForm, id: hiddenSlug(hiddenGroupForm.name) || hiddenGroupForm.id })}><RefreshCw size={16} /> Tạo lại ID từ tên</button> : null}
                <button className="btn" onClick={saveHiddenGroup} disabled={saving === `hidden-group-${hiddenGroupForm.id || hiddenSlug(hiddenGroupForm.name) || "new"}`}>{saving === `hidden-group-${hiddenGroupForm.id || hiddenSlug(hiddenGroupForm.name) || "new"}` ? <Loader2 size={16} className="spin" /> : <Save size={16} />} Lưu Hidden Group</button>
              </div>
            </section>
          </div>
        ) : null}

        {hiddenCodeModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title={hiddenCodeForm.code ? `Hidden Code: ${hiddenCodeForm.code}` : "Tạo Hidden Code"}
                subtitle="Mã reveal catalog hidden group. Có thể giới hạn group, điều kiện và khoảng thời gian sử dụng."
                action={<button className="icon-danger" onClick={() => setHiddenCodeModalOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="modal-content">
                <div className="form-grid">
                  <label className="field">
                    <span>Mã hidden</span>
                    <input value={hiddenCodeForm.code} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, code: event.target.value.toUpperCase().replace(/\s+/g, "-") })} placeholder="VD: PRIME-ALPHA" />
                    <small>Bot chỉ hiện hidden catalog cho người nhập đúng mã này.</small>
                  </label>
                  <label className="field">
                    <span>Tên nội bộ</span>
                    <input value={hiddenCodeForm.name} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, name: event.target.value })} placeholder="VD: Code bán cho cộng tác viên A" />
                  </label>
                  <label className="field">
                    <span>Trạng thái</span>
                    <select value={hiddenCodeForm.is_active ? "ON" : "OFF"} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, is_active: event.target.value === "ON" })}>
                      <option value="ON">Đang bật</option>
                      <option value="OFF">Tạm tắt</option>
                    </select>
                  </label>
                  <label className="field wide">
                    <span>Mô tả ghi chú</span>
                    <textarea value={hiddenCodeForm.description} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, description: event.target.value })} placeholder="Ghi chú nội bộ: mã này dùng cho ai, campaign nào, mục đích gì..." />
                  </label>
                  <label className="field">
                    <span>Phạm vi reveal</span>
                    <select value={hiddenCodeForm.scope_type} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, scope_type: event.target.value })}>
                      {HIDDEN_SCOPE_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                    </select>
                  </label>
                  <label className="field">
                    <span>Điều kiện override</span>
                    <select value={hiddenCodeForm.requirement_type} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, requirement_type: event.target.value, requirement_value: hiddenRequirementNeedsValue(event.target.value) ? hiddenCodeForm.requirement_value : "" })}>
                      <option value="">Dùng rule của hidden group</option>
                      {HIDDEN_REQUIREMENT_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                    </select>
                  </label>
                  <label className="field">
                    <span>Requirement value</span>
                    <input value={hiddenCodeForm.requirement_value} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, requirement_value: event.target.value })} placeholder="VD: FULL_LIFE hoặc HG:prime_alpha:LIFE" disabled={!hiddenRequirementNeedsValue(hiddenCodeForm.requirement_type)} />
                  </label>
                  <label className="field">
                    <span>Max uses</span>
                    <input value={hiddenCodeForm.max_uses} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, max_uses: event.target.value })} inputMode="numeric" placeholder="0 = không giới hạn" />
                  </label>
                  <label className="field">
                    <span>Used count</span>
                    <input value={hiddenCodeForm.used_count} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, used_count: event.target.value })} inputMode="numeric" placeholder="0" />
                  </label>
                  <label className="field">
                    <span>Hiệu lực từ</span>
                    <input type="datetime-local" value={hiddenCodeForm.valid_from} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, valid_from: event.target.value })} />
                  </label>
                  <label className="field">
                    <span>Hiệu lực đến</span>
                    <input type="datetime-local" value={hiddenCodeForm.valid_until} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, valid_until: event.target.value })} />
                  </label>
                </div>
                <div className="coupon-scope">
                  <div className="coupon-scope-head">
                    <strong>Hidden groups được reveal</strong>
                    <span className="muted">{hiddenCodeForm.scope_type === "ALL_ACTIVE_HIDDEN_GROUPS" ? "Đang áp dụng cho mọi hidden group active." : `${hiddenCodeForm.group_ids.length} group đã chọn`}</span>
                  </div>
                  {hiddenCodeForm.scope_type === "SELECTED_GROUPS" ? (
                    hiddenGroups.length ? (
                      <div className="check-grid">
                        {hiddenGroups.map((group) => (
                          <label key={group.id} className={hiddenCodeForm.group_ids.includes(group.id) ? "check-card active" : "check-card"}>
                            <input type="checkbox" checked={hiddenCodeForm.group_ids.includes(group.id)} onChange={() => toggleHiddenCodeGroup(group.id)} />
                            <div>
                              <strong>{group.name || group.id}</strong>
                              <div className="muted">{group.id} • {group.chat_id || "chưa có chat ID"}{group.is_active ? "" : " • đang tắt"}</div>
                            </div>
                          </label>
                        ))}
                      </div>
                    ) : <div className="empty-card">Cần tạo Hidden Group trước khi gán cho Hidden Code.</div>
                  ) : (
                    <div className="hint compact">Code này sẽ tự reveal toàn bộ Hidden Group đang bật, nên không cần chọn group thủ công.</div>
                  )}
                </div>
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setHiddenCodeModalOpen(false)}>Đóng</button>
                <button className="btn secondary" onClick={() => setHiddenCodeForm({ ...hiddenCodeForm, code: hiddenCodeSeed(hiddenCodeForm.name || hiddenCodeForm.description || "hidden-code") })}><RefreshCw size={16} /> Gợi ý mã từ tên</button>
                <button className="btn" onClick={saveHiddenCode} disabled={saving === `hidden-code-${(hiddenCodeForm.code.trim() || hiddenCodeSeed(hiddenCodeForm.name)).toUpperCase()}`}>{saving === `hidden-code-${(hiddenCodeForm.code.trim() || hiddenCodeSeed(hiddenCodeForm.name)).toUpperCase()}` ? <Loader2 size={16} className="spin" /> : <Save size={16} />} Lưu Hidden Code</button>
              </div>
            </section>
          </div>
        ) : null}

        {campaignModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title="Tạo campaign"
                subtitle="Chọn tệp nhận, lọc theo gói và nhập nội dung gửi. Campaign tạo xong vẫn cần bấm Gửi ở danh sách."
                action={<button className="icon-danger" onClick={() => setCampaignModalOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="modal-content">
                <div className="form-grid">
                  <label className="field"><span>Tên campaign</span><input value={campaignForm.title} onChange={(event) => setCampaignForm({ ...campaignForm, title: event.target.value })} placeholder="VD: Sale cuối tuần / Tặng coupon tháng 6" /></label>
                  <label className="field"><span>Tệp người nhận</span><select value={campaignForm.target_segment} onChange={(event) => setCampaignForm({ ...campaignForm, target_segment: event.target.value })}>
                    <option value="ALL">Tất cả user từng tương tác</option>
                    <option value="VIP_PAID">Đã từng mua VIP</option>
                    <option value="VIP_ACTIVE">Đang còn VIP active</option>
                    <option value="VIP_EXPIRED">Đã từng mua nhưng hết hạn</option>
                    <option value="NO_PURCHASE">Chưa mua gói</option>
                  </select><small>Blacklist active sẽ tự bị loại khỏi danh sách gửi.</small></label>
                  <label className="field"><span>Lọc theo gói đã mua</span><select value={campaignForm.plan_filter} onChange={(event) => setCampaignForm({ ...campaignForm, plan_filter: event.target.value })}>
                    <option value="ALL">Tất cả gói</option>
                    {campaignPlanOptions.map((item) => <option key={item} value={item}>{item}</option>)}
                  </select><small>Lấy từ tên gói trong các đơn PAID hiện có.</small></label>
                  <label className="field"><span>Cách so khớp gói</span><select value={campaignForm.plan_match_scope} onChange={(event) => setCampaignForm({ ...campaignForm, plan_match_scope: event.target.value })}>
                    <option value="ANY_PAID">Từng mua gói này</option>
                    <option value="ACTIVE_ONLY">Đang active gói này</option>
                    <option value="LATEST">Gói PAID mới nhất là gói này</option>
                  </select><small>Chỉ áp dụng khi bạn chọn một gói cụ thể.</small></label>
                  <label className="field"><span>Delay mỗi user</span><input value={campaignForm.delay_seconds} onChange={(event) => setCampaignForm({ ...campaignForm, delay_seconds: event.target.value })} inputMode="numeric" placeholder="5" /><small>Tối thiểu 2 giây.</small></label>
                  <label className="field"><span>Số gửi mỗi vòng</span><input value={campaignForm.batch_size} onChange={(event) => setCampaignForm({ ...campaignForm, batch_size: event.target.value })} inputMode="numeric" placeholder="20" /></label>
                  <label className="field"><span>Định dạng</span><select value={campaignForm.parse_mode} onChange={(event) => setCampaignForm({ ...campaignForm, parse_mode: event.target.value })}><option value="HTML">HTML</option><option value="NONE">Text thường</option></select></label>
                  <label className="field wide"><span>Nội dung tin nhắn</span><textarea value={campaignForm.message} onChange={(event) => setCampaignForm({ ...campaignForm, message: event.target.value })} placeholder={"Xin chào {name},\\nShop đang có ưu đãi mới...\\nCoupon của bạn: HANGCU_..."} /><small>Dùng biến {"{name}"}, {"{telegram_user_id}"}, {"{segment}"}, {"{latest_plan_name}"}.</small></label>
                </div>
                <div className="campaign-preview">
                  <strong>Preview: {campaignPreview?.total || 0} người</strong>
                  <span>Active: {campaignPreview?.counts?.VIP_ACTIVE || 0}</span>
                  <span>Hết hạn: {campaignPreview?.counts?.VIP_EXPIRED || 0}</span>
                  <span>Chưa mua: {campaignPreview?.counts?.NO_PURCHASE || 0}</span>
                </div>
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setCampaignModalOpen(false)}>Đóng</button>
                <button className="btn" onClick={saveCampaign} disabled={saving === "campaign-create" || !campaignForm.title.trim() || !campaignForm.message.trim()}>
                  {saving === "campaign-create" ? <Loader2 size={16} className="spin" /> : <Plus size={16} />} Tạo campaign
                </button>
              </div>
            </section>
          </div>
        ) : null}

        {menuModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title={menuForm.page_id ? `Menu: ${menuForm.page_id}` : "Thêm trang menu"}
                subtitle={menuLanguage === "en" ? "Trang tiếng Anh bắt buộc kết thúc bằng _en." : "Trang tiếng Việt không dùng hậu tố _en."}
                action={<button className="icon-danger" onClick={() => setMenuModalOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="form-grid two">
                <label className="field"><span>Tên trang</span><input value={menuForm.page_id} onChange={(event) => setMenuForm({ ...menuForm, page_id: event.target.value })} placeholder={menuLanguage === "en" ? "VD: main_menu_en, support_page_en" : "VD: main_menu, support_page"} /><small>{menuLanguage === "en" ? "Trang tiếng Anh bắt buộc có hậu tố _en." : "Trang tiếng Việt không được dùng hậu tố _en."}</small></label>
                <label className="field"><span>Ảnh cover</span><input value={menuForm.image_url} onChange={(event) => setMenuForm({ ...menuForm, image_url: event.target.value })} placeholder="File ID Telegram hoặc URL ảnh" /></label>
                <label className="field wide"><span>Nội dung trang</span><textarea value={menuForm.body} onChange={(event) => setMenuForm({ ...menuForm, body: event.target.value })} placeholder="Nhập nội dung HTML. Có thể dùng {PRICE_SVIP_30D}, {SALE_LABEL_PRICE_SVIP_30D}..." /></label>
                <label className="field wide"><span>Nút bấm</span><textarea value={menuForm.layout} onChange={(event) => setMenuForm({ ...menuForm, layout: event.target.value })} placeholder={"Mỗi dòng là một hàng nút. Ví dụ:\\nMua SVIP => buy_full_1m | Hỗ trợ => nav:support_page"} /><small>Có thể dùng biến như {"{BTN_BUY_SVIP_30D}"}.</small></label>
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setMenuModalOpen(false)}>Đóng</button>
                <button className="btn danger" onClick={() => removeMenuPage()} disabled={!menuForm.page_id}><Trash2 size={16} /> Xoá trang</button>
                <button className="btn" onClick={saveMenuPage}><Save size={16} /> Lưu menu</button>
              </div>
            </section>
          </div>
        ) : null}

        {saleModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title={saleForm.sale_id ? `Sale: ${saleForm.sale_id}` : "Thêm sale"}
                subtitle="Tạo giảm giá theo phần trăm hoặc giá sale cố định cho một gói."
                action={<button className="icon-danger" onClick={() => setSaleModalOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="form-grid">
                <label className="field"><span>Tên chương trình sale</span><input value={saleForm.sale_id} onChange={(event) => setSaleForm({ ...saleForm, sale_id: event.target.value })} placeholder="VD: FLASH-G1-THANG-5" /></label>
                <label className="field"><span>Gói áp dụng</span><select value={saleForm.price_key} onChange={(event) => setSaleForm({ ...saleForm, price_key: event.target.value })}>{priceKeyOptions.map((item) => <option key={item} value={item}>{priceOptionLabel(item)}</option>)}</select><small>Chỉ hiện nhóm đã setup, cộng với SVIP chung.</small></label>
                <label className="field"><span>Giảm theo phần trăm</span><input value={saleForm.discount_percent} onChange={(event) => setSaleForm({ ...saleForm, discount_percent: event.target.value })} placeholder="VD: 20" /></label>
                <label className="field"><span>Hoặc giá sale cố định</span><input value={saleForm.sale_price} onChange={(event) => setSaleForm({ ...saleForm, sale_price: event.target.value })} placeholder="VD: 79000" /></label>
                <label className="field"><span>Giới hạn slot</span><input value={saleForm.slot_limit} onChange={(event) => setSaleForm({ ...saleForm, slot_limit: event.target.value })} placeholder="Để trống hoặc 0 nếu không giới hạn" /></label>
                <label className="field"><span>Trạng thái</span><select value={saleForm.enabled} onChange={(event) => setSaleForm({ ...saleForm, enabled: event.target.value })}><option value="ON">Bật</option><option value="OFF">Tắt</option></select></label>
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setSaleModalOpen(false)}>Đóng</button>
                <button className="btn danger" onClick={() => removeSaleRule()} disabled={!saleForm.sale_id}><Trash2 size={16} /> Xoá sale</button>
                <button className="btn" onClick={saveSaleRule}><Save size={16} /> Lưu sale</button>
              </div>
            </section>
          </div>
        ) : null}

        {blacklistModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel">
              <PanelHead
                title={blacklistForm.telegram_user_id ? `Blacklist ${blacklistForm.telegram_user_id}` : "Thêm blacklist"}
                subtitle="Chặn seller hoặc user spam theo Telegram ID."
                action={<button className="icon-danger" onClick={() => setBlacklistModalOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="form-grid two">
                <label className="field"><span>Telegram ID</span><input value={blacklistForm.telegram_user_id} onChange={(event) => setBlacklistForm({ ...blacklistForm, telegram_user_id: event.target.value.trim() })} placeholder="VD: 123456789" /></label>
                <label className="field"><span>Username</span><input value={blacklistForm.username} onChange={(event) => setBlacklistForm({ ...blacklistForm, username: event.target.value })} placeholder="@username nếu có" /></label>
                <label className="field"><span>Tên hiển thị</span><input value={blacklistForm.full_name} onChange={(event) => setBlacklistForm({ ...blacklistForm, full_name: event.target.value })} placeholder="Tên user" /></label>
                <label className="field"><span>Lý do</span><input value={blacklistForm.reason} onChange={(event) => setBlacklistForm({ ...blacklistForm, reason: event.target.value })} placeholder="VD: Seller gắn link bio" /></label>
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setBlacklistModalOpen(false)}>Đóng</button>
                <button className="btn danger" onClick={() => removeBlacklistEntry()} disabled={!blacklistForm.telegram_user_id}><Trash2 size={16} /> Gỡ chặn</button>
                <button className="btn" onClick={saveBlacklistEntry}><ShieldCheck size={16} /> Lưu blacklist</button>
              </div>
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

        {channelPostModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title={channelPostForm.id ? "Sửa bài đăng channel" : "Soạn bài đăng channel"}
                subtitle="Giờ nhập trong popup là giờ Việt Nam trên máy admin. Bot sẽ gửi/xóa bằng worker backend."
                action={<button className="icon-danger" onClick={() => setChannelPostModalOpen(false)} title="Đóng"><XCircle size={18} /></button>}
              />
              <div className="modal-content">
                <div className="form-grid two">
                  <label className="field">
                    <span>Channel / group nhận bài</span>
                    <input value={channelPostForm.target_chat_id} onChange={(event) => setChannelPostForm({ ...channelPostForm, target_chat_id: event.target.value })} placeholder="@channel_username hoặc -100..." />
                    <small>Bot phải là admin và có quyền gửi/xóa bài ở nơi này.</small>
                  </label>
                  <label className="field">
                    <span>Tiêu đề quản lý</span>
                    <input value={channelPostForm.title} onChange={(event) => setChannelPostForm({ ...channelPostForm, title: event.target.value })} placeholder="VD: Sale cuối tuần" />
                    <small>Chỉ để admin dễ tìm, không bắt buộc hiển thị cho khách.</small>
                  </label>
                  <label className="field wide">
                    <span>Ảnh / file_id Telegram</span>
                    <input value={channelPostForm.image_ref} onChange={(event) => setChannelPostForm({ ...channelPostForm, image_ref: event.target.value })} placeholder="https://... hoặc file_id ảnh" />
                    <small>Dán link ảnh công khai hoặc file_id ảnh từ Telegram. Để trống nếu chỉ muốn đăng text.</small>
                  </label>
                  <label className="field wide">
                    <span>Nội dung gửi Telegram</span>
                    <textarea value={channelPostForm.content} onChange={(event) => setChannelPostForm({ ...channelPostForm, content: event.target.value })} placeholder="Soạn nội dung bài đăng..." rows={9} />
                  </label>
                  <label className="field wide">
                    <span>Nút inline</span>
                    <textarea value={channelPostForm.buttons_text} onChange={(event) => setChannelPostForm({ ...channelPostForm, buttons_text: event.target.value })} placeholder={"Tên nút | https://link.com\\nNút 1 | https://a.com || Nút 2 | https://b.com"} rows={4} />
                    <small>Mỗi dòng là một hàng nút. Dùng dấu || để đặt nhiều nút cùng hàng.</small>
                  </label>
                  <label className="field">
                    <span>Định dạng</span>
                    <select value={channelPostForm.parse_mode} onChange={(event) => setChannelPostForm({ ...channelPostForm, parse_mode: event.target.value })}>
                      <option value="HTML">HTML</option>
                      <option value="NONE">Text thường</option>
                    </select>
                  </label>
                  <label className="field">
                    <span>Ẩn preview link</span>
                    <select value={channelPostForm.disable_web_page_preview ? "ON" : "OFF"} onChange={(event) => setChannelPostForm({ ...channelPostForm, disable_web_page_preview: event.target.value === "ON" })}>
                      <option value="OFF">Không</option>
                      <option value="ON">Có</option>
                    </select>
                  </label>
                  <label className="field">
                    <span>Hẹn giờ đăng</span>
                    <input type="datetime-local" value={channelPostForm.scheduled_at} onChange={(event) => setChannelPostForm({ ...channelPostForm, scheduled_at: event.target.value })} />
                  </label>
                  <label className="field">
                    <span>Hẹn giờ xóa</span>
                    <input type="datetime-local" value={channelPostForm.delete_at} onChange={(event) => setChannelPostForm({ ...channelPostForm, delete_at: event.target.value })} />
                  </label>
                  <label className="check-card" style={{ gridColumn: "span 1" }}>
                    <input type="checkbox" checked={Boolean(channelPostForm.repeat_daily)} onChange={(event) => setChannelPostForm({ ...channelPostForm, repeat_daily: event.target.checked })} />
                    <div>
                      <strong>Lặp lại mỗi ngày</strong>
                      <div className="muted">Sau khi xóa sẽ tự dời sang ngày kế tiếp.</div>
                    </div>
                  </label>
                  <label className="check-card" style={{ gridColumn: "span 1" }}>
                    <input type="checkbox" checked={Boolean(channelPostForm.sync_bot_schedule)} onChange={(event) => setChannelPostForm({ ...channelPostForm, sync_bot_schedule: event.target.checked })} />
                    <div>
                      <strong>Liên kết giờ bot hoạt động</strong>
                      <div className="muted">Trong khung giờ này bot tự online, ngoài khung giờ bot vào bảo trì.</div>
                    </div>
                  </label>
                  <label className="field wide">
                    <span>Ghi chú</span>
                    <input value={channelPostForm.notes} onChange={(event) => setChannelPostForm({ ...channelPostForm, notes: event.target.value })} placeholder="Ghi chú nội bộ nếu cần" />
                  </label>
                </div>
                <div className="channel-preview">
                  <div><Eye size={16} /> <strong>Preview nhanh</strong></div>
                  <pre>{channelPostForm.image_ref ? `[Ảnh] ${channelPostForm.image_ref}\n\n` : ""}{channelPostForm.content || "Nội dung bài đăng sẽ hiển thị ở đây."}</pre>
                  <small>Nút: {channelPostForm.buttons_text ? channelPostForm.buttons_text.split(/\n+/).filter(Boolean).length : 0} hàng • Ảnh: {channelPostForm.image_ref ? "Có" : "Không"} • Đăng: {channelPostForm.scheduled_at || "gửi ngay"} • Xóa: {channelPostForm.delete_at || "không tự xóa"} • {channelPostForm.repeat_daily ? "Lặp ngày" : "Không lặp"} • {channelPostForm.sync_bot_schedule ? "Gắn giờ bot" : "Không gắn giờ bot"}</small>
                </div>
                {channelEvents.length ? (
                  <div className="channel-events">
                    <strong>Nhật ký bài đăng</strong>
                    {channelEvents.slice(0, 5).map((event) => (
                      <div key={event.id}><span>{dateText(event.created_at)}</span><b>{event.event_type}</b><em>{event.message || "-"}</em></div>
                    ))}
                  </div>
                ) : null}
              </div>
              <div className="modal-actions">
                <button className="btn secondary" onClick={() => setChannelPostModalOpen(false)}>Đóng</button>
                <button className="btn secondary" onClick={() => saveChannelPost("draft")} disabled={saving.startsWith("channel-post")}><Save size={16} /> {channelPostForm.id ? "Lưu thay đổi" : "Lưu nháp"}</button>
                <button className="btn secondary" onClick={() => saveChannelPost("schedule")} disabled={saving.startsWith("channel-post") || !channelPostForm.scheduled_at}><CalendarClock size={16} /> Lên lịch</button>
                <button className="btn" onClick={() => saveChannelPost("send_now")} disabled={saving.startsWith("channel-post")}>{saving.startsWith("channel-post") ? <Loader2 size={16} className="spin" /> : <Send size={16} />} Đăng ngay</button>
              </div>
            </section>
          </div>
        ) : null}

        {renewalSettingsOpen ? (
          <SettingsConfigModal title="Cài đặt gia hạn" subtitle="Bật/tắt nhắc gia hạn, báo hết hạn và nội dung tin nhắn liên quan đến hạn thành viên." fields={RENEWAL_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} onClose={() => setRenewalSettingsOpen(false)} />
        ) : null}

        {supportSettingsOpen ? (
          <SettingsConfigModal title="Cài đặt group hỗ trợ" subtitle="Quản lý link join support, bật/tắt mute khi hết hạn và số ngày giữ mute trước khi kick." fields={SUPPORT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} onClose={() => setSupportSettingsOpen(false)} />
        ) : null}

        {securitySettingsOpen ? (
          <SettingsConfigModal title="Bảo mật bot và coupon" subtitle="Chặn seller, ẩn menu nhập mã và chống dò coupon. Mặc định khách chỉ cần nhắn mã bắt đầu bằng HANGCU_." fields={SECURITY_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} onClose={() => setSecuritySettingsOpen(false)} />
        ) : null}

        {systemSettingsOpen ? (
          <SettingsConfigModal title="Cài đặt hệ thống" subtitle="Các chu kỳ worker, cleanup và retention đang chạy trên backend Render." fields={SYSTEM_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} onClose={() => setSystemSettingsOpen(false)} />
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
                  <small>Với gói tự nhập, nên chứa đúng tên group đang cấu hình trong Nhóm & giá.</small>
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

function ConfigEditor({ title, subtitle, fields, values, setValues, onSave }: { title: string; subtitle: string; fields: ConfigField[]; values: Record<string, string>; setValues: (values: Record<string, string>) => void; onSave: (fields: ConfigField[], values: Record<string, string>) => Promise<boolean> }) {
  const [editingField, setEditingField] = useState<ConfigField | null>(null);
  const [draftValue, setDraftValue] = useState("");
  const [savingField, setSavingField] = useState(false);

  function openField(field: ConfigField) {
    setEditingField(field);
    setDraftValue(values[field.key] || "");
  }

  async function saveField() {
    if (!editingField) return;
    setSavingField(true);
    const nextValues = { ...values, [editingField.key]: draftValue };
    setValues(nextValues);
    try {
      const saved = await onSave([editingField], nextValues);
      if (saved) {
        setEditingField(null);
      } else {
        setValues(values);
      }
    } finally {
      setSavingField(false);
    }
  }

  return (
    <section className="panel">
      <PanelHead title={title} subtitle={`${subtitle} Bấm vào từng mục để chỉnh sửa và lưu riêng.`} />
      <div className="config-list">
        {fields.map((field) => (
          <button className="config-row" key={field.key} onClick={() => openField(field)}>
            <div className="config-row-copy">
              <strong>{field.label}</strong>
              <span>{field.help}</span>
            </div>
            <div className={values[field.key] ? "config-value" : "config-value empty"}>
              {field.kind === "select"
                ? field.options?.find((item) => item.value === (values[field.key] || field.placeholder))?.label || values[field.key] || field.placeholder
                : values[field.key] || "Chưa thiết lập"}
            </div>
            <Pencil size={17} />
          </button>
        ))}
      </div>
      {editingField ? (
        <div className="modal-backdrop config-modal-backdrop" role="dialog" aria-modal="true">
          <section className="modal-panel config-edit-modal">
            <PanelHead
              title={editingField.label}
              subtitle={editingField.help}
              action={<button className="icon-danger" onClick={() => setEditingField(null)} title="Đóng"><XCircle size={18} /></button>}
            />
            <div className="modal-content">
              <label className="field">
                <span>Giá trị</span>
                {editingField.kind === "textarea" ? (
                  <textarea autoFocus value={draftValue} onChange={(event) => setDraftValue(event.target.value)} placeholder={editingField.placeholder} />
                ) : editingField.kind === "select" ? (
                  <select autoFocus value={draftValue || editingField.placeholder} onChange={(event) => setDraftValue(event.target.value)}>
                    {(editingField.options || []).map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
                  </select>
                ) : (
                  <input autoFocus value={draftValue} onChange={(event) => setDraftValue(event.target.value)} placeholder={editingField.placeholder} />
                )}
                <small>Key kỹ thuật: {editingField.key}</small>
              </label>
            </div>
            <div className="modal-actions">
              <button className="btn secondary" onClick={() => setEditingField(null)}>Huỷ</button>
              <button className="btn" onClick={saveField} disabled={savingField}>
                {savingField ? <Loader2 size={16} className="spin" /> : <Save size={16} />} Lưu thay đổi
              </button>
            </div>
          </section>
        </div>
      ) : null}
    </section>
  );
}

function SettingsConfigModal({ title, subtitle, fields, values, setValues, onSave, onClose }: { title: string; subtitle: string; fields: ConfigField[]; values: Record<string, string>; setValues: (values: Record<string, string>) => void; onSave: (fields: ConfigField[], values: Record<string, string>) => Promise<boolean>; onClose: () => void }) {
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <section className="modal-panel wide-modal settings-config-modal">
        <ConfigEditor title={title} subtitle={subtitle} fields={fields} values={values} setValues={setValues} onSave={onSave} />
        <div className="modal-actions">
          <button className="btn secondary" onClick={onClose}>Đóng</button>
        </div>
      </section>
    </div>
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
              <td>{orderMoney(order)}</td>
              <td>{orderCouponCode(order) ? <><strong>{orderCouponCode(order)}</strong><div className="muted">{Number(order.amount || 0) === 0 ? "Kích hoạt miễn phí" : `-${order.coupon_discount_percent || 0}% / ${orderMoney(order, order.coupon_discount_amount || 0)}`}</div></> : "-"}</td>
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
