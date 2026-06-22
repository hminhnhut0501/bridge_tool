"use client";
/* eslint-disable react-hooks/exhaustive-deps, @typescript-eslint/no-unused-vars */

import {
  Activity,
  BadgePercent,
  BadgeDollarSign,
  BarChart3,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  Eye,
  FileText,
  Gift,
  CreditCard,
  Coins,
  Loader2,
  Megaphone,
  Pencil,
  Plus,
  RefreshCw,
  Download,
  Save,
  Send,
  Settings,
  ShieldCheck,
  ShoppingCart,
  Ticket,
  Trash2,
  Users,
  TrendingUp,
  XCircle,
} from "lucide-react";
import {
  AppBar,
  Box,
  Button,
  ButtonBase,
  Alert,
  Checkbox,
  Chip,
  Card,
  CardContent,
  Drawer,
  FormControl,
  FormControlLabel,
  InputLabel,
  IconButton,
  MenuItem,
  Tooltip,
  Select,
  Stack,
  Tab,
  Tabs,
  Toolbar,
  Typography,
  TextField,
  Grid,
} from "@mui/material";
import { Fragment, type ReactNode, useCallback, useEffect, useMemo, useState } from "react";
import * as XLSX from "xlsx";
import {
  channelPostStatusClass,
  channelPostStatusLabel,
  dateMinusDaysText,
  dateText,
  dateTextShort,
  dateTimePreviewText,
  dateTimeInputValue,
  daysUntil,
  activityEventDetailLabel,
  activityEventLabel,
  auditStatusLabel,
  groupDebugText,
  groupDisplayLabel,
  isoDayKey,
  describeActivityEvent,
  displayText,
  formatRevenueCurrency,
  groupNamesForOrder,
  hiddenCodeSeed,
  hiddenRequirementLabel,
  hiddenScopeLabel,
  hiddenSlug,
  hiddenValidityText,
  inferOrderCurrency,
  inferOrderProvider,
  isLifetimeText,
  isOrderActive,
  isTodayDate,
  isWithinPeriod,
  kickAuditReason,
  kickAuditStatusClass,
  money,
  normalizeRevenueCurrency,
  orderCouponCode,
  orderExpireValue,
  orderPlanKind,
  orderMoney,
  payloadText,
  providerRevenueFormat,
  statusClass,
  logEntryTypeLabel,
  orderStatusLabel,
  tooltipLabel,
  supportEventLabel,
  uniqueValues,
} from "./dashboard-helpers";
import { dayKey, getConfigValue, groupConfigKeys, groupOrders, hasAnyGroupConfig, isGroupConfigured, orderStats, type GroupMode } from "./dashboard-business";
import { MuiDialogShell, OrdersTable as MuiOrdersTable, Pagination as MuiPagination, PanelHead, SimpleTable as MuiSimpleTable, statusChipSx } from "./dashboard-components";
import { Metric } from "./metric-card";
import { TrendChart as MuiTrendChart } from "./dashboard-components";
import type { OrderPeriod } from "./dashboard-types";
import { AnalyticsSection, OrdersSection } from "./dashboard-sections";
import { CustomersSection } from "./customers-section";
import { CampaignsSection } from "./campaigns-section";
import { ChannelPostsSection } from "./channel-posts-section";
import { AppSection, AppToolbar } from "./dashboard-components";
import {
  ActivityEvent,
  BroadcastCampaign,
  BroadcastRecipient,
  type BotScheduleStatus,
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
  deleteOrder,
  deleteConfig,
  deleteBlacklist,
  deleteActivationCode,
  deleteCoupon,
  deleteHiddenCode,
  deleteHiddenGroup,
  deleteMenuPage,
  deleteSaleRule,
  getConfig,
  getActivityEvents,
  getBlacklist,
  getBotScheduleStatus,
  getCampaignRecipients,
  getCampaigns,
  getChannelPostEvents,
  getChannelPosts,
  getActivationCodes,
  getCoupons,
  getHiddenCodes,
  getHiddenGroups,
  getHiddenRedemptions,
  getKickAudit,
  getVipGroupAudit,
  getMenuPages,
  getOrders,
  getSaleRules,
  getSupportEvents,
  getUsers,
  getWebhookInfo,
  kickAuditMember,
  pauseCampaign,
  previewCampaign,
  regenerateActivationCode,
  resetWebhook,
  startCampaign,
  updateChannelPost,
  updateConfigs,
  updateMenuPage,
  updateOrder,
  updateOrderStatus,
  updateActivationCode,
  upsertBlacklist,
  upsertHiddenCode,
  upsertHiddenGroup,
  type HiddenRedemption,
  type ActivationCode,
  upsertSaleRule,
  type HiddenCode,
  type HiddenGroup,
  type VipGroupAuditRow,
  type SupportGroupCheck,
} from "@/lib/api";

const DEMO_NOW = new Date("2026-06-19T12:00:00+07:00").getTime();
function demoDate(daysOffset: number, hour = 12, minute = 0) {
  return new Date(DEMO_NOW + daysOffset * 86400000 + (hour - 12) * 3600000 + minute * 60000).toISOString();
}

const DEMO_ORDERS: Order[] = [
  {
    order_id: "178200012345",
    telegram_user_id: "1713655938",
    full_name: "Hoàng",
    plan_name: "VIP 30 Ngày - Hạng Cửu Black",
    amount: 48500,
    status: "PAID",
    paid_at: demoDate(-12, 9, 30),
    expire_at: demoDate(18, 9, 30),
    sale_id: "SUMMER30",
    coupon_code: "SUNNY15",
    coupon_discount_percent: 15,
    coupon_discount_amount: 8500,
    payment_provider: "PAYOS",
    payment_currency: "VND",
    source_type: "manual",
    created_at: demoDate(-12, 9, 10),
    expired_notice_at: null,
    last_reminder_date: null,
  },
  {
    order_id: "178200045678",
    telegram_user_id: "1713655938",
    full_name: "Hoàng",
    plan_name: "SVIP+ Trọn Đời (Full 4 Nhóm)",
    amount: 299000,
    status: "PAID",
    paid_at: demoDate(-45, 15, 0),
    expire_at: demoDate(3650, 15, 0),
    sale_id: "LIFE01",
    coupon_code: null,
    payment_provider: "MANUAL",
    payment_currency: "VND",
    source_type: "manual",
    created_at: demoDate(-45, 14, 25),
    expired_notice_at: null,
    last_reminder_date: null,
  },
  {
    order_id: "178200078901",
    telegram_user_id: "1713655938",
    full_name: "Hoàng",
    plan_name: "VIP 30 Ngày - Hạng Cửu Boy",
    amount: 59000,
    status: "EXPIRED",
    paid_at: demoDate(-96, 11, 10),
    expire_at: demoDate(-2, 11, 10),
    sale_id: null,
    coupon_code: null,
    payment_provider: "PAYOS",
    payment_currency: "VND",
    source_type: "manual",
    created_at: demoDate(-96, 11, 2),
    expired_notice_at: demoDate(-1, 8, 0),
    last_reminder_date: demoDate(-2, 8, 0),
  },
  {
    order_id: "178200092222",
    telegram_user_id: "6845057360",
    full_name: "Jeon Jk",
    plan_name: "SVIP+ 30 Ngày (Full 4 Nhóm)",
    amount: 97000,
    status: "PAID",
    paid_at: demoDate(-6, 8, 45),
    expire_at: demoDate(24, 8, 45),
    sale_id: "WELCOME10",
    coupon_code: "WELCOME10",
    coupon_discount_percent: 10,
    coupon_discount_amount: 9700,
    payment_provider: "PAYPAL",
    payment_currency: "USD",
    source_type: "manual",
    created_at: demoDate(-6, 8, 12),
    expired_notice_at: null,
    last_reminder_date: null,
  },
  {
    order_id: "178200099999",
    telegram_user_id: "6845057360",
    full_name: "Jeon Jk",
    plan_name: "VIP 30 Ngày - Hạng Cửu Prime",
    amount: 59000,
    status: "PENDING",
    paid_at: null,
    expire_at: null,
    sale_id: "PENDING01",
    coupon_code: null,
    payment_provider: "NOWPAYMENTS",
    payment_currency: "USDT",
    source_type: "manual",
    created_at: demoDate(-1, 20, 0),
    expired_notice_at: null,
    last_reminder_date: null,
  },
  {
    order_id: "178200100001",
    telegram_user_id: "2085787503",
    full_name: "Taco",
    plan_name: "VIP 30 Ngày - Hạng Cửu Black",
    amount: 49000,
    status: "CANCELLED",
    paid_at: null,
    expire_at: null,
    sale_id: null,
    coupon_code: null,
    payment_provider: "PAYOS",
    payment_currency: "VND",
    source_type: "manual",
    created_at: demoDate(-3, 10, 15),
    expired_notice_at: null,
    last_reminder_date: null,
  },
];

const DEMO_USERS: UserRow[] = [
  {
    telegram_user_id: "1713655938",
    full_name: "Hoàng",
    status: "ACTIVE",
    plan_name: "SVIP+ Trọn Đời (Full 4 Nhóm)",
    expire_at: demoDate(3650, 15, 0),
    created_at: demoDate(-45, 14, 25),
  },
  {
    telegram_user_id: "6845057360",
    full_name: "Jeon Jk",
    status: "ACTIVE",
    plan_name: "SVIP+ 30 Ngày (Full 4 Nhóm)",
    expire_at: demoDate(24, 8, 45),
    created_at: demoDate(-6, 8, 12),
  },
  {
    telegram_user_id: "2085787503",
    full_name: "Taco",
    status: "EXPIRED",
    plan_name: "VIP 30 Ngày - Hạng Cửu Black",
    expire_at: demoDate(-2, 11, 10),
    created_at: demoDate(-3, 10, 15),
  },
];

const popupFieldSx = {
  "& .MuiOutlinedInput-root": {
    borderRadius: 2,
    backgroundColor: "#ffffff",
  },
  "& .MuiInputBase-input": {
    fontWeight: 500,
  },
  "& .MuiFormHelperText-root": {
    mx: 0,
  },
} as const;

const popupSelectSx = {
  borderRadius: 2,
  backgroundColor: "#ffffff",
} as const;

const customerPopupTabSx = {
  minHeight: 0,
  p: 0.5,
  borderRadius: 1,
  border: 1,
  borderColor: "divider",
  bgcolor: "background.paper",
  overflow: "hidden",
  boxShadow: "0 4px 10px rgba(15, 23, 42, 0.03)",
  "& .MuiTabs-flexContainer": { gap: 0.5 },
  "& .MuiTab-root": {
    alignItems: "center",
    justifyContent: "flex-start",
    minHeight: 38,
    px: 1.35,
    py: 0.75,
    borderRadius: 1,
    textTransform: "none",
    fontWeight: 650,
    letterSpacing: "-0.01em",
    border: "1px solid transparent",
    bgcolor: "transparent",
    boxShadow: "none",
  },
  "& .MuiTab-root:hover": {
    bgcolor: "rgba(37, 99, 235, 0.05)",
    borderColor: "rgba(37, 99, 235, 0.10)",
  },
  "& .MuiTab-root.Mui-selected": {
    bgcolor: "primary.main",
    color: "common.white",
    borderColor: "rgba(37,99,235,0.18)",
    boxShadow: "0 6px 14px rgba(37, 99, 235, 0.12)",
  },
  "& .MuiTabs-indicator": { display: "none" },
} as const;

const customerPopupInputSx = {
  ...popupFieldSx,
  "& .MuiOutlinedInput-root": {
    ...popupFieldSx["& .MuiOutlinedInput-root"],
    bgcolor: "#ffffff",
    boxShadow: "0 8px 18px rgba(15, 23, 42, 0.03)",
  },
  "& .MuiInputLabel-root": {
    fontWeight: 700,
  },
} as const;

const customerInnerCardSx = {
  p: 1.5,
  border: 1,
  borderColor: "divider",
  borderRadius: 2,
  bgcolor: "background.paper",
  boxShadow: "0 8px 18px rgba(15, 23, 42, 0.04)",
} as const;

const customerOrderStateChipSx = (status: string, active: boolean, expiringSoon: boolean) => {
  const normalized = String(status || "").toUpperCase();
  if (normalized === "PAID") {
    return {
      ...statusChipSx("success"),
      bgcolor: "#ecfdf3",
      color: "#047857",
      borderColor: "#86efac",
      boxShadow: "0 12px 24px rgba(16, 185, 129, 0.16)",
    };
  }
  if (normalized === "PENDING") {
    return {
      ...statusChipSx("warning"),
      bgcolor: "#fffbeb",
      color: "#b45309",
      borderColor: "#fcd34d",
      boxShadow: "0 12px 24px rgba(245, 158, 11, 0.12)",
    };
  }
  if (!active || !expiringSoon || normalized === "EXPIRED" || normalized === "CANCELLED" || normalized === "DISABLED") {
    return {
      bgcolor: "action.disabledBackground",
      color: "text.disabled",
      borderColor: "divider",
      fontWeight: 700,
      letterSpacing: "-0.01em",
      opacity: 0.9,
      "& .MuiChip-label": { px: 1 },
    };
  }
  return { ...statusChipSx("muted") };
};

const sectionCardSx = {
  overflow: "hidden",
  position: "relative",
  borderRadius: 2,
  boxShadow: "0 18px 40px rgba(15, 23, 42, 0.06)",
  "&::before": {
    content: '""',
    position: "absolute",
    inset: 0,
    height: 2,
    background: "linear-gradient(90deg, #2563eb, #06b6d4, #10b981, #8b5cf6)",
  },
} as const;

type Tab = "overview" | "analytics" | "setup" | "orders" | "customers" | "activityLog" | "campaigns" | "channelPosts" | "renewals" | "supportGroup" | "content" | "botVi" | "botEn" | "botTools" | "hiddenMessages" | "menuBuilder" | "coupons" | "activationCodes" | "security" | "sales" | "system";
type ContentSubTab = "bot" | "payment" | "currency" | "admin";
type BotUiSubTab = "plans" | "buttons" | "messages" | "saleContent" | "groups";
type BotToolsSubTab = "commandsVi" | "commandsEn" | "alertsVi" | "alertsEn";
type MenuLanguage = "vi" | "en";
type CustomerStatusFilter = "all" | "active" | "expiring" | "lifetime" | "expired" | "paid" | "coupon";
type CustomerOrderTab = "all" | "active" | "expiring" | "lifetime" | "paid" | "expired";
type CustomerDetailTab = "orders" | "groups" | "timeline";
type CustomerTimelineSubTab = "all" | "joinLeft" | "role" | "restricted" | "kickMute" | "orders";
type CustomerTraceEvent = {
  key: string;
  type: string;
  group: string;
  order: string;
  createdAt: string;
  detail: string;
};
type LogDirectionFilter = "all" | "user" | "bot";
type RenewalSubTab = "soon" | "today" | "reminded" | "expiredNotice" | "kicked" | "audit" | "retained" | "vipOut";
type SupportSubTab = "all" | "joined" | "left" | "muted" | "kicked";
type CouponTab = "unsent" | "sent" | "used" | "expired";
type ActivationCodeTab = "ALL" | "PENDING" | "USED" | "DISABLED" | "EXPIRED";
type ActivationCodeSort = "newest" | "expiring" | "recently_used";
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

const TAB_VALUES: Tab[] = ["overview", "analytics", "setup", "orders", "customers", "activityLog", "campaigns", "channelPosts", "renewals", "supportGroup", "content", "botVi", "botEn", "botTools", "hiddenMessages", "menuBuilder", "coupons", "activationCodes", "security", "sales", "system"];
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
    key: "PAYOS_VIETQR_TEMPLATE",
    label: "Template ảnh VietQR",
    placeholder: "qr_only",
    help: "qr_only chỉ hiện QR; compact/compact2/print sẽ hiện thêm thông tin. Khuyến nghị qr_only nếu muốn ẩn tối đa.",
    kind: "select",
    options: [
      { label: "Chỉ QR", value: "qr_only" },
      { label: "Compact", value: "compact" },
      { label: "Compact2", value: "compact2" },
      { label: "Print", value: "print" },
    ],
  },
  {
    key: "PAYOS_VIETQR_SHOW_ACCOUNT_NAME",
    label: "Hiện tên chủ TK trong QR",
    placeholder: "OFF",
    help: "Bật để thêm accountName lên ảnh QR. Tắt để ẩn tối đa thông tin trên ảnh.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
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
    key: "BINANCE_PAY_SIEUTHICODE_ENABLED",
    label: "Bật Binance Pay Sieuthicode",
    placeholder: "OFF",
    help: "Cổng quét lịch sử Binance Pay từ Sieuthicode để đối soát đơn VNĐ song song với PayOS.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "NEW_CUSTOMER_AUTO_PAYMENT_ENABLED",
    label: "Cho khách mới thanh toán tự động",
    placeholder: "OFF",
    help: "Mặc định tắt để chặn khách mua lần đầu đi qua QR/crypto tự động.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "MSG_NEW_CUSTOMER_MANUAL_ONLY",
    label: "Thông báo khách mới",
    placeholder: "Đây là đơn mua đầu tiên của bạn, nên hệ thống đang xử lý thủ công để tránh thanh toán tự động cho khách mới. Vui lòng nhắn admin để được hỗ trợ.",
    help: "Tin nhắn bot trả về khi user chưa từng có đơn PAID và đang bị chặn auto payment.",
    kind: "textarea",
  },
  {
    key: "RETURNING_CUSTOMER_AUTO_PAYMENT_ENABLED",
    label: "Cho khách cũ thanh toán tự động",
    placeholder: "ON",
    help: "Chỉ áp dụng cho user đã từng có ít nhất một đơn PAID trước đó.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "MSG_RETURNING_CUSTOMER_AUTO_DISABLED",
    label: "Thông báo khách cũ",
    placeholder: "Tài khoản của bạn đã từng mua VIP, nhưng thanh toán tự động hiện đang tắt. Vui lòng nhắn admin để được xử lý thủ công.",
    help: "Tin nhắn bot trả về khi user đã từng mua VIP nhưng auto payment cho khách cũ đang tắt.",
    kind: "textarea",
  },
  {
    key: "PAYMENT_PROVIDERS_VI",
    label: "Các cổng cho tiếng Việt",
    placeholder: "PAYOS,PAYPAL,TRON_USDT,BINANCE_PAY",
    help: "Có thể dùng PAYOS,PAYPAL,TRON_USDT,BINANCE_PAY. PayPal/USDT dùng bảng giá USD riêng.",
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
    key: "BINANCE_PAY_SIEUTHICODE_TOKEN",
    label: "Token Binance Pay Sieuthicode",
    placeholder: "TOKEN...",
    help: "Token do Sieuthicode cấp để truy vấn lịch sử giao dịch Binance Pay.",
  },
  {
    key: "BINANCE_PAY_SIEUTHICODE_APPROVAL_URL",
    label: "URL mở Binance Pay",
    placeholder: "https://pay.binance.com",
    help: "URL mở cổng Binance Pay hoặc trang hướng dẫn thanh toán. Có thể để trống nếu không cần nút mở ngoài.",
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

const ORDER_FIELDS: ConfigField[] = [
  {
    key: "MANUAL_ORDER_INFO_TEMPLATE",
    label: "Khối thông tin đơn",
    placeholder: "🧾 Đơn hàng: {order_id}\\n👤 Khách hàng: {full_name} - ID: {telegram_user_id}\\n📦 Gói: {plan_name}\\n⏳ Hạn dùng: {expire_at}",
    help: "Dùng trong cả 2 tin. Biến: {order_id}, {telegram_user_id}, {full_name}, {plan_name}, {expire_at}.",
    kind: "textarea",
  },
  {
    key: "MANUAL_ORDER_MESSAGE_TEMPLATE",
    label: "Tin copy gửi khách",
    placeholder: "{success_text}\\n\\n{order_text}\\n\\n{bot_link_title}\\n{activation_url}\\n\\n{bot_link_subtitle}",
    help: "Tin hiển thị ở CP admin để copy gửi khách. Biến: {success_text}, {order_text}, {bot_link_title}, {activation_url}, {bot_link_subtitle}.",
    kind: "textarea",
  },
  { key: "MANUAL_ORDER_LINK_TITLE", label: "Tiêu đề link bot", placeholder: "🔗 Link kích hoạt", help: "Biến: không cần placeholder. Đây là tiêu đề trước URL bot." },
  { key: "MANUAL_ORDER_LINK_SUBTITLE", label: "Mô tả link bot", placeholder: "Nhấn vào link bên dưới để mở bot và nhận link nhóm riêng.", help: "Biến: không cần placeholder. Dòng mô tả ngay dưới link bot.", kind: "textarea" },
  { key: "MANUAL_ORDER_LINK_TEMPLATE", label: "Deep link bot", placeholder: "t.me/hangcuprivebot?start={code}", help: "Biến: {code}.", },
  { key: "MANUAL_ORDER_LINK_BUTTON_LABEL", label: "Nút copy link", placeholder: "Copy link bot", help: "Biến: không cần placeholder. Text nút admin copy." },
  { key: "MANUAL_ORDER_LINK_SUCCESS_TEXT", label: "Tin bot báo hợp lệ", placeholder: "✅ Đơn của bạn đã được xác minh.", help: "Biến: không cần placeholder. Chỉ dùng khi bot xác minh thành công.", kind: "textarea" },
  { key: "MANUAL_ORDER_LINK_PROCESSING_TEXT", label: "Tin bot đang xử lý", placeholder: "⏳ Bot đang xác minh đơn và tạo link nhóm...", help: "Biến: không cần placeholder. Bot trả ngay khi khách bấm link.", kind: "textarea" },
  { key: "MANUAL_ORDER_LINK_INVALID_TEXT", label: "Tin mã không hợp lệ", placeholder: "❌ Mã kích hoạt không hợp lệ hoặc đã bị vô hiệu hoá.", help: "Biến: không cần placeholder." },
  { key: "MANUAL_ORDER_LINK_USED_TEXT", label: "Tin mã đã dùng", placeholder: "ℹ️ Mã này đã được sử dụng. Nếu cần, admin hãy tạo lại link mới.", help: "Biến: không cần placeholder." },
  { key: "MANUAL_ORDER_LINK_WRONG_USER_TEXT", label: "Tin sai Telegram ID", placeholder: "❌ Mã này không dành cho tài khoản Telegram hiện tại.", help: "Biến: không cần placeholder." },
  { key: "MANUAL_ORDER_LINK_EXPIRED_TEXT", label: "Tin mã hết hạn", placeholder: "⏰ Mã kích hoạt đã hết hạn. Vui lòng liên hệ admin.", help: "Biến: không cần placeholder." },
  { key: "MANUAL_ORDER_LINK_FAIL_TEXT", label: "Tin tạo link thất bại", placeholder: "❌ Bot chưa tạo được link nhóm. Vui lòng thử lại sau.", help: "Biến: không cần placeholder." },
  { key: "MANUAL_ORDER_DELIVERY_TEMPLATE", label: "Tin bot trả khi xác minh xong", placeholder: "{success_text}\\n\\n{order_text}\\n\\n{links_text}\\n\\n{support_text}", help: "Biến: {success_text}, {order_text}, {links_text}, {support_text}. Đây là tin bot gửi cho khách.", kind: "textarea" },
  { key: "MANUAL_ORDER_SUPPORT_TEMPLATE", label: "Khối support trong bot", placeholder: "💬 {support_group_name}:\\n{support_link}", help: "Biến: {support_group_name}, {support_link}. Chỉ hiển thị ở bot.", kind: "textarea" },
  { key: "MANUAL_ORDER_SUPPORT_ERROR_TEMPLATE", label: "Khối lỗi support", placeholder: "💬 {support_group_name}: Không tạo được link hỗ trợ ({support_error})", help: "Biến: {support_group_name}, {support_error}. Chỉ hiển thị ở bot.", kind: "textarea" },
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
    key: "MSG_HIDDEN_VALID_TITLE",
    label: "Hidden hợp lệ - tiêu đề",
    placeholder: "✅ Mã hidden hợp lệ",
    help: "Tiêu đề hiển thị khi hidden code hợp lệ.",
  },
  {
    key: "MSG_HIDDEN_VALID_BODY",
    label: "Hidden hợp lệ - nội dung",
    placeholder: "Chọn gói bên dưới để mua:",
    help: "Dòng mô tả hiển thị khi hidden code hợp lệ.",
  },
  {
    key: "MSG_HIDDEN_GROUP_TEMPLATE",
    label: "Hidden group item",
    placeholder: "• <b>{name}</b>\\n  {description}",
    help: "Mẫu hiển thị từng hidden group trong catalog. Dùng {name}, {description}.",
    kind: "textarea",
  },
  {
    key: "BTN_HIDDEN_BUY_TEMPLATE",
    label: "Nút mua hidden",
    placeholder: "Mua {duration_label} - {name} - {price}",
    help: "Mẫu text nút mua hidden group. Dùng {duration_label}, {name}, {price}, {days}, {group_id}.",
  },
  {
    key: "MSG_HIDDEN_NOT_FOUND",
    label: "Hidden không tồn tại",
    placeholder: "Mã hidden không tồn tại.",
    help: "Tin hiển thị khi user nhập mã sai.",
  },
  {
    key: "MSG_HIDDEN_INACTIVE",
    label: "Hidden đang tắt",
    placeholder: "Mã hidden này đang tắt.",
    help: "Tin hiển thị khi code bị tắt.",
  },
  {
    key: "MSG_HIDDEN_NOT_STARTED",
    label: "Hidden chưa mở",
    placeholder: "Mã hidden này chưa đến thời gian mở.",
    help: "Tin hiển thị khi valid_from chưa tới.",
  },
  {
    key: "MSG_HIDDEN_EXPIRED",
    label: "Hidden hết hạn",
    placeholder: "Mã hidden này đã hết hạn.",
    help: "Tin hiển thị khi valid_until đã qua.",
  },
  {
    key: "MSG_HIDDEN_LIMIT_REACHED",
    label: "Hidden hết lượt",
    placeholder: "Mã hidden này đã hết lượt dùng.",
    help: "Tin hiển thị khi mã đã dùng đủ max_uses.",
  },
  {
    key: "MSG_HIDDEN_NO_GROUPS",
    label: "Hidden không có group",
    placeholder: "Mã hidden hợp lệ nhưng hiện chưa có hidden group nào đang bật.",
    help: "Tin hiển thị khi code hợp lệ nhưng không còn group active.",
  },
  {
    key: "MSG_HIDDEN_REQUIREMENT_SVIP_ACTIVE",
    label: "Hidden cần SVIP active",
    placeholder: "Bạn cần có gói SVIP còn hạn để mở mã này.",
    help: "Tin hiển thị khi rule yêu cầu SVIP active.",
  },
  {
    key: "MSG_HIDDEN_REQUIREMENT_SVIP_LIFETIME",
    label: "Hidden cần SVIP lifetime",
    placeholder: "Bạn cần có gói SVIP trọn đời để mở mã này.",
    help: "Tin hiển thị khi rule yêu cầu SVIP lifetime.",
  },
  {
    key: "MSG_HIDDEN_REQUIREMENT_PLAN_TOKEN_ACTIVE",
    label: "Hidden cần plan token active",
    placeholder: "Bạn cần có gói {plan_token} còn hạn để mở mã này.",
    help: "Tin hiển thị khi rule yêu cầu plan token active.",
  },
  {
    key: "MSG_HIDDEN_REQUIREMENT_PLAN_TOKEN_LIFETIME",
    label: "Hidden cần plan token lifetime",
    placeholder: "Bạn cần có gói {plan_token} trọn đời để mở mã này.",
    help: "Tin hiển thị khi rule yêu cầu plan token lifetime.",
  },
  {
    key: "MSG_HIDDEN_REQUIREMENT_GENERIC",
    label: "Hidden không đủ điều kiện",
    placeholder: "Tài khoản của bạn chưa đủ điều kiện để mở mã này.",
    help: "Fallback nếu rule không khớp riêng.",
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

const HIDDEN_MESSAGE_FIELDS = MESSAGE_FIELDS.filter((field) => field.key.startsWith("MSG_HIDDEN_"));
const VISIBLE_MESSAGE_FIELDS = MESSAGE_FIELDS.filter((field) => !field.key.startsWith("MSG_HIDDEN_"));

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
  expiry_mode: "days",
  duration_days: "30",
  expire_at: "",
  coupon_code: "",
  payment_currency: "VND",
  payment_provider: "MANUAL",
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

function ordersMoney(orders: Order[], field: "amount" | "coupon_discount_amount" = "amount") {
  const totals = orders.reduce((sum, order) => {
    const currency = normalizeRevenueCurrency(inferOrderCurrency(order));
    sum[currency] = (sum[currency] || 0) + Number(order[field] || 0);
    return sum;
  }, {} as Record<string, number>);
  const parts = Object.entries(totals).map(([currency, total]) => formatRevenueCurrency(currency, total));
  return parts.length ? parts.join(" + ") : money(0);
}

function ordersAverageMoney(orders: Order[]) {
  const paid = orders.filter((order) => order.status === "PAID");
  const groups = groupRevenueByCurrency(paid);
  const parts = Object.entries(groups).map(([currency, items]) => formatRevenueCurrency(currency, items.reduce((sum, order) => sum + Number(order.amount || 0), 0) / items.length));
  return parts.join(" + ") || money(0);
}
function groupRevenueByCurrency(orders: Order[]) {
  return orders.reduce((sum, order) => {
    const currency = normalizeRevenueCurrency(inferOrderCurrency(order));
    if (!sum[currency]) sum[currency] = [];
    sum[currency].push(order);
    return sum;
  }, {} as Record<string, Order[]>);
}

function providerLabel(value: string | null | undefined) {
  const provider = String(value || "").toUpperCase();
  const labels: Record<string, string> = {
    MANUAL: "Thủ công",
    PAYOS: "PayOS",
    PAYPAL: "PayPal",
    NOWPAYMENTS: "NOWPayments",
    TRON_USDT: "USDT TRC20",
    BINANCE_PAY: "Binance Pay",
    UNKNOWN: "Chưa rõ",
  };
  return labels[provider] || (provider ? provider : "Chưa rõ");
}

function currencyLabel(value: string | null | undefined) {
  const currency = normalizeRevenueCurrency(value);
  const labels: Record<string, string> = {
    VND: "VNĐ",
    USD: "USD",
    CRYPTO: "Crypto",
  };
  return labels[currency] || currency;
}

function renderLimitedTags(items: string[], prefix: string, limit = 4) {
  const visible = items.slice(0, limit);
  const rest = items.length - visible.length;
  return (
    <>
      {visible.map((item) => <span key={`${prefix}-${item}`}>{item}</span>)}
      {rest > 0 ? <span>+{rest}</span> : null}
    </>
  );
}

function datetimeLocalToIso(value: string) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date.toISOString();
}
function hiddenRequirementNeedsValue(value: string | null | undefined) {
  return ["PLAN_TOKEN_ACTIVE", "PLAN_TOKEN_LIFETIME"].includes(String(value || "").toUpperCase());
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
function datePlusDaysText(value: string | null | undefined, days: number) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  date.setDate(date.getDate() + days);
  return dateText(date.toISOString());
}

function normalizeChatId(value: string | number | null | undefined) {
  const raw = String(value ?? "").trim();
  if (!raw) return "";
  return raw.endsWith(".0") ? raw.slice(0, -2) : raw;
}

export default function Home() {
  const isDevPreview = process.env.NODE_ENV !== "production";
  const [secret, setSecret] = useState("");
  const [savedSecret, setSavedSecret] = useState("");
  const [tab, setTab] = useState<Tab>("overview");
  const [contentTab, setContentTab] = useState<ContentSubTab>("bot");
  const [botViTab, setBotViTab] = useState<BotUiSubTab>("plans");
  const [botEnTab, setBotEnTab] = useState<BotUiSubTab>("plans");
  const [botToolsTab, setBotToolsTab] = useState<BotToolsSubTab>("commandsVi");
  const [menuLanguage, setMenuLanguage] = useState<MenuLanguage>("vi");
  const [overviewTrendRange, setOverviewTrendRange] = useState<"month" | "year">("month");
  const [orders, setOrders] = useState<Order[]>(isDevPreview ? DEMO_ORDERS : []);
  const [users, setUsers] = useState<UserRow[]>(isDevPreview ? DEMO_USERS : []);
  const [config, setConfig] = useState<ConfigRow[]>([]);
  const [menuPages, setMenuPages] = useState<MenuPage[]>([]);
  const [saleRules, setSaleRules] = useState<SaleRule[]>([]);
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [activationCodes, setActivationCodes] = useState<ActivationCode[]>([]);
  const [hiddenGroups, setHiddenGroups] = useState<HiddenGroup[]>([]);
  const [hiddenCodes, setHiddenCodes] = useState<HiddenCode[]>([]);
  const [hiddenRedemptions, setHiddenRedemptions] = useState<HiddenRedemption[]>([]);
  const [blacklist, setBlacklist] = useState<BlacklistEntry[]>([]);
  const [supportEvents, setSupportEvents] = useState<SupportEvent[]>([]);
  const [kickAudit, setKickAudit] = useState<KickAuditRow[]>([]);
  const [vipGroupAudit, setVipGroupAudit] = useState<VipGroupAuditRow[]>([]);
  const [activityEvents, setActivityEvents] = useState<ActivityEvent[]>([]);
  const [campaigns, setCampaigns] = useState<BroadcastCampaign[]>([]);
  const [campaignRecipients, setCampaignRecipients] = useState<BroadcastRecipient[]>([]);
  const [campaignPreview, setCampaignPreview] = useState<CampaignPreview | null>(null);
  const [channelPosts, setChannelPosts] = useState<ChannelPost[]>([]);
  const [channelEvents, setChannelEvents] = useState<ChannelPostEvent[]>([]);
  const [supportCheck, setSupportCheck] = useState<SupportGroupCheck | null>(null);
  const [webhook, setWebhook] = useState<WebhookInfo | null>(null);
  const [botScheduleStatusApi, setBotScheduleStatusApi] = useState<BotScheduleStatus | null>(null);
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
  const [customerDetailTab, setCustomerDetailTab] = useState<CustomerDetailTab>("orders");
  const [customerTimelineSubTab, setCustomerTimelineSubTab] = useState<CustomerTimelineSubTab>("all");
  const [customerOrderTab, setCustomerOrderTab] = useState<CustomerOrderTab>("all");
  const [customerRenewModalOpen, setCustomerRenewModalOpen] = useState(false);
  const [customerRenewForm, setCustomerRenewForm] = useState({
    order_id: "",
    plan_name: "",
    amount: "",
    duration_days: "30",
    payment_currency: "VND",
    payment_provider: "MANUAL",
  });
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
  const [securitySettingsOpen, setSecuritySettingsOpen] = useState(false);
  const [systemSettingsOpen, setSystemSettingsOpen] = useState(false);
  const [orderSettingsOpen, setOrderSettingsOpen] = useState(false);
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
  const [activationCodeTab, setActivationCodeTab] = useState<ActivationCodeTab>("ALL");
  const [activationCodeQuery, setActivationCodeQuery] = useState("");
  const [activationCodeSort, setActivationCodeSort] = useState<ActivationCodeSort>("newest");
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
  const [demoDataInjected, setDemoDataInjected] = useState(false);

  useEffect(() => {
    const isLocalDevHost = ["localhost", "127.0.0.1", "::1"].includes(window.location.hostname);
    const stored = window.localStorage.getItem("prive_admin_secret") || "";
    const envSecret = process.env.NEXT_PUBLIC_ADMIN_SECRET || "";
    const initialSecret = envSecret || stored || (isLocalDevHost ? "dev-admin-secret" : "");
    setSavedSecret(initialSecret);
    setSecret(initialSecret);
    if (isLocalDevHost && initialSecret) {
      window.localStorage.setItem("prive_admin_secret", initialSecret);
    }
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
    [...ADMIN_FIELDS, ...SUPPORT_FIELDS, ...ORDER_FIELDS, ...CURRENCY_FIELDS, ...BOT_FIELDS, ...PAYMENT_FIELDS, ...RENEWAL_FIELDS, ...SECURITY_FIELDS, ...SYSTEM_FIELDS, ...COMMAND_FIELDS, ...COMMAND_EN_FIELDS, ...MESSAGE_FIELDS, ...MESSAGE_EN_FIELDS, ...BUTTON_FIELDS, ...BUTTON_EN_FIELDS, ...ALERT_FIELDS, ...ALERT_EN_FIELDS, ...SALE_CONTENT_FIELDS, ...SALE_CONTENT_EN_FIELDS, ...PLAN_FIELDS, ...PLAN_EN_FIELDS].forEach((field) => {
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
    if (process.env.NODE_ENV === "production") return;
    if (loading) return;
    if (demoDataInjected) return;
    if (orders.length || users.length) return;
    if (savedSecret) return;
    setOrders(DEMO_ORDERS);
    setUsers(DEMO_USERS);
    setDemoDataInjected(true);
  }, [savedSecret, loading, orders.length, users.length, demoDataInjected]);

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
    const botScheduleRes = await getBotScheduleStatus(activeSecret);
    setBotScheduleStatusApi(botScheduleRes.data);
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
      notes: post.notes || "",
    });
    setChannelPostModalOpen(true);
  }

  async function saveChannelPost(mode: "draft" | "send_now" | "schedule") {
    await runAction(`channel-post-${mode}`, async () => {
      const content = String(channelPostForm.content || "");
      const payload: Record<string, unknown> = {
        target_chat_id: channelPostForm.target_chat_id.trim(),
        title: channelPostForm.title,
        image_ref: channelPostForm.image_ref,
        content,
        buttons_text: channelPostForm.buttons_text,
        parse_mode: channelPostForm.parse_mode,
        disable_web_page_preview: channelPostForm.disable_web_page_preview,
        notes: channelPostForm.notes,
        repeat_daily: Boolean(channelPostForm.repeat_daily),
        status: mode === "schedule" ? "scheduled" : mode === "send_now" ? "queued" : channelPostForm.id ? channelPostForm.status || "draft" : "draft",
        created_by: "admin_cp",
      };
      const scheduledAt = datetimeLocalToIso(channelPostForm.scheduled_at);
      const deleteAt = datetimeLocalToIso(channelPostForm.delete_at);
      if (mode === "schedule" || !channelPostForm.id) {
        payload.scheduled_at = scheduledAt;
      } else if (scheduledAt) {
        payload.scheduled_at = scheduledAt;
      }
      if (deleteAt) {
        payload.delete_at = deleteAt;
      } else if (!channelPostForm.id) {
        payload.delete_at = null;
      }
      if (!payload.target_chat_id || !content.trim()) {
        throw new Error("Cần nhập channel/group nhận bài và nội dung bài đăng.");
      }
      if (mode === "schedule" && !payload.scheduled_at) {
        throw new Error("Cần chọn giờ đăng hợp lệ.");
      }
      if (payload.repeat_daily && (!payload.scheduled_at || !payload.delete_at)) {
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
      const needsActivationCodes = !light && shouldLoad("activationCodes");
      const needsHidden = !light && shouldLoad("setup", "coupons");
      const needsBlacklist = !light && shouldLoad("security");
      const needsSupportEvents = !light && shouldLoad("activityLog", "renewals", "supportGroup");
      const needsKickAudit = !light && shouldLoad("renewals");
      const needsVipGroupAudit = !light && shouldLoad("renewals");
      const needsActivityEvents = !light && shouldLoad("activityLog", "analytics");
      const needsCampaigns = shouldLoad("campaigns");
      const needsChannelPosts = shouldLoad("channelPosts");
      const needsWebhook = !light;
      const needsBotScheduleStatus = !light;

      addTask(needsOrders, () => getOrders(activeSecret), setOrders);
      addTask(needsUsers, () => getUsers(activeSecret), setUsers);
      addTask(needsConfig, () => getConfig(activeSecret), setConfig);
      addTask(needsMenu, () => getMenuPages(activeSecret), setMenuPages);
      addTask(needsSales, () => getSaleRules(activeSecret), setSaleRules);
      addTask(needsCoupons, () => getCoupons(activeSecret), setCoupons);
      addTask(needsActivationCodes, () => getActivationCodes(activeSecret), setActivationCodes);
      addTask(needsHidden, () => getHiddenGroups(activeSecret), setHiddenGroups);
      addTask(needsHidden, () => getHiddenCodes(activeSecret), setHiddenCodes);
      addTask(needsHidden, () => getHiddenRedemptions(activeSecret, 200), setHiddenRedemptions);
      addTask(needsBlacklist, () => getBlacklist(activeSecret), setBlacklist);
      addTask(needsSupportEvents, () => getSupportEvents(activeSecret), setSupportEvents);
      addTask(needsKickAudit, () => getKickAudit(activeSecret), setKickAudit);
      addTask(needsVipGroupAudit, () => getVipGroupAudit(activeSecret), setVipGroupAudit);
      addTask(needsActivityEvents, () => getActivityEvents(activeSecret), setActivityEvents);
      addTask(needsCampaigns, () => getCampaigns(activeSecret), setCampaigns);
      addTask(needsChannelPosts, () => getChannelPosts(activeSecret), setChannelPosts);
      addTask(needsWebhook, () => getWebhookInfo(activeSecret), setWebhook);
      addTask(needsBotScheduleStatus, () => getBotScheduleStatus(activeSecret), setBotScheduleStatusApi);

      await Promise.all(tasks);
      if (
        process.env.NODE_ENV !== "production" &&
        !demoDataInjected &&
        !orders.length &&
        !users.length &&
        typeof window !== "undefined" &&
        ["localhost", "127.0.0.1"].includes(window.location.hostname)
      ) {
        setOrders(DEMO_ORDERS);
        setUsers(DEMO_USERS);
        setWebhook((current) =>
          current?.url
            ? current
            : {
                url: "http://127.0.0.1:8000/webhook",
                has_custom_certificate: false,
                pending_update_count: 0,
                allowed_updates: ["message", "callback_query", "chat_member"],
              }
        );
        setDemoDataInjected(true);
      }
      if (resetPages) {
        setOrderPage(1);
        setCouponPage(1);
      }
    } catch (err) {
      if (process.env.NODE_ENV !== "production" && !demoDataInjected) {
        setOrders(DEMO_ORDERS);
        setUsers(DEMO_USERS);
        setDemoDataInjected(true);
      }
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

  async function refreshKickAudit(live = false) {
    await runAction(live ? "kick-audit-live" : "kick-audit-refresh", async () => {
      const res = await getKickAudit(savedSecret, live);
      setKickAudit(res.data);
      if (live) showNotice("ok", "Đã kiểm tra live trạng thái kick trong group.");
    });
  }

  async function refreshVipGroupAudit(live = false) {
    await runAction(live ? "vip-audit-live" : "vip-audit-refresh", async () => {
      const res = await getVipGroupAudit(savedSecret, live);
      setVipGroupAudit(res.data);
      if (live) showNotice("ok", "Đã kiểm tra live trạng thái VIP group.");
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

  function escapeCsvCell(value: unknown) {
    const text = String(value ?? "");
    if (/[",\n\r;]/.test(text)) return `"${text.replace(/"/g, '""')}"`;
    return text;
  }

  function downloadCsv(filename: string, rows: Record<string, unknown>[]) {
    if (!rows.length) {
      showNotice("error", "Không có dòng nào để export.");
      return;
    }
    const headers = Object.keys(rows[0]);
    const csv = [headers.join(","), ...rows.map((row) => headers.map((key) => escapeCsvCell(row[key])).join(","))].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${filename}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function exportOrdersCsv() {
    const rows = filteredOrders.map((item) => ({
      "Mã đơn": item.order_id || "-",
      "Telegram ID": item.telegram_user_id || "-",
      "Khách": item.full_name || "-",
      "Gói": item.plan_name || "-",
      "Số tiền": item.amount || 0,
      "Trạng thái": orderStatusLabel(item.status),
      "Thanh toán lúc": item.paid_at ? dateText(item.paid_at) : "-",
      "Hết hạn": item.expire_at ? dateText(item.expire_at) : "-",
      "Sale ID": item.sale_id || "-",
      "Coupon": item.coupon_code || "-",
      "Cổng": item.payment_provider || "-",
    }));
    downloadCsv(`orders-${new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19)}`, rows);
  }

  function exportCustomersCsv() {
    const rows = filteredCustomers.map((item) => ({
      "Telegram ID": item.id,
      "Khách": item.name || "-",
      "Trạng thái": item.statusLabel,
      "PAID": item.paidOrders.length,
      "Active": item.activeOrders.length,
      "Hạn gần nhất": item.latestExpire ? dateTextShort(item.latestExpire) : "-",
      "Doanh thu": ordersMoney(item.paidOrders),
      "Gói": item.plans.join(" | ") || "-",
      "Group": item.groups.join(" | ") || "-",
      "Coupon": item.coupons.join(" | ") || "-",
      "Đơn": item.orders.length,
      "Trọn đời": item.hasLifetimeOrder ? "Có" : "Không",
    }));
    downloadCsv(`customers-${new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19)}`, rows);
  }

  function exportVipGroupAudit(format: "csv" | "xlsx") {
    const rows: Record<string, string>[] = vipGroupAudit
      .filter((item) => item.status !== "ACTIVE_RETAINED")
      .map((item) => ({
        "Khách": item.customer_name || "-",
        "Telegram ID": item.telegram_user_id || "-",
        "Đơn": item.order_id || "-",
        "Gói": item.plan_name || "-",
        "Hết hạn": item.expire_at ? dateText(item.expire_at) : "-",
        "Group": item.group_name || "-",
        "Group ID": item.group_id || "-",
        "Trạng thái": auditStatusLabel(item.status_label || item.status),
        "Live": item.live_checked ? `${item.live_status || "-"}${item.live_present === true ? " / còn trong group" : item.live_present === false ? " / đã rời" : ""}` : "Chưa kiểm tra live",
        "Lỗi gần nhất": item.latest_error || "-",
      }));
    if (!rows.length) {
      showNotice("error", "Không có dòng nào để export.");
      return;
    }
    const stamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
    const filename = `vip-group-out-${stamp}`;
    if (format === "csv") {
      const headers = Object.keys(rows[0]);
      const csv = [headers.join(","), ...rows.map((row) => headers.map((key) => escapeCsvCell(row[key])).join(","))].join("\n");
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${filename}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      return;
    }
    const worksheet = XLSX.utils.json_to_sheet(rows);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "VIP Out");
    XLSX.writeFile(workbook, `${filename}.xlsx`);
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

  const activationCodesByStatus = useMemo(() => {
    const buckets: Record<string, ActivationCode[]> = { ALL: [], PENDING: [], USED: [], DISABLED: [], EXPIRED: [] };
    const now = Date.now();
    for (const item of activationCodes) {
      const status = String(item.activation_status || "PENDING").toUpperCase();
      const expired = item.expire_at ? new Date(item.expire_at).getTime() < now : false;
      buckets.ALL.push(item);
      if (expired && status !== "USED") buckets.EXPIRED.push(item);
      if (status === "USED") buckets.USED.push(item);
      else if (status === "DISABLED") buckets.DISABLED.push(item);
      else buckets.PENDING.push(item);
    }
    return buckets;
  }, [activationCodes]);

  const activationCodeRows = useMemo(() => {
    const rows = [...(activationCodesByStatus[activationCodeTab] || activationCodesByStatus.ALL)];
    const keyword = activationCodeQuery.trim().toLowerCase();
    const filtered = keyword ? rows.filter((item) =>
      [item.code, item.order_id, item.telegram_user_id]
        .some((value) => String(value || "").toLowerCase().includes(keyword))
    ) : rows;
    return filtered.sort((a, b) => {
      if (activationCodeSort === "expiring") {
        const aTime = a.expire_at ? new Date(a.expire_at).getTime() : Number.MAX_SAFE_INTEGER;
        const bTime = b.expire_at ? new Date(b.expire_at).getTime() : Number.MAX_SAFE_INTEGER;
        return aTime - bTime;
      }
      if (activationCodeSort === "recently_used") {
        const aTime = new Date(a.used_at || a.activated_at || 0).getTime();
        const bTime = new Date(b.used_at || b.activated_at || 0).getTime();
        return bTime - aTime;
      }
      return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
    });
  }, [activationCodeQuery, activationCodeSort, activationCodeTab, activationCodesByStatus]);

  async function refreshActivationCode(code: ActivationCode) {
    await runAction(`activation-reset-${code.code}`, async () => {
      await updateActivationCode(savedSecret, code.code, {
        activation_status: "PENDING",
        activated_at: null,
        activated_by_user_id: null,
        used_at: null,
        used_by_user_id: null,
      });
      await loadAll();
    });
  }

  async function disableActivationCode(code: ActivationCode) {
    await runAction(`activation-disable-${code.code}`, async () => {
      await updateActivationCode(savedSecret, code.code, { activation_status: "DISABLED" });
      await loadAll();
    });
  }

  async function copyActivationLink(code: ActivationCode) {
    await navigator.clipboard.writeText(code.activation_url || "");
    showNotice("ok", `Đã copy link kích hoạt ${code.code}.`);
  }

  async function deleteActivationCodeRow(code: ActivationCode) {
    if (!window.confirm(`Xoá mã kích hoạt ${code.code}?`)) return;
    await runAction(`activation-delete-${code.code}`, async () => {
      await deleteActivationCode(savedSecret, code.code);
      await loadAll();
    });
  }

  async function renewActivationCode(code: ActivationCode) {
    await runAction(`activation-regenerate-${code.code}`, async () => {
      await regenerateActivationCode(savedSecret, code.code);
      await loadAll();
    });
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

  function openCustomerRenewModal() {
    if (!selectedCustomer) return;
    const defaultOrder = selectedCustomerRenewTargetOrder || selectedCustomer.paidOrders[0] || null;
    const defaultPlanName = defaultOrder?.plan_name || selectedCustomerRenewPlanOptions[0] || "";
    setCustomerRenewForm({
      order_id: defaultOrder?.order_id || "",
      plan_name: defaultPlanName,
      amount: defaultOrder ? String(defaultOrder.amount || "") : "",
      duration_days: isLifetimeText(defaultPlanName) ? "0" : "30",
      payment_currency: String(defaultOrder?.payment_currency || "VND").toUpperCase(),
      payment_provider: String(defaultOrder?.payment_provider || "MANUAL").toUpperCase(),
    });
    setCustomerRenewModalOpen(true);
  }

  async function saveCustomerRenewal() {
    if (!selectedCustomer) return;
    const planName = customerRenewForm.plan_name.trim();
    const amount = Number(customerRenewForm.amount);
    const days = Number(customerRenewForm.duration_days);
    if (!planName) {
      showNotice("error", "Vui lòng chọn đúng gói.");
      return;
    }
    if (!Number.isFinite(amount) || amount < 0) {
      showNotice("error", "Vui lòng nhập số tiền hợp lệ.");
      return;
    }
    if (!isLifetimeText(planName) && (!Number.isFinite(days) || days <= 0)) {
      showNotice("error", "Vui lòng nhập số ngày gia hạn hợp lệ.");
      return;
    }
    await runAction(`customer-renew-${selectedCustomer.id}`, async () => {
      await createManualOrder(savedSecret, {
        telegram_user_id: selectedCustomer.id,
        full_name: selectedCustomer.name || selectedCustomer.id,
        plan_name: planName,
        amount: String(amount),
        duration_days: isLifetimeText(planName) ? "0" : String(days),
        sale_id: `RENEWAL_${customerRenewForm.order_id || "MANUAL"}`,
        payment_currency: String(customerRenewForm.payment_currency || "VND").toUpperCase(),
        payment_provider: String(customerRenewForm.payment_provider || "MANUAL").toUpperCase(),
      });
      setCustomerRenewModalOpen(false);
      await loadAll();
    });
  }

  async function removeOrder(orderId: string, label = "") {
    const prompt = label ? `Xóa đơn ${orderId} (${label})?` : `Xóa đơn ${orderId}?`;
    if (!window.confirm(prompt)) return;
    if (!window.confirm("Hành động này sẽ xóa bản ghi đơn hàng khỏi hệ thống. Tiếp tục?")) return;
    await runAction(`order-delete-${orderId}`, async () => {
      await deleteOrder(savedSecret, orderId);
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
  const paidOrders = useMemo(() => orders.filter((item) => item.status === "PAID"), [orders]);
  const paidRevenueByCurrency = useMemo(() => groupRevenueByCurrency(paidOrders), [paidOrders]);
  const paidRevenueByProvider = useMemo(() => {
    return paidOrders.reduce((sum, order) => {
      const provider = inferOrderProvider(order);
      sum[provider] = (sum[provider] || 0) + Number(order.amount || 0);
      return sum;
    }, {} as Record<string, number>);
  }, [paidOrders]);
  const hasPayosOrders = useMemo(() => paidOrders.some((item) => inferOrderProvider(item) === "PAYOS"), [paidOrders]);
  const overviewTrendPoints = useMemo(() => {
    const sourceOrders = orders.filter((item) => item.status === "PAID" && isWithinPeriod(item.created_at, overviewTrendRange));
    const groupMap = new Map<string, Order[]>();
    for (const order of sourceOrders) {
      const key = overviewTrendRange === "month" ? new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "2-digit" }).format(new Date(order.created_at || "")) : new Intl.DateTimeFormat("vi-VN", { month: "2-digit", year: "2-digit" }).format(new Date(order.created_at || ""));
      groupMap.set(key, [...(groupMap.get(key) || []), order]);
    }
    return Array.from(groupMap.entries()).map(([label, items]) => ({
      label,
      value: items.reduce((sum, item) => sum + Number(item.amount || 0), 0),
      vip: new Set(items.map((item) => item.telegram_user_id)).size,
    }));
  }, [orders, overviewTrendRange]);
  const overviewVipPoints = useMemo(() => overviewTrendPoints.map((item) => ({ label: item.label, value: item.vip })), [overviewTrendPoints]);

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
  const reminderNoticeDays = useMemo(() => Number(getConfigValue(config, "REMINDER_DAYS", "3")) || 3, [config]);
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
      const activeOrders = paidOrders.filter((item) => isOrderActive(item));
      const latestExpire = paidOrders
        .map((item) => item.expire_at)
        .filter(Boolean)
        .sort((a, b) => new Date(b || "").getTime() - new Date(a || "").getTime())[0] || "";
      const coupons = uniqueValues(customer.orders.map(orderCouponCode));
      const groups = uniqueValues(customer.orders.flatMap(groupNamesForOrder));
      const plans = uniqueValues(customer.orders.map((item) => item.plan_name));
      const revenue = paidOrders.reduce((sum, item) => sum + (item.amount || 0), 0);
      const lastOrderAt = customer.orders.map((item) => item.created_at).sort((a, b) => new Date(b).getTime() - new Date(a).getTime())[0] || "";
      const hasLifetimeSvip = customer.orders.some((item) => item.status === "PAID" && isLifetimeText(item.plan_name) && String(item.plan_name || "").toLowerCase().includes("svip"));
      const hasLifetimeOrder = customer.orders.some((item) => item.status === "PAID" && isLifetimeText(item.plan_name));
      const expiringWithinWindow = customer.orders.some((item) => item.status === "PAID" && !isLifetimeText(item.plan_name) && (() => {
        const days = daysUntil(item.expire_at);
        return days >= 0 && days <= reminderNoticeDays;
      })());
      const hasAnyPaidOrder = paidOrders.length > 0;
      const hasAnyExpiredPaidOrder = paidOrders.some((item) => !isOrderActive(item) && !isLifetimeText(item.plan_name));
      const status = activeOrders.length
        ? "active"
        : expiringWithinWindow
          ? "expiring"
          : hasAnyPaidOrder
            ? "expired"
            : "no_paid";
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
        hasLifetimeSvip,
        hasLifetimeOrder,
        expiringWithinWindow,
        hasAnyPaidOrder,
        hasAnyExpiredPaidOrder,
        status,
        statusLabel: status === "active" ? "Đang còn hạn" : status === "expiring" ? "Sắp hết hạn" : status === "expired" ? "Hết hạn / chờ kick" : "Chưa PAID",
        statusColor: status === "active" ? "success" : status === "expiring" ? "warning" : status === "expired" ? "error" : "default",
      };
    }).sort((a, b) => new Date(b.lastOrderAt || "").getTime() - new Date(a.lastOrderAt || "").getTime());
  }, [orders, reminderNoticeDays]);
  const customerNameById = useMemo(() => new Map(customerSummaries.map((item) => [item.id, item.name] as const)), [customerSummaries]);
  const customerGroupOptions = useMemo(() => uniqueValues(customerSummaries.flatMap((item) => item.groups)).sort(), [customerSummaries]);
  const filteredCustomers = useMemo(() => {
    const q = query.toLowerCase();
    return customerSummaries.filter((customer) => {
      const text = `${customer.id} ${customer.name} ${customer.plans.join(" ")} ${customer.groups.join(" ")} ${customer.coupons.join(" ")}`.toLowerCase();
      if (q && !text.includes(q)) return false;
      if (customerStatus === "active" && !customer.activeOrders.length) return false;
      if (customerStatus === "expiring" && !customer.expiringWithinWindow) return false;
      if (customerStatus === "lifetime" && !customer.hasLifetimeOrder) return false;
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
  const selectedCustomerOrders = useMemo(() => {
    if (!selectedCustomer) return [];
    const score = (order: Order) => {
      const status = String(order.status || "").toUpperCase();
      if (status === "PAID") return 0;
      if (isOrderActive(order)) return 1;
      if (status === "PENDING") return 2;
      if (status === "EXPIRED") return 3;
      if (status === "CANCELLED") return 4;
      return 5;
    };
    return [...selectedCustomer.orders].sort((a, b) => {
      const statusDiff = score(a) - score(b);
      if (statusDiff !== 0) return statusDiff;
      const aExpire = new Date(a.expire_at || 0).getTime();
      const bExpire = new Date(b.expire_at || 0).getTime();
      if (!Number.isNaN(aExpire) && !Number.isNaN(bExpire) && aExpire !== bExpire) return aExpire - bExpire;
      return new Date(b.created_at || "").getTime() - new Date(a.created_at || "").getTime();
    });
  }, [selectedCustomer]);
  const selectedCustomerRenewTargetOrder = useMemo(() => {
    if (!selectedCustomer) return null;
    const candidates = selectedCustomer.activeOrders.length ? selectedCustomer.activeOrders : selectedCustomer.paidOrders;
    return [...candidates].sort((a, b) => {
      const aExpire = new Date(a.expire_at || 0).getTime();
      const bExpire = new Date(b.expire_at || 0).getTime();
      if (!Number.isNaN(aExpire) && !Number.isNaN(bExpire) && aExpire !== bExpire) return aExpire - bExpire;
      return new Date(b.created_at || "").getTime() - new Date(a.created_at || "").getTime();
    })[0] || null;
  }, [selectedCustomer]);
  const selectedCustomerRenewPlanOptions = useMemo(() => {
    if (!selectedCustomer) return [];
    return uniqueValues(selectedCustomer.paidOrders.map((item) => item.plan_name)).sort((a, b) => a.localeCompare(b));
  }, [selectedCustomer]);
  const selectedCustomerActiveGroups = useMemo(() => {
    if (!selectedCustomer) return [];
    return uniqueValues(selectedCustomer.activeOrders.flatMap(groupNamesForOrder)).sort((a, b) => a.localeCompare(b));
  }, [selectedCustomer]);
  const selectedCustomerGroupAuditSummary = useMemo(() => {
    if (!selectedCustomer) return { total: 0, liveChecked: 0, retained: 0, kicked: 0, currentGroups: 0 };
    const customerId = selectedCustomer.id;
    const vipRows = vipGroupAudit.filter((item) => String(item.telegram_user_id || "").trim() === customerId);
    const kickRows = kickAudit.filter((item) => String(item.telegram_user_id || "").trim() === customerId);
    const total = vipRows.length + kickRows.length;
    const liveChecked = [...vipRows, ...kickRows].filter((item) => item.live_checked).length;
    const retained = kickRows.filter((item) => item.status === "ACTIVE_RETAINED").length;
    const kicked = kickRows.filter((item) => item.status !== "ACTIVE_RETAINED").length;
    return {
      total,
      liveChecked,
      retained,
      kicked,
      currentGroups: selectedCustomerActiveGroups.length,
    };
  }, [selectedCustomer, vipGroupAudit, kickAudit, selectedCustomerActiveGroups.length]);
  const selectedCustomerGroupAuditRows = useMemo(() => {
    if (!selectedCustomer) return [];
    const customerId = selectedCustomer.id;
    const vipRows = vipGroupAudit
      .filter((item) => String(item.telegram_user_id || "").trim() === customerId)
      .map((item) => ({
        key: `vip-${item.audit_id}`,
        type: item.status,
        sortKey: new Date(item.latest_kick_at || item.expire_at || 0).getTime(),
        row: [
          <Tooltip key={`vip-${item.audit_id}-status-tip`} title={tooltipLabel(auditStatusLabel(item.status_label || item.status), item.status)} arrow>
            <span key={`vip-${item.audit_id}-status`} className={statusClass(item.status)}>{auditStatusLabel(item.status_label || item.status)}</span>
          </Tooltip>,
          <Tooltip key={`vip-${item.audit_id}-group-tip`} title={groupDebugText(item.group_name, item.group_id)} arrow>
            <Box component="span">
              <strong>{groupDisplayLabel(item.group_name, item.group_id)}</strong>
              <div className="muted">{item.group_id || "-"}</div>
            </Box>
          </Tooltip>,
          <><strong>{item.plan_name || "-"}</strong><div className="muted">{item.order_id || "-"}</div></>,
          item.expire_at ? dateText(item.expire_at) : "-",
          <Tooltip key={`vip-${item.audit_id}-live-tip`} title={item.live_checked ? `Mã live: ${item.live_status || "-"}` : "Chưa kiểm tra live"} arrow>
            <span>{item.live_checked ? `${item.live_status || "-"}${item.live_present === true ? " / còn trong group" : item.live_present === false ? " / đã rời" : ""}` : "Chưa live"}</span>
          </Tooltip>,
          <Tooltip key={`vip-${item.audit_id}-err-tip`} title={item.latest_error || "Không có lỗi"} arrow>
            <span>{item.latest_error || "-"}</span>
          </Tooltip>,
        ],
      }));
    const kickRows = kickAudit
      .filter((item) => String(item.telegram_user_id || "").trim() === customerId)
      .map((item) => ({
        key: `kick-${item.audit_id}`,
        type: item.status,
        sortKey: new Date(item.latest_kick_at || item.expire_at || 0).getTime(),
        row: [
          <Tooltip key={`kick-${item.audit_id}-status-tip`} title={tooltipLabel(auditStatusLabel(item.status_label || item.status), item.status)} arrow>
            <span key={`kick-${item.audit_id}-status`} className={kickAuditStatusClass(item.status)}>{auditStatusLabel(item.status_label || item.status)}</span>
          </Tooltip>,
          <Tooltip key={`kick-${item.audit_id}-group-tip`} title={groupDebugText(item.group_name, item.group_id)} arrow>
            <Box component="span">
              <strong>{groupDisplayLabel(item.group_name, item.group_id)}</strong>
              <div className="muted">{item.group_id || "-"}</div>
            </Box>
          </Tooltip>,
          <><strong>{item.plan_name || "-"}</strong><div className="muted">{item.order_id || "-"}</div></>,
          item.expire_at ? dateText(item.expire_at) : "-",
          <Tooltip key={`kick-${item.audit_id}-live-tip`} title={item.live_checked ? `Mã live: ${item.live_status || "-"}` : "Chưa kiểm tra live"} arrow>
            <span>{item.live_checked ? `${item.live_status || "-"}${item.live_present === true ? " / còn trong group" : item.live_present === false ? " / đã rời" : ""}` : "Chưa live"}</span>
          </Tooltip>,
          <Tooltip key={`kick-${item.audit_id}-reason-tip`} title={kickAuditReason(item)} arrow>
            <span>{kickAuditReason(item)}</span>
          </Tooltip>,
        ],
      }));
    return [...vipRows, ...kickRows]
      .sort((a, b) => (b.sortKey || 0) - (a.sortKey || 0))
      .map((item) => item.row);
  }, [selectedCustomer, vipGroupAudit, kickAudit]);
  const selectedCustomerSupportEvents = useMemo(() => {
    if (!selectedCustomer) return [];
    return supportEvents
      .filter((item) => String(item.telegram_user_id || "").trim() === selectedCustomer.id)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }, [selectedCustomer, supportEvents]);
  const selectedCustomerTimelineRows = useMemo(() => {
    if (!selectedCustomer) return [];
    const customerId = selectedCustomer.id;
    const orderTrace: CustomerTraceEvent[] = selectedCustomer.orders.map((item) => ({
      key: `order-${item.order_id}`,
      type: item.status === "PAID" ? "order_paid" : item.status === "EXPIRED" ? "order_expired" : "order_created",
      group: groupNamesForOrder(item).join(", ") || "-",
      order: item.order_id || "-",
      createdAt: item.paid_at || item.created_at || item.expired_notice_at || "",
      detail: [
        item.plan_name || "",
        item.coupon_code ? `Coupon: ${item.coupon_code}` : "",
        item.expire_at ? `Hạn: ${dateText(item.expire_at)}` : "",
        item.status ? `Trạng thái: ${item.status}` : "",
      ].filter(Boolean).join(" • ") || "-",
    }));
    const supportTrace: CustomerTraceEvent[] = selectedCustomerSupportEvents.map((item) => ({
      key: `support-${item.id}`,
      type: supportEventLabel(item.event_type),
      group: item.chat_title || item.chat_id || "-",
      order: item.order_id || "-",
      createdAt: item.created_at,
      detail: [
        item.plan_name || "",
        item.raw_data?.reason ? String(item.raw_data.reason) : "",
      ].filter(Boolean).join(" • ") || "-",
    }));

    const kickTrace: CustomerTraceEvent[] = kickAudit
      .filter((item) => String(item.telegram_user_id || "").trim() === customerId)
      .map((item) => ({
        key: `kick-${item.audit_id}`,
        type: item.status_label || item.status,
        group: item.group_name || item.group_id || "-",
        order: item.order_id || "-",
        createdAt: item.latest_kick_at || item.expire_at || "",
        detail: kickAuditReason(item),
      }));

    const vipTrace: CustomerTraceEvent[] = vipGroupAudit
      .filter((item) => String(item.telegram_user_id || "").trim() === customerId)
      .map((item) => ({
        key: `vip-${item.audit_id}`,
        type: item.status_label || item.status,
        group: item.group_name || item.group_id || "-",
        order: item.order_id || "-",
        createdAt: item.latest_kick_at || item.expire_at || "",
        detail: item.latest_error || (item.live_checked ? `${item.live_status || "-"}` : "Chưa kiểm tra live") || "-",
      }));

    const rows = [...orderTrace, ...supportTrace, ...kickTrace, ...vipTrace]
      .filter((item) => item.createdAt)
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
      .map((item) => ({
        key: item.key,
        type: item.type,
        row: [
          <Tooltip key={`${item.key}-type-tip`} title={tooltipLabel(supportEventLabel(item.type), item.type)} arrow>
            <span key={`${item.key}-type`} className={statusClass(item.type)}>{supportEventLabel(item.type)}</span>
          </Tooltip>,
          <Tooltip key={`${item.key}-group-tip`} title={item.group} arrow>
            <Box component="span">
              <strong>{item.group}</strong>
              <div className="muted">{item.order}</div>
            </Box>
          </Tooltip>,
          item.order,
          dateText(item.createdAt),
          <Tooltip key={`${item.key}-detail-tip`} title={item.detail} arrow>
            <span>{item.detail}</span>
          </Tooltip>,
        ],
      }));
    if (customerTimelineSubTab === "all") return rows.map((item) => item.row);
    if (customerTimelineSubTab === "joinLeft") return rows.filter((item) => ["vip_joined", "vip_left", "support_joined", "support_left"].includes(item.type)).map((item) => item.row);
    if (customerTimelineSubTab === "role") return rows.filter((item) => ["vip_role_changed"].includes(item.type)).map((item) => item.row);
    if (customerTimelineSubTab === "restricted") return rows.filter((item) => ["vip_restricted_changed", "vip_muted", "vip_unmuted"].includes(item.type)).map((item) => item.row);
    if (customerTimelineSubTab === "kickMute") return rows.filter((item) => ["vip_kicked", "vip_muted", "vip_unmuted", "member_kicked", "member_muted", "member_unmuted"].includes(item.type)).map((item) => item.row);
    if (customerTimelineSubTab === "orders") return rows.filter((item) => ["order_created", "order_paid", "order_expired"].includes(item.type)).map((item) => item.row);
    return rows.map((item) => item.row);
  }, [selectedCustomer, selectedCustomerSupportEvents, kickAudit, vipGroupAudit, customerTimelineSubTab]);
  const selectedCustomerTimelineCounts = useMemo(() => {
    if (!selectedCustomer) return { total: 0, joined: 0, left: 0, muted: 0, kicked: 0 };
    const supportJoined = selectedCustomerSupportEvents.filter((item) => item.event_type === "support_joined").length;
    const supportLeft = selectedCustomerSupportEvents.filter((item) => item.event_type === "support_left").length;
    const supportMuted = selectedCustomerSupportEvents.filter((item) => item.event_type === "member_muted").length;
    const supportKicked = selectedCustomerSupportEvents.filter((item) => item.event_type === "member_kicked").length;
    const orderKicked = kickAudit.filter((item) => String(item.telegram_user_id || "").trim() === selectedCustomer.id && item.status !== "ACTIVE_RETAINED").length;
    return {
      total: selectedCustomerTimelineRows.length,
      joined: supportJoined,
      left: supportLeft,
      muted: supportMuted,
      kicked: supportKicked + orderKicked,
    };
  }, [selectedCustomer, selectedCustomerSupportEvents, selectedCustomerTimelineRows, kickAudit]);
  const paidMemberOrders = useMemo(() => orders.filter((item) => item.status === "PAID" && item.expire_at), [orders]);
  const expiringToday = useMemo(() => paidMemberOrders.filter((item) => daysUntil(item.expire_at) === 0), [paidMemberOrders]);
  const expiringSoon = useMemo(() => {
    return paidMemberOrders.filter((item) => {
      const days = daysUntil(item.expire_at);
      return days >= 0 && days <= reminderNoticeDays;
    });
  }, [paidMemberOrders, reminderNoticeDays]);
  const remindedToday = useMemo(() => paidMemberOrders.filter((item) => item.last_reminder_date && isTodayDate(item.last_reminder_date)), [paidMemberOrders]);
  const supportNameById = useMemo(() => {
    const map = new Map<string, string>();
    for (const item of supportEvents) {
      const id = String(item.telegram_user_id || "").trim();
      const name = displayText(item.full_name) || displayText(item.username);
      if (id && name && !map.has(id)) map.set(id, name);
    }
    return map;
  }, [supportEvents]);
  const supportGroupId = useMemo(() => normalizeChatId(getConfigValue(config, "SUPPORT_GROUP_ID")), [config]);
  const supportGroupEvents = useMemo(() => {
    if (!supportGroupId) return [];
    return supportEvents.filter((item) => normalizeChatId(item.chat_id) === supportGroupId);
  }, [supportEvents, supportGroupId]);
  const supportGroupTodayEvents = useMemo(() => supportGroupEvents.filter((item) => isTodayDate(item.created_at)), [supportGroupEvents]);
  const renewalReminderEvents = useMemo(() => supportEvents.filter((item) => item.event_type === "renewal_reminder_sent"), [supportEvents]);
  const expiredNoticeEvents = useMemo(() => supportEvents.filter((item) => item.event_type === "expired_notice_sent"), [supportEvents]);
  const supportKickedToday = useMemo(() => supportGroupTodayEvents.filter((item) => item.event_type === "member_kicked"), [supportGroupTodayEvents]);
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
  const supportEventRows = useMemo(() => {
    const filtered = supportGroupEvents.filter((item) => {
      if (supportTab === "joined") return item.event_type === "support_joined";
      if (supportTab === "left") return item.event_type === "support_left";
      if (supportTab === "muted") return item.event_type === "member_muted";
      if (supportTab === "kicked") return item.event_type === "member_kicked";
      return true;
    });
    return filtered.map((item) => [
      <Tooltip key={`${item.id}-type-tip`} title={tooltipLabel(supportEventLabel(item.event_type), item.event_type)} arrow>
        <span>{supportEventLabel(item.event_type)}</span>
      </Tooltip>,
      supportCustomerName(item),
      item.telegram_user_id || "-",
      <Tooltip key={`${item.id}-chat-tip`} title={tooltipLabel(groupDisplayLabel(item.chat_title, item.chat_id), item.chat_id)} arrow>
        <span>{groupDisplayLabel(item.chat_title, item.chat_id)}</span>
      </Tooltip>,
      dateText(item.created_at),
      <Tooltip key={`${item.id}-detail-tip`} title={tooltipLabel([
        item.raw_data?.old_status ? `Cũ: ${item.raw_data.old_status}` : "",
        item.raw_data?.new_status ? `Mới: ${item.raw_data.new_status}` : "",
        item.raw_data?.reason ? `Lý do: ${String(item.raw_data.reason)}` : "",
      ].filter(Boolean).join(" • ") || "-", item.event_type)} arrow>
        <span>{[item.raw_data?.old_status, item.raw_data?.new_status].filter(Boolean).join(" → ") || (item.raw_data?.reason ? String(item.raw_data.reason) : "-")}</span>
      </Tooltip>,
    ]);
  }, [supportGroupEvents, supportTab, supportCustomerName]);
  const supportEventHeaders = useMemo(() => ["Loại", "Khách", "Telegram ID", "Group", "Giờ", "Chi tiết"], []);
  const totalSupportPages = Math.max(1, Math.ceil(supportEventRows.length / SUPPORT_PAGE_SIZE));
  const pagedSupportRows = useMemo(() => {
    const safePage = Math.min(supportPage, totalSupportPages);
    const start = (safePage - 1) * SUPPORT_PAGE_SIZE;
    return supportEventRows.slice(start, start + SUPPORT_PAGE_SIZE);
  }, [supportEventRows, supportPage, totalSupportPages]);
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
        <span key="status" className={kickAuditStatusClass(item.status)}>{auditStatusLabel(item.status_label || item.status)}</span>,
        kickAuditReason(item),
        item.live_checked ? `${item.live_status || "-"}${item.live_present === true ? " / còn trong group" : item.live_present === false ? " / đã rời" : ""}` : "Chưa kiểm tra live",
        item.needs_action && item.group_id ? (
          <Button variant="outlined" size="small" color="error" onClick={() => manualKickAudit(item)} disabled={saving === `kick-audit-${item.audit_id}`} startIcon={saving === `kick-audit-${item.audit_id}` ? <Loader2 size={16} className="spin" /> : <XCircle size={16} />}>
            Kick lại
          </Button>
        ) : "-",
      ]),
      retained: kickAudit.filter((item) => item.status === "ACTIVE_RETAINED").map((item) => [
        <Fragment key={`retained-customer-${item.audit_id}`}><strong>{item.customer_name || "-"}</strong><div className="muted">{item.telegram_user_id || "-"}</div></Fragment>,
        <Fragment key={`retained-plan-${item.audit_id}`}><strong>{item.plan_name || "-"}</strong><div className="muted">Đơn {item.order_id || "-"}</div></Fragment>,
        <Fragment key={`retained-group-${item.audit_id}`}><strong>{item.group_name || "-"}</strong><div className="muted">{item.group_id || "-"}</div></Fragment>,
        dateText(item.expire_at),
        <span key={`retained-status-${item.audit_id}`} className={kickAuditStatusClass(item.status)}>{auditStatusLabel(item.status_label || item.status)}</span>,
        <Fragment key={`retained-reason-${item.audit_id}`}><strong>{item.retained_reason || "Còn đơn active khác nên không kick"}</strong><div className="muted">{item.retained_orders?.length ? `Đơn giữ nhóm: ${item.retained_orders.join(", ")}` : "Hệ thống giữ quyền vì user còn membership active khác."}</div></Fragment>,
        item.live_checked ? `${item.live_status || "-"}${item.live_present === true ? " / còn trong group" : item.live_present === false ? " / đã rời" : ""}` : "Chưa kiểm tra live",
      ]),
      vipOut: vipGroupAudit.filter((item) => item.status !== "ACTIVE_RETAINED").map((item) => [
        <Fragment key={`vipout-customer-${item.audit_id}`}><strong>{item.customer_name || "-"}</strong><div className="muted">{item.telegram_user_id || "-"}</div></Fragment>,
        <Fragment key={`vipout-plan-${item.audit_id}`}><strong>{item.plan_name || "-"}</strong><div className="muted">Đơn {item.order_id || "-"}</div></Fragment>,
        <Fragment key={`vipout-group-${item.audit_id}`}><strong>{item.group_name || "-"}</strong><div className="muted">{item.group_id || "-"}</div></Fragment>,
        dateText(item.expire_at),
        <span key={`vipout-status-${item.audit_id}`} className={kickAuditStatusClass(item.status)}>{auditStatusLabel(item.status_label || item.status)}</span>,
        <Fragment key={`vipout-live-${item.audit_id}`}><strong>{item.live_checked ? `${item.live_status || "-"}` : "Chưa live"}</strong><div className="muted">{item.live_present === true ? "Còn trong group" : item.live_present === false ? "Đã rời group" : "Chưa kiểm tra"}</div></Fragment>,
        item.latest_error || "-",
      ]),
    };
    return rows;
  }, [expiringSoon, expiringToday, renewalReminderEvents, expiredNoticeEvents, uniqueKickedEvents, kickAudit, vipGroupAudit, latestReminderByOrder, reminderNoticeDays, saving, renewalCustomerName, manualKickAudit]);
  const renewalHeaders: Record<RenewalSubTab, string[]> = {
    soon: ["Khách", "Telegram ID", "Gói", "Hết hạn lúc", "Còn lại", "Bắt đầu nhắc từ", "Nhắc gần nhất"],
    today: ["Khách", "Telegram ID", "Gói", "Hết hạn lúc", "Trạng thái", "Báo hết hạn lúc"],
    reminded: ["Khách", "Telegram ID", "Gói", "Đơn", "Giờ nhắc", "Hạn dùng"],
    expiredNotice: ["Khách", "Telegram ID", "Gói", "Đơn", "Giờ báo hết hạn", "Hạn dùng"],
    kicked: ["Khách", "Telegram ID", "Gói", "Đơn", "Group", "Giờ kick"],
    audit: ["Khách", "Gói / Đơn", "Group", "Hạn dùng", "Trạng thái", "Kick / lỗi gần nhất", "Live", "Thao tác"],
    retained: ["Khách", "Gói / Đơn", "Group", "Hạn dùng", "Trạng thái", "Lý do giữ quyền", "Live"],
    vipOut: ["Khách", "Gói / Đơn", "Group", "Hạn dùng", "Trạng thái", "Live", "Lỗi"],
  };
  const currentRenewalRows = useMemo(() => renewalRows[renewalTab] || [], [renewalRows, renewalTab]);
  const totalRenewalPages = Math.max(1, Math.ceil(currentRenewalRows.length / RENEWAL_PAGE_SIZE));
  const pagedRenewalRows = useMemo(() => {
    const safePage = Math.min(renewalPage, totalRenewalPages);
    const start = (safePage - 1) * RENEWAL_PAGE_SIZE;
    return currentRenewalRows.slice(start, start + RENEWAL_PAGE_SIZE);
  }, [currentRenewalRows, renewalPage, totalRenewalPages]);
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
        typeLabel: activityEventLabel(payloadText(payload, "event_type") || event.event_name || "event"),
        userId: event.telegram_user_id || payloadText(payload, "user_id"),
        username: payloadText(payload, "username"),
        fullName: payloadText(payload, "full_name"),
        title: activityEventDetailLabel(payloadText(payload, "event_type") || event.event_name || "event", describeActivityEvent(event), payloadText(payload, "callback_data") || payloadText(payload, "command") || payloadText(payload, "chat_type")),
        detail: payloadText(payload, "callback_data") || payloadText(payload, "command") || payloadText(payload, "chat_type"),
        createdAt: event.created_at,
      };
    });
    const botEvents = supportEvents.map((event) => ({
      id: `s-${event.id}`,
      direction: "bot" as const,
      type: event.event_type,
      typeLabel: supportEventLabel(event.event_type),
      userId: event.telegram_user_id || "",
      username: event.username || "",
      fullName: supportCustomerName(event),
      title: supportEventLabel(event.event_type),
      detail: [event.plan_name, event.chat_title, event.order_id].filter(Boolean).join(" • "),
      createdAt: event.created_at,
    }));
    return [...userEvents, ...botEvents].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
  }, [activityEvents, supportEvents, supportCustomerName]);
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
  const botScheduleStatus = botScheduleStatusApi;
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
      expiry_mode: lifetime ? "date" : manualOrderForm.expiry_mode || "days",
      duration_days: lifetime ? lifetimeCouponDays : manualOrderForm.duration_days || "30",
      expire_at: lifetime ? manualOrderForm.expire_at : manualOrderForm.expire_at,
    });
  }

  function manualExpiryPreview() {
    if (manualOrderForm.expiry_mode === "date") {
      return `Sẽ áp dụng: ${dateTimePreviewText(manualOrderForm.expire_at, "Chưa chọn ngày hết hạn")}`;
    }
    return `Sẽ áp dụng: ${manualOrderForm.duration_days || "30"} ngày`;
  }

  async function saveManualOrder() {
    const planName = manualOrderForm.plan_key === "CUSTOM" ? manualOrderForm.plan_name.trim() : manualPlanNameFromKey(manualOrderForm.plan_key);
    const paymentCurrency = String(manualOrderForm.payment_currency || "VND").toUpperCase();
    const paymentProvider = String(manualOrderForm.payment_provider || "MANUAL").toUpperCase();
    const durationDays = manualOrderForm.expiry_mode === "days" ? manualOrderForm.duration_days : "";
    const expireAt = manualOrderForm.expiry_mode === "date" ? manualOrderForm.expire_at : "";
    await runAction("manual-order", async () => {
      const res = await createManualOrder(savedSecret, {
        telegram_user_id: manualOrderForm.telegram_user_id.trim(),
        full_name: manualOrderForm.full_name.trim(),
        plan_name: planName,
        amount: manualOrderForm.amount,
        duration_days: durationDays,
        expire_at: expireAt,
        coupon_code: manualOrderForm.coupon_code.trim(),
        sale_id: "MANUAL",
        payment_currency: paymentCurrency,
        payment_provider: paymentProvider,
      });
      setManualOrderResult(res.data);
      setManualOrderForm({ ...EMPTY_MANUAL_ORDER_FORM, plan_name: manualPlanNameFromKey("FULL_1M"), amount: manualPriceFromKey("FULL_1M") || "0" });
      await loadAll();
    });
  }

  function appliesLabel(value: string | undefined) {
    if (!value || value === "ALL") return "Tất cả gói";
    const labels = value.split(",").filter(Boolean).map((item) => planOptionLabel(item));
    if (labels.length <= 2) return labels.join(", ");
    return `${labels.slice(0, 2).join(", ")} +${labels.length - 2} gói`;
  }

  if (!savedSecret) {
    return (
      <Box component="main" sx={{ minHeight: "100vh", display: "grid", placeItems: "center", px: 2, bgcolor: "background.default" }}>
        <Card variant="outlined" sx={{ width: "100%", maxWidth: 520 }}>
          <CardContent sx={{ display: "grid", gap: 2.5, p: 3 }}>
            <Box>
              <Typography variant="h4" sx={{ fontWeight: 800 }}>Prive Admin</Typography>
              <Typography variant="body2" color="text.secondary">Nhập mật khẩu admin đã đặt trong Render.</Typography>
            </Box>
            <TextField type="password" label="Mật khẩu admin" value={secret} onChange={(event) => setSecret(event.target.value)} placeholder="Dán ADMIN_SECRET tại đây" fullWidth />
            <Button variant="contained" onClick={login} size="large">Đăng nhập</Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar
        position="fixed"
        elevation={0}
        color="default"
        sx={{
          borderBottom: "none",
          boxShadow: "0 1px 0 rgba(15, 23, 42, 0.06)",
          bgcolor: "rgba(255,255,255,0.96)",
          backdropFilter: "blur(14px)",
          zIndex: (theme) => theme.zIndex.drawer + 2,
          left: 0,
          width: "100%",
        }}
      >
        <Toolbar disableGutters sx={{ minHeight: 68, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2, pl: { xs: 2, md: 3 }, pr: 3 }}>
          <Box sx={{ minWidth: 0, display: "flex", alignItems: "center", gap: 1.25 }}>
            <Typography variant="h6" sx={{ fontWeight: 900, letterSpacing: "-0.04em", lineHeight: 1 }}>
              Privé+
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap sx={{ display: { xs: "none", sm: "block" } }}>
              {ui("Dashboard vận hành: nhóm nhận link, đơn hàng, coupon, sale và nội dung bot.", "Operations dashboard for groups, orders, coupons, sales, and bot content.")}
            </Typography>
          </Box>
          <Box sx={{ minWidth: 0, display: "flex", alignItems: "center", gap: 1.25, flexWrap: "nowrap", justifyContent: "flex-end" }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, whiteSpace: "nowrap", px: 1.15, py: 0.7, borderRadius: 999, border: "1px solid rgba(148, 163, 184, 0.16)", bgcolor: "rgba(15,23,42,0.03)", boxShadow: "inset 0 1px 0 rgba(255,255,255,0.76)" }}>
              <Box sx={{ width: 8, height: 8, borderRadius: "50%", bgcolor: webhook?.url ? "#22c55e" : "#ef4444", boxShadow: webhook?.url ? "0 0 0 5px rgba(34,197,94,0.12)" : "0 0 0 5px rgba(239,68,68,0.12)" }} />
              <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 700, lineHeight: 1 }}>
                {webhook?.url ? ui("Webhook đang bật", "Webhook active") : ui("Webhook cần kiểm tra", "Check webhook")}
              </Typography>
            </Box>
            <Button variant="outlined" onClick={() => loadAll()} disabled={loading} startIcon={loading ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}>
              {ui("Tải lại", "Reload")}
            </Button>
          </Box>
        </Toolbar>
      </AppBar>

      <Box sx={{ display: "flex", flexGrow: 1, minHeight: 0 }}>
      <Drawer
        variant="permanent"
        sx={{
          width: 280,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: 280,
            boxSizing: "border-box",
            borderRight: "1px solid",
            borderColor: "divider",
            bgcolor: "#111827",
            color: "#f9fafb",
            top: "68px",
            height: "calc(100vh - 68px)",
          },
        }}
      >
        <Box sx={{ px: 1.5, pt: 0.75, pb: 2, display: "flex", flexDirection: "column", minHeight: 0 }}>
        <Tabs
          orientation="vertical"
          value={tab}
          onChange={(_, next) => selectTab(next)}
          variant="scrollable"
          scrollButtons={false}
          textColor="inherit"
          sx={{
            mt: 1,
            minHeight: 0,
            pr: 0.5,
            overflow: "visible",
            bgcolor: "transparent",
            backgroundColor: "transparent",
            border: 0,
            borderRadius: 0,
            boxShadow: "none",
            p: 0,
            "& .MuiTabs-flexContainer": {
              gap: 0.35,
              alignItems: "stretch",
              width: "100%",
            },
            "& .MuiTab-root": {
              justifyContent: "flex-start",
              minHeight: 40,
              px: 1.4,
              py: 0.82,
              borderRadius: 1.5,
              border: "1px solid rgba(148,163,184,0.08)",
              bgcolor: "rgba(255,255,255,0.03)",
              width: "100%",
              boxSizing: "border-box",
              textTransform: "none",
              fontWeight: 600,
              color: "#94a3b8",
              boxShadow: "none",
              transition: "background-color 160ms ease, border-color 160ms ease, color 160ms ease, box-shadow 160ms ease, transform 160ms ease",
              borderLeft: "3px solid transparent",
              overflow: "hidden",
              "& .MuiTab-iconWrapper": {
                marginRight: 7,
                minWidth: 0,
              },
              "& .MuiTab-iconWrapper > *": {
                display: "block",
              },
              "& .MuiChip-root": {
                bgcolor: "rgba(255,255,255,0.06)",
                color: "#cbd5e1",
                borderColor: "rgba(255,255,255,0.08)",
              },
            },
            "& .MuiTab-root:hover": {
              bgcolor: "rgba(255,255,255,0.06)",
              borderColor: "rgba(96,165,250,0.12)",
              color: "#fff",
            },
            "& .MuiTab-root.Mui-selected": {
              backgroundImage: "linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%)",
              color: "#fff",
              borderColor: "rgba(96,165,250,0.22)",
              boxShadow: "0 8px 18px rgba(37, 99, 235, 0.16)",
              borderLeftColor: "rgba(255,255,255,0.72)",
            },
            "& .MuiTab-root.Mui-selected:hover": {
              backgroundImage: "linear-gradient(135deg, #1d4ed8 0%, #0284c7 100%)",
              borderColor: "rgba(96,165,250,0.5)",
            },
            "& .MuiTabs-indicator": { display: "none" },
          }}
        >
          <Tab value="overview" icon={<Activity size={16} />} iconPosition="start" label={<Box sx={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}><span>{ui("Tổng quan", "Overview")}</span><Chip size="small" label={String(orders.length)} sx={{ height: 22, fontSize: "0.7rem", fontWeight: 800, bgcolor: "rgba(255,255,255,0.08)", color: "#e2e8f0", borderColor: "rgba(255,255,255,0.10)" }} variant="outlined" /></Box>} />
          <Tab value="analytics" icon={<BarChart3 size={16} />} iconPosition="start" label={ui("Thống kê", "Analytics")} />
          <Tab value="setup" icon={<ShieldCheck size={16} />} iconPosition="start" label={ui("Nhóm & giá", "Groups & pricing")} />
          <Tab value="orders" icon={<ShoppingCart size={16} />} iconPosition="start" label={<Box sx={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}><span>{ui("Đơn hàng", "Orders")}</span><Chip size="small" label={String(orders.filter((item) => item.status === "PENDING").length)} sx={{ height: 22, fontSize: "0.7rem", fontWeight: 800, bgcolor: "rgba(255,255,255,0.08)", color: "#e2e8f0", borderColor: "rgba(255,255,255,0.10)" }} variant="outlined" /></Box>} />
          <Tab value="customers" icon={<Users size={16} />} iconPosition="start" label={<Box sx={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}><span>{ui("Khách hàng", "Customers")}</span><Chip size="small" label={String(customerSummaries.length)} sx={{ height: 22, fontSize: "0.7rem", fontWeight: 800, bgcolor: "rgba(255,255,255,0.08)", color: "#e2e8f0", borderColor: "rgba(255,255,255,0.10)" }} variant="outlined" /></Box>} />
          <Tab value="activityLog" icon={<ClipboardList size={16} />} iconPosition="start" label={ui("Nhật ký", "Activity log")} />
          <Tab value="campaigns" icon={<Megaphone size={16} />} iconPosition="start" label={<Box sx={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}><span>Campaign</span><Chip size="small" label={String(campaigns.length)} sx={{ height: 22, fontSize: "0.7rem", fontWeight: 800, bgcolor: "rgba(255,255,255,0.08)", color: "#e2e8f0", borderColor: "rgba(255,255,255,0.10)" }} variant="outlined" /></Box>} />
          <Tab value="channelPosts" icon={<Send size={16} />} iconPosition="start" label={<Box sx={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}><span>Đăng channel</span><Chip size="small" label={String(channelPosts.length)} sx={{ height: 22, fontSize: "0.7rem", fontWeight: 800, bgcolor: "rgba(255,255,255,0.08)", color: "#e2e8f0", borderColor: "rgba(255,255,255,0.10)" }} variant="outlined" /></Box>} />
          <Tab value="renewals" icon={<RefreshCw size={16} />} iconPosition="start" label={ui("Gia hạn", "Renewals")} />
          <Tab value="supportGroup" icon={<ShieldCheck size={16} />} iconPosition="start" label={ui("Group hỗ trợ", "Support group")} />
          <Tab value="content" icon={<Settings size={16} />} iconPosition="start" label={ui("Cấu hình bot", "Bot config")} />
          <Tab value="botVi" icon={<FileText size={16} />} iconPosition="start" label="UI Bot tiếng Việt" />
          <Tab value="botEn" icon={<FileText size={16} />} iconPosition="start" label="UI Bot tiếng Anh" />
          <Tab value="botTools" icon={<ClipboardList size={16} />} iconPosition="start" label="Lệnh & cảnh báo" />
          <Tab value="hiddenMessages" icon={<Ticket size={16} />} iconPosition="start" label={<Box sx={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}><span>Hidden text</span><Chip size="small" label={String(hiddenGroups.length)} sx={{ height: 22, fontSize: "0.7rem", fontWeight: 800, bgcolor: "rgba(255,255,255,0.08)", color: "#e2e8f0", borderColor: "rgba(255,255,255,0.10)" }} variant="outlined" /></Box>} />
          <Tab value="menuBuilder" icon={<FileText size={16} />} iconPosition="start" label="Menu Builder" />
          <Tab value="coupons" icon={<Ticket size={16} />} iconPosition="start" label={<Box sx={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}><span>Coupon</span><Chip size="small" label={String(coupons.length)} sx={{ height: 22, fontSize: "0.7rem", fontWeight: 800, bgcolor: "rgba(255,255,255,0.08)", color: "#e2e8f0", borderColor: "rgba(255,255,255,0.10)" }} variant="outlined" /></Box>} />
          <Tab value="activationCodes" icon={<Ticket size={16} />} iconPosition="start" label={<Box sx={{ width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}><span>Activation code</span><Chip size="small" label={String(activationCodes.length)} sx={{ height: 22, fontSize: "0.7rem", fontWeight: 800, bgcolor: "rgba(255,255,255,0.08)", color: "#e2e8f0", borderColor: "rgba(255,255,255,0.10)" }} variant="outlined" /></Box>} />
          <Tab value="security" icon={<ShieldCheck size={16} />} iconPosition="start" label={ui("Bảo mật", "Security")} />
          <Tab value="sales" icon={<BadgePercent size={16} />} iconPosition="start" label="Sale" />
          <Tab value="system" icon={<Settings size={16} />} iconPosition="start" label={ui("Hệ thống", "System")} />
        </Tabs>
        </Box>
      </Drawer>

      <Box
        component="section"
        sx={{
          flexGrow: 1,
          minWidth: 0,
          px: { xs: 2, md: 3 },
          pt: "68px",
          pb: { xs: 2, md: 2.5 },
          overflowX: "hidden",
        }}
      >

        {notice ? (
          <Alert
            severity={notice.type === "ok" ? "success" : "error"}
            variant="filled"
            sx={{
              position: "fixed",
              top: "50%",
              left: "50%",
              transform: "translate(-50%, -50%)",
              zIndex: 100,
              minWidth: { xs: "min(360px, calc(100vw - 32px))", sm: 420 },
              maxWidth: "min(520px, calc(100vw - 32px))",
              boxShadow: "0 18px 48px rgba(15, 23, 42, 0.24)",
              borderRadius: 4,
              alignItems: "center",
            }}
          >
            {notice.text}
          </Alert>
        ) : null}

        {missingCore.length ? (
          <Alert severity="warning" variant="outlined" sx={{ mb: 2 }}>
            <strong>Cần hoàn tất cấu hình</strong>
            <Box component="span" sx={{ display: "block" }}>{missingCore.join(" • ")}</Box>
          </Alert>
        ) : null}

        {tab === "overview" ? (
          <Stack spacing={2}>
            <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" } }}>
              <Metric label="Doanh thu đã thanh toán" value={ordersMoney(orders.filter((item) => item.status === "PAID"))} tone="vnd" icon={<TrendingUp size={16} />} />
              <Metric label="Đơn đang chờ" value={String(metrics.pending)} tone="usd" icon={<CalendarClock size={16} />} />
              <Metric label="Khách gần đây" value={String(metrics.users)} tone="crypto" icon={<Users size={16} />} />
              <Metric label="Nhóm đang bán" value={String(configuredGroups.length)} tone="payos" icon={<ShieldCheck size={16} />} />
            </Box>
            <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" } }}>
              <Metric label="Doanh thu VNĐ" value={formatRevenueCurrency("VND", (paidRevenueByCurrency.VND || []).reduce((sum, item) => sum + Number(item.amount || 0), 0))} tone="vnd" note="Nguồn chính: PayOS / manual nội địa" icon={<CreditCard size={16} />} />
              <Metric label="Doanh thu USD" value={formatRevenueCurrency("USD", (paidRevenueByCurrency.USD || []).reduce((sum, item) => sum + Number(item.amount || 0), 0))} tone="usd" note="Chỉ cho khách quốc tế" icon={<Send size={16} />} />
              <Metric label="Doanh thu Crypto" value={formatRevenueCurrency("CRYPTO", (paidRevenueByCurrency.CRYPTO || []).reduce((sum, item) => sum + Number(item.amount || 0), 0))} tone="crypto" note="USDT / thanh toán crypto" icon={<Coins size={16} />} />
              <Metric label="Doanh thu PayOS" value={providerRevenueFormat("PAYOS", paidRevenueByProvider.PAYOS || 0)} tone="payos" note={hasPayosOrders ? "Đã có đơn PayOS" : "Chưa có đơn nào gắn PAYOS"} icon={<Gift size={16} />} />
            </Box>
            <Box sx={{ display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" } }}>
              <Metric label="Doanh thu hôm nay" value={ordersMoney(orders.filter((item) => item.status === "PAID" && isWithinPeriod(item.created_at, "today")))} tone="paypal" icon={<CalendarClock size={16} />} />
              <Metric label="Đơn PAID hôm nay" value={String(todayStats.paid)} tone="vnd" icon={<CheckCircle2 size={16} />} />
              <Metric label="Doanh thu tháng này" value={ordersMoney(orders.filter((item) => item.status === "PAID" && isWithinPeriod(item.created_at, "month")))} tone="usd" icon={<BarChart3 size={16} />} />
              <Metric label="Tỉ lệ thanh toán tháng" value={`${monthStats.conversion}%`} tone="crypto" icon={<BadgePercent size={16} />} />
            </Box>
            <Card variant="outlined" sx={sectionCardSx}>
              <PanelHead
                title="Xu hướng vận hành"
                subtitle="Doanh thu và user VIP theo ngày, có thể chuyển sang view theo tháng."
                action={
                  <Stack direction="row" spacing={1}>
                    <Button variant={overviewTrendRange === "month" ? "contained" : "outlined"} size="small" onClick={() => setOverviewTrendRange("month")}>Theo ngày</Button>
                    <Button variant={overviewTrendRange === "year" ? "contained" : "outlined"} size="small" onClick={() => setOverviewTrendRange("year")}>Theo tháng</Button>
                  </Stack>
                }
              />
              <Stack spacing={2} sx={{ p: 2 }}>
                <MuiTrendChart
                  title="Doanh thu tăng giảm"
                  subtitle="Chỉ tính đơn PAID trong kỳ đang xem."
                  rangeLabel={overviewTrendRange === "month" ? "Theo ngày" : "Theo tháng"}
                  points={overviewTrendPoints}
                  valueLabel={`Tổng: ${ordersMoney(orders.filter((item) => item.status === "PAID" && isWithinPeriod(item.created_at, overviewTrendRange)))}`}
                  secondaryLabel={`Mốc: ${overviewTrendPoints.length}`}
                />
                <MuiTrendChart
                  title="User VIP tăng giảm"
                  subtitle="Đếm user Telegram đã có đơn PAID trong từng mốc."
                  rangeLabel={overviewTrendRange === "month" ? "Theo ngày" : "Theo tháng"}
                  points={overviewVipPoints}
                  valueLabel={`Tổng VIP: ${overviewTrendPoints.reduce((sum, item) => sum + item.vip, 0)}`}
                  secondaryLabel={`Mốc: ${overviewVipPoints.length}`}
                />
              </Stack>
            </Card>
            <Card variant="outlined" sx={sectionCardSx}>
              <PanelHead title="Trạng thái vận hành" subtitle="Kiểm tra nhanh các phần cần có trước khi bán." />
              <Box sx={{ p: 2, display: "grid", gap: 2, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))", lg: "repeat(4, minmax(0, 1fr))" } }}>
                <HealthItem ok={Boolean(webhook?.url)} title="Telegram webhook" detail={webhook?.url || "Chưa set webhook"} />
                <HealthItem ok={configuredGroups.length > 0} title="Nhóm nhận link" detail={configuredGroups.length ? `Đã có ${configuredGroups.length} nhóm` : "Vào Nhóm & giá để cấu hình"} />
                <HealthItem ok={metrics.menu > 0} title="Menu bot" detail={`${metrics.menu} trang menu`} />
                <HealthItem ok={metrics.coupons >= 0} title="Coupon" detail={`${metrics.coupons} mã trong hệ thống`} />
              </Box>
            </Card>
            <Card variant="outlined" sx={sectionCardSx}>
              <PanelHead title="Đơn hàng mới nhất" subtitle="10 đơn gần nhất." />
              <Box sx={{ p: 0 }}>
                <MuiOrdersTable orders={orders.slice(0, 10)} onStatusChange={changeOrderStatus} onDeleteOrder={removeOrder} saving={saving} />
              </Box>
            </Card>
          </Stack>
        ) : null}

        {tab === "analytics" ? (
          <AnalyticsSection
            orders={orders}
            yearStats={yearStats}
            monthStats={monthStats}
            paidRevenueByCurrency={paidRevenueByCurrency}
            paidRevenueByProvider={paidRevenueByProvider}
            formatRevenueCurrency={formatRevenueCurrency}
            providerRevenueFormat={providerRevenueFormat}
            isWithinPeriod={isWithinPeriod}
            groupOrders={groupOrders}
            SummaryTable={SummaryTable}
            ordersMoney={ordersMoney}
            ordersAverageMoney={ordersAverageMoney}
          />
        ) : null}

        {tab === "setup" ? (
          <div className="stack">
            <section className="panel">
              <PanelHead
                title="Bảng giá SVIP chung"
                subtitle="Giá SVIP được quản lý tập trung tại đây. Bấm Cài đặt để chỉnh trong popup."
                action={<Button variant="outlined" size="small" onClick={() => setSvipPriceSettingsOpen(true)} startIcon={<Settings size={16} />}>Cài đặt giá SVIP</Button>}
              />
              <div className="system-list">
                <Info label="SVIP 30 ngày VNĐ" value={money(Number(getConfigValue(config, "PRICE_SVIP_30D", "0") || 0))} icon={<BadgeDollarSign size={16} />} />
                <Info label="SVIP trọn đời VNĐ" value={money(Number(getConfigValue(config, "PRICE_SVIP_LIFE", "0") || 0))} icon={<ShieldCheck size={16} />} />
                <Info label="SVIP 30 ngày USD" value={getConfigValue(config, "PRICE_SVIP_30D_USD", "-") || "-"} icon={<CreditCard size={16} />} />
                <Info label="SVIP trọn đời USD" value={getConfigValue(config, "PRICE_SVIP_LIFE_USD", "-") || "-"} icon={<Coins size={16} />} />
              </div>
            </section>
            <section className="panel">
              <PanelHead
                title="Nhóm lẻ & bảng giá"
                subtitle="Bấm một nhóm để sửa trong popup. Không còn form dài nằm sẵn trên trang."
                action={<Button variant="contained" size="small" onClick={openNewGroupModal} startIcon={<Plus size={16} />}>Thêm nhóm mới</Button>}
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
                    {hiddenSetupView === "groups" ? <Button variant="contained" size="small" onClick={openNewHiddenGroupModal} startIcon={<Plus size={16} />}>Thêm Hidden Group</Button> : null}
                    {hiddenSetupView === "codes" ? <Button variant="contained" size="small" onClick={openNewHiddenCodeModal} startIcon={<Plus size={16} />}>Thêm Hidden Code</Button> : null}
                  </div>
                )}
              />
              <div className="status-grid">
                <Metric label="Hidden group" value={String(hiddenGroups.length)} />
                <Metric label="Đang bật" value={String(hiddenGroups.filter((item) => item.is_active).length)} />
                <Metric label="Hidden code" value={String(hiddenCodes.length)} />
                <Metric label="Lượt mở catalog" value={String(hiddenRedemptions.length)} />
              </div>
              <Tabs value={hiddenSetupView} onChange={(_, next) => setHiddenSetupView(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="groups" label="Nhóm ẩn" />
                <Tab value="codes" label="Mã reveal" />
                <Tab value="activity" label="Lịch sử mở mã" />
              </Tabs>
              {hiddenSetupView === "groups" ? (
                <>
                  <div className="hint compact">
                    Mỗi hidden group là một entitlement riêng. ID nên ngắn gọn, ổn định như <code>prime_alpha</code> vì nó đi vào plan token và scheduler.
                  </div>
                  <div className="toolbar hidden-toolbar">
                    <TextField value={hiddenGroupQuery} onChange={(event) => setHiddenGroupQuery(event.target.value)} placeholder="Tìm theo ID, tên nhóm, chat ID..." size="small" fullWidth />
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
                          <Button variant="outlined" size="small" onClick={() => openEditHiddenGroupModal(item)} disabled={saving === `hidden-group-${item.id}`}>Sửa</Button>
                          <Button variant="outlined" color="error" size="small" onClick={() => removeHiddenGroupAction(item.id)} disabled={saving === `hidden-group-delete-${item.id}`}>Xóa</Button>
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
                    <TextField value={hiddenCodeQuery} onChange={(event) => setHiddenCodeQuery(event.target.value)} placeholder="Tìm theo mã, tên, rule, group..." size="small" fullWidth />
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
                          <Button variant="outlined" size="small" onClick={() => copyHiddenCode(item.code)} disabled={saving === `hidden-code-copy-${item.code}`}>Copy mã</Button>
                          <Button variant="outlined" size="small" onClick={() => openEditHiddenCodeModal(item)} disabled={saving === `hidden-code-${item.code}`}>Sửa</Button>
                          <Button variant="outlined" color="error" size="small" onClick={() => removeHiddenCodeAction(item.code)} disabled={saving === `hidden-code-delete-${item.code}`}>Xóa</Button>
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
          <OrdersSection
            filteredOrders={filteredOrders}
            filteredOrderStats={filteredOrderStats}
            exportOrdersCsv={exportOrdersCsv}
            query={query}
            setQuery={setQuery}
            orderStatus={orderStatus}
            setOrderStatus={setOrderStatus}
            orderPeriod={orderPeriod}
            setOrderPeriod={setOrderPeriod}
            orderGroupMode={orderGroupMode}
            setOrderGroupMode={setOrderGroupMode}
            groupedFilteredOrders={groupedFilteredOrders}
            pagedOrders={pagedOrders}
            changeOrderStatus={changeOrderStatus}
            removeOrder={removeOrder}
            saving={saving}
            orderPage={orderPage}
            totalOrderPages={totalOrderPages}
            setOrderPage={setOrderPage}
            SummaryTable={SummaryTable}
            ordersMoney={ordersMoney}
            openOrderSettings={() => setOrderSettingsOpen(true)}
            openManualOrder={() => { setManualOrderResult(null); setManualOrderModalOpen(true); }}
          />
        ) : null}

        {tab === "customers" ? (
          <CustomersSection
            filteredCustomers={filteredCustomers}
            customerSummaries={customerSummaries}
            ordersMoney={ordersMoney}
            exportCustomersCsv={exportCustomersCsv}
            query={query}
            setQuery={setQuery}
            customerStatus={customerStatus}
            setCustomerStatus={setCustomerStatus}
            customerGroup={customerGroup}
            setCustomerGroup={setCustomerGroup}
            customerGroupOptions={customerGroupOptions}
            customerPlanKind={customerPlanKind}
            setCustomerPlanKind={setCustomerPlanKind}
            pagedCustomers={pagedCustomers}
            setSelectedCustomerId={setSelectedCustomerId}
            setCustomerOrderTab={setCustomerOrderTab}
            setCustomerDetailTab={setCustomerDetailTab}
            setCustomerTimelineSubTab={setCustomerTimelineSubTab}
            setCustomerModalOpen={setCustomerModalOpen}
            customerPage={customerPage}
            totalCustomerPages={totalCustomerPages}
            setCustomerPage={setCustomerPage}
          />
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
              <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: { xs: "1fr", md: "minmax(0, 1fr) repeat(3, 220px)" }, p: 2 }}>
                <TextField value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm tên, Telegram ID, event, callback, gói, đơn..." size="small" fullWidth />
                <TextField select value={logDirection} onChange={(event) => setLogDirection(event.target.value as LogDirectionFilter)} size="small" fullWidth>
                  <MenuItem value="all">Tất cả hướng</MenuItem>
                  <MenuItem value="user">User → Bot</MenuItem>
                  <MenuItem value="bot">Bot → User</MenuItem>
                </TextField>
                <TextField select value={logType} onChange={(event) => setLogType(event.target.value)} size="small" fullWidth>
                  <MenuItem value="ALL">Tất cả loại event</MenuItem>
                  {logTypeOptions.map((item) => <MenuItem key={item} value={item}>{logEntryTypeLabel(item)}</MenuItem>)}
                </TextField>
                <TextField select value={logDate} onChange={(event) => setLogDate(event.target.value)} size="small" fullWidth>
                  <MenuItem value="ALL">Tất cả ngày</MenuItem>
                  {logDateOptions.map((item) => <MenuItem key={item} value={item}>{item === "UNKNOWN" ? "Không rõ ngày" : dayKey(item)}</MenuItem>)}
                </TextField>
              </Box>
              <SimpleTable
                headers={["Thời điểm", "Hướng", "Khách", "Loại", "Nội dung", "Chi tiết"]}
                rows={pagedLogEntries.map((item) => [
                  dateText(item.createdAt),
                  item.direction === "user" ? "User → Bot" : "Bot → User",
                  <><strong>{item.fullName || item.username || "-"}</strong><div className="muted">{item.userId || "-"}</div></>,
                  item.typeLabel || logEntryTypeLabel(item.type),
                  item.title,
                  item.detail || "-",
                ])}
              />
              <Pagination page={logPage} totalPages={totalLogPages} totalItems={filteredLogEntries.length} onPage={setLogPage} label="event" />
            </section>
          </div>
        ) : null}

        {tab === "campaigns" ? (
          <CampaignsSection
            campaigns={campaigns}
            campaignPreview={campaignPreview}
            selectedCampaign={selectedCampaign}
            campaignRecipientCounts={campaignRecipientCounts}
            pagedCampaignRecipients={pagedCampaignRecipients}
            campaignRecipients={campaignRecipients}
            totalCampaignRecipientPages={totalCampaignRecipientPages}
            campaignRecipientPage={campaignRecipientPage}
            setCampaignRecipientPage={setCampaignRecipientPage}
            changeCampaignStatus={changeCampaignStatus}
            setSelectedCampaignId={setSelectedCampaignId}
            setCampaignModalOpen={setCampaignModalOpen}
            setCampaignForm={setCampaignForm}
            EMPTY_CAMPAIGN_FORM={EMPTY_CAMPAIGN_FORM}
          />
        ) : null}

        {tab === "channelPosts" ? (
          <ChannelPostsSection
            channelPosts={channelPosts}
            channelPostCounts={channelPostCounts}
            channelPostTab={channelPostTab}
            setChannelPostTab={setChannelPostTab}
            openNewChannelPostModal={openNewChannelPostModal}
            pagedChannelPosts={pagedChannelPosts}
            channelPostPage={channelPostPage}
            totalChannelPostPages={totalChannelPostPages}
            visibleChannelPosts={visibleChannelPosts}
            setChannelPostPage={setChannelPostPage}
            editChannelPost={editChannelPost}
            runChannelPostAction={runChannelPostAction}
            channelPostStatusClass={channelPostStatusClass}
            channelPostStatusLabel={channelPostStatusLabel}
          />
        ) : null}

        {tab === "renewals" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Hết hạn hôm nay" value={String(expiringToday.length)} />
              <Metric label="Sắp hết hạn" value={String(expiringSoon.length)} />
              <Metric label="Đã nhắc hôm nay" value={String(renewalReminderEvents.filter((item) => isTodayDate(item.created_at)).length || remindedToday.length)} />
              <Metric label="Đã kick hôm nay" value={String(uniqueKickedEvents.filter((item) => isTodayDate(item.created_at)).length)} />
              <Metric label="Cần kiểm tra kick" value={String(kickAudit.filter((item) => item.needs_action).length)} />
            </div>
            <section className="panel">
              <PanelHead
                title="Quản lý gia hạn"
                subtitle="Theo dõi hạn dùng, lịch nhắc, báo hết hạn và lịch sử kick theo từng tab để danh sách không bị quá dài."
                action={
                  <div className="panel-actions">
                    <Button variant="outlined" size="small" onClick={() => refreshVipGroupAudit(true)} disabled={saving === "vip-audit-live"} startIcon={saving === "vip-audit-live" ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}>
                      Kiểm tra VIP live
                    </Button>
                    <Button variant="outlined" size="small" onClick={() => exportVipGroupAudit("csv")} disabled={!vipGroupAudit.length} startIcon={<Download size={16} />}>CSV</Button>
                    <Button variant="outlined" size="small" onClick={() => exportVipGroupAudit("xlsx")} disabled={!vipGroupAudit.length} startIcon={<Download size={16} />}>XLSX</Button>
                    <Button variant="outlined" size="small" onClick={() => refreshKickAudit(true)} disabled={saving === "kick-audit-live"} startIcon={saving === "kick-audit-live" ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}>
                      Kiểm tra live
                    </Button>
                    <Button variant="contained" size="small" onClick={() => setRenewalSettingsOpen(true)} startIcon={<Settings size={16} />}>Cài đặt</Button>
                  </div>
                }
              />
              <Tabs value={renewalTab} onChange={(_, next) => { setRenewalTab(next); setRenewalPage(1); }} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="soon" label={`Sắp hết hạn (${expiringSoon.length})`} />
                <Tab value="today" label={`Hết hạn hôm nay (${expiringToday.length})`} />
                <Tab value="reminded" label={`Đã nhắc (${renewalReminderEvents.length})`} />
                <Tab value="expiredNotice" label={`Báo hết hạn (${expiredNoticeEvents.length})`} />
                <Tab value="kicked" label={`Đã kick (${uniqueKickedEvents.length})`} />
                <Tab value="audit" label={`Cần kiểm tra kick (${kickAudit.filter((item) => item.needs_action).length}/${kickAudit.length})`} />
                <Tab value="retained" label={`Còn active khác không kick (${kickAudit.filter((item) => item.status === "ACTIVE_RETAINED").length})`} />
                <Tab value="vipOut" label={`VIP out (${vipGroupAudit.filter((item) => item.status !== "ACTIVE_RETAINED").length})`} />
              </Tabs>
              <SimpleTable headers={renewalHeaders[renewalTab]} rows={pagedRenewalRows} />
              <Pagination page={renewalPage} totalPages={totalRenewalPages} totalItems={currentRenewalRows.length} onPage={setRenewalPage} label="dòng" />
            </section>
          </div>
        ) : null}

        {tab === "supportGroup" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Join hôm nay" value={String(supportGroupTodayEvents.filter((item) => item.event_type === "support_joined").length)} icon={<Plus size={16} />} />
              <Metric label="Rời hôm nay" value={String(supportGroupTodayEvents.filter((item) => item.event_type === "support_left").length)} icon={<TrendingUp size={16} />} />
              <Metric label="Mute hôm nay" value={String(supportGroupTodayEvents.filter((item) => item.event_type === "member_muted").length)} icon={<XCircle size={16} />} />
              <Metric label="Kick hôm nay" value={String(supportKickedToday.length)} icon={<ShieldCheck size={16} />} />
              <Metric label="Sự kiện group hỗ trợ" value={String(supportGroupEvents.length)} icon={<Activity size={16} />} />
              <Metric label="Group hỗ trợ" value={getConfigValue(config, "SUPPORT_GROUP_NAME", "Nhóm hỗ trợ")} icon={<Users size={16} />} />
            </div>
            <section className="panel">
              <PanelHead
                title="Group hỗ trợ"
                subtitle="Chỉ hiển thị sự kiện của group hỗ trợ theo SUPPORT_GROUP_ID. Không trộn dữ liệu VIP."
                action={
                  <div className="panel-actions">
                    <Button variant="contained" size="small" onClick={runSupportGroupCheck} disabled={saving === "support-check"} startIcon={saving === "support-check" ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}>Kiểm tra</Button>
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
              <Tabs value={supportTab} onChange={(_, next) => setSupportTab(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="all" label={`Tất cả (${supportGroupEvents.length})`} />
                <Tab value="joined" label={`Join (${supportGroupEvents.filter((item) => item.event_type === "support_joined").length})`} />
                <Tab value="left" label={`Left (${supportGroupEvents.filter((item) => item.event_type === "support_left").length})`} />
                <Tab value="muted" label={`Đã mute (${supportGroupEvents.filter((item) => item.event_type === "member_muted").length})`} />
                <Tab value="kicked" label={`Đã kick (${supportGroupEvents.filter((item) => item.event_type === "member_kicked").length})`} />
              </Tabs>
              <SimpleTable headers={supportEventHeaders} rows={pagedSupportRows} />
              <Pagination page={supportPage} totalPages={totalSupportPages} totalItems={supportEventRows.length} onPage={setSupportPage} label="sự kiện" />
            </section>
          </div>
        ) : null}

        {tab === "content" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="Cấu hình vận hành Bot" subtitle="Chỉ chứa thiết lập hệ thống. Nội dung khách nhìn thấy, lệnh, cảnh báo và Menu Builder đã được tách thành menu riêng." />
              <Tabs value={contentTab} onChange={(_, next) => setContentTab(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="bot" label="Cài đặt bot" />
                <Tab value="payment" label="Thanh toán" />
                <Tab value="currency" label="Tiền tệ" />
                <Tab value="admin" label="Admin ID" />
              </Tabs>
            </section>
            {contentTab === "bot" ? (
              <>
                <section className="panel">
                  <PanelHead
                    title="Trạng thái giờ bot"
                    subtitle="Bot chỉ còn chạy theo bảo trì thủ công, BOT_ACTIVE_HOURS hoặc luôn hoạt động. Bài đăng channel không còn điều khiển trạng thái bot."
                  />
                  <div className="status-grid">
                    <div className={`health-item ${botScheduleStatus?.active ? "good" : "bad"}`}>
                      <Activity size={18} />
                      <div>
                        <strong>{botScheduleStatus ? (botScheduleStatus.active ? "Bot đang hoạt động" : "Bot đang offline") : "Không đọc được runtime"}</strong>
                        <span>{botScheduleStatus?.title || "Không có dữ liệu runtime"}</span>
                      </div>
                    </div>
                    {botScheduleStatus ? (
                      <>
                        <div className="health-item">
                          <Settings size={18} />
                          <div>
                            <strong>Nguồn hiện tại</strong>
                            <span>{botScheduleStatus?.source === "fixed" ? "Theo BOT_ACTIVE_HOURS" : botScheduleStatus?.source === "maintenance" ? "Bảo trì thủ công" : "Luôn hoạt động"}</span>
                          </div>
                        </div>
                        <div className="health-item">
                          <Send size={18} />
                          <div>
                            <strong>Khung giờ / lý do</strong>
                            <span>{botScheduleStatus?.window || "Không có khung giờ runtime"}</span>
                          </div>
                        </div>
                        <div className="health-item">
                          <ClipboardList size={18} />
                          <div>
                            <strong>Lặp bài channel</strong>
                            <span>Độc lập với giờ hoạt động bot</span>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="health-item bad">
                        <Settings size={18} />
                        <div>
                          <strong>Không đọc được runtime</strong>
                          <span>Không đọc được trạng thái giờ bot từ API.</span>
                        </div>
                      </div>
                    )}
                  </div>
                  {botScheduleStatus ? (
                    <>
                      <div className="hint compact" style={{ padding: "0 16px 16px" }}>
                        Múi giờ bot: <strong>{botScheduleStatus?.timezone || "-"}</strong> • Bảo trì thủ công: <strong>{botScheduleStatus?.maintenanceMode ? "ON" : "OFF"}</strong>
                      </div>
                    </>
                  ) : (
                    <div className="hint compact" style={{ padding: "0 16px 16px" }}>
                      Không đọc được runtime từ API.
                    </div>
                  )}
                </section>
                <ConfigEditor title="Cài đặt bot" subtitle="Bảo trì thủ công, lịch hoạt động giờ Việt Nam, QR và tần suất kiểm tra thanh toán." fields={BOT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} />
              </>
            ) : null}
            {contentTab === "payment" ? <ConfigEditor title="Phương thức thanh toán" subtitle="PayOS dùng giá VNĐ; PayPal và NOWPayments dùng giá USD riêng, không quy đổi tỷ giá. Credentials vẫn đặt an toàn trong Render Environment." fields={PAYMENT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {contentTab === "currency" ? <ConfigEditor title="Tiền tệ hiển thị" subtitle="Chỉ đổi cách hiển thị trong bot/UI. Số tiền QR PayOS vẫn giữ nguyên VND." fields={CURRENCY_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {contentTab === "admin" ? <ConfigEditor title="Setup Admin ID" subtitle="Quản lý Telegram ID có quyền admin. Nhiều ID thì cách nhau bằng dấu phẩy." fields={ADMIN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
          </div>
        ) : null}

        {tab === "botVi" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="UI Bot tiếng Việt" subtitle="Chỉ quản lý tên gói và nội dung khách Việt nhìn thấy. Giá được quản lý tập trung tại Nhóm & giá." />
              <Tabs value={botViTab} onChange={(_, next) => setBotViTab(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="plans" label="Tên gói & nút mua" />
                <Tab value="groups" label="Mô tả group" />
                <Tab value="buttons" label="Nút bấm" />
                <Tab value="messages" label="Tin nhắn" />
                <Tab value="saleContent" label="Flash sale" />
              </Tabs>
            </section>
            {botViTab === "plans" ? <ConfigEditor title="Tên gói và nút mua tiếng Việt" subtitle="Không chứa giá. Giá bán được quản lý tập trung tại Nhóm & giá." fields={PLAN_VI_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botViTab === "groups" ? <ConfigEditor title="Mô tả group lẻ tiếng Việt" subtitle="Chỉ chỉnh nội dung mô tả. Tên group và giá nằm tại Nhóm & giá." fields={groupViContentFields} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botViTab === "buttons" ? <ConfigEditor title="Nút bấm tiếng Việt" subtitle="Text nút Telegram dành cho khách Việt." fields={BUTTON_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botViTab === "messages" ? <ConfigEditor title="Tin nhắn tiếng Việt" subtitle="Các mẫu tin Bot gửi cho khách Việt." fields={VISIBLE_MESSAGE_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botViTab === "saleContent" ? <ConfigEditor title="Flash sale tiếng Việt" subtitle="Nội dung flash sale dành cho khách Việt." fields={SALE_CONTENT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
          </div>
        ) : null}

        {tab === "hiddenMessages" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="Hidden text" subtitle="Toàn bộ text hiển thị khi nhập hidden code hoặc gặp lỗi hidden được gom ở đây." />
              <Tabs value="messages" onChange={() => undefined} textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="messages" label="Messages" />
              </Tabs>
            </section>
            <ConfigEditor
              title="Hidden messages"
              subtitle="Chỉnh text hợp lệ, không hợp lệ và các rule hidden tại một nơi."
              fields={HIDDEN_MESSAGE_FIELDS}
              values={fieldValues}
              setValues={setFieldValues}
              onSave={saveFields}
            />
          </div>
        ) : null}

        {tab === "botEn" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="UI Bot tiếng Anh" subtitle="Chỉ quản lý tên gói và nội dung tiếng Anh. Giá USD PayPal được quản lý tập trung tại Nhóm & giá." />
              <Tabs value={botEnTab} onChange={(_, next) => setBotEnTab(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="plans" label="Tên gói & nút mua" />
                <Tab value="groups" label="Mô tả group" />
                <Tab value="buttons" label="Nút bấm" />
                <Tab value="messages" label="Tin nhắn" />
                <Tab value="saleContent" label="Flash sale" />
              </Tabs>
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
              <Tabs value={botToolsTab} onChange={(_, next) => setBotToolsTab(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="commandsVi" label="Lệnh tiếng Việt" />
                <Tab value="commandsEn" label="Lệnh tiếng Anh" />
                <Tab value="alertsVi" label="Cảnh báo tiếng Việt" />
                <Tab value="alertsEn" label="Cảnh báo tiếng Anh" />
              </Tabs>
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
              <Tabs value={menuLanguage} onChange={(_, next) => { setMenuLanguage(next); resetMenuForm(); }} textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="vi" label="Trang tiếng Việt" />
                <Tab value="en" label="Trang tiếng Anh" />
              </Tabs>
            </section>
              <section className="panel">
                <PanelHead
                  title={menuLanguage === "en" ? "Menu Builder tiếng Anh" : "Menu Builder tiếng Việt"}
                  subtitle={menuLanguage === "en" ? "Tên trang bắt buộc kết thúc bằng _en, ví dụ main_menu_en." : "Trang gốc tiếng Việt không dùng hậu tố _en."}
                  action={
                      <div className="panel-actions">
                      <Button variant="contained" size="small" onClick={() => { resetMenuForm(); setMenuModalOpen(true); }} startIcon={<Plus size={16} />}>Thêm trang</Button>
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
                    <IconButton color="error" size="small" onClick={(event) => { event.stopPropagation(); removeMenuPage(visibleMenuPages[idx].page_id); }} title="Xoá trang">
                      <Trash2 size={16} />
                    </IconButton>
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
                  <Button variant="contained" size="small" onClick={openNewCouponModal} startIcon={<Plus size={16} />}>Thêm coupon</Button>
                </div>
              }
            />
            <div className="grid">
              <Metric label="Chưa gửi" value={String(couponTabCounts.unsent)} />
              <Metric label="Đã gửi" value={String(couponTabCounts.sent)} />
              <Metric label="Đã sử dụng" value={String(couponTabCounts.used)} />
              <Metric label="Đã hết hạn" value={String(couponTabCounts.expired)} />
            </div>
            <Tabs value={couponTab} onChange={(_, next) => setCouponTab(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
              <Tab value="unsent" label={`Chưa gửi (${couponTabCounts.unsent})`} />
              <Tab value="sent" label={`Đã gửi (${couponTabCounts.sent})`} />
              <Tab value="used" label={`Đã sử dụng (${couponTabCounts.used})`} />
              <Tab value="expired" label={`Đã hết hạn (${couponTabCounts.expired})`} />
            </Tabs>
            <SimpleTable
              headers={["Mã", "Loại", "Áp dụng / Gói", "Giảm", "Trạng thái", "Đã gửi", "Đã dùng", "Người dùng gần nhất"]}
              rows={pagedCoupons.map((item) => [
                <Button
                  key="coupon-code"
                  variant="text"
                  disabled={saving === `coupon-copy-${item.code}`}
                  onClick={(event) => {
                    event.stopPropagation();
                    copyCouponAndMarkSent(item);
                  }}
                  title="Copy mã và đánh dấu đã gửi"
                  sx={{ justifyContent: "flex-start", px: 0, minWidth: 0, textTransform: "none" }}
                >
                  {item.code}
                </Button>,
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
                  <FormControlLabel
                    title="Đánh dấu đã gửi coupon"
                    sx={{ m: 0, mr: 0.5 }}
                    control={
                      <Checkbox
                        checked={isCouponSent(pagedCoupons[idx])}
                        disabled={saving === `coupon-sent-${pagedCoupons[idx].code}`}
                        onChange={(event) => {
                          event.stopPropagation();
                          toggleCouponSent(pagedCoupons[idx], event.target.checked);
                        }}
                        onClick={(event) => event.stopPropagation()}
                      />
                    }
                    label="Gửi"
                  />
                  <IconButton color="error" size="small" onClick={(event) => { event.stopPropagation(); removeCoupon(pagedCoupons[idx].code); }} title="Xoá coupon">
                    <Trash2 size={16} />
                  </IconButton>
                </div>
              )}
            />
            <Pagination page={couponPage} totalPages={totalCouponPages} totalItems={visibleCoupons.length} onPage={setCouponPage} label="coupon" />
          </section>
        ) : null}

        {tab === "activationCodes" ? (
          <section className="panel">
            <PanelHead
              title="Activation codes"
              subtitle="Danh sách mã kích hoạt cho đơn thủ công. Reset để cho khách bấm lại link bot, disable để chặn mã ngay lập tức."
              action={<div className="panel-actions"><Button variant="outlined" size="small" onClick={() => loadAll()} startIcon={<RefreshCw size={16} />}>Tải lại</Button></div>}
            />
            <div className="grid">
              <Metric label="Tổng mã" value={String(activationCodesByStatus.ALL.length)} />
              <Metric label="Chờ kích hoạt" value={String(activationCodesByStatus.PENDING.length)} />
              <Metric label="Đã dùng" value={String(activationCodesByStatus.USED.length)} />
              <Metric label="Đã vô hiệu" value={String(activationCodesByStatus.DISABLED.length)} />
            </div>
            <Tabs value={activationCodeTab} onChange={(_, next) => setActivationCodeTab(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
              <Tab value="ALL" label={`Tất cả (${activationCodesByStatus.ALL.length})`} />
              <Tab value="PENDING" label={`PENDING (${activationCodesByStatus.PENDING.length})`} />
              <Tab value="USED" label={`USED (${activationCodesByStatus.USED.length})`} />
              <Tab value="DISABLED" label={`DISABLED (${activationCodesByStatus.DISABLED.length})`} />
              <Tab value="EXPIRED" label={`EXPIRED (${activationCodesByStatus.EXPIRED.length})`} />
            </Tabs>
            <div className="hint compact" style={{ marginBottom: 12 }}>
              <TextField value={activationCodeQuery} onChange={(event) => setActivationCodeQuery(event.target.value)} placeholder="Tìm theo code, order_id, telegram_user_id..." size="small" fullWidth />
            </div>
            <Tabs value={activationCodeSort} onChange={(_, next) => setActivationCodeSort(next)} textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5, mb: 1.5 }}>
              <Tab value="newest" label="Mới nhất" />
              <Tab value="expiring" label="Sắp hết hạn" />
              <Tab value="recently_used" label="Vừa dùng gần đây" />
            </Tabs>
            <SimpleTable
              headers={["Code", "Đơn", "Khách", "Gói", "Hạn", "Trạng thái", "Link bot", "Cập nhật"]}
              rows={activationCodeRows.map((item) => [
                <strong key={`c-${item.code}`}>{item.code}</strong>,
                item.order_id,
                <><strong>{item.full_name || "-"}</strong><div className="muted">{item.telegram_user_id}</div></>,
                item.plan_name,
                dateText(item.expire_at),
                item.activation_status,
                <Button key={`copy-${item.code}`} variant="outlined" size="small" onClick={(event) => { event.stopPropagation(); copyActivationLink(item); }}>Copy</Button>,
                <div key={`updated-${item.code}`}><div>{dateText(item.updated_at)}</div><div className="muted">{item.activated_at ? `Activated ${dateText(item.activated_at)}` : ""}</div></div>,
              ])}
              actions={(idx) => (
                <div className="coupon-row-actions">
                  <IconButton color="error" size="small" onClick={(event) => { event.stopPropagation(); disableActivationCode(activationCodeRows[idx]); }} title="Vô hiệu hoá mã"><XCircle size={16} /></IconButton>
                  <IconButton color="primary" size="small" onClick={(event) => { event.stopPropagation(); refreshActivationCode(activationCodeRows[idx]); }} title="Reset mã"><RefreshCw size={16} /></IconButton>
                  <IconButton color="primary" size="small" onClick={(event) => { event.stopPropagation(); renewActivationCode(activationCodeRows[idx]); }} title="Tạo lại link mới"><Plus size={16} /></IconButton>
                  <IconButton color="error" size="small" onClick={(event) => { event.stopPropagation(); deleteActivationCodeRow(activationCodeRows[idx]); }} title="Xoá mã"><Trash2 size={16} /></IconButton>
                </div>
              )}
            />
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
                    <Button variant="outlined" size="small" onClick={() => setSecuritySettingsOpen(true)} startIcon={<Settings size={16} />}>Cài đặt</Button>
                    <Button variant="contained" size="small" onClick={() => { setBlacklistForm({ telegram_user_id: "", username: "", full_name: "", reason: "" }); setBlacklistModalOpen(true); }} startIcon={<Plus size={16} />}>Thêm blacklist</Button>
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
                  <IconButton color="error" size="small" onClick={(event) => { event.stopPropagation(); removeBlacklistEntry(blacklist[idx].telegram_user_id); }} title="Gỡ blacklist">
                    <Trash2 size={16} />
                  </IconButton>
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
                    <Button variant="contained" size="small" onClick={() => { resetSaleForm(); setSaleModalOpen(true); }} startIcon={<Plus size={16} />}>Thêm sale</Button>
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
                <IconButton color="error" size="small" onClick={(event) => { event.stopPropagation(); removeSaleRule(saleRules[idx].sale_id); }} title="Xoá sale"><Trash2 size={16} /></IconButton>
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
                    <Button variant="outlined" size="small" onClick={() => setSystemSettingsOpen(true)} startIcon={<Settings size={16} />}>Cài đặt</Button>
                    <Button variant="contained" size="small" onClick={handleWebhookReset} startIcon={<RefreshCw size={16} />}>Reset webhook</Button>
                  </div>
                }
              />
              <div className="system-list">
                <Info label="Webhook URL" value={webhook?.url || "Chưa cấu hình"} icon={<Activity size={16} />} />
                <Info label="Update đang chờ" value={String(webhook?.pending_update_count ?? 0)} icon={<BadgePercent size={16} />} />
                <Info label="Lỗi gần nhất" value={webhook?.last_error_message || "Không có"} icon={<XCircle size={16} />} />
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
                action={<IconButton color="error" size="small" onClick={() => setGroupModalOpen(false)} title="Đóng"><XCircle size={18} /></IconButton>}
              />
              <div className="form-grid">
                <FormControl className="field" fullWidth size="small">
                  <InputLabel id="group-no-label">Nhóm cần cấu hình</InputLabel>
                  <Select labelId="group-no-label" label="Nhóm cần cấu hình" value={groupNo} onChange={(event) => fillGroupForm(event.target.value)} sx={popupSelectSx}>
                    {groupSelectOptions.map((item) => (
                      <MenuItem key={item} value={item}>G{item}{visibleGroups.includes(item) ? "" : " - nhóm mới"}</MenuItem>
                    ))}
                  </Select>
                  <Typography variant="caption" color="text.secondary">Coupon và sale sẽ hiện tên nhóm này trong dropdown.</Typography>
                </FormControl>
                <TextField className="field" label="Tên nhóm tiếng Việt" value={groupName} onChange={(event) => setGroupName(event.target.value)} placeholder={getConfigValue(config, `BTN_G${groupNo}`) || "VD: Hang Cú Prime"} fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Tên nhóm tiếng Anh" value={groupNameEn} onChange={(event) => setGroupNameEn(event.target.value)} placeholder={getConfigValue(config, `BTN_G${groupNo}_EN`) || "VD: Prime Group"} fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Telegram group ID" value={groupId} onChange={(event) => setGroupId(event.target.value)} placeholder={getConfigValue(config, `ID_G${groupNo}`) || "VD: -1001234567890"} fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Giá VNĐ 30 ngày" value={groupPrice1m} onChange={(event) => setGroupPrice1m(event.target.value)} placeholder={getConfigValue(config, `PRICE_G${groupNo}_1M`) || "VD: 99000"} fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Giá VNĐ trọn đời" value={groupPriceLife} onChange={(event) => setGroupPriceLife(event.target.value)} placeholder={getConfigValue(config, `PRICE_G${groupNo}_LIFE`) || "VD: 299000"} fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Giá USD 30 ngày" value={groupPrice1mUsd} onChange={(event) => setGroupPrice1mUsd(event.target.value)} placeholder="VD: 4.99" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Giá USD trọn đời" value={groupPriceLifeUsd} onChange={(event) => setGroupPriceLifeUsd(event.target.value)} placeholder="VD: 14.99" fullWidth size="small" sx={popupFieldSx} />
              </div>
              <div className="modal-actions">
                <Button variant="outlined" onClick={() => setGroupModalOpen(false)}>Đóng</Button>
                <Button variant="outlined" color="error" onClick={removeGroupConfig} disabled={saving === "group-delete"} startIcon={<Trash2 size={16} />}>Xoá nhóm</Button>
                <Button variant="contained" onClick={saveGroupConfig} disabled={saving === "group"} startIcon={saving === "group" ? <Loader2 size={16} className="spin" /> : <Save size={16} />}>Lưu nhóm</Button>
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
                action={<IconButton color="error" size="small" onClick={() => setHiddenGroupModalOpen(false)} title="Đóng"><XCircle size={18} /></IconButton>}
              />
              <div className="form-grid">
                <TextField className="field" label="ID kỹ thuật" value={hiddenGroupForm.id} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, id: hiddenSlug(event.target.value) })} placeholder="VD: prime_alpha" fullWidth size="small" sx={popupFieldSx} helperText={<span>Dùng trong plan token dạng <code>HG:prime_alpha:1M</code>. Để trống thì hệ thống tự tạo từ tên.</span>} />
                <TextField className="field" label="Tên hiển thị" value={hiddenGroupForm.name} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, name: event.target.value })} placeholder="VD: Prime Alpha" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Telegram group ID" value={hiddenGroupForm.chat_id} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, chat_id: event.target.value })} placeholder="-1001234567890" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field wide" label="Mô tả ngắn" value={hiddenGroupForm.description} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, description: event.target.value })} placeholder="Mô tả nội bộ hoặc nội dung bot dùng để giới thiệu hidden group." fullWidth multiline minRows={4} sx={popupFieldSx} />
                <div className="hint compact wide">Giá duration nào để 0 thì bot sẽ không hiện nút mua duration đó. Nếu chỉ bán trọn đời, để giá 30 ngày VND/USD = 0 và chỉ nhập giá trọn đời.</div>
                <TextField className="field" label="Giá VNĐ 30 ngày" value={hiddenGroupForm.price_1m_vnd} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, price_1m_vnd: event.target.value })} inputMode="numeric" placeholder="99000" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Giá VNĐ trọn đời" value={hiddenGroupForm.price_life_vnd} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, price_life_vnd: event.target.value })} inputMode="numeric" placeholder="299000" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Giá USD 30 ngày" value={hiddenGroupForm.price_1m_usd} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, price_1m_usd: event.target.value })} inputMode="decimal" placeholder="4.99" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Giá USD trọn đời" value={hiddenGroupForm.price_life_usd} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, price_life_usd: event.target.value })} inputMode="decimal" placeholder="14.99" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Hạn 30 ngày (days)" value={hiddenGroupForm.duration_1m_days} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, duration_1m_days: event.target.value })} inputMode="numeric" placeholder="30" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Hạn trọn đời (days)" value={hiddenGroupForm.lifetime_days} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, lifetime_days: event.target.value })} inputMode="numeric" placeholder="3650" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Sort order" value={hiddenGroupForm.sort_order} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, sort_order: event.target.value })} inputMode="numeric" placeholder="1" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Ảnh / File ID" value={hiddenGroupForm.image_url} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, image_url: event.target.value })} placeholder="URL hoặc Telegram file_id nếu có" fullWidth size="small" sx={popupFieldSx} />
                <FormControl className="field" fullWidth size="small">
                  <InputLabel id="hidden-group-requirement-label">Điều kiện mặc định</InputLabel>
                  <Select labelId="hidden-group-requirement-label" label="Điều kiện mặc định" value={hiddenGroupForm.requirement_type} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, requirement_type: event.target.value, requirement_value: hiddenRequirementNeedsValue(event.target.value) ? hiddenGroupForm.requirement_value : "" })} sx={popupSelectSx}>
                    {HIDDEN_REQUIREMENT_OPTIONS.map((item) => <MenuItem key={item.value} value={item.value}>{item.label}</MenuItem>)}
                  </Select>
                </FormControl>
                <TextField className="field" label="Requirement value" value={hiddenGroupForm.requirement_value} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, requirement_value: event.target.value })} placeholder="VD: FULL_LIFE hoặc HG:prime_alpha:LIFE" disabled={!hiddenRequirementNeedsValue(hiddenGroupForm.requirement_type)} fullWidth size="small" sx={popupFieldSx} />
                <FormControl className="field" fullWidth size="small">
                  <InputLabel id="hidden-group-active-label">Trạng thái</InputLabel>
                  <Select labelId="hidden-group-active-label" label="Trạng thái" value={hiddenGroupForm.is_active ? "ON" : "OFF"} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, is_active: event.target.value === "ON" })} sx={popupSelectSx}>
                    <MenuItem value="ON">Đang bật</MenuItem>
                    <MenuItem value="OFF">Tạm tắt</MenuItem>
                  </Select>
                </FormControl>
              </div>
              <div className="modal-actions">
                <Button variant="outlined" onClick={() => setHiddenGroupModalOpen(false)}>Đóng</Button>
                {hiddenGroupForm.id ? <Button variant="outlined" onClick={() => setHiddenGroupForm({ ...hiddenGroupForm, id: hiddenSlug(hiddenGroupForm.name) || hiddenGroupForm.id })} startIcon={<RefreshCw size={16} />}>Tạo lại ID từ tên</Button> : null}
                <Button variant="contained" onClick={saveHiddenGroup} disabled={saving === `hidden-group-${hiddenGroupForm.id || hiddenSlug(hiddenGroupForm.name) || "new"}`} startIcon={saving === `hidden-group-${hiddenGroupForm.id || hiddenSlug(hiddenGroupForm.name) || "new"}` ? <Loader2 size={16} className="spin" /> : <Save size={16} />}>Lưu Hidden Group</Button>
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
                action={<IconButton color="error" size="small" onClick={() => setHiddenCodeModalOpen(false)} title="Đóng"><XCircle size={18} /></IconButton>}
              />
              <Box sx={{ display: "grid", gap: 1.5, p: 2 }}>
                <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" } }}>
                  <TextField className="field" label="Mã hidden" value={hiddenCodeForm.code} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, code: event.target.value.toUpperCase().replace(/\s+/g, "-") })} placeholder="VD: PRIME-ALPHA" fullWidth size="small" sx={popupFieldSx} helperText="Bot chỉ hiện hidden catalog cho người nhập đúng mã này." />
                  <TextField className="field" label="Tên nội bộ" value={hiddenCodeForm.name} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, name: event.target.value })} placeholder="VD: Code bán cho cộng tác viên A" fullWidth size="small" sx={popupFieldSx} />
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="hidden-code-active-label">Trạng thái</InputLabel>
                    <Select labelId="hidden-code-active-label" label="Trạng thái" value={hiddenCodeForm.is_active ? "ON" : "OFF"} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, is_active: event.target.value === "ON" })} sx={popupSelectSx}>
                      <MenuItem value="ON">Đang bật</MenuItem>
                      <MenuItem value="OFF">Tạm tắt</MenuItem>
                    </Select>
                  </FormControl>
                  <TextField className="field wide" label="Mô tả ghi chú" value={hiddenCodeForm.description} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, description: event.target.value })} placeholder="Ghi chú nội bộ: mã này dùng cho ai, campaign nào, mục đích gì..." fullWidth multiline minRows={4} sx={popupFieldSx} />
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="hidden-code-scope-label">Phạm vi reveal</InputLabel>
                    <Select labelId="hidden-code-scope-label" label="Phạm vi reveal" value={hiddenCodeForm.scope_type} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, scope_type: event.target.value })} sx={popupSelectSx}>
                      {HIDDEN_SCOPE_OPTIONS.map((item) => <MenuItem key={item.value} value={item.value}>{item.label}</MenuItem>)}
                    </Select>
                  </FormControl>
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="hidden-code-requirement-label">Điều kiện override</InputLabel>
                    <Select labelId="hidden-code-requirement-label" label="Điều kiện override" value={hiddenCodeForm.requirement_type} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, requirement_type: event.target.value, requirement_value: hiddenRequirementNeedsValue(event.target.value) ? hiddenCodeForm.requirement_value : "" })} sx={popupSelectSx}>
                      <MenuItem value="">Dùng rule của hidden group</MenuItem>
                      {HIDDEN_REQUIREMENT_OPTIONS.map((item) => <MenuItem key={item.value} value={item.value}>{item.label}</MenuItem>)}
                    </Select>
                  </FormControl>
                  <TextField className="field" label="Requirement value" value={hiddenCodeForm.requirement_value} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, requirement_value: event.target.value })} placeholder="VD: FULL_LIFE hoặc HG:prime_alpha:LIFE" disabled={!hiddenRequirementNeedsValue(hiddenCodeForm.requirement_type)} fullWidth size="small" sx={popupFieldSx} />
                  <TextField className="field" label="Max uses" value={hiddenCodeForm.max_uses} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, max_uses: event.target.value })} inputMode="numeric" placeholder="0 = không giới hạn" fullWidth size="small" sx={popupFieldSx} />
                  <TextField className="field" label="Used count" value={hiddenCodeForm.used_count} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, used_count: event.target.value })} inputMode="numeric" placeholder="0" fullWidth size="small" sx={popupFieldSx} />
                  <TextField className="field" label="Hiệu lực từ" type="datetime-local" value={hiddenCodeForm.valid_from} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, valid_from: event.target.value })} fullWidth size="small" sx={popupFieldSx} slotProps={{ inputLabel: { shrink: true } }} />
                  <TextField className="field" label="Hiệu lực đến" type="datetime-local" value={hiddenCodeForm.valid_until} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, valid_until: event.target.value })} fullWidth size="small" sx={popupFieldSx} slotProps={{ inputLabel: { shrink: true } }} />
                </Box>
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
                            <Checkbox checked={hiddenCodeForm.group_ids.includes(group.id)} onChange={() => toggleHiddenCodeGroup(group.id)} size="small" />
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
              </Box>
              <div className="modal-actions">
                <Button variant="outlined" onClick={() => setHiddenCodeModalOpen(false)}>Đóng</Button>
                <Button variant="outlined" onClick={() => setHiddenCodeForm({ ...hiddenCodeForm, code: hiddenCodeSeed(hiddenCodeForm.name || hiddenCodeForm.description || "hidden-code") })} startIcon={<RefreshCw size={16} />}>Gợi ý mã từ tên</Button>
                <Button variant="contained" onClick={saveHiddenCode} disabled={saving === `hidden-code-${(hiddenCodeForm.code.trim() || hiddenCodeSeed(hiddenCodeForm.name)).toUpperCase()}`} startIcon={saving === `hidden-code-${(hiddenCodeForm.code.trim() || hiddenCodeSeed(hiddenCodeForm.name)).toUpperCase()}` ? <Loader2 size={16} className="spin" /> : <Save size={16} />}>Lưu Hidden Code</Button>
              </div>
            </section>
          </div>
        ) : null}

        {campaignModalOpen ? (
          <MuiDialogShell open title="Tạo campaign" subtitle="Chọn tệp nhận, lọc theo gói và nhập nội dung gửi. Campaign tạo xong vẫn cần bấm Gửi ở danh sách." onClose={() => setCampaignModalOpen(false)} maxWidth="lg">
              <Box sx={{ display: "grid", gap: 1.5 }}>
                  <TextField className="field" label="Tên campaign" value={campaignForm.title} onChange={(event) => setCampaignForm({ ...campaignForm, title: event.target.value })} placeholder="VD: Sale cuối tuần / Tặng coupon tháng 6" fullWidth size="small" sx={popupFieldSx} />
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="campaign-target-label">Tệp người nhận</InputLabel>
                    <Select labelId="campaign-target-label" label="Tệp người nhận" value={campaignForm.target_segment} onChange={(event) => setCampaignForm({ ...campaignForm, target_segment: event.target.value })} sx={popupSelectSx}>
                      <MenuItem value="ALL">Tất cả user từng tương tác</MenuItem>
                      <MenuItem value="VIP_PAID">Đã từng mua VIP</MenuItem>
                      <MenuItem value="VIP_ACTIVE">Đang còn VIP active</MenuItem>
                      <MenuItem value="VIP_EXPIRED">Đã từng mua nhưng hết hạn</MenuItem>
                      <MenuItem value="NO_PURCHASE">Chưa mua gói</MenuItem>
                    </Select>
                    <Typography variant="caption" color="text.secondary">Blacklist active sẽ tự bị loại khỏi danh sách gửi.</Typography>
                  </FormControl>
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="campaign-plan-filter-label">Lọc theo gói đã mua</InputLabel>
                    <Select labelId="campaign-plan-filter-label" label="Lọc theo gói đã mua" value={campaignForm.plan_filter} onChange={(event) => setCampaignForm({ ...campaignForm, plan_filter: event.target.value })} sx={popupSelectSx}>
                      <MenuItem value="ALL">Tất cả gói</MenuItem>
                      {campaignPlanOptions.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
                    </Select>
                    <Typography variant="caption" color="text.secondary">Lấy từ tên gói trong các đơn PAID hiện có.</Typography>
                  </FormControl>
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="campaign-match-label">Cách so khớp gói</InputLabel>
                    <Select labelId="campaign-match-label" label="Cách so khớp gói" value={campaignForm.plan_match_scope} onChange={(event) => setCampaignForm({ ...campaignForm, plan_match_scope: event.target.value })} sx={popupSelectSx}>
                      <MenuItem value="ANY_PAID">Từng mua gói này</MenuItem>
                      <MenuItem value="ACTIVE_ONLY">Đang active gói này</MenuItem>
                      <MenuItem value="LATEST">Gói PAID mới nhất là gói này</MenuItem>
                    </Select>
                    <Typography variant="caption" color="text.secondary">Chỉ áp dụng khi bạn chọn một gói cụ thể.</Typography>
                  </FormControl>
                  <TextField className="field" label="Delay mỗi user" value={campaignForm.delay_seconds} onChange={(event) => setCampaignForm({ ...campaignForm, delay_seconds: event.target.value })} inputMode="numeric" placeholder="5" fullWidth size="small" sx={popupFieldSx} helperText="Tối thiểu 2 giây." />
                  <TextField className="field" label="Số gửi mỗi vòng" value={campaignForm.batch_size} onChange={(event) => setCampaignForm({ ...campaignForm, batch_size: event.target.value })} inputMode="numeric" placeholder="20" fullWidth size="small" sx={popupFieldSx} />
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="campaign-parse-label">Định dạng</InputLabel>
                    <Select labelId="campaign-parse-label" label="Định dạng" value={campaignForm.parse_mode} onChange={(event) => setCampaignForm({ ...campaignForm, parse_mode: event.target.value })} sx={popupSelectSx}>
                      <MenuItem value="HTML">HTML</MenuItem>
                      <MenuItem value="NONE">Text thường</MenuItem>
                    </Select>
                  </FormControl>
                  <TextField className="field wide" label="Nội dung tin nhắn" value={campaignForm.message} onChange={(event) => setCampaignForm({ ...campaignForm, message: event.target.value })} placeholder={"Xin chào {name},\\nShop đang có ưu đãi mới...\\nCoupon của bạn: HANGCU_..."} fullWidth multiline minRows={6} sx={popupFieldSx} helperText={<span>Dùng biến {"{name}"}, {"{telegram_user_id}"}, {"{segment}"}, {"{latest_plan_name}"}.</span>} />
              </Box>
              <Box sx={{ display: "flex", alignItems: "center", flexWrap: "wrap", gap: 1.5, px: 2, py: 1.5, borderTop: 1, borderColor: "divider", color: "text.secondary" }}>
                  <strong>Preview: {campaignPreview?.total || 0} người</strong>
                  <span>Active: {campaignPreview?.counts?.VIP_ACTIVE || 0}</span>
                  <span>Hết hạn: {campaignPreview?.counts?.VIP_EXPIRED || 0}</span>
                  <span>Chưa mua: {campaignPreview?.counts?.NO_PURCHASE || 0}</span>
              </Box>
              <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider" }}>
                <Button variant="outlined" onClick={() => setCampaignModalOpen(false)}>Đóng</Button>
                <Button variant="contained" onClick={saveCampaign} disabled={saving === "campaign-create" || !campaignForm.title.trim() || !campaignForm.message.trim()} startIcon={saving === "campaign-create" ? <Loader2 size={16} className="spin" /> : <Plus size={16} />}>Tạo campaign</Button>
              </Stack>
          </MuiDialogShell>
        ) : null}

        {menuModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true">
            <section className="modal-panel wide-modal">
              <PanelHead
                title={menuForm.page_id ? `Menu: ${menuForm.page_id}` : "Thêm trang menu"}
                subtitle={menuLanguage === "en" ? "Trang tiếng Anh bắt buộc kết thúc bằng _en." : "Trang tiếng Việt không dùng hậu tố _en."}
                action={<IconButton color="error" size="small" onClick={() => setMenuModalOpen(false)} title="Đóng"><XCircle size={18} /></IconButton>}
              />
              <div className="form-grid two">
                <TextField className="field" label="Tên trang" value={menuForm.page_id} onChange={(event) => setMenuForm({ ...menuForm, page_id: event.target.value })} placeholder={menuLanguage === "en" ? "VD: main_menu_en, support_page_en" : "VD: main_menu, support_page"} fullWidth size="small" sx={popupFieldSx} helperText={menuLanguage === "en" ? "Trang tiếng Anh bắt buộc có hậu tố _en." : "Trang tiếng Việt không được dùng hậu tố _en."} />
                <TextField className="field" label="Ảnh cover" value={menuForm.image_url} onChange={(event) => setMenuForm({ ...menuForm, image_url: event.target.value })} placeholder="File ID Telegram hoặc URL ảnh" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field wide" label="Nội dung trang" value={menuForm.body} onChange={(event) => setMenuForm({ ...menuForm, body: event.target.value })} placeholder="Nhập nội dung HTML. Có thể dùng {PRICE_SVIP_30D}, {SALE_LABEL_PRICE_SVIP_30D}..." fullWidth multiline minRows={8} sx={popupFieldSx} />
                <TextField className="field wide" label="Nút bấm" value={menuForm.layout} onChange={(event) => setMenuForm({ ...menuForm, layout: event.target.value })} placeholder={"Mỗi dòng là một hàng nút. Ví dụ:\\nMua SVIP => buy_full_1m | Hỗ trợ => nav:support_page"} fullWidth multiline minRows={5} sx={popupFieldSx} helperText={<span>Có thể dùng biến như {"{BTN_BUY_SVIP_30D}"}.</span>} />
              </div>
              <div className="modal-actions">
                <Button variant="outlined" onClick={() => setMenuModalOpen(false)}>Đóng</Button>
                <Button variant="outlined" color="error" onClick={() => removeMenuPage()} disabled={!menuForm.page_id} startIcon={<Trash2 size={16} />}>Xoá trang</Button>
                <Button variant="contained" onClick={saveMenuPage} startIcon={<Save size={16} />}>Lưu menu</Button>
              </div>
            </section>
          </div>
        ) : null}

        {saleModalOpen ? (
          <MuiDialogShell open title="Thêm sale" subtitle="Tạo giảm giá theo phần trăm hoặc giá sale cố định cho một gói." onClose={() => setSaleModalOpen(false)} maxWidth="lg">
              <Box sx={{ display: "grid", gap: 1.5 }}>
                <TextField className="field" label="Tên chương trình sale" value={saleForm.sale_id} onChange={(event) => setSaleForm({ ...saleForm, sale_id: event.target.value })} placeholder="VD: FLASH-G1-THANG-5" fullWidth size="small" sx={popupFieldSx} />
                <FormControl className="field" fullWidth size="small">
                  <InputLabel id="sale-price-key-label">Gói áp dụng</InputLabel>
                  <Select labelId="sale-price-key-label" label="Gói áp dụng" value={saleForm.price_key} onChange={(event) => setSaleForm({ ...saleForm, price_key: event.target.value })} sx={popupSelectSx}>
                    {priceKeyOptions.map((item) => <MenuItem key={item} value={item}>{priceOptionLabel(item)}</MenuItem>)}
                  </Select>
                  <Typography variant="caption" color="text.secondary">Chỉ hiện nhóm đã setup, cộng với SVIP chung.</Typography>
                </FormControl>
                <TextField className="field" label="Giảm theo phần trăm" value={saleForm.discount_percent} onChange={(event) => setSaleForm({ ...saleForm, discount_percent: event.target.value })} placeholder="VD: 20" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Hoặc giá sale cố định" value={saleForm.sale_price} onChange={(event) => setSaleForm({ ...saleForm, sale_price: event.target.value })} placeholder="VD: 79000" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Giới hạn slot" value={saleForm.slot_limit} onChange={(event) => setSaleForm({ ...saleForm, slot_limit: event.target.value })} placeholder="Để trống hoặc 0 nếu không giới hạn" fullWidth size="small" sx={popupFieldSx} />
                <FormControl className="field" fullWidth size="small">
                  <InputLabel id="sale-enabled-label">Trạng thái</InputLabel>
                  <Select labelId="sale-enabled-label" label="Trạng thái" value={saleForm.enabled} onChange={(event) => setSaleForm({ ...saleForm, enabled: event.target.value })} sx={popupSelectSx}>
                    <MenuItem value="ON">Bật</MenuItem>
                    <MenuItem value="OFF">Tắt</MenuItem>
                  </Select>
                </FormControl>
              </Box>
              <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider" }}>
                <Button variant="outlined" onClick={() => setSaleModalOpen(false)}>Đóng</Button>
                <Button variant="outlined" color="error" onClick={() => removeSaleRule()} disabled={!saleForm.sale_id} startIcon={<Trash2 size={16} />}>Xoá sale</Button>
                <Button variant="contained" onClick={saveSaleRule} startIcon={<Save size={16} />}>Lưu sale</Button>
              </Stack>
          </MuiDialogShell>
        ) : null}

        {blacklistModalOpen ? (
          <MuiDialogShell open title={blacklistForm.telegram_user_id ? `Blacklist ${blacklistForm.telegram_user_id}` : "Thêm blacklist"} subtitle="Chặn seller hoặc user spam theo Telegram ID." onClose={() => setBlacklistModalOpen(false)} maxWidth="sm">
              <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: { xs: "1fr", sm: "repeat(2, minmax(0, 1fr))" } }}>
                <TextField className="field" label="Telegram ID" value={blacklistForm.telegram_user_id} onChange={(event) => setBlacklistForm({ ...blacklistForm, telegram_user_id: event.target.value.trim() })} placeholder="VD: 123456789" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Username" value={blacklistForm.username} onChange={(event) => setBlacklistForm({ ...blacklistForm, username: event.target.value })} placeholder="@username nếu có" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Tên hiển thị" value={blacklistForm.full_name} onChange={(event) => setBlacklistForm({ ...blacklistForm, full_name: event.target.value })} placeholder="Tên user" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Lý do" value={blacklistForm.reason} onChange={(event) => setBlacklistForm({ ...blacklistForm, reason: event.target.value })} placeholder="VD: Seller gắn link bio" fullWidth size="small" sx={popupFieldSx} />
              </Box>
              <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider" }}>
                <Button variant="outlined" onClick={() => setBlacklistModalOpen(false)}>Đóng</Button>
                <Button variant="outlined" color="error" onClick={() => removeBlacklistEntry()} disabled={!blacklistForm.telegram_user_id} startIcon={<Trash2 size={16} />}>Gỡ chặn</Button>
                <Button variant="contained" onClick={saveBlacklistEntry} startIcon={<ShieldCheck size={16} />}>Lưu blacklist</Button>
              </Stack>
          </MuiDialogShell>
        ) : null}

        {couponModalOpen ? (
          <MuiDialogShell open title={couponForm.Code ? `Coupon ${couponForm.Code}` : "Thêm coupon"} subtitle="Tạo mã giảm giá, mã kích hoạt hoặc gen nhiều mã cùng điều kiện trong popup này." onClose={() => setCouponModalOpen(false)} maxWidth="lg">
              <Box sx={{ display: "grid", gap: 1.5 }}>
                <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", alignItems: "center", px: 2, pt: 1.5 }}>
                  <Button variant="outlined" onClick={generateCouponCode} startIcon={<RefreshCw size={16} />}>Gen mã HANGCU_</Button>
                  <TextField value={couponBatchCount} onChange={(event) => setCouponBatchCount(event.target.value)} inputMode="numeric" size="small" title="Số lượng mã cần gen cùng điều kiện" sx={{ width: 140 }} />
                  <Button variant="outlined" onClick={generateManyCoupons} startIcon={<RefreshCw size={16} />}>Gen nhiều cùng điều kiện</Button>
                </Stack>
                <Box sx={{ display: "grid", gap: 1.5 }}>
                  <TextField className="field" label="Mã coupon" value={couponForm.Code} onChange={(event) => setCouponForm({ ...couponForm, Code: event.target.value.toUpperCase() })} placeholder="VD: VIP2026" fullWidth size="small" sx={popupFieldSx} />
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="coupon-type-label">Loại coupon</InputLabel>
                    <Select labelId="coupon-type-label" label="Loại coupon" value={couponForm.Coupon_Type} onChange={(event) => setCouponForm({ ...couponForm, Coupon_Type: event.target.value })} sx={popupSelectSx}>
                      <MenuItem value="DISCOUNT">Giảm giá khi mua QR</MenuItem>
                      <MenuItem value="ACTIVATION">Kích hoạt miễn phí</MenuItem>
                    </Select>
                    <Typography variant="caption" color="text.secondary">Giảm giá: khách nhập mã rồi chọn gói để tạo QR đã trừ tiền. Kích hoạt: nhập mã là cấp link ngay.</Typography>
                  </FormControl>
                  {couponForm.Coupon_Type === "DISCOUNT" ? (
                    <TextField className="field" label="Phần trăm giảm" value={couponForm.Discount_Percent} onChange={(event) => setCouponForm({ ...couponForm, Discount_Percent: event.target.value })} placeholder="VD: 15" fullWidth size="small" sx={popupFieldSx} helperText="Nhập 1-99. Nếu muốn miễn phí 100%, dùng loại Kích hoạt miễn phí." />
                  ) : (
                    <>
                      <FormControl className="field" fullWidth size="small">
                        <InputLabel id="coupon-plan-label">Gói cấp cho khách</InputLabel>
                        <Select labelId="coupon-plan-label" label="Gói cấp cho khách" value={couponForm.Plan_Name} onChange={(event) => {
                        const nextPlan = event.target.value;
                        setCouponForm({
                          ...couponForm,
                          Plan_Name: nextPlan,
                          Duration_Days: isLifetimeCouponPlan(nextPlan) ? lifetimeCouponDays : couponForm.Duration_Days,
                        });
                      }}>{planKeyOptions.map((item) => <MenuItem key={item} value={item}>{planOptionLabel(item)}</MenuItem>)}</Select>
                        <Typography variant="caption" color="text.secondary">Chọn một gói cố định, hoặc để khách tự chọn group lẻ sau khi nhập mã.</Typography>
                      </FormControl>
                      <TextField className="field" label="Số ngày sử dụng" value={lifetimeCouponSelected ? lifetimeCouponDays : couponForm.Duration_Days} onChange={(event) => setCouponForm({ ...couponForm, Duration_Days: event.target.value })} placeholder="VD: 30" disabled={lifetimeCouponSelected} fullWidth size="small" sx={popupFieldSx} helperText={lifetimeCouponSelected ? "Gói trọn đời tự dùng số ngày trọn đời, không cần nhập 0." : "Dùng cho coupon kích hoạt theo ngày."} />
                      <TextField className="field" label="Nhãn thời hạn" value={couponForm.Duration_Label} onChange={(event) => setCouponForm({ ...couponForm, Duration_Label: event.target.value })} placeholder="VD: 30 ngày, dùng thử, trọn đời" fullWidth size="small" sx={popupFieldSx} helperText={lifetimeCouponSelected ? "Để trống thì bot tự hiện “trọn đời”." : "Để trống thì bot tự dùng “N ngày”."} />
                      <TextField className="field" label="Mẫu tên gói" value={couponForm.Plan_Name_Template} onChange={(event) => setCouponForm({ ...couponForm, Plan_Name_Template: event.target.value })} placeholder="VIP {duration_label} - {group}" fullWidth size="small" sx={popupFieldSx} helperText={<span>Lưu vào đơn và hiện trong tin thành công. Dùng {"{duration_label}"}, {"{days}"}, {"{group}"}.</span>} />
                      <TextField className="field" label="Mẫu nút chọn group" value={couponForm.Button_Template} onChange={(event) => setCouponForm({ ...couponForm, Button_Template: event.target.value })} placeholder="{plan_name}" fullWidth size="small" sx={popupFieldSx} helperText={<span>Dùng khi khách tự chọn group. Dùng {"{plan_name}"}, {"{duration_label}"}, {"{group}"}.</span>} />
                    </>
                  )}
                  <TextField className="field" label="Số lượt dùng tối đa" value={couponForm.Max_Uses} onChange={(event) => setCouponForm({ ...couponForm, Max_Uses: event.target.value })} placeholder="VD: 1" fullWidth size="small" sx={popupFieldSx} />
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="coupon-enabled-label">Trạng thái</InputLabel>
                    <Select labelId="coupon-enabled-label" label="Trạng thái" value={couponForm.Enabled} onChange={(event) => setCouponForm({ ...couponForm, Enabled: event.target.value })} sx={popupSelectSx}>
                      <MenuItem value="ON">Bật</MenuItem>
                      <MenuItem value="OFF">Tắt</MenuItem>
                    </Select>
                  </FormControl>
                </Box>
                {couponForm.Coupon_Type === "DISCOUNT" ? (
                  <Box sx={{ display: "grid", gap: 1.25, px: 2, pb: 2 }}>
                    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2 }}>
                      <strong>Gói được áp dụng</strong>
                      <Button variant={couponForm.Applies_To === "ALL" ? "contained" : "outlined"} onClick={() => setCouponForm({ ...couponForm, Applies_To: "ALL" })}>Tất cả gói</Button>
                    </Box>
                    <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
                      {discountPlanKeyOptions.map((item) => {
                        const selected = couponForm.Applies_To === "ALL" || couponForm.Applies_To.split(",").includes(item);
                        return (
                          <FormControlLabel
                            key={item}
                            sx={{ m: 0, px: 1, py: 0.75, borderRadius: 4, border: 1, borderColor: selected ? "primary.main" : "divider", bgcolor: selected ? "action.selected" : "background.paper" }}
                            control={<Checkbox checked={selected} onChange={() => toggleCouponPlan(item)} />}
                            label={planOptionLabel(item)}
                          />
                        );
                      })}
                    </Box>
                  </Box>
                ) : null}
              </Box>
              <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider" }}>
                <Button variant="outlined" onClick={() => setCouponModalOpen(false)}>Đóng</Button>
                <Button variant="outlined" color="error" onClick={() => removeCoupon()} disabled={!couponForm.Code} startIcon={<Trash2 size={16} />}>Xoá coupon</Button>
                <Button variant="contained" onClick={saveCoupon} startIcon={<Gift size={16} />}>Lưu coupon</Button>
              </Stack>
          </MuiDialogShell>
        ) : null}

        {channelPostModalOpen ? (
          <MuiDialogShell open title={channelPostForm.id ? "Sửa bài đăng channel" : "Soạn bài đăng channel"} subtitle="Giờ nhập trong popup là giờ Việt Nam trên máy admin. Bot sẽ gửi/xóa bằng worker backend." onClose={() => setChannelPostModalOpen(false)} maxWidth="lg">
              <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" } }}>
                  <TextField className="field" label="Channel / group nhận bài" value={channelPostForm.target_chat_id} onChange={(event) => setChannelPostForm({ ...channelPostForm, target_chat_id: event.target.value })} placeholder="@channel_username hoặc -100..." fullWidth size="small" sx={popupFieldSx} helperText="Bot phải là admin và có quyền gửi/xóa bài ở nơi này." />
                  <TextField className="field" label="Tiêu đề quản lý" value={channelPostForm.title} onChange={(event) => setChannelPostForm({ ...channelPostForm, title: event.target.value })} placeholder="VD: Sale cuối tuần" fullWidth size="small" sx={popupFieldSx} helperText="Chỉ để admin dễ tìm, không bắt buộc hiển thị cho khách." />
                  <TextField className="field wide" label="Ảnh / file_id Telegram" value={channelPostForm.image_ref} onChange={(event) => setChannelPostForm({ ...channelPostForm, image_ref: event.target.value })} placeholder="https://... hoặc file_id ảnh" fullWidth size="small" sx={popupFieldSx} helperText="Dán link ảnh công khai hoặc file_id ảnh từ Telegram. Để trống nếu chỉ muốn đăng text." />
                  <TextField className="field wide" label="Nội dung gửi Telegram" value={channelPostForm.content} onChange={(event) => setChannelPostForm({ ...channelPostForm, content: event.target.value })} placeholder="Soạn nội dung bài đăng..." fullWidth multiline minRows={9} sx={popupFieldSx} />
                  <TextField className="field wide" label="Nút inline" value={channelPostForm.buttons_text} onChange={(event) => setChannelPostForm({ ...channelPostForm, buttons_text: event.target.value })} placeholder={"Tên nút | https://link.com\\nNút 1 | https://a.com || Nút 2 | https://b.com"} fullWidth multiline minRows={4} sx={popupFieldSx} helperText="Mỗi dòng là một hàng nút. Dùng dấu || để đặt nhiều nút cùng hàng." />
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="channel-post-parse-label">Định dạng</InputLabel>
                    <Select labelId="channel-post-parse-label" label="Định dạng" value={channelPostForm.parse_mode} onChange={(event) => setChannelPostForm({ ...channelPostForm, parse_mode: event.target.value })} sx={popupSelectSx}>
                      <MenuItem value="HTML">HTML</MenuItem>
                      <MenuItem value="NONE">Text thường</MenuItem>
                    </Select>
                  </FormControl>
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="channel-post-preview-label">Ẩn preview link</InputLabel>
                    <Select labelId="channel-post-preview-label" label="Ẩn preview link" value={channelPostForm.disable_web_page_preview ? "ON" : "OFF"} onChange={(event) => setChannelPostForm({ ...channelPostForm, disable_web_page_preview: event.target.value === "ON" })} sx={popupSelectSx}>
                      <MenuItem value="OFF">Không</MenuItem>
                      <MenuItem value="ON">Có</MenuItem>
                    </Select>
                  </FormControl>
                  <TextField className="field" label="Hẹn giờ đăng" type="datetime-local" value={channelPostForm.scheduled_at} onChange={(event) => setChannelPostForm({ ...channelPostForm, scheduled_at: event.target.value })} fullWidth size="small" sx={popupFieldSx} slotProps={{ inputLabel: { shrink: true } }} />
                  <TextField className="field" label="Hẹn giờ xóa" type="datetime-local" value={channelPostForm.delete_at} onChange={(event) => setChannelPostForm({ ...channelPostForm, delete_at: event.target.value })} fullWidth size="small" sx={popupFieldSx} slotProps={{ inputLabel: { shrink: true } }} />
                  <FormControlLabel
                    sx={{ gridColumn: "span 1", alignItems: "flex-start", border: 1, borderColor: "divider", borderRadius: 4, px: 1.5, py: 1, m: 0 }}
                    control={<Checkbox checked={Boolean(channelPostForm.repeat_daily)} onChange={(event) => setChannelPostForm({ ...channelPostForm, repeat_daily: event.target.checked })} />}
                    label={<Box><strong>Lặp lại mỗi ngày</strong><Box className="muted">Sau khi xóa sẽ tự dời sang ngày kế tiếp.</Box></Box>}
                  />
                  <TextField className="field wide" label="Ghi chú" value={channelPostForm.notes} onChange={(event) => setChannelPostForm({ ...channelPostForm, notes: event.target.value })} placeholder="Ghi chú nội bộ nếu cần" fullWidth size="small" sx={popupFieldSx} />
              </Box>
              <Box sx={{ display: "grid", gap: 1.25, px: 2, pb: 2, pt: 1.5, borderTop: 1, borderColor: "divider" }}>
                  <div><Eye size={16} /> <strong>Preview nhanh</strong></div>
                  <pre>{channelPostForm.image_ref ? `[Ảnh] ${channelPostForm.image_ref}\n\n` : ""}{channelPostForm.content || "Nội dung bài đăng sẽ hiển thị ở đây."}</pre>
                  <small>Nút: {channelPostForm.buttons_text ? channelPostForm.buttons_text.split(/\n+/).filter(Boolean).length : 0} hàng • Ảnh: {channelPostForm.image_ref ? "Có" : "Không"} • Đăng: {dateTimePreviewText(channelPostForm.scheduled_at, "gửi ngay")} • Xóa: {dateTimePreviewText(channelPostForm.delete_at, "không tự xóa")} • {channelPostForm.repeat_daily ? "Lặp ngày" : "Không lặp"}</small>
                  <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 1.25 }}>
                    {channelPostForm.repeat_daily ? <Chip size="small" label="Bật lặp ngày" variant="outlined" sx={statusChipSx("success")} /> : <Chip size="small" label="Không lặp" variant="outlined" sx={statusChipSx("muted")} />}
                    {channelPostForm.delete_at ? <Chip size="small" label="Có giờ xóa" variant="outlined" sx={statusChipSx("warning")} /> : <Chip size="small" label="Không tự xóa" variant="outlined" sx={statusChipSx("muted")} />}
                  </Box>
              </Box>
                {channelEvents.length ? (
                  <Box sx={{ display: "grid", gap: 1.25, px: 2, pb: 2 }}>
                    <strong>Nhật ký bài đăng</strong>
                    {channelEvents.slice(0, 5).map((event) => (
                      <Box key={event.id} sx={{ display: "grid", gap: 1, gridTemplateColumns: "130px 170px minmax(0, 1fr)", py: 1 }}>
                        <span>{dateText(event.created_at)}</span><b>{event.event_type}</b><em>{event.message || "-"}</em>
                      </Box>
                    ))}
                  </Box>
                ) : null}
              <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider" }}>
                <Button variant="outlined" onClick={() => setChannelPostModalOpen(false)}>Đóng</Button>
                <Button variant="outlined" onClick={() => saveChannelPost("draft")} disabled={saving.startsWith("channel-post")} startIcon={<Save size={16} />}>{channelPostForm.id ? "Lưu thay đổi" : "Lưu nháp"}</Button>
                <Button variant="outlined" onClick={() => saveChannelPost("schedule")} disabled={saving.startsWith("channel-post") || !channelPostForm.scheduled_at} startIcon={<CalendarClock size={16} />}>Lên lịch</Button>
                <Button variant="contained" onClick={() => saveChannelPost("send_now")} disabled={saving.startsWith("channel-post")} startIcon={saving.startsWith("channel-post") ? <Loader2 size={16} className="spin" /> : <Send size={16} />}>Đăng ngay</Button>
              </Stack>
          </MuiDialogShell>
        ) : null}

        {renewalSettingsOpen ? (
          <SettingsConfigModal title="Cài đặt gia hạn" subtitle="Bật/tắt nhắc gia hạn, báo hết hạn và nội dung tin nhắn liên quan đến hạn thành viên." fields={RENEWAL_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} onClose={() => setRenewalSettingsOpen(false)} />
        ) : null}

        {securitySettingsOpen ? (
          <SettingsConfigModal title="Bảo mật bot và coupon" subtitle="Chặn seller, ẩn menu nhập mã và chống dò coupon. Mặc định khách chỉ cần nhắn mã bắt đầu bằng HANGCU_." fields={SECURITY_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} onClose={() => setSecuritySettingsOpen(false)} />
        ) : null}

        {systemSettingsOpen ? (
          <SettingsConfigModal title="Cài đặt hệ thống" subtitle="Các chu kỳ worker, cleanup và retention đang chạy trên backend Render." fields={SYSTEM_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} onClose={() => setSystemSettingsOpen(false)} />
        ) : null}

        {orderSettingsOpen ? (
          <SettingsConfigModal
            title="Cài đặt đơn thủ công"
            subtitle="Chỉnh template nội dung gen link và nội dung hỗ trợ đi kèm cho đơn thủ công."
            fields={ORDER_FIELDS}
            values={fieldValues}
            setValues={setFieldValues}
            onSave={saveFields}
            onClose={() => setOrderSettingsOpen(false)}
          />
        ) : null}

        {manualOrderModalOpen ? (
          <MuiDialogShell open title="Tạo đơn thủ công" subtitle="Nhập thông tin khách, tạo order PAID và gen link join group." onClose={() => setManualOrderModalOpen(false)} maxWidth="lg">
              <Box sx={{ display: "grid", gap: 1.5 }}>
                <TextField label="Telegram ID" value={manualOrderForm.telegram_user_id} onChange={(event) => setManualOrderForm({ ...manualOrderForm, telegram_user_id: event.target.value })} placeholder="VD: 7344961485" size="small" helperText="ID số của khách. Không dùng username @." />
                <TextField label="Tên khách" value={manualOrderForm.full_name} onChange={(event) => setManualOrderForm({ ...manualOrderForm, full_name: event.target.value })} placeholder="Tên hiển thị để dễ quản lý" size="small" />
                <TextField select label="Gói cấp cho khách" value={manualOrderForm.plan_key} onChange={(event) => changeManualPlanKey(event.target.value)} size="small">
                  {manualPlanKeyOptions.map((item) => <MenuItem key={item} value={item}>{item === "CUSTOM" ? "Tự nhập tên gói" : planOptionLabel(item)}</MenuItem>)}
                </TextField>
                <TextField label="Tên gói lưu vào đơn" value={manualOrderForm.plan_key === "CUSTOM" ? manualOrderForm.plan_name : manualPlanNameFromKey(manualOrderForm.plan_key)} onChange={(event) => setManualOrderForm({ ...manualOrderForm, plan_name: event.target.value, plan_key: "CUSTOM" })} placeholder="VD: VIP 30 Ngày - Hang Cú Prime" size="small" sx={{ gridColumn: "1 / -1" }} helperText="Với gói tự nhập, nên chứa đúng tên group đang cấu hình trong Nhóm & giá." />
                <TextField label="Số tiền" value={manualOrderForm.amount} onChange={(event) => setManualOrderForm({ ...manualOrderForm, amount: event.target.value })} placeholder="0" inputMode="decimal" size="small" helperText="Nhập số thực. VNĐ thường không có thập phân, USD / crypto có thể có." />
                <TextField select label="Tiền tệ" value={manualOrderForm.payment_currency} onChange={(event) => setManualOrderForm({ ...manualOrderForm, payment_currency: event.target.value })} size="small">
                  <MenuItem value="VND">VNĐ</MenuItem>
                  <MenuItem value="USD">USD</MenuItem>
                  <MenuItem value="USDT">USDT / Crypto</MenuItem>
                </TextField>
                <TextField select label="Phương thức thanh toán" value={manualOrderForm.payment_provider} onChange={(event) => setManualOrderForm({ ...manualOrderForm, payment_provider: event.target.value })} size="small" helperText="Chỉ để ghi nhận báo cáo và đối soát, không đổi flow cấp quyền chính.">
                  <MenuItem value="MANUAL">Thủ công</MenuItem>
                  <MenuItem value="PAYOS">PayOS / VietQR</MenuItem>
                  <MenuItem value="PAYPAL">PayPal</MenuItem>
                  <MenuItem value="NOWPAYMENTS">NOWPayments</MenuItem>
                  <MenuItem value="TRON_USDT">USDT TRC20</MenuItem>
                </TextField>
                <TextField select label="Kiểu hết hạn" value={manualOrderForm.expiry_mode} onChange={(event) => setManualOrderForm({ ...manualOrderForm, expiry_mode: event.target.value, expire_at: event.target.value === "days" ? "" : manualOrderForm.expire_at })} size="small" helperText="Chọn 1 cách duy nhất: theo số ngày hoặc ngày cụ thể." sx={{ gridColumn: "1 / -1" }}>
                  <MenuItem value="days">Theo số ngày</MenuItem>
                  <MenuItem value="date">Ngày cụ thể</MenuItem>
                </TextField>
                {manualOrderForm.expiry_mode === "days" ? (
                  <TextField label="Số ngày sử dụng" value={manualOrderForm.duration_days} onChange={(event) => setManualOrderForm({ ...manualOrderForm, duration_days: event.target.value })} placeholder="30" inputMode="numeric" size="small" helperText={manualExpiryPreview()} />
                ) : (
                  <TextField label="Ngày hết hạn cụ thể" type="datetime-local" value={manualOrderForm.expire_at} onChange={(event) => setManualOrderForm({ ...manualOrderForm, expire_at: event.target.value })} size="small" slotProps={{ inputLabel: { shrink: true } }} helperText={manualExpiryPreview()} />
                )}
                <TextField label="Coupon / ghi chú mã" value={manualOrderForm.coupon_code} onChange={(event) => setManualOrderForm({ ...manualOrderForm, coupon_code: event.target.value.toUpperCase() })} placeholder="VD: MANUAL_ADMIN" size="small" sx={{ gridColumn: "1 / -1" }} />
              </Box>
              <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider" }}>
                <Button variant="outlined" onClick={() => setManualOrderModalOpen(false)}>Đóng</Button>
                <Button variant="contained" onClick={saveManualOrder} disabled={saving === "manual-order"} startIcon={saving === "manual-order" ? <Loader2 size={18} className="spin" /> : <Plus size={18} />}>Tạo đơn & gen link</Button>
              </Stack>
                {manualOrderResult ? (
                  <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" } }}>
                    <TextField
                      className="field wide"
                      label="Tin nhắn hoàn chỉnh"
                      value={stripHtml(manualOrderResult.manual_order_text || manualOrderResult.links_text || "")}
                      slotProps={{ input: { readOnly: true } }}
                      fullWidth
                      multiline
                      minRows={10}
                      sx={popupFieldSx}
                    />
                    <TextField
                      label={manualOrderResult.bot_link_title || "Link kích hoạt"}
                      value={manualOrderResult.activation_url || ""}
                      slotProps={{ input: { readOnly: true } }}
                      fullWidth
                      multiline
                      minRows={4}
                      sx={popupFieldSx}
                    />
                    <Box sx={{ gridColumn: "1 / -1" }}>
                      <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-start" }}>
                        <Button variant="outlined" onClick={() => navigator.clipboard.writeText(manualOrderResult.activation_url || "")}>{manualOrderResult.bot_link_button_label || "Copy link bot"}</Button>
                        <Button
                          variant="outlined"
                          onClick={() => {
                            if (!manualOrderResult) return;
                            navigator.clipboard.writeText(stripHtml(manualOrderResult.manual_order_text || manualOrderResult.links_text || ""));
                            showNotice("ok", "Đã copy toàn bộ nội dung hiển thị.");
                          }}
                        >
                          Copy toàn bộ nội dung
                        </Button>
                      </Stack>
                      {manualOrderResult.support_error ? <small className="danger-text">Group hỗ trợ chưa tạo được link: {manualOrderResult.support_error}</small> : <small>Đơn đã được ghi PAID. Khách bấm link bot để nhận link join group riêng.</small>}
                    </Box>
                  </Box>
                ) : null}
          </MuiDialogShell>
        ) : null}

        {customerModalOpen && selectedCustomer ? (
          <MuiDialogShell open title={selectedCustomer.name} subtitle={`Telegram ID: ${selectedCustomer.id}`} onClose={() => setCustomerModalOpen(false)} maxWidth="xl">
              <Box sx={{ display: "flex", gap: 2.5, alignItems: "stretch", minHeight: "72vh", flexDirection: { xs: "column", md: "row" } }}>
                <Box
                  component="aside"
                  sx={{
                    width: { xs: "100%", md: 300 },
                    flexShrink: 0,
                    display: "flex",
                    flexDirection: "column",
                    gap: 2,
                    p: 2,
                    border: 1,
                    borderColor: "divider",
                    bgcolor: "background.paper",
                    borderRadius: 4,
                    boxShadow: "0 10px 30px rgba(15, 23, 42, 0.06)",
                  }}
                >
                  <Box sx={{ p: 1.5, borderRadius: 4, bgcolor: "#f8fafb", border: 1, borderColor: "divider" }}>
                    {(() => {
                      const customerStatusTone = selectedCustomer.statusColor === "default" ? "muted" : (selectedCustomer.statusColor as "success" | "warning" | "error" | "muted" | "purple");
                      return (
                    <Chip
                      size="small"
                      label={selectedCustomer.statusLabel}
                      variant="outlined"
                      sx={{ ...statusChipSx(customerStatusTone), mb: 1 }}
                    />
                      );
                    })()}
                    <Stack spacing={1.25}>
                      <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}>
                        <Typography variant="body2" color="text.secondary">Đơn PAID</Typography>
                        <Typography sx={{ fontWeight: 800 }}>{selectedCustomer.paidOrders.length}</Typography>
                      </Box>
                      <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}>
                        <Typography variant="body2" color="text.secondary">Gói active</Typography>
                        <Typography sx={{ fontWeight: 800 }}>{selectedCustomer.activeOrders.length}</Typography>
                      </Box>
                      <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}>
                        <Typography variant="body2" color="text.secondary">Hạn gần nhất</Typography>
        <Typography sx={{ fontWeight: 800 }}>{dateTextShort(selectedCustomer.latestExpire)}</Typography>
                      </Box>
                      <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}>
                        <Typography variant="body2" color="text.secondary">Tổng tiền</Typography>
                        <Typography sx={{ fontWeight: 800 }}>{money(selectedCustomer.revenue)}</Typography>
                      </Box>
                    </Stack>
                    <Box sx={{ mt: 1.5, p: 1.5, borderRadius: 4, bgcolor: "#f0f7ff", border: 1, borderColor: "rgba(37,99,235,0.16)" }}>
                      <Typography variant="body2" color="text.secondary">Gia hạn nhanh</Typography>
                      <Typography sx={{ fontWeight: 800, mt: 0.25 }}>{selectedCustomerRenewTargetOrder ? `${selectedCustomerRenewTargetOrder.order_id} • ${selectedCustomerRenewTargetOrder.plan_name}` : "Chưa có đơn phù hợp"}</Typography>
                      <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: "center" }}>
                        <Button
                          variant="contained"
                          size="small"
                          onClick={openCustomerRenewModal}
                          sx={{ borderRadius: 999, minWidth: 96 }}
                        >
                          Tạo gia hạn
                        </Button>
                      </Stack>
                    </Box>
                    <Box sx={{ mt: 1.5, display: "flex", flexWrap: "wrap", gap: 0.75 }}>
                      {selectedCustomer.groups.length ? renderLimitedTags(selectedCustomer.groups, "g") : null}
                      {selectedCustomer.coupons.length ? renderLimitedTags(selectedCustomer.coupons.map((item) => `Coupon: ${item}`), "c") : null}
                    </Box>
                  </Box>

                  <Tabs
                    orientation="vertical"
                    value={customerDetailTab}
                    onChange={(_, next) => setCustomerDetailTab(next)}
                    textColor="inherit"
                    indicatorColor="primary"
                    sx={customerPopupTabSx}
                  >
                    <Tab value="orders" label="Đơn hàng" />
                    <Tab value="groups" label="Nhóm" />
                    <Tab value="timeline" label="Theo dõi" />
                  </Tabs>
                </Box>

              <Box component="section" sx={{ flex: 1, minWidth: 0, p: 0.25 }}>
                {customerDetailTab === "orders" ? (
                  <>
                    <Tabs
                      value={customerOrderTab}
                      onChange={(_, next) => setCustomerOrderTab(next)}
                      variant="scrollable"
                      scrollButtons="auto"
                      textColor="inherit"
                      indicatorColor="primary"
                      sx={{ ...customerPopupTabSx, mb: 2 }}
                    >
                      <Tab value="all" label={`Tất cả (${selectedCustomerOrders.length})`} />
                      <Tab value="active" label={`Active (${selectedCustomerOrders.filter((item) => isOrderActive(item)).length})`} />
                      <Tab value="expiring" label={`Sắp hết hạn (${selectedCustomerOrders.filter((item) => !isOrderActive(item) && daysUntil(item.expire_at) >= 0 && daysUntil(item.expire_at) <= reminderNoticeDays).length})`} />
                      <Tab value="lifetime" label={`Trọn đời (${selectedCustomerOrders.filter((item) => isLifetimeText(item.plan_name)).length})`} />
                      <Tab value="paid" label={`PAID (${selectedCustomerOrders.filter((item) => item.status === "PAID").length})`} />
                      <Tab value="expired" label={`Expired (${selectedCustomerOrders.filter((item) => item.status === "EXPIRED" || (item.status === "PAID" && !isOrderActive(item) && !isLifetimeText(item.plan_name))).length})`} />
                    </Tabs>
                    <CustomerOrdersTable
                      orders={selectedCustomerOrders.filter((item) => {
                        if (customerOrderTab === "active") return isOrderActive(item);
                        if (customerOrderTab === "expiring") return !isOrderActive(item) && daysUntil(item.expire_at) >= 0 && daysUntil(item.expire_at) <= reminderNoticeDays;
                        if (customerOrderTab === "lifetime") return isLifetimeText(item.plan_name);
                        if (customerOrderTab === "paid") return item.status === "PAID";
                        if (customerOrderTab === "expired") return item.status === "EXPIRED" || (item.status === "PAID" && !isOrderActive(item) && !isLifetimeText(item.plan_name));
                        return true;
                      })}
                      saving={saving}
                      onExpireChange={changeOrderExpire}
                      onPlanChange={changeOrderPlan}
                      onStatusChange={changeOrderStatus}
                    />
                  </>
                ) : null}
                {customerDetailTab === "groups" ? (
                    <>
                    <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" }, mb: 2 }}>
                      <Metric label="Group active" value={String(selectedCustomer.activeOrders.length)} icon={<Users size={16} />} />
                      <Metric label="Group còn trong hệ thống" value={selectedCustomerActiveGroups.length ? String(selectedCustomerActiveGroups.length) : "0"} icon={<ShieldCheck size={16} />} />
                      <Metric label="Audit group" value={String(selectedCustomerGroupAuditSummary.total)} icon={<ClipboardList size={16} />} />
                      <Metric label="Có live check" value={String(selectedCustomerGroupAuditSummary.liveChecked)} icon={<Eye size={16} />} />
                    </Box>
                    <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" }, mb: 2 }}>
                      <Metric label="Group giữ quyền" value={String(selectedCustomerGroupAuditSummary.retained)} icon={<CheckCircle2 size={16} />} />
                      <Metric label="Group đã kick" value={String(selectedCustomerGroupAuditSummary.kicked)} icon={<XCircle size={16} />} />
                      <Metric label="Nhóm active hiện tại" value={String(selectedCustomerGroupAuditSummary.currentGroups)} icon={<Users size={16} />} />
                      <Metric label="Có dữ liệu lịch sử" value={String(selectedCustomerGroupAuditSummary.total > 0 ? 1 : 0)} icon={<Activity size={16} />} />
                    </Box>
                    <section className="panel nested-panel">
                      <PanelHead title="Nhóm còn active" subtitle="Nhóm mà user vẫn đang có quyền theo dữ liệu đơn hàng hiện tại." />
                      {selectedCustomerActiveGroups.length ? (
                        <div className="tag-list">
                          {selectedCustomerActiveGroups.map((group) => <span key={group}>{group}</span>)}
                        </div>
                      ) : <div className="empty-card">Chưa có nhóm active nào.</div>}
                    </section>
                    <section className="panel nested-panel">
                      <PanelHead title="Dấu vết group" subtitle="Audit mà bot ghi nhận được từ quyền hiện tại, live check và trạng thái kick/giữ quyền." />
                      {selectedCustomerGroupAuditRows.length ? (
                        <SimpleTable
                          headers={["Trạng thái", "Group", "Gói / Đơn", "Hạn dùng", "Live", "Chi tiết"]}
                          rows={selectedCustomerGroupAuditRows}
                        />
                      ) : (
                        <div className="empty-card">Chưa có audit group nào cho khách này.</div>
                      )}
                    </section>
                  </>
                ) : null}
                {customerDetailTab === "timeline" ? (
                  <>
                    <Tabs
                      value={customerTimelineSubTab}
                      onChange={(_, next) => setCustomerTimelineSubTab(next)}
                      variant="scrollable"
                      scrollButtons="auto"
                      textColor="inherit"
                      indicatorColor="primary"
                      sx={{ ...customerPopupTabSx, mb: 2 }}
                    >
                      <Tab value="all" label="Tất cả" />
                      <Tab value="joinLeft" label="Join/Left" />
                      <Tab value="role" label="Role" />
                      <Tab value="restricted" label="Restricted" />
                      <Tab value="kickMute" label="Kick/Mute" />
                      <Tab value="orders" label="Order timeline" />
                    </Tabs>
                    <div className="grid">
                      <Metric label="Sự kiện support" value={String(selectedCustomerTimelineCounts.total)} icon={<Activity size={16} />} />
                      <Metric label="Join" value={String(selectedCustomerTimelineCounts.joined)} icon={<Plus size={16} />} />
                      <Metric label="Left" value={String(selectedCustomerTimelineCounts.left)} icon={<TrendingUp size={16} />} />
                      <Metric label="Kick / mute" value={`${selectedCustomerTimelineCounts.kicked} / ${selectedCustomerTimelineCounts.muted}`} icon={<XCircle size={16} />} />
                    </div>
                    <section className="panel nested-panel">
                      <PanelHead title="Timeline group" subtitle="Lịch sử join / out / mute / kick / nhắc gia hạn của khách theo dữ liệu bot theo dõi được." />
                      <SimpleTable
                        headers={["Sự kiện", "Group", "Đơn", "Giờ", "Chi tiết"]}
                        rows={selectedCustomerTimelineRows.slice(0, 12)}
                      />
                    </section>
                  </>
                  ) : null}
              </Box>
              </Box>
          </MuiDialogShell>
        ) : null}

        {customerRenewModalOpen && selectedCustomer ? (
          <MuiDialogShell open title="Tạo gia hạn" subtitle={`Khách: ${selectedCustomer.name} • Telegram ID: ${selectedCustomer.id}`} onClose={() => setCustomerRenewModalOpen(false)} maxWidth="sm">
            <Box sx={{ display: "grid", gap: 1.5 }}>
              <TextField
                select
                label="Đơn / Gói cần gia hạn"
                value={customerRenewForm.plan_name}
                onChange={(event) => {
                  const nextPlan = event.target.value;
                  const matchedOrder = selectedCustomer.paidOrders.find((item) => item.plan_name === nextPlan) || null;
                  setCustomerRenewForm((current) => ({
                    ...current,
                    order_id: matchedOrder?.order_id || "",
                    plan_name: nextPlan,
                    amount: matchedOrder ? String(matchedOrder.amount || "") : current.amount,
                    duration_days: isLifetimeText(nextPlan) ? "0" : current.duration_days || "30",
                    payment_currency: String(matchedOrder?.payment_currency || current.payment_currency || "VND").toUpperCase(),
                    payment_provider: String(matchedOrder?.payment_provider || current.payment_provider || "MANUAL").toUpperCase(),
                  }));
                }}
                fullWidth
                size="small"
              >
                {selectedCustomerRenewPlanOptions.map((plan) => <MenuItem key={plan} value={plan}>{plan}</MenuItem>)}
              </TextField>
              <TextField
                label="Số tiền thanh toán"
                value={customerRenewForm.amount}
                onChange={(event) => setCustomerRenewForm((current) => ({ ...current, amount: event.target.value }))}
                placeholder="99000"
                fullWidth
                size="small"
              />
              <TextField
                label="Số ngày gia hạn"
                type="number"
                value={customerRenewForm.duration_days}
                onChange={(event) => setCustomerRenewForm((current) => ({ ...current, duration_days: event.target.value }))}
                slotProps={{ htmlInput: { min: 1, step: 1 } }}
                disabled={isLifetimeText(customerRenewForm.plan_name)}
                helperText={isLifetimeText(customerRenewForm.plan_name) ? "Gói trọn đời không cần nhập số ngày." : "Sẽ tạo đơn mới và cộng hạn từ đơn này."}
                fullWidth
                size="small"
              />
              <Stack direction="row" spacing={1}>
                <TextField
                  select
                  label="Tiền tệ"
                  value={customerRenewForm.payment_currency}
                  onChange={(event) => setCustomerRenewForm((current) => ({ ...current, payment_currency: event.target.value }))}
                  fullWidth
                  size="small"
                >
                  <MenuItem value="VND">VND</MenuItem>
                  <MenuItem value="USD">USD</MenuItem>
                  <MenuItem value="USDT">USDT</MenuItem>
                </TextField>
                <TextField
                  select
                  label="Phương thức"
                  value={customerRenewForm.payment_provider}
                  onChange={(event) => setCustomerRenewForm((current) => ({ ...current, payment_provider: event.target.value }))}
                  fullWidth
                  size="small"
                >
                  <MenuItem value="MANUAL">MANUAL</MenuItem>
                  <MenuItem value="PAYOS">PAYOS</MenuItem>
                  <MenuItem value="PAYPAL">PAYPAL</MenuItem>
                  <MenuItem value="NOWPAYMENTS">NOWPAYMENTS</MenuItem>
                  <MenuItem value="BINANCE_PAY">BINANCE_PAY</MenuItem>
                  <MenuItem value="TRON_USDT">TRON_USDT</MenuItem>
                </TextField>
              </Stack>
              <div className="modal-actions">
                <Button variant="outlined" onClick={() => setCustomerRenewModalOpen(false)}>Huỷ</Button>
                <Button variant="contained" onClick={saveCustomerRenewal}>Tạo đơn gia hạn</Button>
              </div>
            </Box>
          </MuiDialogShell>
        ) : null}
      </Box>
      </Box>
    </Box>
  );
}

function HealthItem({ ok, title, detail }: { ok: boolean; title: string; detail: string }) {
  return (
    <Card
      variant="outlined"
      sx={{
        height: "100%",
        borderRadius: 4,
        boxShadow: "0 12px 26px rgba(15, 23, 42, 0.05)",
        bgcolor: ok ? "rgba(236,253,245,0.9)" : "rgba(254,242,242,0.9)",
        borderColor: ok ? "rgba(167,243,208,0.9)" : "rgba(254,202,202,0.9)",
      }}
    >
      <CardContent sx={{ display: "flex", gap: 1.5, alignItems: "flex-start", py: 1.75, "&:last-child": { pb: 1.75 } }}>
        <Box sx={{ width: 34, height: 34, borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: ok ? "rgba(16,185,129,0.12)" : "rgba(239,68,68,0.12)", color: ok ? "success.main" : "error.main" }}>
          {ok ? <CheckCircle2 size={18} /> : <XCircle size={18} />}
        </Box>
        <Box sx={{ minWidth: 0 }}>
          <Typography sx={{ fontWeight: 800, lineHeight: 1.2 }}>{title}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.35, lineHeight: 1.45, wordBreak: "break-word" }}>
            {detail}
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
}

function Info({ label, value, icon }: { label: string; value: string; icon?: ReactNode }) {
  return (
    <Card
      variant="outlined"
      sx={{
        borderRadius: 4,
        boxShadow: "0 10px 24px rgba(15, 23, 42, 0.04)",
      }}
    >
      <CardContent sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2, py: 1.5, "&:last-child": { pb: 1.5 } }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.25, minWidth: 0 }}>
          {icon ? <Box sx={{ width: 32, height: 32, borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: "rgba(37,99,235,0.08)", color: "primary.main" }}>{icon}</Box> : null}
          <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 700, lineHeight: 1.2 }}>
            {label}
          </Typography>
        </Box>
        <Typography sx={{ fontWeight: 800, letterSpacing: "-0.02em" }}>{value}</Typography>
      </CardContent>
    </Card>
  );
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
          <ButtonBase
            key={field.key}
            onClick={() => openField(field)}
            sx={{
              width: "100%",
              display: "grid",
              gridTemplateColumns: "minmax(0, 1fr) auto",
              gap: 1,
              alignItems: "start",
              px: 2,
              py: 1.5,
              borderRadius: 4,
              border: 1,
              borderColor: "divider",
              bgcolor: "background.paper",
              textAlign: "left",
            }}
          >
            <Box sx={{ display: "grid", gap: 0.25, minWidth: 0 }}>
              <strong>{field.label}</strong>
              <span className="muted">{field.help}</span>
            </Box>
            <Pencil size={17} />
            <Box
              sx={{
                gridColumn: "1 / -1",
                minWidth: 0,
                fontWeight: 700,
                color: values[field.key] ? "text.primary" : "text.secondary",
                lineHeight: 1.45,
                overflowWrap: "anywhere",
              }}
            >
              {field.kind === "select"
                ? field.options?.find((item) => item.value === (values[field.key] || field.placeholder))?.label || values[field.key] || field.placeholder
                : values[field.key] || "Chưa thiết lập"}
            </Box>
          </ButtonBase>
        ))}
      </div>
      {editingField ? (
        <MuiDialogShell
          open
          title={editingField.label}
          subtitle={editingField.help}
          onClose={() => setEditingField(null)}
          maxWidth="sm"
        >
          <Stack spacing={1.5}>
            <Box sx={{ display: "grid", gap: 0.75 }}>
              <Typography variant="subtitle2" sx={{ fontWeight: 800 }}>
                Giá trị
              </Typography>
              {editingField.kind === "textarea" ? (
                <TextField
                  autoFocus
                  multiline
                  minRows={5}
                  value={draftValue}
                  onChange={(event) => setDraftValue(event.target.value)}
                  placeholder={editingField.placeholder}
                  fullWidth
                  sx={popupFieldSx}
                />
              ) : editingField.kind === "select" ? (
                <TextField
                  select
                  autoFocus
                  value={draftValue || editingField.placeholder}
                  onChange={(event) => setDraftValue(event.target.value)}
                  fullWidth
                  sx={popupFieldSx}
                >
                  {(editingField.options || []).map((item) => (
                    <MenuItem key={item.value} value={item.value}>
                      {item.label}
                    </MenuItem>
                  ))}
                </TextField>
              ) : (
                <TextField
                  autoFocus
                  value={draftValue}
                  onChange={(event) => setDraftValue(event.target.value)}
                  placeholder={editingField.placeholder}
                  fullWidth
                  sx={popupFieldSx}
                />
              )}
            </Box>
            <Typography variant="caption" color="text.secondary">
              Key kỹ thuật: {editingField.key}
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", pt: 1 }}>
            <Button variant="outlined" onClick={() => setEditingField(null)}>
              Huỷ
            </Button>
            <Button
              variant="contained"
              onClick={saveField}
              disabled={savingField}
              startIcon={savingField ? <Loader2 size={16} className="spin" /> : <Save size={16} />}
            >
              Lưu thay đổi
            </Button>
          </Stack>
        </MuiDialogShell>
      ) : null}
    </section>
  );
}

function SettingsConfigModal({ title, subtitle, fields, values, setValues, onSave, onClose }: { title: string; subtitle: string; fields: ConfigField[]; values: Record<string, string>; setValues: (values: Record<string, string>) => void; onSave: (fields: ConfigField[], values: Record<string, string>) => Promise<boolean>; onClose: () => void }) {
  return (
    <MuiDialogShell open title={title} subtitle={subtitle} onClose={onClose} maxWidth="lg">
      <ConfigEditor title={title} subtitle={subtitle} fields={fields} values={values} setValues={setValues} onSave={onSave} />
      <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", pt: 1 }}>
        <Button variant="outlined" onClick={onClose}>Đóng</Button>
      </Stack>
    </MuiDialogShell>
  );
}

function CustomerOrdersTable({ orders, saving, onExpireChange, onPlanChange, onStatusChange }: { orders: Order[]; saving: string; onExpireChange: (orderId: string, expireAt: string) => void; onPlanChange: (orderId: string, planName: string) => void; onStatusChange: (orderId: string, status: string) => void }) {
  const sorted = [...orders].sort((a, b) => {
    const rank = (order: Order) => {
      const status = String(order.status || "").toUpperCase();
      if (status === "PAID") return 0;
      if (status === "PENDING") return 1;
      if (status === "CANCELLED") return 3;
      if (status === "EXPIRED") return 4;
      return 2;
    };
    const statusDiff = rank(a) - rank(b);
    if (statusDiff !== 0) return statusDiff;
    const activeDiff = Number(isOrderActive(b)) - Number(isOrderActive(a));
    if (activeDiff !== 0) return activeDiff;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
  const [expandedOrders, setExpandedOrders] = useState<Record<string, boolean>>({});
  const statusChip = (order: Order) => {
    const normalized = String(order.status || "").toUpperCase();
    const active = isOrderActive(order);
    const expiringSoon = daysUntil(order.expire_at) >= 0 && daysUntil(order.expire_at) <= 3;
    return <Chip size="small" label={String(order.status || "-")} variant="outlined" sx={customerOrderStateChipSx(normalized, active, expiringSoon)} />;
  };
  return (
    <Stack spacing={1.5}>
      {sorted.map((order) => (
        <Card
          key={order.order_id}
          variant="outlined"
          sx={{
            borderRadius: 2,
            overflow: "hidden",
            position: "relative",
            transition: "transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease",
            "&:hover": {
              transform: "translateY(-2px)",
              boxShadow: "0 18px 36px rgba(15, 23, 42, 0.10)",
              borderColor: "rgba(37, 99, 235, 0.24)",
            },
            backgroundImage: "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,0.95) 100%)",
            boxShadow: "0 14px 30px rgba(15, 23, 42, 0.06)",
          }}
        >
          <CardContent sx={{ display: "grid", gap: 1.75, "&:last-child": { pb: 2 } }}>
            <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 2 }}>
              <Box>
                <Typography sx={{ fontWeight: 800, lineHeight: 1.2 }}>{order.order_id}</Typography>
                <Typography variant="body2" color="text.secondary">{dateText(order.created_at)}</Typography>
              </Box>
              <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, alignItems: "center", justifyContent: "flex-end" }}>
                <Chip size="small" label={currencyLabel(inferOrderCurrency(order))} variant="outlined" sx={statusChipSx("purple")} />
                <Chip size="small" label={providerLabel(inferOrderProvider(order))} variant="outlined" sx={statusChipSx("warning")} />
                <Button variant={expandedOrders[order.order_id] ? "contained" : "outlined"} color="inherit" size="small" onClick={() => setExpandedOrders((current) => ({ ...current, [order.order_id]: !current[order.order_id] }))} sx={{ fontWeight: 700, textTransform: "none", borderRadius: 4, minWidth: 100 }}>
                  {expandedOrders[order.order_id] ? "Thu gọn" : "Chi tiết"}
                </Button>
              </Box>
            </Box>

            <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" } }}>
              <Box sx={customerInnerCardSx}>
                <Typography variant="body2" color="text.secondary">Gói / Group</Typography>
                <Typography sx={{ fontWeight: 800, mt: 0.5 }}>{order.plan_name}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{groupNamesForOrder(order).join(", ") || orderPlanKind(order)}</Typography>
              </Box>
              <Box sx={customerInnerCardSx}>
                <Typography variant="body2" color="text.secondary">Coupon</Typography>
                <Typography sx={{ fontWeight: 800, mt: 0.5 }}>{orderCouponCode(order) || "-"}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{orderCouponCode(order) ? (Number(order.amount || 0) === 0 ? "Kích hoạt miễn phí" : money(order.coupon_discount_amount || 0)) : "Không có coupon"}</Typography>
              </Box>
              <Box sx={customerInnerCardSx}>
                <Typography variant="body2" color="text.secondary">Hạn dùng</Typography>
                <Typography sx={{ fontWeight: 800, mt: 0.5 }}>{dateText(order.expire_at)}</Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: "wrap" }}>
                  {isLifetimeText(order.plan_name) ? <Chip size="small" label="Trọn đời" variant="outlined" sx={statusChipSx("purple")} /> : null}
                  {isOrderActive(order) ? <Chip size="small" label="Đang active" variant="outlined" sx={statusChipSx("success")} /> : daysUntil(order.expire_at) >= 0 && daysUntil(order.expire_at) <= 3 ? <Chip size="small" label="Sắp hết hạn" variant="outlined" sx={statusChipSx("warning")} /> : <Chip size="small" label="Hết hạn" variant="outlined" sx={{ ...statusChipSx("muted"), bgcolor: "action.disabledBackground", color: "text.disabled", borderColor: "divider" }} />}
                </Stack>
              </Box>
              <Box sx={customerInnerCardSx}>
                <Typography variant="body2" color="text.secondary">Trạng thái</Typography>
                <Box sx={{ mt: 0.75 }}>{statusChip(order)}</Box>
              </Box>
            </Box>

            <Box sx={{ display: expandedOrders[order.order_id] ? "grid" : "none", gap: 2, gridTemplateColumns: { xs: "1fr", md: "repeat(3, minmax(0, 1fr))" }, pt: 0.5 }}>
              <Box sx={customerInnerCardSx}>
                <Typography variant="body2" color="text.secondary">Sửa tên gói</Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: "center" }}>
                  <TextField defaultValue={order.plan_name} id={`plan-${order.order_id}`} size="small" fullWidth sx={customerPopupInputSx} />
                  <Button variant="contained" size="small" disabled={saving === `order-plan-${order.order_id}`} onClick={() => {
                    const input = document.getElementById(`plan-${order.order_id}`) as HTMLInputElement | null;
                    onPlanChange(order.order_id, input?.value || "");
                  }} sx={{ borderRadius: 4, minWidth: 72 }}>Lưu</Button>
                </Stack>
              </Box>

              <Box sx={customerInnerCardSx}>
                <Typography variant="body2" color="text.secondary">Đổi trạng thái</Typography>
                <Box sx={{ mt: 1, display: "flex", flexWrap: "wrap", gap: 1, alignItems: "center" }}>
                  <Chip
                    size="small"
                    label={String(order.status || "-")}
                    variant="outlined"
                    sx={customerOrderStateChipSx(order.status, isOrderActive(order), daysUntil(order.expire_at) >= 0 && daysUntil(order.expire_at) <= 3)}
                  />
                  <Typography variant="caption" color="text.secondary">Chỉ xem nhanh, không chỉnh ở đây.</Typography>
                </Box>
              </Box>

              <Box sx={customerInnerCardSx}>
                <Typography variant="body2" color="text.secondary">Cập nhật hạn</Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: "center" }}>
                  <TextField type="datetime-local" defaultValue={orderExpireValue(order.expire_at)} id={`expire-${order.order_id}`} size="small" fullWidth sx={customerPopupInputSx} slotProps={{ inputLabel: { shrink: true } }} />
                  <Button variant="contained" size="small" disabled={saving === `order-expire-${order.order_id}`} onClick={() => {
                    const input = document.getElementById(`expire-${order.order_id}`) as HTMLInputElement | null;
                    onExpireChange(order.order_id, input?.value || "");
                  }} sx={{ borderRadius: 4, minWidth: 84 }}>Lưu hạn</Button>
                </Stack>
              </Box>

            </Box>
          </CardContent>
        </Card>
      ))}
    </Stack>
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

const Pagination = MuiPagination;
const SimpleTable = MuiSimpleTable;
