"use client";
/* eslint-disable react-hooks/exhaustive-deps, @typescript-eslint/no-unused-vars */

import {
  Activity,
  BadgePercent,
  BadgeDollarSign,
  BarChart3,
  Clock3,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  BellRing,
  Eye,
  FileText,
  Gift,
  CreditCard,
  History,
  Coins,
  Loader2,
  Megaphone,
  MessageSquare,
  MessagesSquare,
  Pencil,
  Search,
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
  ChevronRight,
  Copy,
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
  Badge,
  Drawer,
  FormControl,
  FormControlLabel,
  InputLabel,
  IconButton,
  Menu,
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
import { Fragment, type MouseEvent, type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import * as XLSX from "xlsx";
import { ManualOrderDialog } from "./manual-order-dialog";
import {
  channelPostStatusClass,
  channelPostStatusLabel,
  dateMinusDaysText,
  dateText,
  dateTextShort,
  dateTimePreviewText,
  dateTimeInputValue,
  daysUntil,
  activityEventBadgeTone,
  activityEventDetailLabel,
  activityLogDetailLabel,
  friendlyDetailText,
  activityEventLabel,
  auditStatusLabel,
  groupDebugText,
  groupDisplayLabel,
  isoDayKey,
  describeActivityEvent,
  displayText,
  formatDisplayCurrency,
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
  isLifetimeAllAccessText,
  isOrderActive,
  isTodayDate,
  isWithinPeriod,
  kickAuditReason,
  kickAuditStatusClass,
  money,
  normalizeRevenueCurrency,
  orderCouponCode,
  orderExpireValue,
  orderLifecycleLabel,
  orderPlanKind,
  orderAmountValue,
  orderMoney,
  orderNoteText,
  resolveOrderLabel,
  payloadText,
  providerRevenueFormat,
  safeDateMillis,
  statusClass,
  logEntryTypeLabel,
  orderStatusLabel,
  tooltipLabel,
  supportEventLabel,
  uniqueValues,
} from "./dashboard-helpers";
import { dayKey, getConfigValue, groupConfigKeys, groupOrders, hasAnyGroupConfig, isGroupConfigured, orderStats, canonicalConfigKey, type GroupMode } from "./dashboard-business";
import { MuiDialogShell, OrdersTable as MuiOrdersTable, Pagination as MuiPagination, PanelHead, SimpleTable as MuiSimpleTable, SupportThreadPanel, statusChipSx } from "./dashboard-components";
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
  ActivityLogResponse,
  type ActivityLogEntry,
  BroadcastCampaign,
  BroadcastRecipient,
  type BotScheduleStatus,
  CampaignPreview,
  ChannelPost,
  ChannelPostEvent,
  ConfigRow,
  CustomerSearchResult,
  BlacklistEntry,
  Coupon,
  KickAuditRow,
  LicenseRecord,
  LicenseSession,
  LicenseAuditEvent,
  ManualOrderResult,
  MenuPage,
  Order,
  SaleRule,
  SupportCaseItem,
  SupportEvent,
  SupportMessage,
  UserRow,
  WebhookInfo,
  WebhookInfoMeta,
  checkSupportGroup,
  cancelCampaign,
  channelPostAction,
  createChannelPost,
  createCampaign,
  createCoupon,
  createCoupons,
  createManualOrder,
  generateManualActiveCode,
  generateManualJoinLink,
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
  getActivityLog,
  getBlacklist,
  getBotScheduleStatus,
  getDashboardSummary,
  getCampaignRecipients,
  getCampaigns,
  getChannelPostEvents,
  getChannelPosts,
  getDashboardOverview,
  getMarketingStats,
  getAdminNotifications,
  getPaymentSchema,
  getActivationCodes,
  getCoupons,
  getLicenses,
  getLicenseSessions,
  getLicenseAudits,
  getHiddenCodes,
  getHiddenGroups,
  getHiddenRedemptions,
  getKickAudit,
  getVipGroupAudit,
  getVipMemberAudit,
  getMenuPages,
  getOrders,
  getSaleRules,
  searchCustomers,
  getSupportCases,
  getSupportEvents,
  getCustomerIdentityHistory,
  getUsers,
  getWebhookInfo,
  kickAuditMember,
  cleanupVipInviteLinks,
  pauseCampaign,
  previewCampaign,
  regenerateActivationCode,
  clearWebhookMaintenance,
  resetWebhook,
  sendAdminReply,
  startCampaign,
  updateChannelPost,
  updateConfigs,
  updateConfig,
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
  type DashboardSummary,
  type MarketingStatsResponse,
  type OverviewDashboard,
  type AdminNotificationItem,
  type VipGroupAuditRow,
  type VipMemberAuditRow,
  type CustomerIdentityHistoryRow,
  type SupportGroupCheck,
  type PaymentSchemaGroup,
  type PaymentSchemaResponse,
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
    plan_name: "Collection 30 Ngày - Hạng Cửu Black",
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
    plan_name: "Combo Trọn Đời (Full 4 Collection)",
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
    plan_name: "Collection 30 Ngày - Hạng Cửu Boy",
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
    plan_name: "Combo 30 Ngày (Full 4 Collection)",
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
    plan_name: "Collection 30 Ngày - Hạng Cửu Prime",
    amount: 59000,
    status: "PENDING",
    paid_at: null,
    expire_at: null,
    sale_id: "PENDING01",
    coupon_code: null,
    payment_provider: "PAYOS",
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
    plan_name: "Collection 30 Ngày - Hạng Cửu Black",
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
    plan_name: "Combo Trọn Đời (Full 4 Collection)",
    expire_at: demoDate(3650, 15, 0),
    created_at: demoDate(-45, 14, 25),
  },
  {
    telegram_user_id: "6845057360",
    full_name: "Jeon Jk",
    status: "ACTIVE",
    plan_name: "Combo 30 Ngày (Full 4 Collection)",
    expire_at: demoDate(24, 8, 45),
    created_at: demoDate(-6, 8, 12),
  },
  {
    telegram_user_id: "2085787503",
    full_name: "Taco",
    status: "EXPIRED",
    plan_name: "Collection 30 Ngày - Hạng Cửu Black",
    expire_at: demoDate(-2, 11, 10),
    created_at: demoDate(-3, 10, 15),
  },
];

const popupFieldSx = {
  "& .MuiOutlinedInput-root": {
    borderRadius: "10px",
    backgroundColor: "rgba(255,255,255,0.9)",
    backdropFilter: "blur(8px)",
    transition: "all 200ms ease",
    "&:hover": {
      backgroundColor: "#ffffff",
      boxShadow: "0 4px 12px rgba(15,23,42,0.04)",
    },
    "&.Mui-focused": {
      backgroundColor: "#ffffff",
      boxShadow: "0 0 0 3px rgba(0,102,255,0.1), 0 4px 12px rgba(15,23,42,0.04)",
    },
  },
  "& .MuiInputBase-input": {
    fontWeight: 500,
  },
  "& .MuiFormHelperText-root": {
    mx: 0,
  },
} as const;

const popupSelectSx = {
  borderRadius: "10px",
  backgroundColor: "rgba(255,255,255,0.9)",
  backdropFilter: "blur(8px)",
  transition: "all 200ms ease",
  "&:hover": {
    backgroundColor: "#ffffff",
    boxShadow: "0 4px 12px rgba(15,23,42,0.04)",
  },
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
    boxShadow: "0 4px 10px rgba(15, 23, 42, 0.03)",
  },
  "& .MuiInputLabel-root": {
    fontWeight: 700,
  },
} as const;

const customerInnerCardSx = {
  p: 1.1,
  border: 1,
  borderColor: "divider",
  borderRadius: 1.75,
  bgcolor: "background.paper",
  boxShadow: "0 4px 12px rgba(15, 23, 42, 0.03)",
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
  borderRadius: "16px",
  bgcolor: "rgba(255,255,255,0.78)",
  backdropFilter: "blur(20px)",
  border: "1px solid rgba(148,163,184,0.12)",
  boxShadow: "0 8px 32px rgba(15, 23, 42, 0.06), 0 1px 2px rgba(15,23,42,0.04)",
  transition: "box-shadow 0.3s ease, transform 0.3s ease",
  "&:hover": {
    boxShadow: "0 16px 48px rgba(15, 23, 42, 0.10), 0 2px 4px rgba(15,23,42,0.06)",
  },
  "&::before": {
    content: '""',
    position: "absolute",
    inset: 0,
    height: 4,
    background: "linear-gradient(90deg, #0066ff, #06b6d4, #10b981, #8b5cf6, #f43f5e)",
    backgroundSize: "200% 100%",
    animation: "gradientShift 8s linear infinite",
    zIndex: 1,
  },
} as const;

const sidebarTabSx = {
  mt: 0.5,
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
    borderRadius: "10px",
    border: "1px solid rgba(148,163,184,0.06)",
    bgcolor: "rgba(255,255,255,0.02)",
    width: "100%",
    boxSizing: "border-box",
    textTransform: "none",
    fontWeight: 600,
    fontSize: "0.84rem",
    color: "#94a3b8",
    boxShadow: "none",
    transition: "all 250ms cubic-bezier(0.4, 0, 0.2, 1)",
    borderLeft: "3px solid transparent",
    overflow: "hidden",
    letterSpacing: "0.01em",
    "& .MuiTab-iconWrapper": {
      marginRight: 7,
      minWidth: 0,
      transition: "transform 200ms ease, color 200ms ease",
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
    bgcolor: "rgba(96,165,250,0.08)",
    borderColor: "rgba(96,165,250,0.15)",
    color: "#e2e8f0",
    transform: "translateX(2px)",
    "& .MuiTab-iconWrapper": {
      color: "#60a5fa",
    },
  },
  "& .MuiTab-root.Mui-selected": {
    backgroundImage: "linear-gradient(135deg, #0066ff 0%, #0ea5e9 100%)",
    color: "#fff",
    borderColor: "rgba(96,165,250,0.25)",
    boxShadow: "0 8px 24px rgba(0, 102, 255, 0.22), inset 0 1px 0 rgba(255,255,255,0.12)",
    borderLeftColor: "rgba(255,255,255,0.72)",
    fontWeight: 700,
    "& .MuiTab-iconWrapper": {
      color: "#fff",
      transform: "scale(1.1)",
    },
    "& .MuiChip-root": {
      bgcolor: "rgba(255,255,255,0.2)",
      color: "#fff",
      borderColor: "rgba(255,255,255,0.3)",
    },
  },
  "& .MuiTab-root.Mui-selected:hover": {
    backgroundImage: "linear-gradient(135deg, #1d4ed8 0%, #0284c7 100%)",
    borderColor: "rgba(96,165,250,0.5)",
    boxShadow: "0 12px 32px rgba(0, 102, 255, 0.3), inset 0 1px 0 rgba(255,255,255,0.15)",
  },
  "& .MuiTabs-indicator": { display: "none" },
} as const;

const sidebarTabLabelSx = { width: "100%", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 } as const;
const sidebarTabChipSx = { height: 22, fontSize: "0.7rem", fontWeight: 800, bgcolor: "rgba(255,255,255,0.08)", color: "#e2e8f0", borderColor: "rgba(255,255,255,0.10)" } as const;

type Tab = "overview" | "analytics" | "setup" | "orders" | "customers" | "activityLog" | "campaigns" | "channelPosts" | "renewals" | "supportGroup" | "content" | "autoPayment" | "botVi" | "botEn" | "botTools" | "specialGroups" | "menuBot" | "coupons" | "activationCodes" | "security" | "vipAudit" | "sales" | "system" | "license" | "payment";
type ContentSubTab = "bot" | "payment" | "currency" | "admin";
type BotUiSubTab = "plans" | "buttons" | "messages" | "saleContent" | "groups";
type BotToolsSubTab = "groupReplies" | "alerts";
type MenuBotSubTab = "pages" | "language" | "commands";
type MenuLanguage = "vi" | "en";
type CustomerStatusFilter = "all" | "active" | "expiring" | "lifetime" | "expired" | "paid" | "coupon";
type CustomerOrderTab = "paid" | "other";
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
type RenewalSubTab = "soon" | "reminded" | "expired" | "lifetime";
type RenewalFocusFilter = "all" | "important" | "new" | "svip" | "unreminded" | "chokick" | "review" | "kicked" | "retained" | "error";
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

const TAB_STORAGE_KEY = "prive_admin_tab";
const AUTO_REFRESH_SECONDS = 60;

type ConfigField = {
  key: string;
  label: string;
  placeholder: string;
  help: string;
  kind?: "input" | "textarea" | "select" | "multiselect";
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

const MENU_LANGUAGE_FIELDS: ConfigField[] = [
  {
    key: "LANGUAGE_SWITCH_ENABLED",
    label: "Hiện nút đổi ngôn ngữ",
    placeholder: "ON",
    help: "Bật để hiện nút đổi English/Vietnamese trong menu chính. Khi tắt, các nút set_lang trong Menu Builder cũng bị ẩn.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "DEFAULT_LANGUAGE",
    label: "Ngôn ngữ mặc định",
    placeholder: "vi",
    help: "Ngôn ngữ dùng cho user mới khi chưa tự chọn. Giá trị hợp lệ: vi hoặc en.",
    kind: "select",
    options: [
      { label: "Tiếng Việt", value: "vi" },
      { label: "English", value: "en" },
    ],
  },
  {
    key: "LANGUAGE_SWITCH_LABEL_EN",
    label: "Nhãn nút chuyển sang English",
    placeholder: "🇬🇧 English",
    help: "Nút này hiện khi khách đang ở giao diện tiếng Việt.",
  },
  {
    key: "LANGUAGE_SWITCH_LABEL_VI",
    label: "Nhãn nút chuyển sang Vietnamese",
    placeholder: "🇻🇳 Vietnamese",
    help: "Nút này hiện khi khách đang ở giao diện tiếng Anh.",
  },
];

const PAYMENT_FIELDS: ConfigField[] = [
  {
    key: "WEB_PAYMENT_ENABLED",
    label: "Bật thanh toán web",
    placeholder: "OFF",
    help: "Bật ON để bot hiển thị nút thanh toán web riêng và gọi sang Hangcu_web để lấy checkout link.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "WEB_PAYMENT_SECRET",
    label: "Secret gọi web checkout",
    placeholder: "shared-secret",
    help: "Secret dùng để ký request checkout gửi sang web. Nên khớp với WEB_PAYMENT_SECRET bên web.",
  },
  {
    key: "WEB_PAYMENT_LABEL_VI",
    label: "Nhãn nút web (VI)",
    placeholder: "🌐 Thanh toán web",
    help: "Nhãn hiển thị cho người dùng tiếng Việt trên nút web checkout.",
  },
  {
    key: "WEB_PAYMENT_LABEL_EN",
    label: "Nhãn nút web (EN)",
    placeholder: "🌐 Web checkout",
    help: "Nhãn hiển thị cho người dùng tiếng Anh trên nút web checkout.",
  },
  {
    key: "PAYOS_PAYMENT_ENABLED",
    label: "Bật thanh toán PayOS",
    placeholder: "ON",
    help: "PayOS/VietQR for VND payments in Vietnam.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "PAYPAL_PAYMENT_ENABLED",
    label: "Bật thanh toán PayPal",
    placeholder: "OFF",
    help: "Only works when Render has PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET set.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "NOWPAYMENTS_PAYMENT_ENABLED",
    label: "Bật NOWPayments",
    placeholder: "OFF",
    help: "Bật ON để bot cho phép thanh toán crypto qua NOWPayments. Chỉ hiện khi backend và credentials đã cấu hình.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "TRON_USDT_PAYMENT_ENABLED",
    label: "Bật USDT TRC20 tự quét",
    placeholder: "OFF",
    help: "Custom gateway: the bot shows a TRC20 wallet and auto-checks TronGrid. You must configure the receiving wallet.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "BINANCE_PAY_SIEUTHICODE_ENABLED",
    label: "Bật Binance Pay",
    placeholder: "OFF",
    help: "Bật ON để bot cho phép thanh toán qua Binance Pay Sieuthicode. Chỉ dùng khi token và endpoint đã cấu hình.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "PAYMENT_PROVIDERS_VI",
    label: "Các cổng cho tiếng Việt",
    placeholder: "PAYOS,PAYPAL,TRON_USDT",
    help: "Chỉ chọn rail thanh toán thật sẽ hiện cho tiếng Việt. WEB là nút hành động riêng, không đặt ở đây.",
    kind: "multiselect",
    options: [
      { label: "PAYOS", value: "PAYOS" },
      { label: "PAYPAL", value: "PAYPAL" },
      { label: "NOWPAYMENTS", value: "NOWPAYMENTS" },
      { label: "TRON_USDT", value: "TRON_USDT" },
      { label: "BINANCE_PAY", value: "BINANCE_PAY" },
    ],
  },
  {
    key: "PAYMENT_PROVIDERS_EN",
    label: "Các cổng cho tiếng Anh",
    placeholder: "PAYPAL,TRON_USDT",
    help: "Chỉ chọn rail thanh toán thật sẽ hiện cho tiếng Anh. WEB là nút hành động riêng, không đặt ở đây.",
    kind: "multiselect",
    options: [
      { label: "PAYOS", value: "PAYOS" },
      { label: "PAYPAL", value: "PAYPAL" },
      { label: "NOWPAYMENTS", value: "NOWPAYMENTS" },
      { label: "TRON_USDT", value: "TRON_USDT" },
      { label: "BINANCE_PAY", value: "BINANCE_PAY" },
    ],
  },
  {
    key: "PAYPAL_BRAND_NAME",
    label: "Tên shop trên PayPal",
    placeholder: "Hang Cú VIP",
    help: "Tên hiển thị trên trang thanh toán PayPal.",
  },
  {
    key: "TRON_USDT_WALLET_ADDRESS",
    label: "Ví nhận USDT TRC20",
    placeholder: "T...",
    help: "TRON wallet address for receiving USDT TRC20. Do not enter seed or private key here.",
  },
  {
    key: "TRON_USDT_UNIQUE_AMOUNT_ENABLED",
    label: "Tạo số USDT riêng cho từng đơn",
    placeholder: "ON",
    help: "Turn ON to add a 0.000001-0.000999 suffix to each USDT amount so identical orders are easy to match.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "TRON_USDT_TTL_SECONDS",
    label: "Thời gian chờ USDT",
    placeholder: "7200",
    help: "Seconds the bot keeps a USDT order pending. Default is 2 hours.",
  },
  {
    key: "PAYMENT_SPAM_WINDOW_SECONDS",
    label: "Cửa sổ chống spam payment",
    placeholder: "10",
    help: "Xét số lần bấm trong khoảng N giây gần nhất trước khi kết luận spam.",
  },
  {
    key: "PAYMENT_SPAM_MAX_ATTEMPTS",
    label: "Số lần được phép",
    placeholder: "2",
    help: "Số lần bấm hợp lệ trong cùng cửa sổ trước khi bot chặn tạm ở lần kế tiếp.",
  },
  {
    key: "PAYMENT_SPAM_BLOCK_SECONDS",
    label: "Thời gian chặn spam",
    placeholder: "15",
    help: "Số giây bot sẽ khóa tạm khi vượt ngưỡng spam.",
  },
];

const PAYMENT_RAIL_KEYS = new Set([
  "PAYOS_PAYMENT_ENABLED",
  "PAYPAL_PAYMENT_ENABLED",
  "NOWPAYMENTS_PAYMENT_ENABLED",
  "TRON_USDT_PAYMENT_ENABLED",
  "BINANCE_PAY_SIEUTHICODE_ENABLED",
  "PAYMENT_PROVIDERS_VI",
  "PAYMENT_PROVIDERS_EN",
]);

const PAYMENT_ACTION_KEYS = new Set([
  "WEB_PAYMENT_ENABLED",
  "WEB_PAYMENT_SECRET",
  "WEB_PAYMENT_LABEL_VI",
  "WEB_PAYMENT_LABEL_EN",
]);

const PAYMENT_RAIL_FIELDS = PAYMENT_FIELDS.filter((field) => PAYMENT_RAIL_KEYS.has(field.key));
const PAYMENT_ACTION_FIELDS = PAYMENT_FIELDS.filter((field) => PAYMENT_ACTION_KEYS.has(field.key));

const AUTO_PAYMENT_VI_FIELDS: ConfigField[] = [
  {
    key: "AUTO_PAYMENT_VI_NEW_ENABLED",
    label: "Khách mới (VI): bật thanh toán tự động",
    placeholder: "ON",
    help: "Bật ON để khách Việt mới được đi auto payment khi khung giờ cho phép cũng bật.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "AUTO_PAYMENT_VI_NEW_SCHEDULE_ENABLED",
    label: "Khách mới (VI): bật khung giờ",
    placeholder: "ON",
    help: "Bật ON để áp dụng khung giờ cho khách Việt mới. Tắt thì khách mới luôn theo cờ bật/tắt chính.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "AUTO_PAYMENT_VI_NEW_WINDOWS",
    label: "Khách mới (VI): khung giờ",
    placeholder: "22:00-06:00",
    help: "Nhập theo giờ Việt Nam. Có thể nhập nhiều khung, cách nhau bằng dấu phẩy. Ví dụ: 22:00-06:00 hoặc 22:00-23:30,00:30-06:00.",
  },
  {
    key: "AUTO_PAYMENT_VI_RETURNING_ENABLED",
    label: "Khách cũ (VI): bật thanh toán tự động",
    placeholder: "ON",
    help: "Bật ON để khách Việt cũ được đi auto payment khi khung giờ cho phép cũng bật.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "AUTO_PAYMENT_VI_RETURNING_SCHEDULE_ENABLED",
    label: "Khách cũ (VI): bật khung giờ",
    placeholder: "ON",
    help: "Bật ON để áp dụng khung giờ cho khách Việt cũ. Tắt thì khách cũ luôn theo cờ bật/tắt chính.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "AUTO_PAYMENT_VI_RETURNING_WINDOWS",
    label: "Khách cũ (VI): khung giờ",
    placeholder: "22:00-06:00",
    help: "Nhập theo giờ Việt Nam. Có thể nhập nhiều khung, cách nhau bằng dấu phẩy. Ví dụ: 22:00-06:00 hoặc 22:00-23:30,00:30-06:00.",
  },
];

const AUTO_PAYMENT_EN_FIELDS: ConfigField[] = [
  {
    key: "AUTO_PAYMENT_EN_NEW_ENABLED",
    label: "New users (EN): auto payment",
    placeholder: "ON",
    help: "Turn ON to let new English-speaking users use auto payment when the schedule also allows it.",
    kind: "select",
    options: [{ label: "On", value: "ON" }, { label: "Off", value: "OFF" }],
  },
  {
    key: "AUTO_PAYMENT_EN_NEW_SCHEDULE_ENABLED",
    label: "New users (EN): time window",
    placeholder: "ON",
    help: "Turn ON to enforce time windows for new English-speaking users.",
    kind: "select",
    options: [{ label: "On", value: "ON" }, { label: "Off", value: "OFF" }],
  },
  {
    key: "AUTO_PAYMENT_EN_NEW_WINDOWS",
    label: "New users (EN): windows",
    placeholder: "22:00-06:00",
    help: "Examples: 22:00-06:00 or 22:00-23:30,00:30-06:00.",
  },
  {
    key: "AUTO_PAYMENT_EN_RETURNING_ENABLED",
    label: "Returning users (EN): auto payment",
    placeholder: "ON",
    help: "Turn ON to let returning English-speaking users use auto payment when the schedule also allows it.",
    kind: "select",
    options: [{ label: "On", value: "ON" }, { label: "Off", value: "OFF" }],
  },
  {
    key: "AUTO_PAYMENT_EN_RETURNING_SCHEDULE_ENABLED",
    label: "Returning users (EN): time window",
    placeholder: "ON",
    help: "Turn ON to enforce time windows for returning English-speaking users.",
    kind: "select",
    options: [{ label: "On", value: "ON" }, { label: "Off", value: "OFF" }],
  },
  {
    key: "AUTO_PAYMENT_EN_RETURNING_WINDOWS",
    label: "Returning users (EN): windows",
    placeholder: "22:00-06:00",
    help: "Examples: 22:00-06:00 or 22:00-23:30,00:30-06:00.",
  },
];

const AUTO_PAYMENT_SUPPORT_FIELDS: ConfigField[] = [
  {
    key: "MANUAL_SUPPORT_BOT_URL",
    label: "Link chuyển sang hỗ trợ",
    placeholder: "https://t.me/cuhotro_bot?start={payload}",
    help: "Ưu tiên để link nick admin hoặc link hỗ trợ thủ công. Dùng {payload}; backend sẽ tự tạo payload act_ đồng bộ cho link kích hoạt. Nếu cấu hình dạng ...?start=act_ thì backend sẽ tự nối phần sau act_.",
  },
  {
    key: "MANUAL_SUPPORT_CONTACT_URL",
    label: "Link admin hỗ trợ",
    placeholder: "https://t.me/username",
    help: "Khi auto payment tắt, bot sẽ chuyển người dùng sang link này trước. Nếu để trống sẽ dùng link hỗ trợ cũ.",
  },
  {
    key: "MANUAL_SUPPORT_PAYLOAD_INCLUDE_USER_ID",
    label: "Kèm Telegram ID trong payload",
    placeholder: "OFF",
    help: "Mặc định OFF để link gọn hơn. Bật ON nếu muốn bot hỗ trợ nhận luôn Telegram ID trong start payload.",
    kind: "select",
    options: [{ label: "Tắt", value: "OFF" }, { label: "Bật", value: "ON" }],
  },
  {
    key: "MANUAL_SUPPORT_BOT_LABEL",
    label: "Text nút bot hỗ trợ",
    placeholder: "💬 Liên hệ hỗ trợ",
    help: "Tên nút dẫn sang bot hỗ trợ thủ công.",
  },
  {
    key: "MSG_MANUAL_SUPPORT_REDIRECT",
    label: "Tin chuyển sang bot hỗ trợ",
    placeholder: "⚠️ Auto payment is currently unavailable.\nPlease contact support to continue your VIP purchase 👑",
    help: "Message shown with the support button when auto payment is blocked.",
    kind: "textarea",
  },
];

const AUTO_PAYMENT_SUPPORT_EN_FIELDS: ConfigField[] = [
  {
    key: "MANUAL_SUPPORT_BOT_URL_EN",
    label: "Support redirect link (EN)",
    placeholder: "https://t.me/cuhotro_bot?start={payload}",
    help: "Prefer a direct admin contact link or manual support link. Use {payload}; backend will generate a standardized act_ payload for activation links. Can be ...?start={payload} or ...?start=act_.",
  },
  {
    key: "MANUAL_SUPPORT_CONTACT_URL_EN",
    label: "Admin contact link (EN)",
    placeholder: "https://t.me/username",
    help: "When auto payment is off, the bot will send EN users here first. Falls back to the old support link if empty.",
  },
  {
    key: "MANUAL_SUPPORT_BOT_LABEL_EN",
    label: "Text nút bot hỗ trợ (EN)",
    placeholder: "💬 Contact support",
    help: "Tên nút dẫn sang bot hỗ trợ thủ công cho khách tiếng Anh.",
  },
  {
    key: "MANUAL_SUPPORT_REDIRECT_LANGUAGE_SWITCH_ENABLED",
    label: "Hiện nút đổi ngôn ngữ ở redirect",
    placeholder: "ON",
    help: "Bật để hiển thị nút đổi VI/EN chỉ trong tin MSG_MANUAL_SUPPORT_REDIRECT khi autopay bị chặn.",
    kind: "select",
    options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }],
  },
  {
    key: "MSG_MANUAL_SUPPORT_REDIRECT_EN",
    label: "Support redirect text (EN)",
    placeholder: "👋 Auto payment is off for this account.\nTap the button below and we’ll handle it manually.",
    help: "Message shown together with the support button when auto payment is blocked.",
    kind: "textarea",
  },
];

const AUTO_PAYMENT_VI_NEW_FIELDS = AUTO_PAYMENT_VI_FIELDS.slice(0, 3);
const AUTO_PAYMENT_VI_RETURNING_FIELDS = AUTO_PAYMENT_VI_FIELDS.slice(3, 6);
const AUTO_PAYMENT_EN_NEW_FIELDS = AUTO_PAYMENT_EN_FIELDS.slice(0, 3);
const AUTO_PAYMENT_EN_RETURNING_FIELDS = AUTO_PAYMENT_EN_FIELDS.slice(3, 6);

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
    label: "Nút gia hạn Combo",
    placeholder: "🌟 Gia hạn / Lên Combo",
    help: "Text nút gia hạn cho gói Combo/full.",
  },
  {
    key: "BTN_RENEW_GROUP",
    label: "Nút gia hạn collection",
    placeholder: "🔄 Gia hạn / Mở rộng collection",
    help: "Text nút gia hạn cho gói collection lẻ.",
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
    label: "Hiện nút nhập mã trong menu",
    placeholder: "OFF",
    help: "OFF sẽ ẩn các nút Menu Builder có action nhập mã.",
    kind: "select",
    options: [
      { label: "Ẩn", value: "OFF" },
      { label: "Hiện", value: "ON" },
    ],
  },
  {
    key: "COUPON_COMMAND_ENABLED",
    label: "Hiện lệnh /code",
    placeholder: "OFF",
    help: "OFF sẽ không đưa /code vào danh sách lệnh Telegram và bỏ qua lệnh nhập mã từ khách.",
    kind: "select",
    options: [
      { label: "Ẩn", value: "OFF" },
      { label: "Hiện", value: "ON" },
    ],
  },
  {
    key: "COUPON_AUTO_REDEEM_ENABLED",
    label: "Tự nhận diện mã",
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
    label: "Prefix tự nhận diện mã",
    placeholder: "HANGCU_",
    help: "Nhiều prefix thì cách nhau bằng dấu phẩy. Ví dụ: HANGCU_,VIP_",
  },
  {
    key: "COUPON_ABUSE_ENABLED",
    label: "Chống dò mã",
    placeholder: "ON",
    help: "Giới hạn số lần nhập mã theo cửa sổ thời gian.",
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
    label: "Thời gian khóa nhập mã",
    placeholder: "30",
    help: "Số phút chặn nhập mã khi vượt giới hạn.",
  },
  {
    key: "COUPON_ABUSE_NOTIFY_USER",
    label: "Báo khách khi bị khóa mã",
    placeholder: "ON",
    help: "Bật để gửi tin nhắn khi user bị giới hạn nhập mã.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "MSG_COUPON_RATE_LIMITED",
    label: "Tin giới hạn mã",
    placeholder: "⛔ Bạn nhập mã quá nhiều lần. Vui lòng thử lại sau {minutes} phút.",
    help: "Dùng biến {minutes}.",
    kind: "textarea",
  },
  {
    key: "COUPON_ABUSE_AUTO_BLACKLIST",
    label: "Tự blacklist khi dò mã",
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
    label: "Delay xoá dòng Sheet (legacy)",
    placeholder: "2",
    help: "Legacy cũ, runtime hiện tại không còn dùng Google Sheet.",
  },
  {
    key: "SHEET_APPEND_DELAY_SECONDS",
    label: "Delay ghi dòng Sheet (legacy)",
    placeholder: "1",
    help: "Legacy cũ, runtime hiện tại không còn dùng Google Sheet.",
  },
  {
    key: "COUPON_CLEANUP_INITIAL_DELAY_SECONDS",
    label: "Delay cleanup mã khi boot",
    placeholder: "30",
    help: "Số giây chờ trước worker cleanup mã.",
  },
  {
    key: "COUPON_CLEANUP_INTERVAL_HOURS",
    label: "Chu kỳ cleanup mã",
    placeholder: "12",
    help: "Chu kỳ cleanup mã runtime hiện tại.",
  },
  {
    key: "COUPON_CLEANUP_AFTER_DAYS",
    label: "Số ngày giữ mã đã dùng",
    placeholder: "7",
    help: "Số ngày giữ mã/redemption đã dùng trước khi cleanup.",
  },
  {
    key: "ANALYTICS_DAILY_RETENTION_DAYS",
    label: "Số ngày giữ analytics ngày",
    placeholder: "120",
    help: "Giới hạn dữ liệu analytics daily giữ lại.",
  },
  {
    key: "ADMIN_NOTIFICATION_ENABLED",
    label: "Bật float thông báo admin",
    placeholder: "ON",
    help: "Hiện icon nổi khi có đơn auto-paid mới hoặc tin nhắn private mới của khách.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "ADMIN_NOTIFICATION_ORDERS_ENABLED",
    label: "Báo đơn auto-paid",
    placeholder: "ON",
    help: "Bật để float icon nhận đơn auto-paid mới.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "ADMIN_NOTIFICATION_PRIVATE_MESSAGES_ENABLED",
    label: "Báo tin nhắn private",
    placeholder: "ON",
    help: "Bật để float icon nhận tin nhắn riêng của khách.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "ADMIN_NOTIFICATION_POLL_SECONDS",
    label: "Chu kỳ quét thông báo",
    placeholder: "20",
    help: "Số giây giữa mỗi lần quét thông báo nổi. Nên để ngắn để icon lên gần realtime mà vẫn nhẹ Render.",
  },
];

const LICENSE_FIELDS: ConfigField[] = [
  {
    key: "LICENSE_FLOW_ENABLED",
    label: "Bật license flow",
    placeholder: "ON",
    help: "Bật ON để bot nhận /start lic_... và verify qua web.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "LICENSE_VERIFY_REQUIRED",
    label: "Bắt buộc verify signature",
    placeholder: "ON",
    help: "Bật ON để web chỉ chấp nhận verify có chữ ký hợp lệ từ bot.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "LICENSE_RENEWAL_ENABLED",
    label: "Bật nhắc hạn license",
    placeholder: "ON",
    help: "Bật ON để scheduler gửi reminder/revoke cho license.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "LICENSE_LINK_TEMPLATE",
    label: "Template deep link license",
    placeholder: "https://t.me/bot?start=lic_{code}",
    help: "Dùng {code}. Đây là link deep link user bấm để kích hoạt license.",
  },
  {
    key: "LICENSE_PLAN_MAPPING_JSON",
    label: "Map plan -> group",
    placeholder: '{"VIP_BASIC":{"groups":["group_a"],"duration_days":30,"allow_renew":true}}',
    help: "JSON mapping plan_code sang group_ids, duration_days, allow_renew.",
    kind: "textarea",
  },
  {
    key: "MSG_LICENSE_REMINDER",
    label: "Tin nhắc hạn license",
    placeholder: "⏰ License <b>{plan}</b> của bạn sẽ hết hạn sau <b>{days} ngày</b> nữa.",
    help: "Biến hỗ trợ: {plan}, {days}, {date}.",
    kind: "textarea",
  },
  {
    key: "MSG_LICENSE_REVOKED",
    label: "Tin thu hồi license",
    placeholder: "⛔ License <b>{plan}</b> của bạn đã bị thu hồi.",
    help: "Gửi khi license bị revoked.",
    kind: "textarea",
  },
  {
    key: "BTN_LICENSE_RENEW",
    label: "Nút gia hạn license",
    placeholder: "🔄 Gia hạn license",
    help: "Text nút bấm trong reminder license.",
  },
];

const COMMAND_FIELDS: ConfigField[] = [
  { key: "BOT_COMMAND_DESC_START", label: "Mô tả /start", placeholder: "Trang chủ / Mua gói", help: "Mô tả lệnh Telegram." },
  { key: "BOT_COMMAND_DESC_LANG", label: "Mô tả /lang", placeholder: "Đổi ngôn ngữ", help: "Mô tả lệnh Telegram." },
  { key: "BOT_COMMAND_DESC_ME", label: "Mô tả /me", placeholder: "Kiểm tra gói & Hạn dùng", help: "Mô tả lệnh Telegram." },
  { key: "BOT_COMMAND_DESC_CODE", label: "Mô tả /code", placeholder: "Nhập mã / code / hidden code", help: "Chỉ hiện khi bật lệnh /code." },
  { key: "BOT_COMMAND_DESC_SUPPORT", label: "Mô tả /support", placeholder: "Nhắn admin trợ giúp", help: "Mô tả lệnh Telegram." },
  { key: "BOT_COMMAND_DESC_POLICY", label: "Mô tả /policy", placeholder: "Đọc quy định nhóm", help: "Mô tả lệnh Telegram." },
];

const GROUP_COMMAND_FIELDS: ConfigField[] = [
  {
    key: "BOT_GROUP_COMMANDS_ENABLED",
    label: "Phản hồi lệnh trong group",
    placeholder: "ON",
    help: "Bật ON để /start, /me, /support, /policy vẫn phản hồi trong group bằng nội dung rút gọn.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "BOT_GROUP_COMMAND_HINT",
    label: "Dòng nhắc cuối",
    placeholder: "Dùng lệnh này trong group để xem hướng dẫn ngắn. Nếu cần thao tác riêng tư, hãy mở bot trong inbox.",
    help: "Câu chốt cuối cho mọi lệnh group. Giữ ngắn để đỡ spam chat.",
  },
];

const PRIVATE_MENU_FIELDS: ConfigField[] = [
  { key: "BOT_MENU_PRIVATE_START_ENABLED", label: "Hiện /start", placeholder: "ON", help: "Bật/tắt /start trong menu private.", kind: "select", options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }] },
  { key: "BOT_MENU_PRIVATE_LANG_ENABLED", label: "Hiện /lang", placeholder: "ON", help: "Bật/tắt /lang trong menu private.", kind: "select", options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }] },
  { key: "BOT_MENU_PRIVATE_ME_ENABLED", label: "Hiện /me", placeholder: "ON", help: "Bật/tắt /me trong menu private.", kind: "select", options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }] },
  { key: "BOT_MENU_PRIVATE_SUPPORT_ENABLED", label: "Hiện /support", placeholder: "ON", help: "Bật/tắt /support trong menu private.", kind: "select", options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }] },
  { key: "BOT_MENU_PRIVATE_POLICY_ENABLED", label: "Hiện /policy", placeholder: "ON", help: "Bật/tắt /policy trong menu private.", kind: "select", options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }] },
  { key: "BOT_MENU_PRIVATE_COUPON_ENABLED", label: "Hiện /code", placeholder: "ON", help: "Chỉ hiện nếu lệnh nhập mã đang bật.", kind: "select", options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }] },
];

const GROUP_MENU_FIELDS: ConfigField[] = [
  { key: "BOT_MENU_GROUP_START_ENABLED", label: "Hiện /start", placeholder: "ON", help: "Bật/tắt /start trong menu group.", kind: "select", options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }] },
  { key: "BOT_MENU_GROUP_LANG_ENABLED", label: "Hiện /lang", placeholder: "ON", help: "Bật/tắt /lang trong menu group.", kind: "select", options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }] },
  { key: "BOT_MENU_GROUP_ME_ENABLED", label: "Hiện /me", placeholder: "ON", help: "Bật/tắt /me trong menu group.", kind: "select", options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }] },
  { key: "BOT_MENU_GROUP_SUPPORT_ENABLED", label: "Hiện /support", placeholder: "ON", help: "Bật/tắt /support trong menu group.", kind: "select", options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }] },
  { key: "BOT_MENU_GROUP_POLICY_ENABLED", label: "Hiện /policy", placeholder: "ON", help: "Bật/tắt /policy trong menu group.", kind: "select", options: [{ label: "Bật", value: "ON" }, { label: "Tắt", value: "OFF" }] },
];

const ADMIN_FIELDS: ConfigField[] = [
  {
    key: "ADMIN_IDS",
    label: "Telegram Admin ID",
    placeholder: "887869657",
    help: "Nhập một hoặc nhiều Telegram ID admin, cách nhau bằng dấu phẩy. Admin được bỏ qua bảo trì/spam và dùng lệnh quản trị.",
  },
];

const SUPPORT_GROUP_FIELDS: ConfigField[] = [
  {
    key: "SUPPORT_GROUP_ENABLED",
    label: "Bật nhóm hỗ trợ",
    placeholder: "OFF",
    help: "Bật ON để gửi nút join nhóm hỗ trợ kèm link tham gia sau thanh toán/coupon.",
    kind: "select",
    options: [
      { label: "Tắt", value: "OFF" },
      { label: "Bật", value: "ON" },
    ],
  },
  {
    key: "SUPPORT_GROUP_MODE",
    label: "Chế độ hỗ trợ",
    placeholder: "group",
    help: "group: giữ flow nhóm hỗ trợ như hiện tại. channel: đổi sang channel hỗ trợ, chỉ phát link vào channel.",
    kind: "select",
    options: [
      { label: "Group", value: "group" },
      { label: "Channel", value: "channel" },
    ],
  },
  {
    key: "SUPPORT_GROUP_ID",
    label: "Support group/channel ID",
    placeholder: "-1001234567890",
    help: "ID group hoặc channel hỗ trợ. Khi chọn channel thì chỉ dùng để phát link, không dùng cho kick/mute.",
  },
  {
    key: "SUPPORT_GROUP_NAME",
    label: "Tên khu vực hỗ trợ",
    placeholder: "Nhóm hỗ trợ Hang Cú",
    help: "Tên hiển thị trong log/lỗi.",
  },
  {
    key: "SUPPORT_GROUP_BUTTON_TEXT",
    label: "Text nút join hỗ trợ",
    placeholder: "💬 Join nhóm hỗ trợ",
    help: "Nút URL riêng, mỗi link chỉ dùng được 1 lần.",
  },
  {
    key: "SUPPORT_GROUP_MUTE_ENABLED",
    label: "Mute khi hết hạn",
    placeholder: "ON",
    help: "Bật ON để user hết hạn bị mute trong nhóm hỗ trợ trước khi kick.",
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
    help: "Gói ngày/coupon hết hạn sẽ bị mute, sau N ngày không gia hạn mới bị kick khỏi nhóm hỗ trợ.",
  },
];

const SUPPORT_INBOX_FIELDS: ConfigField[] = [
  {
    key: "SUPPORT_INBOX_ENABLED",
    label: "Bật inbox support",
    placeholder: "ON",
    help: "Bắt cả tin riêng, ảnh, file, voice... gửi thẳng vào bot để vào luồng support.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "SUPPORT_INBOX_AUTO_REPLY_ENABLED",
    label: "Bật auto-reply support",
    placeholder: "ON",
    help: "Tự gửi 1 tin nhắn chào / xác nhận khi khách lần đầu mở ticket support. Có mẫu riêng cho vi/en.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "SUPPORT_INBOX_AUTO_REPLY_TEXT_VI",
    label: "Auto-reply tiếng Việt",
    placeholder: "✅ Cảm ơn bạn đã nhắn cho support. Team sẽ phản hồi sớm nhất có thể.",
    help: "Biến hỗ trợ: {ticket_no}, {full_name}, {username}, {subject}.",
    kind: "textarea",
  },
  {
    key: "SUPPORT_INBOX_AUTO_REPLY_TEXT_EN",
    label: "Auto-reply tiếng Anh",
    placeholder: "✅ Thanks for messaging us. Our support team will reply soon.",
    help: "Biến hỗ trợ: {ticket_no}, {full_name}, {username}, {subject}.",
    kind: "textarea",
  },
];

const SUPPORT_INBOX_EFFECT_FIELDS: ConfigField[] = [
  {
    key: "SUPPORT_INBOX_STATUS_ENABLED",
    label: "Bật hiệu ứng trạng thái kết nối",
    placeholder: "ON",
    help: "Mặc định nên để ON để khách thấy rõ trạng thái đang kết nối trước khi bot báo admin đã sẵn sàng.",
    kind: "select",
    options: [
      { label: "Bật", value: "ON" },
      { label: "Tắt", value: "OFF" },
    ],
  },
  {
    key: "SUPPORT_INBOX_STATUS_STYLE",
    label: "Kiểu hiệu ứng",
    placeholder: "pulse",
    help: "Chọn đúng preset muốn chạy. Chỉ khi chọn Custom frames thì bot mới đọc danh sách frame tự nhập bên dưới.",
    kind: "select",
    options: [
      { label: "Pulse - chớp điểm sáng", value: "pulse" },
      { label: "Dots - dấu chấm chờ", value: "dots" },
      { label: "Blink - nhấp nháy", value: "blink" },
      { label: "Wave - sóng", value: "wave" },
      { label: "Custom frames - tự nhập", value: "custom" },
    ],
  },
  {
    key: "SUPPORT_INBOX_STATUS_FRAMES",
    label: "Custom frames",
    placeholder: "{message} ✦ ✧ ✦\\n{message} ✧ ✦ ✧\\n{message} ✦ ✧ ✦",
    help: "Mỗi dòng là một frame edit. Dùng {message} để chèn tin nhắn ban đầu. Khối này chỉ hoạt động khi Kiểu hiệu ứng = Custom frames.",
    kind: "textarea",
  },
  {
    key: "SUPPORT_INBOX_CONNECTING_TEXT",
    label: "Tin nhắn trạng thái ban đầu",
    placeholder: "Đang kết nối",
    help: "Gửi vào chat user ngay khi nhận /start hoặc case mới.",
    kind: "textarea",
  },
  {
    key: "SUPPORT_INBOX_READY_TEXT",
    label: "Format final khi nhân viên sẵn sàng",
    placeholder: "{staff_name} đã sẵn sàng hỗ trợ 🤗",
    help: "Biến hỗ trợ: {staff_name}, {admin_name}, {admin_username}.",
    kind: "textarea",
  },
  {
    key: "SUPPORT_INBOX_STATUS_FRAME_DELAY_MS",
    label: "Delay giữa frame (ms)",
    placeholder: "420",
    help: "Tăng/giảm tốc độ chạy frame khi đang kết nối.",
  },
  {
    key: "SUPPORT_INBOX_STATUS_TOTAL_MS",
    label: "Thời gian kết nối trước khi chốt final (ms)",
    placeholder: "3600",
    help: "Hiệu ứng sẽ loop liên tục trong toàn bộ thời gian này. Hết thời gian mới chuyển sang tin final.",
  },
  {
    key: "SUPPORT_INBOX_STATUS_FINAL_HOLD_MS",
    label: "Giữ khung final trong preview (ms)",
    placeholder: "800",
    help: "Chỉ dùng cho preview trong CPAdmin để xem trạng thái final lâu hơn. Bot thật sẽ chốt final ngay sau thời gian kết nối.",
  },
];

const SUPPORT_INBOX_TEMPLATE_FIELDS: ConfigField[] = [
  {
    key: "SUPPORT_INBOX_GROUP_HEADER_DETAILED",
    label: "Header chi tiết cho ticket mới/bot action",
    placeholder: "🎫 <b>{ticket_no}</b> - {full_name}\\nID: <code>{telegram_user_id}</code>\\n🔎 {subject}\\nTrạng thái: <b>{status}</b>",
    help: "Dùng cho ticket mới hoặc bot action đẩy vào inbox. Biến: {ticket_no}, {full_name}, {telegram_user_id}, {username}, {subject}, {status}.",
    kind: "textarea",
  },
  {
    key: "SUPPORT_INBOX_GROUP_HEADER_COMPACT",
    label: "Header gọn cho follow-up",
    placeholder: "👤 <b>{full_name}</b>",
    help: "Dùng cho các tin follow-up trong cùng case để group đỡ rối. Biến: {ticket_no}, {full_name}, {telegram_user_id}, {username}, {subject}, {status}.",
    kind: "textarea",
  },
  {
    key: "SUPPORT_INBOX_GROUP_TEMPLATE_FIRST",
    label: "Body ticket mới",
    placeholder: "📩 <b>Tin nhắn từ khách</b>\\nTicket: <code>{ticket_no}</code>\\nKhách: <b>{full_name}</b>\\nID: <code>{telegram_user_id}</code>\\n\\n{message}",
    help: "Biến: {ticket_no}, {full_name}, {telegram_user_id}, {username}, {subject}, {status}, {message}.",
    kind: "textarea",
  },
  {
    key: "SUPPORT_INBOX_GROUP_TEMPLATE_FOLLOWUP",
    label: "Body follow-up",
    placeholder: "{message}",
    help: "Dùng cho các tin về sau trong cùng case. Có thể để rất gọn để admin đọc nhanh. Biến: {ticket_no}, {full_name}, {telegram_user_id}, {username}, {subject}, {status}, {message}.",
    kind: "textarea",
  },
  {
    key: "SUPPORT_INBOX_REPLY_TEMPLATE",
    label: "Template reply user",
    placeholder: "💬 <b>Phản hồi từ hỗ trợ</b>\\nTicket: <code>{ticket_no}</code>\\n{admin_name}{admin_username}\\n\\n{message}",
    help: "Biến: {ticket_no}, {full_name}, {telegram_user_id}, {subject}, {status}, {admin_name}, {admin_username}, {message}.",
    kind: "textarea",
  },
];

const SUPPORT_INBOX_PREVIEW_MESSAGE = "Đang kết nối với admin...";
const SUPPORT_INBOX_PREVIEW_PRESETS = [
  { key: "pulse", label: "Pulse", badge: "Nhịp sáng", accent: "linear-gradient(135deg, rgba(59,130,246,0.16), rgba(255,255,255,0.98))" },
  { key: "dots", label: "Dots", badge: "Chấm chờ", accent: "linear-gradient(135deg, rgba(16,185,129,0.16), rgba(255,255,255,0.98))" },
  { key: "blink", label: "Blink", badge: "Nhấp nháy", accent: "linear-gradient(135deg, rgba(249,115,22,0.16), rgba(255,255,255,0.98))" },
  { key: "wave", label: "Wave", badge: "Sóng", accent: "linear-gradient(135deg, rgba(139,92,246,0.16), rgba(255,255,255,0.98))" },
  { key: "custom", label: "Custom", badge: "Tự nhập", accent: "linear-gradient(135deg, rgba(236,72,153,0.16), rgba(255,255,255,0.98))" },
] as const;

function supportInboxPresetMeta(style: string) {
  return SUPPORT_INBOX_PREVIEW_PRESETS.find((preset) => preset.key === style) ?? SUPPORT_INBOX_PREVIEW_PRESETS[0];
}

function supportInboxPreviewFrames(style: string, message: string) {
  if (style === "dots") return [message, `${message}.`, `${message}..`, `${message}...`];
  if (style === "blink") return [`● ${message}`, `○ ${message}`, `● ${message}`];
  if (style === "wave") return [message, `${message} ~`, `${message} ~~`, `${message} ~~~`];
  return [`${message} ·`, `${message} ··`, `${message} ···`];
}

function supportInboxPreviewFrameList(style: string, message: string, rawFrames = "") {
  if (style === "custom") {
    const customFrames = String(rawFrames || "")
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => line.replaceAll("{message}", message));
    if (customFrames.length) return customFrames;
  }
  return supportInboxPreviewFrames(style, message);
}

function supportInboxPreviewTotalMs(delayMs: number, finalHoldMs: number, frameCount: number, configuredTotalMs?: number) {
  if (Number.isFinite(configuredTotalMs) && Number(configuredTotalMs) > 0) {
    return Math.max(1200, Number(configuredTotalMs));
  }
  return Math.max(1200, delayMs * Math.max(1, frameCount || 1) * 2 + finalHoldMs);
}

function supportInboxPreviewCurrentFrame(params: {
  frames: string[];
  delayMs: number;
  totalMs?: number;
  clockMs: number;
}) {
  const safeFrames = params.frames.length ? params.frames : [SUPPORT_INBOX_PREVIEW_MESSAGE];
  const safeDelayMs = Math.max(120, params.delayMs || 420);
  const totalVisibleMs = supportInboxPreviewTotalMs(safeDelayMs, 0, safeFrames.length, params.totalMs);
  const animationWindowMs = Math.max(safeDelayMs, totalVisibleMs);
  const phaseMs = ((params.clockMs % animationWindowMs) + animationWindowMs) % animationWindowMs;
  const frameIndex = Math.floor(phaseMs / safeDelayMs) % safeFrames.length;
  return {
    text: safeFrames[frameIndex] || safeFrames[0],
    progress: animationWindowMs ? phaseMs / animationWindowMs : 0,
    totalVisibleMs,
    animationWindowMs,
  };
}

function renderInboxReplyPreview(template: string, context: Record<string, string>) {
  let text = String(template || "").trim();
  if (!text) {
    text = "💬 <b>Phản hồi từ hỗ trợ</b>\nTicket: <code>{ticket_no}</code>\n{admin_name}{admin_username}\n\n{message}";
  }
  Object.entries(context).forEach(([key, value]) => {
    text = text.replaceAll(`{${key}}`, String(value || ""));
  });
  return text;
}

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
    help: "Tin hiển thị ở CP admin để copy gửi khách. Biến: {success_text}, {order_text}, {plan_name}, {bot_link_title}, {activation_url}, {bot_link_subtitle}.",
    kind: "textarea",
  },
  { key: "MANUAL_ORDER_LINK_TITLE", label: "Tiêu đề link bot", placeholder: "🔗 Link kích hoạt", help: "Biến: không cần placeholder. Đây là tiêu đề trước URL bot." },
  { key: "MANUAL_ORDER_LINK_SUBTITLE", label: "Mô tả link bot", placeholder: "Nhấn vào link bên dưới để mở bot và nhận link nhóm riêng.", help: "Biến: không cần placeholder. Dòng mô tả ngay dưới link bot.", kind: "textarea" },
  { key: "MANUAL_ORDER_LINK_TEMPLATE", label: "Deep link bot", placeholder: "https://t.me/hangcuvipbot?start=act_{code}", help: "Biến: {code}. Prefix act_ sẽ được tự chuẩn hoá.", },
  { key: "MANUAL_ORDER_LINK_BUTTON_LABEL", label: "Nút copy link", placeholder: "Copy link bot", help: "Biến: không cần placeholder. Text nút admin copy." },
  { key: "MANUAL_ORDER_MESSAGE_LINK_TITLE", label: "Tiêu đề tin active code", placeholder: "💬 Tin nhắn active code", help: "Tiêu đề cho khối tin nhắn hoàn chỉnh có active code." },
  { key: "MANUAL_ORDER_MESSAGE_LINK_SUBTITLE", label: "Mô tả tin active code", placeholder: "Dùng tin này để gửi khách kèm link active code.", help: "Mô tả dưới khối tin active code.", kind: "textarea" },
  { key: "MANUAL_ORDER_MESSAGE_LINK_BUTTON_LABEL", label: "Nút copy tin active code", placeholder: "Copy tin active code", help: "Text nút admin copy tin active code." },
  { key: "MANUAL_ORDER_JOIN_LINK_TITLE", label: "Tiêu đề tin join group", placeholder: "💬 Tin nhắn join group", help: "Tiêu đề cho khối tin nhắn hoàn chỉnh có link join group." },
  { key: "MANUAL_ORDER_JOIN_LINK_SUBTITLE", label: "Mô tả tin join group", placeholder: "Dùng tin này để gửi khách khi cần có sẵn link join group.", help: "Mô tả dưới khối tin join group.", kind: "textarea" },
  { key: "MANUAL_ORDER_JOIN_LINK_TEMPLATE", label: "Template tin join group", placeholder: "{order_text}\\n\\n{bot_link_title}\\n{links_text}\\n\\n{bot_link_subtitle}\\n\\n{support_text}", help: "Biến: {order_text}, {plan_name}, {links_text}, {support_text}. Dùng để xuất tin hoàn chỉnh có link join group.", kind: "textarea" },
  { key: "MANUAL_ORDER_JOIN_LINK_BUTTON_LABEL", label: "Nút copy tin join group", placeholder: "Copy tin join group", help: "Text nút admin copy tin join group." },
  { key: "MANUAL_ORDER_LINK_SUCCESS_TEXT", label: "Tin bot báo hợp lệ", placeholder: "✅ Đơn của bạn đã được xác minh.", help: "Biến: không cần placeholder. Chỉ dùng khi bot xác minh thành công.", kind: "textarea" },
  { key: "MANUAL_ORDER_LINK_PROCESSING_TEXT", label: "Tin bot đang xử lý", placeholder: "⏳ Bot đang xác minh đơn và tạo link nhóm...", help: "Biến: không cần placeholder. Bot trả ngay khi khách bấm link.", kind: "textarea" },
  { key: "MANUAL_ORDER_LINK_INVALID_TEXT", label: "Tin mã không hợp lệ", placeholder: "❌ Mã kích hoạt không hợp lệ hoặc đã bị vô hiệu hoá.", help: "Biến: không cần placeholder." },
  { key: "MANUAL_ORDER_LINK_USED_TEXT", label: "Tin mã đã dùng", placeholder: "ℹ️ Mã này đã được sử dụng. Nếu cần, admin hãy tạo lại link mới.", help: "Biến: không cần placeholder." },
  { key: "MANUAL_ORDER_LINK_WRONG_USER_TEXT", label: "Tin sai Telegram ID", placeholder: "❌ Mã này không dành cho tài khoản Telegram hiện tại.", help: "Biến: không cần placeholder." },
  { key: "MANUAL_ORDER_LINK_EXPIRED_TEXT", label: "Tin mã hết hạn", placeholder: "⏰ Mã kích hoạt đã hết hạn. Vui lòng liên hệ admin.", help: "Biến: không cần placeholder." },
  { key: "MANUAL_ORDER_LINK_FAIL_TEXT", label: "Tin tạo link thất bại", placeholder: "❌ Bot chưa tạo được link nhóm. Vui lòng thử lại sau.", help: "Biến: không cần placeholder." },
  { key: "MANUAL_ORDER_DELIVERY_TEMPLATE", label: "Tin bot trả khi xác minh xong", placeholder: "{success_text}\\n\\n{order_text}\\n\\n{links_text}\\n\\n{partial_text}\\n\\n{support_text}", help: "Biến: {success_text}, {order_text}, {links_text}, {partial_text}, {support_text}. Đây là tin bot gửi cho khách.", kind: "textarea" },
  { key: "MANUAL_ORDER_SUPPORT_TEMPLATE", label: "Khối trợ giúp trong bot", placeholder: "💬 {support_group_name}:\\n{support_link}", help: "Biến: {support_group_name}, {support_link}. Chỉ hiển thị ở bot.", kind: "textarea" },
  { key: "MANUAL_ORDER_SUPPORT_ERROR_TEMPLATE", label: "Khối lỗi trợ giúp", placeholder: "💬 {support_group_name}: Không tạo được link trợ giúp ({support_error})", help: "Biến: {support_group_name}, {support_error}. Chỉ hiển thị ở bot.", kind: "textarea" },
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
    placeholder: "🧾 Mã đơn: {desc}\\n💵 Số tiền: {amount}\\n🏦 Ngân hàng: {bank}",
    help: "Dùng biến {plan}, {amount}, {bank}, {name}, {stk}, {desc}.",
    kind: "textarea",
  },
  {
    key: "MSG_PAYPAL_BILL_TEMPLATE",
    label: "Nội dung bill PayPal",
    placeholder: "💳 <b>THANH TOÁN PAYPAL</b>\\n\\n🎁 Gói: <b>{plan}</b>\\n💵 Số tiền: <b>${paypal_amount} USD</b>\\n🧾 Đơn: <code>{desc}</code>",
    help: "Dùng biến {plan}, {amount}, {paypal_amount}, {desc}.",
    kind: "textarea",
  },
  {
    key: "MSG_TRON_USDT_BILL_TEMPLATE",
    label: "Nội dung bill USDT TRC20",
    placeholder: "₮ <b>THANH TOÁN USDT TRC20</b>\\n\\n🎁 Gói: <b>{plan}</b>\\n💵 Số tiền: <code>{usdt_amount} USDT</code>\\n🌐 Mạng: <b>TRC20</b>\\n👛 Ví nhận:\\n<code>{wallet}</code>\\n🧾 Đơn: <code>{desc}</code>\\n\\nVui lòng gửi đúng số USDT trên. Bot sẽ tự quét blockchain và cấp quyền ngay khi giao dịch được xác nhận.",
    help: "Dùng biến {plan}, {amount}, {usdt_amount}, {wallet}, {desc}.",
    kind: "textarea",
  },
  {
    key: "MSG_CHOOSE_PAYMENT_PROVIDER",
    label: "Tin chọn phương thức thanh toán",
    placeholder: "Chọn phương thức thanh toán. VietQR dùng VND; PayPal và Crypto dùng giá USD riêng.",
    help: "Tin bot gửi khi một gói có nhiều phương thức thanh toán được bật.",
    kind: "textarea",
  },
  {
    key: "MSG_NEW_CUSTOMER_MANUAL_ONLY",
    label: "Tin chặn khách mới auto payment",
    placeholder: "Đây là đơn mua đầu tiên của bạn, nên bot đang chuyển sang xử lý thủ công để an toàn hơn. Vui lòng nhắn admin để được hỗ trợ.",
    help: "Tin hiển thị khi khách mới bị chặn auto payment.",
    kind: "textarea",
  },
  {
    key: "MSG_RETURNING_CUSTOMER_AUTO_DISABLED",
    label: "Tin chặn khách cũ auto payment",
    placeholder: "Tài khoản của bạn đã từng mua VIP, nhưng thanh toán tự động hiện đang tắt. Vui lòng nhắn admin để được xử lý thủ công.",
    help: "Tin hiển thị khi khách cũ bị chặn auto payment.",
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
    placeholder: "✅ Thanh toán thành công!\\n\\n🎁 Gói: {plan}\\n📅 Hạn dùng: {date}\\n\\n🔗 Link của bạn:\\n{links}\\n\\n💬 Nhóm hỗ trợ: {support}",
    help: "Dùng biến {plan}, {date}, {links}, {support}. Tin QR sẽ được xóa trước khi gửi link.",
    kind: "textarea",
  },
  {
    key: "MSG_COUPON_SUCCESS",
    label: "Tin kích hoạt mã thành công",
    placeholder: "✅ Mã: {code}\\n🎁 Gói: {plan}\\n📅 Hạn: {expire}\\n{links}",
    help: "Dùng biến {code}, {plan}, {expire}, {links}.",
    kind: "textarea",
  },
  {
    key: "MSG_COUPON_PROMPT",
    label: "Tin yêu cầu nhập mã",
    placeholder: "<b>Nhập mã kích hoạt / Enter activation code</b>\\n\\nGửi mã bạn nhận được vào đây.",
    help: "Tin bot gửi khi khách bấm nhập mã.",
    kind: "textarea",
  },
  {
    key: "MSG_COUPON_DISCOUNT_OPTIONS",
    label: "Tin mã giảm giá hợp lệ",
    placeholder: "Mã: {code}\\nGiảm: {percent}%\\nChọn gói muốn mua bên dưới.",
    help: "Dùng biến {code}, {percent}.",
    kind: "textarea",
  },
  {
    key: "MSG_COUPON_GROUP_OPTIONS",
    label: "Tin mã chọn collection",
    placeholder: "Mã: {code}\\nThời hạn: {duration_label}\\nChọn collection bạn muốn kích hoạt bên dưới.",
    help: "Dùng khi mã kích hoạt cho phép khách tự chọn collection lẻ. Dùng biến {code}, {days}, {duration_label}.",
    kind: "textarea",
  },
  {
    key: "COUPON_ACTIVATION_PLAN_TEMPLATE",
    label: "Tên gói mã kích hoạt",
    placeholder: "Collection {duration_label} - {group}",
    help: "Tên lưu vào đơn và hiển thị khi kích hoạt mã chọn collection. Dùng {duration_label}, {days}, {group}.",
  },
  {
    key: "COUPON_ACTIVATION_BUTTON_TEMPLATE",
    label: "Nút chọn collection mã",
    placeholder: "{plan_name}",
    help: "Text nút chọn collection sau khi nhập mã. Dùng {plan_name}, {duration_label}, {days}, {group}.",
  },
  {
    key: "MSG_WAIT_QR",
    label: "Tin đang tạo QR",
    placeholder: "⏳ Đang tạo mã QR cho đơn của bạn...",
    help: "Tin tạm khi bot gọi PayOS.",
  },
  {
    key: "MSG_QR_ERROR",
    label: "Tin lỗi tạo QR",
    placeholder: "❌ Không tạo được mã thanh toán. Vui lòng thử lại sau.",
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
    help: "Dùng khi chưa có menu page trợ giúp.",
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
    placeholder: "🔄 Đã nạp lại toàn bộ dữ liệu & giao diện từ hệ thống!",
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
    label: "Tin mã thiếu collection chọn",
    placeholder: "❌ Mã hợp lệ nhưng chưa có collection lẻ nào được cấu hình để khách chọn.",
    help: "Dùng khi coupon chọn collection nhưng dashboard chưa cấu hình collection.",
  },
  {
    key: "MSG_COUPON_PLAN_NOT_CONFIGURED",
    label: "Tin mã thiếu collection cấp link",
    placeholder: "❌ Mã hợp lệ nhưng gói này chưa cấu hình collection nhận link.",
    help: "Dùng khi coupon hợp lệ nhưng không tạo được link vì thiếu collection.",
  },
  {
    key: "MSG_COUPON_PRIVATE_ONLY",
    label: "Tin mã chỉ private",
    placeholder: "Vui lòng nhắn riêng với bot để nhập mã, tránh lộ mã trong group.",
    help: "Tin gửi khi khách nhập mã trong group.",
  },
  {
    key: "MSG_COUPON_INVALID_FORMAT",
    label: "Tin format mã sai",
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
    key: "LABEL_HIDDEN_DURATION_1M",
    label: "Nhãn hidden 30 ngày",
    placeholder: "30 ngày",
    help: "Text thay cho {duration_label} khi nút mua hidden là gói 30 ngày.",
  },
  {
    key: "LABEL_HIDDEN_DURATION_LIFE",
    label: "Nhãn hidden trọn đời",
    placeholder: "trọn đời",
    help: "Text thay cho {duration_label} khi nút mua hidden là gói trọn đời.",
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
    label: "Hidden cần Combo active",
    placeholder: "Bạn cần có gói Combo còn hạn để mở mã này.",
    help: "Tin hiển thị khi rule yêu cầu Combo active.",
  },
  {
    key: "MSG_HIDDEN_REQUIREMENT_SVIP_LIFETIME",
    label: "Hidden cần Combo trọn đời",
    placeholder: "Bạn cần có gói Combo trọn đời để mở mã này.",
    help: "Tin hiển thị khi rule yêu cầu Combo trọn đời.",
  },
  {
    key: "MSG_HIDDEN_REQUIREMENT_PLAN_TOKEN_ACTIVE",
    label: "Hidden cần plan token active",
    placeholder: "Bạn cần có gói {plan_token} còn hạn để mở mã này.",
    help: "Tin hiển thị khi rule yêu cầu plan token active.",
  },
  {
    key: "MSG_HIDDEN_REQUIREMENT_PLAN_TOKEN_LIFETIME",
    label: "Hidden cần plan token trọn đời",
    placeholder: "Bạn cần có gói {plan_token} trọn đời để mở mã này.",
    help: "Tin hiển thị khi rule yêu cầu plan token trọn đời.",
  },
  {
    key: "MSG_HIDDEN_REQUIREMENT_GENERIC",
    label: "Hidden không đủ điều kiện",
    placeholder: "Tài khoản của bạn chưa đủ điều kiện để mở mã này.",
    help: "Fallback nếu rule không khớp riêng.",
  },
  {
    key: "MSG_HIDDEN_DEEPLINK_INVALID",
    label: "Hidden deeplink sai",
    placeholder: "❌ Link mua hidden không hợp lệ.",
    help: "Tin hiển thị khi payload /start hidden bị sai format.",
  },
  {
    key: "TXT_COMBO_DESCRIPTION",
    label: "Mô tả trang Combo",
    placeholder: "🔥 <b>ĐẶC QUYỀN COMBO</b> 🔥\\n\\n👇 <i>Chọn gói đăng ký bên dưới:</i>",
    help: "Nội dung trang gói Combo fallback nếu chưa dùng Menu Builder.",
    kind: "textarea",
  },
  {
    key: "IMG_COMBO_PAGE",
    label: "Ảnh trang Combo",
    placeholder: "File ID Telegram hoặc URL ảnh",
    help: "Ảnh cover trang Combo fallback.",
  },
  {
    key: "IMG_POLICY",
    label: "Ảnh trang policy",
    placeholder: "File ID Telegram hoặc URL ảnh",
    help: "Ảnh fallback cho trang policy.",
  },
  {
    key: "IMG_SUPPORT",
    label: "Ảnh trang trợ giúp",
    placeholder: "File ID Telegram hoặc URL ảnh",
    help: "Ảnh fallback cho trang trợ giúp.",
  },
  {
    key: "IMG_ME",
    label: "Ảnh trang /me",
    placeholder: "File ID Telegram hoặc URL ảnh",
    help: "Ảnh fallback cho trang tài khoản /me.",
  },
];

const AUTO_PAYMENT_MESSAGE_KEYS = new Set([
  "MSG_NEW_CUSTOMER_MANUAL_ONLY",
  "MSG_RETURNING_CUSTOMER_AUTO_DISABLED",
  "MSG_MANUAL_SUPPORT_REDIRECT",
]);
const AUTO_PAYMENT_MESSAGE_EN_KEYS = new Set([
  "MSG_NEW_CUSTOMER_MANUAL_ONLY_EN",
  "MSG_RETURNING_CUSTOMER_AUTO_DISABLED_EN",
  "MSG_MANUAL_SUPPORT_REDIRECT_EN",
]);

const HIDDEN_MESSAGE_FIELD_KEYS = new Set(["BTN_HIDDEN_BUY_TEMPLATE", "LABEL_HIDDEN_DURATION_1M", "LABEL_HIDDEN_DURATION_LIFE"]);
const HIDDEN_MESSAGE_FIELDS = MESSAGE_FIELDS.filter((field) => field.key.startsWith("MSG_HIDDEN_") || HIDDEN_MESSAGE_FIELD_KEYS.has(field.key));
const VISIBLE_MESSAGE_FIELDS = MESSAGE_FIELDS.filter((field) => !field.key.startsWith("MSG_HIDDEN_") && !HIDDEN_MESSAGE_FIELD_KEYS.has(field.key) && !AUTO_PAYMENT_MESSAGE_KEYS.has(field.key));

const BUTTON_FIELDS: ConfigField[] = [
  { key: "BTN_BACK", label: "Nút quay lại", placeholder: "🔙 Quay lại Menu", help: "Dùng ở hầu hết trang bot." },
  { key: "BTN_CHECK_PAYMENT", label: "Nút đã chuyển khoản", placeholder: "🔄 Đã chuyển khoản", help: "Nút dưới QR để khách check thủ công." },
  { key: "BTN_CANCEL_ORDER", label: "Nút hủy đơn", placeholder: "❌ Hủy", help: "Nút dưới QR để hủy đơn pending." },
  { key: "BTN_PAYPAL_CHECKOUT", label: "Nút thanh toán PayPal", placeholder: "💳 Pay with PayPal", help: "Nút mở trang checkout PayPal." },
  { key: "BTN_TRONSCAN_ADDRESS", label: "Nút xem ví Tronscan", placeholder: "🔎 Xem ví trên Tronscan", help: "Nút dưới bill USDT TRC20." },
  { key: "BTN_VIEW_QR", label: "Nút xem QR", placeholder: "🖼 Xem QR", help: "Dùng khi Telegram không gửi được ảnh QR." },
  { key: "BTN_BUY_COLLECTION_30D", label: "Nút mua collection 30 ngày", placeholder: "💎 COLLECTION 30 NGÀY", help: "Nút trên trang chi tiết collection." },
  { key: "BTN_BUY_COLLECTION_LIFE", label: "Nút mua collection trọn đời", placeholder: "👑 COLLECTION TRỌN ĐỜI", help: "Nút trên trang chi tiết collection." },
  { key: "BTN_VIEW_COMBO_PAGE", label: "Nút xem Combo", placeholder: "🌟 XEM COMBO", help: "Nút từ collection riêng sang trang Combo." },
  { key: "BTN_RENEW", label: "Nút gia hạn", placeholder: "🔄 Gia hạn ngay", help: "Nút khi gói hết hạn." },
  { key: "BTN_EARLY_RENEW", label: "Nút gia hạn sớm", placeholder: "🔥 Gia hạn sớm -{discount_percent}%", help: "Nút ưu đãi gia hạn sớm." },
  { key: "BTN_RENEW_FULL", label: "Nút gia hạn/lên Combo", placeholder: "🌟 Gia hạn / Lên Combo", help: "Nút trong tin nhắc gia hạn." },
  { key: "BTN_RENEW_GROUP", label: "Nút mở rộng collection", placeholder: "🔄 Gia hạn / Mở rộng collection", help: "Nút trong tin nhắc gia hạn." },
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
  { key: "ALERT_SUPPORT_UNAVAILABLE", label: "Không mở được trang trợ giúp", placeholder: "Không thể mở trang trợ giúp lúc này.", help: "Alert khi trang trợ giúp lỗi." },
  { key: "ALERT_COUPON_MENU_DISABLED", label: "Menu nhập mã đang ẩn", placeholder: "Chức năng nhập mã trên menu đang được ẩn.", help: "Khi khách bấm nút nhập mã đã ẩn." },
  { key: "ALERT_COUPON_PRIVATE_ONLY", label: "Mã chỉ private", placeholder: "Vui lòng nhắn riêng với bot để nhập mã.", help: "Alert khi bấm nhập mã trong group." },
  { key: "ALERT_COUPON_SELECTION_INVALID", label: "Mã chọn collection lỗi", placeholder: "Lựa chọn mã không hợp lệ.", help: "Callback chọn collection sai format." },
  { key: "ALERT_COUPON_NOT_GROUP_SELECT", label: "Không phải mã chọn collection", placeholder: "Mã này không phải mã chọn collection.", help: "Callback chọn collection không hợp lệ." },
  { key: "ALERT_COUPON_GROUP_OUT_OF_SCOPE", label: "Collection ngoài phạm vi mã", placeholder: "Collection này không nằm trong phạm vi mã.", help: "Khi mã không áp dụng cho collection đã chọn." },
  { key: "ALERT_RENEW_CODE_INVALID", label: "Mã gia hạn không hợp lệ", placeholder: "Mã gia hạn không hợp lệ.", help: "Khi callback gia hạn sai format." },
  { key: "ALERT_RENEW_OFFER_INVALID", label: "Offer gia hạn không hợp lệ", placeholder: "Ưu đãi gia hạn không còn hợp lệ.", help: "Khi offer không còn dữ liệu." },
  { key: "ALERT_RENEW_NOT_OWNER", label: "Offer không thuộc user", placeholder: "Ưu đãi này không thuộc tài khoản của bạn.", help: "Khi user bấm offer của người khác." },
  { key: "ALERT_RENEW_EXPIRED", label: "Offer gia hạn hết hạn", placeholder: "Ưu đãi gia hạn sớm đã hết hạn hoặc không còn hợp lệ.", help: "Khi offer không đủ điều kiện." },
  { key: "ALERT_DISCOUNT_INVALID", label: "Mã giảm giá lỗi", placeholder: "Mã giảm giá không hợp lệ.", help: "Callback coupon giảm giá sai format." },
  { key: "ALERT_DISCOUNT_NOT_APPLICABLE", label: "Coupon không áp dụng", placeholder: "Mã này không áp dụng cho gói đã chọn.", help: "Khi coupon không match gói." },
  { key: "ALERT_DISCOUNT_PLAN_INVALID", label: "Gói coupon không hợp lệ", placeholder: "Gói áp dụng không hợp lệ.", help: "Khi plan key không đọc được." },
  { key: "ALERT_DISCOUNT_ZERO_AMOUNT", label: "Coupon về 0đ", placeholder: "Mã giảm giá làm đơn về 0đ. Hãy dùng coupon kích hoạt thay vì coupon giảm giá.", help: "Chặn coupon giảm giá làm đơn còn 0đ." },
];

const ALERT_EN_OVERRIDES: Partial<Record<string, Partial<ConfigField>>> = {
  ALERT_SPAM: {
    placeholder: "⏳ Please slow down a bit.",
    help: "Shown when the user taps too quickly.",
  },
  ALERT_SPAM_QR: {
    placeholder: "⏳ Slow down a bit. Please wait 15 seconds before creating this payment again.",
    help: "Shown when the user creates payment too quickly.",
  },
  ALERT_MAINTENANCE: {
    placeholder: "🛠 The bot is under maintenance. Please come back later.",
    help: "Shown while the bot is in maintenance mode.",
  },
  ALERT_QR_EXPIRED: {
    placeholder: "⏳ Your QR code has expired. Please create a new order.",
    help: "Shown when the user checks an expired QR.",
  },
  ALERT_PAID_SUCCESS: {
    placeholder: "✅ Payment received successfully!",
    help: "Shown when the gateway confirms PAID.",
  },
  ALERT_NOT_PAID: {
    placeholder: "⏳ We have not received the payment yet.",
    help: "Shown when the user checks payment but the gateway is not PAID yet.",
  },
  ALERT_CANCELLED: {
    placeholder: "🚫 The order has been cancelled.",
    help: "Shown when the user cancels the QR order.",
  },
  ALERT_EARLY_RENEW_OFF: {
    placeholder: "Early renewal is currently off. Please renew at the regular price.",
    help: "Shown when the early renew offer is disabled.",
  },
  ALERT_POLICY_UNAVAILABLE: {
    placeholder: "The policy page is unavailable right now.",
    help: "Shown when the policy page cannot be opened.",
  },
  ALERT_SUPPORT_UNAVAILABLE: {
    placeholder: "The support page is unavailable right now.",
    help: "Shown when the support page cannot be opened.",
  },
  ALERT_COUPON_MENU_DISABLED: {
    placeholder: "The coupon entry feature is hidden in the menu.",
    help: "Shown when the coupon menu is disabled.",
  },
  ALERT_COUPON_PRIVATE_ONLY: {
    placeholder: "Please DM the bot to enter the code.",
    help: "Shown when coupon entry is blocked in group chat.",
  },
  ALERT_COUPON_SELECTION_INVALID: {
    placeholder: "Invalid coupon selection.",
    help: "Shown when coupon selection callback format is invalid.",
  },
  ALERT_COUPON_NOT_GROUP_SELECT: {
    placeholder: "This is not a collection-selection coupon.",
    help: "Shown when the callback does not match a selectable-group coupon.",
  },
  ALERT_COUPON_GROUP_OUT_OF_SCOPE: {
    placeholder: "This collection is outside the coupon scope.",
    help: "Shown when a coupon does not apply to the selected collection.",
  },
  ALERT_RENEW_CODE_INVALID: {
    placeholder: "Invalid renewal code.",
    help: "Shown when renewal callback format is invalid.",
  },
  ALERT_RENEW_OFFER_INVALID: {
    placeholder: "The renewal offer is no longer valid.",
    help: "Shown when the renewal offer data is missing or stale.",
  },
  ALERT_RENEW_NOT_OWNER: {
    placeholder: "This offer does not belong to your account.",
    help: "Shown when a user taps someone else's offer.",
  },
  ALERT_RENEW_EXPIRED: {
    placeholder: "This early-renew offer has expired or is no longer valid.",
    help: "Shown when the offer is no longer eligible.",
  },
  ALERT_DISCOUNT_INVALID: {
    placeholder: "Invalid discount code.",
    help: "Shown when the discount callback format is invalid.",
  },
  ALERT_DISCOUNT_NOT_APPLICABLE: {
    placeholder: "This code does not apply to the selected plan.",
    help: "Shown when the coupon does not match the plan.",
  },
  ALERT_DISCOUNT_PLAN_INVALID: {
    placeholder: "Invalid plan for this coupon.",
    help: "Shown when the plan key cannot be read.",
  },
  ALERT_DISCOUNT_ZERO_AMOUNT: {
    placeholder: "This discount would reduce the order to 0. Use an activation coupon instead.",
    help: "Shown when a discount coupon would make the order free.",
  },
};

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
    placeholder: "🔥 <b>FLASH SALE HANG CÚ VIP ĐANG MỞ</b>\\n\\n{sale_lines}\\n\\nSale kết thúc sau: {countdown}",
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
    placeholder: "🔥 Mua Combo Trọn Đời => buy_full_life\\n💎 Mua Combo 30 Ngày => buy_full_1m",
    help: "Mỗi dòng là một nút. Dùng cú pháp Text => callback.",
    kind: "textarea",
  },
];

const PLAN_FIELDS: ConfigField[] = [
  { key: "PLAN_COMBO_30D", label: "Tên gói Combo 30 ngày", placeholder: "Combo 30 Ngày", help: "Tên gói hiển thị khi khách mua Combo 30 ngày. Fallback từ PLAN_ALL_ACCESS_30D." },
  { key: "PLAN_COMBO_LIFE", label: "Tên gói Combo trọn đời", placeholder: "Combo Trọn Đời", help: "Tên gói hiển thị khi khách mua Combo trọn đời. Fallback từ PLAN_ALL_ACCESS_LIFE." },
  { key: "PLAN_COMBO_30D_ALIASES", label: "Alias gói Combo 30 ngày", placeholder: "All Access 30 Ngày, SVIP 30 Ngày, FULL 30D", help: "Các tên cũ vẫn được hiểu là cùng gói 30 ngày. Phân tách bằng dấu phẩy hoặc xuống dòng.", kind: "textarea" },
  { key: "PLAN_COMBO_LIFE_ALIASES", label: "Alias gói Combo trọn đời", placeholder: "All Access Trọn Đời, SVIP Trọn Đời, FULL LIFE", help: "Các tên cũ vẫn được hiểu là cùng gói trọn đời. Phân tách bằng dấu phẩy hoặc xuống dòng.", kind: "textarea" },
  { key: "PLAN_COLLECTION_30D", label: "Tiền tố gói collection 30 ngày", placeholder: "Collection 30 Ngày", help: "Ghép với tên collection, ví dụ: Collection 30 Ngày - Hang Cú Prime." },
  { key: "PLAN_COLLECTION_LIFE", label: "Tiền tố gói collection trọn đời", placeholder: "Collection Trọn Đời", help: "Ghép với tên collection, ví dụ: Collection Trọn Đời - Hang Cú Prime." },
  { key: "PRICE_COMBO_30D", label: "Giá Combo 30 ngày", placeholder: "99000", help: "Nhập số tiền VND, không cần dấu chấm." },
  { key: "PRICE_COMBO_LIFE", label: "Giá Combo trọn đời", placeholder: "499000", help: "Nhập số tiền VND, không cần dấu chấm." },
  { key: "PRICE_COMBO_30D_USD", label: "Giá USD Combo 30 ngày", placeholder: "4.99", help: "Giá PayPal độc lập, không quy đổi từ VNĐ." },
  { key: "PRICE_COMBO_LIFE_USD", label: "Giá USD Combo trọn đời", placeholder: "19.99", help: "Giá PayPal độc lập, không quy đổi từ VNĐ." },
  { key: "BTN_BUY_COMBO_30D", label: "Nút mua Combo 30 ngày", placeholder: "MUA 30 NGÀY", help: "Text nút trong bot." },
  { key: "BTN_BUY_COMBO_LIFE", label: "Nút mua Combo trọn đời", placeholder: "MUA TRỌN ĐỜI", help: "Text nút trong bot." },
];

function localizedFields(fields: ConfigField[], language: "EN"): ConfigField[] {
  return fields.map((field) => ({
    ...field,
    key: `${field.key}_${language}`,
    label: `${field.label} - English`,
    help: `English-only content for the bot. ${field.help}`,
  }));
}

const PLAN_DISPLAY_FIELDS = PLAN_FIELDS.filter((field) => !field.key.startsWith("PRICE_"));
const COMBO_PRICE_FIELDS = PLAN_FIELDS.filter((field) => field.key.startsWith("PRICE_"));
const PLAN_VI_FIELDS = PLAN_DISPLAY_FIELDS;
const PLAN_EN_FIELDS: ConfigField[] = localizedFields(PLAN_DISPLAY_FIELDS, "EN");
const BUTTON_EN_FIELDS = localizedFields(BUTTON_FIELDS, "EN");
const MESSAGE_EN_FIELDS = localizedFields(MESSAGE_FIELDS, "EN");
const ALERT_EN_FIELDS = localizedFields(ALERT_FIELDS, "EN").map((field) => ({ ...field, ...ALERT_EN_OVERRIDES[field.key] }));
const MESSAGE_EN_PAYMENT_OVERRIDES: Partial<Record<string, Partial<ConfigField>>> = {
  MSG_BILL_TEMPLATE: {
    placeholder: "Order ID: {desc}\nAmount: {amount}\nBank: {bank}",
    help: "Use {plan}, {amount}, {bank}, {name}, {stk}, {desc}.",
  },
  MSG_PAYPAL_BILL_TEMPLATE: {
    placeholder: "💳 <b>PAYPAL PAYMENT</b>\n\n🎁 Plan: <b>{plan}</b>\n💵 Amount: <b>{amount}</b>\n🧾 Order: <code>{desc}</code>",
    help: "Use {plan}, {amount}, {paypal_amount}, {desc}.",
  },
  MSG_TRON_USDT_BILL_TEMPLATE: {
    placeholder: "₮ <b>USDT TRC20 PAYMENT</b>\n\n🎁 Plan: <b>{plan}</b>\n💵 Amount: <code>{amount}</code>\n🌐 Network: <b>TRC20</b>\n👛 Receiving wallet:\n<code>{wallet}</code>\n🧾 Order: <code>{desc}</code>\n\nPlease send the exact amount shown above. The bot will monitor the blockchain and grant access once the transaction is confirmed.",
    help: "Use {plan}, {amount}, {usdt_amount}, {wallet}, {desc}.",
  },
  MSG_CHOOSE_PAYMENT_PROVIDER: {
    placeholder: "Choose a payment method. VietQR uses VND; PayPal and Crypto use separate USD pricing.",
    help: "Sent when a plan has multiple enabled payment methods.",
  },
  MSG_NEW_CUSTOMER_MANUAL_ONLY: {
    placeholder: "This is your first purchase, so the order is handled manually to avoid auto payment for new users. Please contact admin for help.",
    help: "Shown when a new user is blocked from auto payment.",
  },
  MSG_RETURNING_CUSTOMER_AUTO_DISABLED: {
    placeholder: "You have bought VIP before, but auto payment is currently turned off. Please contact admin for manual handling.",
    help: "Shown when a returning user is blocked from auto payment.",
  },
  MSG_TIMEOUT_QR: {
    placeholder: "⏳ Your QR code expired after {minutes} minutes. Please create a new order to pay.",
    help: "Use {minutes}. Sent after the auto-check timer expires.",
  },
  MSG_DELIVERY: {
    placeholder: "✅ <b>PAYMENT CONFIRMED!</b>\n\n🎁 Plan: <b>{plan}</b>\n📅 Access until: <code>{date}</code>\n\n🔗 Your access links:\n{links}\n\n💬 Support group: {support}",
    help: "Use {plan}, {date}, {links}, {support}. QR message is removed before delivery.",
  },
  MSG_COUPON_SUCCESS: {
    placeholder: "Code: {code}\nPlan: {plan}\nValid until: {expire}\n{links}",
    help: "Use {code}, {plan}, {expire}, {links}.",
  },
  MSG_COUPON_PROMPT: {
    placeholder: "<b>Enter your discount code / activation code</b>\n\nSend the code you received here.",
    help: "Shown when the user taps coupon entry.",
  },
  MSG_COUPON_DISCOUNT_OPTIONS: {
    placeholder: "Code: {code}\nDiscount: {percent}%\nChoose the plan you want below.",
    help: "Use {code}, {percent}.",
  },
  MSG_COUPON_GROUP_OPTIONS: {
    placeholder: "Code: {code}\nDuration: {duration_label}\nChoose the collection you want to activate below.",
    help: "Use {code}, {days}, {duration_label}.",
  },
  MSG_WAIT_QR: {
    placeholder: "⏳ Generating your QR code...",
    help: "Temporary text while the bot calls PayOS.",
  },
  MSG_QR_ERROR: {
    placeholder: "❌ Payment gateway error!",
    help: "Shown when PayOS cannot create an order.",
  },
  MSG_ME_TITLE: {
    placeholder: "👤 <b>YOUR CURRENT PLAN(S):</b>\n\n",
    help: "Header for the account page.",
  },
  MSG_ME_EMPTY: {
    placeholder: "❌ You do not have any VIP plan yet.",
    help: "Shown when the customer has no PAID order.",
  },
  MSG_ME_ITEM: {
    placeholder: "🎁 Plan: <b>{plan}</b>\n📅 Valid until: <code>{date}</code>\n\n",
    help: "Use {plan}, {date}.",
  },
  MSG_POLICY: {
    placeholder: "Policy is being updated...",
    help: "Used when policy_page menu page is missing.",
  },
  MSG_SUPPORT: {
    placeholder: "Support is being updated...",
    help: "Used when the support menu page is missing.",
  },
  MSG_UPDATING: {
    placeholder: "🌟 <b>UPDATING CONTENT...</b>",
    help: "Fallback when a page has no content.",
  },
  MSG_RELOAD_DONE: {
    placeholder: "🔄 Refreshed all bot data and UI from the system!",
    help: "Returned when admin runs /reload.",
  },
  MSG_ADMIN_ONLY: {
    placeholder: "⚠️ This command is for admins only.",
    help: "Used when a regular user calls an admin command.",
  },
  MSG_CHECK_EXPIRY_STARTED: {
    placeholder: "⏳ Running expiry check now...",
    help: "Returned when admin runs /check_expiry.",
  },
  MSG_CHECK_EXPIRY_DONE: {
    placeholder: "✅ Finished one expiry scan.",
    help: "Returned when /check_expiry completes.",
  },
  MSG_EARLY_RENEW_STATUS: {
    placeholder: "EARLY_RENEW status: <b>{status}</b>\nUse: /early_renew on or /early_renew off",
    help: "Use {status}.",
  },
  MSG_EARLY_RENEW_ON: {
    placeholder: "✅ EARLY_RENEW is now ON. Renewal reminders will include a discount when eligible.",
    help: "Returned when admin enables /early_renew.",
  },
  MSG_EARLY_RENEW_OFF: {
    placeholder: "✅ EARLY_RENEW is now OFF. Renewal reminders will use the normal renewal text and button.",
    help: "Returned when admin disables /early_renew.",
  },
  MSG_EARLY_RENEW_USAGE: {
    placeholder: "Usage: /early_renew on or /early_renew off",
    help: "Returned when /early_renew is used with a wrong syntax.",
  },
  MSG_COUPON_NO_SELECTABLE_GROUPS: {
    placeholder: "❌ The code is valid, but no selectable collection has been configured yet.",
    help: "Used when coupon selection is enabled but no collection is configured.",
  },
  MSG_COUPON_PLAN_NOT_CONFIGURED: {
    placeholder: "❌ The code is valid, but this plan has no collection configured for link delivery.",
    help: "Used when a coupon is valid but no collection link can be generated.",
  },
  MSG_COUPON_PRIVATE_ONLY: {
    placeholder: "Please DM the bot to enter the code so it does not leak in the group.",
    help: "Shown when the user enters a coupon in a group.",
  },
  MSG_COUPON_INVALID_FORMAT: {
    placeholder: "Invalid code. Please enter the code you received again.",
    help: "Shown when the code is too short or empty.",
  },
  MSG_HIDDEN_VALID_TITLE: {
    placeholder: "✅ Hidden code is valid",
    help: "Title shown when a hidden code is valid.",
  },
  MSG_HIDDEN_VALID_BODY: {
    placeholder: "Choose a plan below to buy:",
    help: "Description shown when a hidden code is valid.",
  },
  MSG_HIDDEN_GROUP_TEMPLATE: {
    placeholder: "• <b>{name}</b>\n  {description}",
    help: "Template for each hidden group in the catalog. Uses {name}, {description}.",
  },
  BTN_HIDDEN_BUY_TEMPLATE: {
    placeholder: "Buy {duration_label} - {name} - {price}",
    help: "Template for hidden group purchase buttons. Uses {duration_label}, {name}, {price}, {days}, {group_id}.",
  },
  LABEL_HIDDEN_DURATION_1M: {
    placeholder: "30 days",
    help: "Text used for {duration_label} on hidden 30-day purchase buttons.",
  },
  LABEL_HIDDEN_DURATION_LIFE: {
    placeholder: "lifetime",
    help: "Text used for {duration_label} on hidden lifetime purchase buttons.",
  },
  MSG_HIDDEN_NOT_FOUND: {
    placeholder: "Hidden code not found.",
    help: "Shown when the user enters an invalid code.",
  },
  MSG_HIDDEN_INACTIVE: {
    placeholder: "This hidden code is disabled.",
    help: "Shown when the code is turned off.",
  },
  MSG_HIDDEN_NOT_STARTED: {
    placeholder: "This hidden code is not open yet.",
    help: "Shown when valid_from is still in the future.",
  },
  MSG_HIDDEN_EXPIRED: {
    placeholder: "This hidden code has expired.",
    help: "Shown when valid_until has passed.",
  },
  MSG_HIDDEN_LIMIT_REACHED: {
    placeholder: "This hidden code has reached its usage limit.",
    help: "Shown when the code has reached max uses.",
  },
  MSG_HIDDEN_NO_GROUPS: {
    placeholder: "This code is valid, but no hidden group is currently available.",
    help: "Shown when the code is valid but no active hidden group remains.",
  },
  MSG_HIDDEN_REQUIREMENT_SVIP_ACTIVE: {
    placeholder: "You need an active Combo plan to unlock this code.",
    help: "Shown when the rule requires an active Combo plan.",
  },
  MSG_HIDDEN_REQUIREMENT_SVIP_LIFETIME: {
    placeholder: "You need a lifetime Combo plan to unlock this code.",
    help: "Shown when the rule requires lifetime Combo.",
  },
  MSG_HIDDEN_REQUIREMENT_PLAN_TOKEN_ACTIVE: {
    placeholder: "You need an active {plan_token} plan to unlock this code.",
    help: "Shown when the rule requires an active plan token.",
  },
  MSG_HIDDEN_REQUIREMENT_PLAN_TOKEN_LIFETIME: {
    placeholder: "You need a lifetime {plan_token} plan to unlock this code.",
    help: "Shown when the rule requires a lifetime plan token.",
  },
  MSG_HIDDEN_REQUIREMENT_GENERIC: {
    placeholder: "Your account is not eligible to unlock this code.",
    help: "Fallback when the requirement does not match a specific message.",
  },
  MSG_HIDDEN_DEEPLINK_INVALID: {
    placeholder: "❌ This hidden purchase link is invalid.",
    help: "Shown when the hidden /start payload has an invalid format.",
  },
};
const MESSAGE_EN_FIELDS_WITH_DEFAULTS = MESSAGE_EN_FIELDS.map((field) => ({ ...field, ...MESSAGE_EN_PAYMENT_OVERRIDES[field.key] }));
const VISIBLE_MESSAGE_EN_FIELDS = MESSAGE_EN_FIELDS_WITH_DEFAULTS.filter((field) => !AUTO_PAYMENT_MESSAGE_EN_KEYS.has(field.key) && !field.key.startsWith("MSG_HIDDEN_") && !HIDDEN_MESSAGE_FIELD_KEYS.has(field.key.replace(/_EN$/, "")));
const HIDDEN_MESSAGE_EN_FIELDS = localizedFields(HIDDEN_MESSAGE_FIELDS, "EN").map((field) => ({ ...field, ...MESSAGE_EN_PAYMENT_OVERRIDES[field.key] }));
const COMMAND_EN_FIELDS = localizedFields(COMMAND_FIELDS, "EN");
const SALE_CONTENT_EN_FIELDS = localizedFields(SALE_CONTENT_FIELDS.filter((field) => field.key !== "SALE_ANNOUNCE_ENABLED"), "EN");

const PRICE_KEY_OPTIONS = [
  "PRICE_COMBO_30D",
  "PRICE_COMBO_LIFE",
  "PRICE_COMBO_30D_USD",
  "PRICE_COMBO_LIFE_USD",
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
  plan_mode: "",
  entitlement_type: "ALL_ACCESS",
  entitlement_key: "",
  
  special_group_id: "",
  special_group_duration: "1M",
  note: "",
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
  { value: "SVIP_ACTIVE", label: "Phải có Combo active" },
  { value: "SVIP_LIFETIME", label: "Phải có Combo trọn đời" },
  { value: "PLAN_TOKEN_ACTIVE", label: "Phải có plan token active" },
  { value: "PLAN_TOKEN_LIFETIME", label: "Phải có plan token trọn đời" },
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

const DEFAULT_LIFETIME_DAYS = "3650";

const ORDER_PAGE_SIZE = 25;
const CUSTOMER_PAGE_SIZE = 25;
const LOG_PAGE_SIZE = 40;
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

function isLifetimePlanKey(planName: string) {
  const key = String(planName || "").trim().toUpperCase().replace(/\s+/g, "");
  return key === "FULL_LIFE" || key === "SVIP_LIFE" || key === "SELECT_GROUP_LIFE" || key.endsWith("_LIFE");
}

function isLifetimeCouponPlan(planName: string) {
  return isLifetimePlanKey(planName);
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
  const expire = safeDateMillis(coupon.expires_at);
  return expire !== null && expire <= Date.now();
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
    sum[currency] = (sum[currency] || 0) + orderAmountValue(order, order[field]);
    return sum;
  }, {} as Record<string, number>);
  const parts = Object.entries(totals).map(([currency, total]) => formatRevenueCurrency(currency, total));
  return parts.length ? parts.join(" + ") : money(0);
}

function ordersAverageMoney(orders: Order[]) {
  const paid = orders.filter((order) => order.status === "PAID");
  const groups = groupRevenueByCurrency(paid);
  const parts = Object.entries(groups).map(([currency, items]) => formatRevenueCurrency(currency, items.reduce((sum, order) => sum + orderAmountValue(order), 0) / items.length));
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
    TRON_USDT: "USDT TRC20",
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
  const millis = safeDateMillis(value);
  return millis === null ? null : new Date(millis).toISOString();
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
  const date = safeDateMillis(value);
  if (date === null) return "-";
  return dateText(new Date(date + days * 86400000).toISOString());
}

function normalizeChatId(value: string | number | null | undefined) {
  const raw = String(value ?? "").trim();
  if (!raw) return "";
  return raw.endsWith(".0") ? raw.slice(0, -2) : raw;
}

function configIsOn(config: ConfigRow[], key: string, fallback = "OFF") {
  return ["ON", "TRUE", "YES", "1", "BẬT", "BAT"].includes(String(getConfigValue(config, key, fallback) || fallback).trim().toUpperCase());
}

export default function Home() {
  const isDevPreview = process.env.NODE_ENV !== "production";
  const router = useRouter();
  const [secret, setSecret] = useState("");
  const [savedSecret, setSavedSecret] = useState("");
  const [tab, setTab] = useState<Tab>("overview");
  const [contentTab, setContentTab] = useState<ContentSubTab>("bot");
  const [botViTab, setBotViTab] = useState<BotUiSubTab>("plans");
  const [botEnTab, setBotEnTab] = useState<BotUiSubTab>("plans");
  const [botToolsTab, setBotToolsTab] = useState<BotToolsSubTab>("groupReplies");
  const [menuBotTab, setMenuBotTab] = useState<MenuBotSubTab>("pages");
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
  const [vipMemberAudit, setVipMemberAudit] = useState<VipMemberAuditRow[]>([]);
  const [licenses, setLicenses] = useState<LicenseRecord[]>([]);
  const [licenseSessions, setLicenseSessions] = useState<LicenseSession[]>([]);
  const [licenseAudits, setLicenseAudits] = useState<LicenseAuditEvent[]>([]);
  const [vipMemberAuditRiskType, setVipMemberAuditRiskType] = useState<"ALL" | "NO_ORDER" | "EXPIRED_ORDER">("ALL");
  const [dashboardSummary, setDashboardSummary] = useState<DashboardSummary | null>(null);
  const [dashboardOverview, setDashboardOverview] = useState<OverviewDashboard | null>(null);
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.location.pathname !== "/") return;
    if (window.localStorage.getItem("prive_admin_desktop") === "1") return;
    if (!window.matchMedia("(max-width: 900px)").matches) return;
    router.replace("/mobile");
  }, [router]);
  const [marketingStats, setMarketingStats] = useState<MarketingStatsResponse | null>(null);
  const [marketingRange, setMarketingRange] = useState<"today" | "7d" | "month" | "year">("month");
  const marketingRefreshTimerRef = useRef<number | null>(null);
  const [activityEvents, setActivityEvents] = useState<ActivityEvent[]>([]);
  const [customerIdentityHistory, setCustomerIdentityHistory] = useState<CustomerIdentityHistoryRow[]>([]);
  const [activityLogResponse, setActivityLogResponse] = useState<ActivityLogResponse | null>(null);
  const [activityLogLoading, setActivityLogLoading] = useState(false);
  const [campaigns, setCampaigns] = useState<BroadcastCampaign[]>([]);
  const [campaignRecipients, setCampaignRecipients] = useState<BroadcastRecipient[]>([]);
  const [campaignPreview, setCampaignPreview] = useState<CampaignPreview | null>(null);
  const [channelPosts, setChannelPosts] = useState<ChannelPost[]>([]);
  const [channelEvents, setChannelEvents] = useState<ChannelPostEvent[]>([]);
  const [supportCheck, setSupportCheck] = useState<SupportGroupCheck | null>(null);
  const [webhook, setWebhook] = useState<WebhookInfo | null>(null);
  const [webhookMeta, setWebhookMeta] = useState<WebhookInfoMeta | null>(null);
  const [botScheduleStatusApi, setBotScheduleStatusApi] = useState<BotScheduleStatus | null>(null);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState("");
  const [query, setQuery] = useState("");
  const [orderTab, setOrderTab] = useState<"paid" | "other">("paid");
  const [orderPeriod, setOrderPeriod] = useState<OrderPeriod>("all");
  const [orderPage, setOrderPage] = useState(1);
  const [customerPage, setCustomerPage] = useState(1);
  const [customerStatus, setCustomerStatus] = useState<CustomerStatusFilter>("all");
  const [customerGroup, setCustomerGroup] = useState("ALL");
  const [customerPlanKind, setCustomerPlanKind] = useState("ALL");
  const [selectedCustomerId, setSelectedCustomerId] = useState("");
  const [customerModalOpen, setCustomerModalOpen] = useState(false);
  const [customerDetailTab, setCustomerDetailTab] = useState<CustomerDetailTab>("orders");
  const [customerTimelineSubTab, setCustomerTimelineSubTab] = useState<CustomerTimelineSubTab>("all");
  const [customerOrderTab, setCustomerOrderTab] = useState<CustomerOrderTab>("paid");
  const [customerRenewModalOpen, setCustomerRenewModalOpen] = useState(false);
  const [customerRenewForm, setCustomerRenewForm] = useState({
    order_id: "",
    plan_name: "",
    note: "",
    amount: "",
    duration_days: "30",
    payment_currency: "VND",
    payment_provider: "MANUAL",
  });
  const [customerQuickLookupOpen, setCustomerQuickLookupOpen] = useState(false);
  const [customerQuickLookupQuery, setCustomerQuickLookupQuery] = useState("");
  const [customerQuickLookupResults, setCustomerQuickLookupResults] = useState<CustomerSearchResult[]>([]);
  const [customerQuickLookupLoading, setCustomerQuickLookupLoading] = useState(false);
  const [customerQuickLookupSearched, setCustomerQuickLookupSearched] = useState(false);
  const [logDirection, setLogDirection] = useState<LogDirectionFilter>("all");
  const [logType, setLogType] = useState("ALL");
  const [logDate, setLogDate] = useState("ALL");
  const [logPage, setLogPage] = useState(1);
  const activityLogFilterRef = useRef({ query: "", direction: "all" as LogDirectionFilter, type: "ALL", date: "ALL" });
  const activityLogSkipNextFetchRef = useRef(false);
  const activityLogRequestIdRef = useRef(0);
  const [adminReplyOpen, setAdminReplyOpen] = useState(false);
  const [adminReplyTarget, setAdminReplyTarget] = useState<{ id: string; userId: string; fullName: string; username: string; sourceText: string; ticketId?: string } | null>(null);
  const [adminReplyThread, setAdminReplyThread] = useState<SupportCaseItem | null>(null);
  const [adminReplyThreadLoading, setAdminReplyThreadLoading] = useState(false);
  const [adminReplyThreadMessageLimit, setAdminReplyThreadMessageLimit] = useState(12);
  const [adminReplyText, setAdminReplyText] = useState("");
  const [adminReplyOptimisticMessage, setAdminReplyOptimisticMessage] = useState<SupportMessage | null>(null);
  const adminReplyFallbackTimerRef = useRef<number | null>(null);
  const adminReplyThreadBottomRef = useRef<HTMLDivElement | null>(null);
  const adminReplyStickToBottomRef = useRef(false);
  const [campaignForm, setCampaignForm] = useState({ ...EMPTY_CAMPAIGN_FORM });
  const [campaignModalOpen, setCampaignModalOpen] = useState(false);
  const [selectedCampaignId, setSelectedCampaignId] = useState("");
  const [campaignRecipientPage, setCampaignRecipientPage] = useState(1);
  const [channelPostForm, setChannelPostForm] = useState({ ...EMPTY_CHANNEL_POST_FORM });
  const [channelPostModalOpen, setChannelPostModalOpen] = useState(false);
  const [adminNotifications, setAdminNotifications] = useState<AdminNotificationItem[]>([]);
  const [notificationSeenIds, setNotificationSeenIds] = useState<string[]>([]);
  const [notificationExpandedIds, setNotificationExpandedIds] = useState<string[]>([]);
  const [notificationMenuAnchorEl, setNotificationMenuAnchorEl] = useState<HTMLElement | null>(null);
  const [supportInboxSeenIds, setSupportInboxSeenIds] = useState<string[]>([]);
  const [supportInboxMenuAnchorEl, setSupportInboxMenuAnchorEl] = useState<HTMLElement | null>(null);
  const [supportInboxCases, setSupportInboxCases] = useState<SupportCaseItem[]>([]);
  const [supportInboxCasesLoading, setSupportInboxCasesLoading] = useState(false);
  const refreshSupportInboxCases = useCallback(async () => {
    if (!savedSecret) return;
    setSupportInboxCasesLoading(true);
    try {
      const res = await getSupportCases(savedSecret, "", 12);
      setSupportInboxCases(res.data || []);
    } catch (err) {
      console.warn("⚠️ Không tải được support cases:", err);
    } finally {
      setSupportInboxCasesLoading(false);
    }
  }, [savedSecret]);
  const [channelPostTab, setChannelPostTab] = useState<ChannelPostTab>("queue");
  const [channelPostPage, setChannelPostPage] = useState(1);
  const [selectedChannelPostId, setSelectedChannelPostId] = useState<number | null>(null);
  const [renewalTab, setRenewalTab] = useState<RenewalSubTab>("soon");
  const [renewalPage, setRenewalPage] = useState(1);
  const [renewalSettingsOpen, setRenewalSettingsOpen] = useState(false);
  const [renewalQuery, setRenewalQuery] = useState("");
  const [renewalFocusFilter, setRenewalFocusFilter] = useState<RenewalFocusFilter>("all");
  const [renewalLiveCheck, setRenewalLiveCheck] = useState(false);
  const [supportTab, setSupportTab] = useState<SupportSubTab>("all");
  const [supportPage, setSupportPage] = useState(1);
  const [securitySettingsOpen, setSecuritySettingsOpen] = useState(false);
  const [systemSettingsOpen, setSystemSettingsOpen] = useState(false);
  const [orderSettingsOpen, setOrderSettingsOpen] = useState(false);
  const [orderEditorOpen, setOrderEditorOpen] = useState(false);
  const [orderEditorOrderId, setOrderEditorOrderId] = useState("");
  const [orderEditorForm, setOrderEditorForm] = useState({
    status: "PENDING",
    plan_name: "",
    amount: "",
    payment_currency: "VND",
    expire_at: "",
    paid_at: "",
    coupon_code: "",
    note: "",
  });
  const orderEditorPlanInputRef = useRef<HTMLInputElement | null>(null);
  const notificationSoundRef = useRef<{ playedAt: number }>({ playedAt: 0 });
  const [comboSettingsOpen, setComboSettingsOpen] = useState(false);
  const [comboSettingsTab, setComboSettingsTab] = useState<"price" | "name">("price");
  const [comboSettingsVariant, setComboSettingsVariant] = useState<"30d" | "life">("30d");
  const [groupModalOpen, setGroupModalOpen] = useState(false);
  const [groupNo, setGroupNo] = useState("1");
  const [groupName, setGroupName] = useState("");
  const [groupNameEn, setGroupNameEn] = useState("");
  const [groupAliases, setGroupAliases] = useState("");
  const [groupId, setGroupId] = useState("");
  const [groupPrice1m, setGroupPrice1m] = useState("");
  const [groupPriceLife, setGroupPriceLife] = useState("");
  const [groupPrice1mUsd, setGroupPrice1mUsd] = useState("");
  const [groupPriceLifeUsd, setGroupPriceLifeUsd] = useState("");
  const groupAliasRef = useRef<HTMLTextAreaElement | null>(null);
  const [groupAliasFocusKey, setGroupAliasFocusKey] = useState("");
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [menuForm, setMenuForm] = useState({ page_id: "main_menu", image_url: "", body: "", layout: "" });
  const [menuModalOpen, setMenuModalOpen] = useState(false);
  const [saleForm, setSaleForm] = useState({ sale_id: "", price_key: "PRICE_COMBO_30D", discount_percent: "", sale_price: "", slot_limit: "", enabled: "ON", start_at: "", end_at: "" });
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
  const [specialGroupSettingsOpen, setSpecialGroupSettingsOpen] = useState(false);
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
  const [blacklistQuery, setBlacklistQuery] = useState("");
  const [blacklistStatusFilter, setBlacklistStatusFilter] = useState<"all" | "active" | "inactive" | "reason">("all");
  const [demoDataInjected, setDemoDataInjected] = useState(false);
  const [paymentSchema, setPaymentSchema] = useState<PaymentSchemaResponse | null>(null);
  const supportStaffRows = useMemo(() => {
    const raw = getConfigValue(config, "ADMIN_IDS", "");
    const ids = uniqueValues(raw.split(",").map((item) => item.trim()).filter(Boolean));
    const supportConnected = Boolean(supportCheck?.get_chat?.ok && supportCheck?.bot_member?.ok && supportCheck?.invite_link?.ok);
    const supportDetail = supportCheck
      ? supportCheck.get_chat.ok
        ? supportCheck.bot_member.ok
          ? `Đã kết nối ${supportCheck.group_name || "group hỗ trợ"}`
          : supportCheck.bot_member.message || "Bot chưa có quyền trong group hỗ trợ"
        : supportCheck.get_chat.message || "Chưa kết nối group hỗ trợ"
      : "Chưa kiểm tra group hỗ trợ";
    if (!ids.length) {
      return [{ id: "-", alias: "Chưa cấu hình", status: supportConnected ? "Online" : "Offline", tone: supportConnected ? ("good" as const) : ("bad" as const), note: supportDetail, avatar: "?" }];
    }
    return ids.map((id, index) => ({
      id,
      alias: `Staff ${index + 1}`,
      status: supportConnected ? "Online" : "Offline",
      tone: supportConnected ? ("good" as const) : ("bad" as const),
      note: supportDetail,
      avatar: `S${index + 1}`,
    }));
  }, [config, supportCheck]);
  const paymentRailFields = useMemo(() => {
    if (!paymentSchema?.rails?.length) return PAYMENT_RAIL_FIELDS;
    return paymentSchema.rails.flatMap((group) => group.fields || []);
  }, [paymentSchema]);
  const paymentActionFields = useMemo(() => {
    if (!paymentSchema?.actions?.length) return PAYMENT_ACTION_FIELDS;
    return paymentSchema.actions.flatMap((group) => group.fields || []);
  }, [paymentSchema]);
  const notificationEnabled = configIsOn(config, "ADMIN_NOTIFICATION_ENABLED", "ON");
  const notificationOrdersEnabled = configIsOn(config, "ADMIN_NOTIFICATION_ORDERS_ENABLED", "ON");
  const notificationPrivateMessagesEnabled = configIsOn(config, "ADMIN_NOTIFICATION_PRIVATE_MESSAGES_ENABLED", "ON");
  const notificationPollSeconds = Math.max(10, Number(getConfigValue(config, "ADMIN_NOTIFICATION_POLL_SECONDS", "20")) || 20);

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
    const queryTab = new URLSearchParams(window.location.search).get("tab");
    const storedTab = window.localStorage.getItem(TAB_STORAGE_KEY);
    const nextTab = queryTab || storedTab;
    if (nextTab) setTab(nextTab as Tab);
  }, []);

  useEffect(() => {
    const nextValues: Record<string, string> = {};
    config.forEach((item) => {
      nextValues[item.key] = item.value;
    });
    [...ADMIN_FIELDS, ...SUPPORT_GROUP_FIELDS, ...SUPPORT_INBOX_FIELDS, ...SUPPORT_INBOX_EFFECT_FIELDS, ...ORDER_FIELDS, ...CURRENCY_FIELDS, ...BOT_FIELDS, ...MENU_LANGUAGE_FIELDS, ...PAYMENT_FIELDS, ...AUTO_PAYMENT_VI_FIELDS, ...AUTO_PAYMENT_EN_FIELDS, ...AUTO_PAYMENT_SUPPORT_FIELDS, ...AUTO_PAYMENT_SUPPORT_EN_FIELDS, ...RENEWAL_FIELDS, ...SECURITY_FIELDS, ...SYSTEM_FIELDS, ...PRIVATE_MENU_FIELDS, ...GROUP_MENU_FIELDS, ...COMMAND_FIELDS, ...COMMAND_EN_FIELDS, ...GROUP_COMMAND_FIELDS, ...MESSAGE_FIELDS, ...MESSAGE_EN_FIELDS, ...BUTTON_FIELDS, ...BUTTON_EN_FIELDS, ...ALERT_FIELDS, ...ALERT_EN_FIELDS, ...SALE_CONTENT_FIELDS, ...SALE_CONTENT_EN_FIELDS, ...PLAN_FIELDS, ...PLAN_EN_FIELDS].forEach((field) => {
      if (!(field.key in nextValues)) nextValues[field.key] = "";
    });
    Object.keys(nextValues).forEach((key) => {
      if (/^AUTO_PAYMENT_(NEW|RETURNING)_/.test(key)) {
        delete nextValues[key];
      }
    });
    setFieldValues(nextValues);
  }, [config]);

  useEffect(() => {
    if (!customerQuickLookupOpen || blacklist.length || !savedSecret) return;
    void getBlacklist(savedSecret)
      .then((res) => setBlacklist(res.data || []))
      .catch(() => undefined);
  }, [blacklist.length, customerQuickLookupOpen, savedSecret]);

  useEffect(() => {
    const query = customerQuickLookupQuery.trim();
    if (!customerQuickLookupOpen || !savedSecret) return;
    if (query.length < 2) {
      setCustomerQuickLookupResults([]);
      setCustomerQuickLookupLoading(false);
      setCustomerQuickLookupSearched(false);
      return;
    }
    let cancelled = false;
    setCustomerQuickLookupLoading(true);
    const timer = window.setTimeout(() => {
      void searchCustomers(savedSecret, query, 20)
        .then((res) => {
          if (cancelled) return;
          setCustomerQuickLookupResults(res.data || []);
          setCustomerQuickLookupSearched(true);
        })
        .catch((error) => {
          if (cancelled) return;
          setCustomerQuickLookupResults([]);
          setCustomerQuickLookupSearched(true);
          showNotice("error", `Không tra cứu được khách: ${error instanceof Error ? error.message : String(error)}`);
        })
        .finally(() => {
          if (!cancelled) setCustomerQuickLookupLoading(false);
        });
    }, 350);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [customerQuickLookupOpen, customerQuickLookupQuery, savedSecret]);

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
    if (typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem("prive_admin_notification_seen_ids");
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          setNotificationSeenIds(parsed.map((item) => String(item)).filter(Boolean));
        }
      }
    } catch {
      setNotificationSeenIds([]);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const raw = window.localStorage.getItem("prive_admin_support_inbox_seen_ids");
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          setSupportInboxSeenIds(parsed.map((item) => String(item)).filter(Boolean));
        }
      }
    } catch {
      setSupportInboxSeenIds([]);
    }
  }, []);

  useEffect(() => {
    if (!savedSecret) return;
    void loadAdminNotifications(savedSecret, { silent: true });
  }, [savedSecret, notificationEnabled, notificationOrdersEnabled, notificationPrivateMessagesEnabled]);

  useEffect(() => {
    if (!savedSecret || !notificationEnabled) return;
    const baseDelay = Math.max(30, notificationPollSeconds);
    let timeoutId: number | null = null;
    let cancelled = false;
    const schedule = () => {
      const delaySeconds = notificationMenuAnchorEl ? Math.max(baseDelay, 90) : baseDelay;
      timeoutId = window.setTimeout(async () => {
        if (document.visibilityState === "visible") {
          await loadAdminNotifications(savedSecret, { silent: true });
        }
        if (!cancelled) schedule();
      }, delaySeconds * 1000);
    };
    schedule();
    return () => {
      cancelled = true;
      if (timeoutId !== null) window.clearTimeout(timeoutId);
    };
  }, [savedSecret, notificationEnabled, notificationPollSeconds, notificationMenuAnchorEl]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem("prive_admin_notification_seen_ids", JSON.stringify(notificationSeenIds));
    } catch {
      // ignore storage errors
    }
  }, [notificationSeenIds]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem("prive_admin_support_inbox_seen_ids", JSON.stringify(supportInboxSeenIds));
    } catch {
      // ignore storage errors
    }
  }, [supportInboxSeenIds]);

  useEffect(() => {
    if (!savedSecret || tab !== "activityLog") return;
    const currentFilters = { query, direction: logDirection, type: logType, date: logDate };
    const previousFilters = activityLogFilterRef.current;
    const filtersChanged =
      previousFilters.query !== currentFilters.query ||
      previousFilters.direction !== currentFilters.direction ||
      previousFilters.type !== currentFilters.type ||
      previousFilters.date !== currentFilters.date;
    const loadPage = filtersChanged ? 1 : logPage;
    if (filtersChanged) {
      activityLogFilterRef.current = currentFilters;
      if (logPage !== 1) {
        setLogPage(1);
        activityLogSkipNextFetchRef.current = true;
      } else {
        activityLogSkipNextFetchRef.current = false;
      }
    } else if (activityLogSkipNextFetchRef.current && logPage === 1) {
      activityLogSkipNextFetchRef.current = false;
      return;
    }
    const timer = window.setTimeout(() => {
      void loadActivityLogPage(savedSecret, { page: loadPage, query, direction: logDirection, type: logType, date: logDate });
    }, 250);
    return () => window.clearTimeout(timer);
  }, [savedSecret, tab, logPage, logDirection, logType, logDate, query]);

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
    if (!savedSecret) return;
    const interval = window.setInterval(async () => {
      try {
        const res = await getSupportEvents(savedSecret, 200);
        setSupportEvents(res.data || []);
      } catch (err) {
        console.warn("⚠️ Không tải được support events nền:", err);
      }
    }, 30 * 1000);
    return () => window.clearInterval(interval);
  }, [savedSecret]);

  useEffect(() => {
    if (!savedSecret) return;
    void refreshSupportInboxCases();
    const interval = window.setInterval(() => {
      void refreshSupportInboxCases();
    }, 15 * 1000);
    return () => window.clearInterval(interval);
  }, [savedSecret, refreshSupportInboxCases]);

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

  useEffect(() => {
    if (!savedSecret || !selectedCustomerId) {
      setCustomerIdentityHistory([]);
      return;
    }
    let cancelled = false;
    getCustomerIdentityHistory(savedSecret, selectedCustomerId, 50)
      .then((res) => {
        if (!cancelled) setCustomerIdentityHistory(res.data || []);
      })
      .catch(() => {
        if (!cancelled) setCustomerIdentityHistory([]);
      });
    return () => {
      cancelled = true;
    };
  }, [savedSecret, selectedCustomerId]);

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

      const overviewLite = scope === "overview";
      addTask(true, () => getDashboardSummary(activeSecret), setDashboardSummary);
      if (overviewLite) {
        addTask(true, () => getDashboardOverview(activeSecret), setDashboardOverview);
      }
      if (!light && shouldLoad("analytics", "overview")) {
        addTask(true, () => getMarketingStats(activeSecret, marketingRange), setMarketingStats);
      }
      const needsOrders = (!light && shouldLoad("analytics", "orders", "customers", "campaigns", "renewals")) || overviewLite;
      const needsUsers = (!light && shouldLoad("analytics")) || overviewLite;
      const needsConfig = !light;
      const needsPaymentSchema = !light && shouldLoad("payment");
      const needsMenu = !light && shouldLoad("overview", "content", "botVi", "botEn", "menuBot");
      const needsSales = !light && shouldLoad("sales");
      const needsCoupons = !light && shouldLoad("overview", "coupons");
      const needsLicense = !light && shouldLoad("license");
      const needsActivationCodes = !light && shouldLoad("activationCodes");
      const needsHidden = !light && shouldLoad("setup", "coupons", "specialGroups");
      const needsBlacklist = !light && shouldLoad("security");
      const needsSupportEvents = (!light && shouldLoad("renewals", "supportGroup")) || overviewLite;
      const needsKickAudit = !light && shouldLoad("renewals");
      const needsVipGroupAudit = !light && shouldLoad("renewals");
      const needsVipMemberAudit = !light && shouldLoad("vipAudit", "renewals", "security");
      const needsActivityEvents = (!light && shouldLoad("analytics")) || overviewLite;
      const needsCampaigns = shouldLoad("campaigns");
      const needsChannelPosts = shouldLoad("channelPosts");
      const needsWebhook = !light;
      const needsBotScheduleStatus = !light;

      addTask(needsOrders, () => getOrders(activeSecret, overviewLite ? 50 : 5000), setOrders);
      addTask(needsUsers, () => getUsers(activeSecret), setUsers);
      addTask(needsConfig, () => getConfig(activeSecret), setConfig);
      addTask(needsPaymentSchema, () => getPaymentSchema(activeSecret), setPaymentSchema);
      addTask(needsMenu, () => getMenuPages(activeSecret), setMenuPages);
      addTask(needsSales, () => getSaleRules(activeSecret), setSaleRules);
      addTask(needsCoupons, () => getCoupons(activeSecret), setCoupons);
      addTask(needsLicense, () => getLicenses(activeSecret), setLicenses);
      addTask(needsLicense, () => getLicenseSessions(activeSecret), setLicenseSessions);
      addTask(needsLicense, () => getLicenseAudits(activeSecret), setLicenseAudits);
      addTask(needsActivationCodes, () => getActivationCodes(activeSecret), setActivationCodes);
      addTask(needsHidden, () => getHiddenGroups(activeSecret), setHiddenGroups);
      addTask(needsHidden, () => getHiddenCodes(activeSecret), setHiddenCodes);
      addTask(needsHidden, () => getHiddenRedemptions(activeSecret, 200), setHiddenRedemptions);
      addTask(needsBlacklist, () => getBlacklist(activeSecret), setBlacklist);
      addTask(needsSupportEvents, () => getSupportEvents(activeSecret, overviewLite ? 25 : 1000), setSupportEvents);
      addTask(needsKickAudit, () => getKickAudit(activeSecret), setKickAudit);
      addTask(needsVipGroupAudit, () => getVipGroupAudit(activeSecret), setVipGroupAudit);
      addTask(needsVipMemberAudit, () => getVipMemberAudit(activeSecret), setVipMemberAudit);
      addTask(needsActivityEvents, () => getActivityEvents(activeSecret, overviewLite ? 25 : 50), setActivityEvents);
      addTask(needsCampaigns, () => getCampaigns(activeSecret), setCampaigns);
      addTask(needsChannelPosts, () => getChannelPosts(activeSecret), setChannelPosts);
      if (needsWebhook) {
        tasks.push(
          getWebhookInfo(activeSecret).then((res) => {
            setWebhook(res.data);
            setWebhookMeta(res.meta);
          })
        );
      }
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
        setWebhookMeta((current) =>
          current ?? {
            expected_url: "http://127.0.0.1:8000/webhook",
            last_reset_reason: "",
            failure_streak: 0,
            problem_reason: "",
            maintenance_override: { active: false, reason: "", source: "" },
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

  const refreshMarketingStatsDebounced = useCallback((nextRange?: "today" | "7d" | "month" | "year") => {
    if (marketingRefreshTimerRef.current) {
      window.clearTimeout(marketingRefreshTimerRef.current);
    }
    marketingRefreshTimerRef.current = window.setTimeout(async () => {
      if (!savedSecret) return;
      const range = nextRange || marketingRange;
      if (nextRange) setMarketingRange(nextRange);
      const res = await getMarketingStats(savedSecret, range);
      setMarketingStats(res.data);
    }, 280);
  }, [savedSecret, marketingRange]);

  useEffect(() => {
    return () => {
      if (marketingRefreshTimerRef.current) {
        window.clearTimeout(marketingRefreshTimerRef.current);
      }
    };
  }, []);

  async function loadAdminNotifications(activeSecret = savedSecret, options: { silent?: boolean } = {}) {
    if (!activeSecret || !notificationEnabled) {
      setAdminNotifications([]);
      return;
    }
    try {
      const response = await getAdminNotifications(activeSecret, 16);
      setAdminNotifications(response.data.notifications || []);
    } catch (err) {
      if (!options.silent) {
        console.warn("⚠️ Không tải được admin notifications:", err);
      }
    }
  }

  async function loadActivityLogPage(activeSecret = savedSecret, options: { page?: number; limit?: number; query?: string; direction?: string; type?: string; date?: string; silent?: boolean } = {}) {
    if (!activeSecret) return;
    const requestId = ++activityLogRequestIdRef.current;
    const page = Math.max(1, options.page || logPage || 1);
    const limit = Math.max(1, options.limit || LOG_PAGE_SIZE);
    const silent = Boolean(options.silent);
    if (!silent) {
      setActivityLogLoading(true);
    }
    try {
      const response = await getActivityLog(activeSecret, {
        page,
        limit,
        query: options.query ?? query,
        direction: options.direction ?? logDirection,
        type: options.type ?? logType,
        date: options.date ?? logDate,
      });
      if (requestId !== activityLogRequestIdRef.current) return;
      setActivityLogResponse(response);
    } catch (err) {
      if (requestId !== activityLogRequestIdRef.current) return;
      if (!silent) showNotice("error", err instanceof Error ? err.message : "Không tải được nhật ký.");
    } finally {
      if (requestId !== activityLogRequestIdRef.current) return;
      if (!silent) {
        setActivityLogLoading(false);
      }
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
    if (validFrom && validUntil && (safeDateMillis(validUntil) ?? 0) < (safeDateMillis(validFrom) ?? 0)) {
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
      const returnedKeys = new Set((res.data || []).map((item) => item.key));
      setConfig((current) => [
        ...current.filter((item) => !changedKeys.has(item.key) && !returnedKeys.has(item.key)),
        ...res.data,
      ]);
      setFieldValues((current) => ({ ...current, ...Object.fromEntries(items.map((item) => [item.key, item.value])) }));
    });
  }

  function autoPaymentUiValue(key: string, fallback = "", legacyKey = "") {
    const localValue = String(fieldValues[key] || "").trim();
    if (localValue) return localValue;
    return getConfigValue(config, key, legacyKey ? getConfigValue(config, legacyKey, fallback) : fallback);
  }

  async function quickSetAutoPaymentWindow(enabled: boolean) {
    if (!savedSecret) return;
    await runAction(enabled ? "auto-payment-schedule-on" : "auto-payment-schedule-off", async () => {
      const items = enabled
        ? [
          { key: "AUTO_PAYMENT_VI_NEW_ENABLED", value: "ON" },
          { key: "AUTO_PAYMENT_VI_NEW_SCHEDULE_ENABLED", value: "ON" },
          { key: "AUTO_PAYMENT_VI_NEW_WINDOWS", value: "22:00-06:00" },
          { key: "AUTO_PAYMENT_VI_RETURNING_ENABLED", value: "ON" },
          { key: "AUTO_PAYMENT_VI_RETURNING_SCHEDULE_ENABLED", value: "ON" },
          { key: "AUTO_PAYMENT_VI_RETURNING_WINDOWS", value: "22:00-06:00" },
        ]
        : [
          { key: "AUTO_PAYMENT_VI_NEW_ENABLED", value: "OFF" },
          { key: "AUTO_PAYMENT_VI_RETURNING_ENABLED", value: "OFF" },
        ];
      const res = await updateConfigs(savedSecret, items);
      const changedKeys = new Set(items.map((item) => item.key));
      setConfig((current) => [
        ...current.filter((item) => !changedKeys.has(item.key)),
        ...res.data,
      ]);
      setFieldValues((current) => ({ ...current, ...Object.fromEntries(items.map((item) => [item.key, item.value])) }));
      showNotice("ok", enabled ? "Đã bật lịch auto payment cho khách Việt." : "Đã tắt auto payment cho khách Việt.");
    });
  }

  async function quickSetAutoPaymentWindowEn(enabled: boolean) {
    if (!savedSecret) return;
    await runAction(enabled ? "auto-payment-schedule-en-on" : "auto-payment-schedule-en-off", async () => {
      const items = enabled
        ? [
          { key: "AUTO_PAYMENT_EN_NEW_ENABLED", value: "ON" },
          { key: "AUTO_PAYMENT_EN_NEW_SCHEDULE_ENABLED", value: "ON" },
          { key: "AUTO_PAYMENT_EN_NEW_WINDOWS", value: "22:00-06:00" },
          { key: "AUTO_PAYMENT_EN_RETURNING_ENABLED", value: "ON" },
          { key: "AUTO_PAYMENT_EN_RETURNING_SCHEDULE_ENABLED", value: "ON" },
          { key: "AUTO_PAYMENT_EN_RETURNING_WINDOWS", value: "22:00-06:00" },
        ]
        : [
          { key: "AUTO_PAYMENT_EN_NEW_ENABLED", value: "OFF" },
          { key: "AUTO_PAYMENT_EN_RETURNING_ENABLED", value: "OFF" },
        ];
      const res = await updateConfigs(savedSecret, items);
      const changedKeys = new Set(items.map((item) => item.key));
      setConfig((current) => [
        ...current.filter((item) => !changedKeys.has(item.key)),
        ...res.data,
      ]);
      setFieldValues((current) => ({ ...current, ...Object.fromEntries(items.map((item) => [item.key, item.value])) }));
      showNotice("ok", enabled ? "Đã bật lịch auto payment cho khách nước ngoài." : "Đã tắt auto payment cho khách nước ngoài.");
    });
  }

  function normalizeGroupNo(value: string) {
    const normalized = String(value || "").trim().replace(/^G/i, "");
    const match = normalized.match(/^\d+$/);
    return match ? String(Number(match[0])) : "";
  }

  function clearGroupFields() {
    setGroupName("");
    setGroupNameEn("");
    setGroupAliases("");
    setGroupId("");
    setGroupPrice1m("");
    setGroupPriceLife("");
    setGroupPrice1mUsd("");
    setGroupPriceLifeUsd("");
  }

  function loadGroupForm(nextGroupNo: string, mode: "load" | "reset" = "load") {
    const normalized = normalizeGroupNo(nextGroupNo);
    if (!normalized) {
      setGroupNo("");
      clearGroupFields();
      return;
    }
    setGroupNo(normalized);
    const hasValues = hasAnyGroupConfig(config, Number(normalized));
    if (mode === "reset" || !hasValues) {
      clearGroupFields();
      return;
    }
    setGroupName(getConfigValue(config, `BTN_G${normalized}`));
    setGroupNameEn(getConfigValue(config, `BTN_G${normalized}_EN`));
    setGroupAliases(getConfigValue(config, `BTN_G${normalized}_ALIASES`));
    setGroupId(getConfigValue(config, `ID_G${normalized}`));
    setGroupPrice1m(getConfigValue(config, `PRICE_G${normalized}_1M`));
    setGroupPriceLife(getConfigValue(config, `PRICE_G${normalized}_LIFE`));
    setGroupPrice1mUsd(getConfigValue(config, `PRICE_G${normalized}_1M_USD`));
    setGroupPriceLifeUsd(getConfigValue(config, `PRICE_G${normalized}_LIFE_USD`));
  }

  function resetGroupForm(nextGroupNo?: string) {
    const used = new Set(Array.from({ length: maxGroups }, (_, idx) => idx + 1).filter(item => hasAnyGroupConfig(config, item)).map(String));
    const firstEmpty = Array.from({ length: maxGroups }, (_, idx) => String(idx + 1)).find((item) => !used.has(item)) || "1";
    loadGroupForm(nextGroupNo || firstEmpty, "reset");
  }

  function openNewGroupModal() {
    resetGroupForm();
    setGroupModalOpen(true);
  }

  function fillGroupForm(nextGroupNo: string) {
    loadGroupForm(nextGroupNo);
  }

  function openEditGroupModal(nextGroupNo: string) {
    fillGroupForm(nextGroupNo);
    setGroupModalOpen(true);
  }

  function openGroupAliasEditor(nextGroupNo: string) {
    const normalized = normalizeGroupNo(nextGroupNo);
    if (!normalized) return;
    setGroupAliasFocusKey(normalized);
    openEditGroupModal(normalized);
  }

  useEffect(() => {
    if (!groupModalOpen) return;
    if (!groupAliasFocusKey || groupAliasFocusKey !== normalizeGroupNo(groupNo)) return;
    const timer = window.setTimeout(() => {
      groupAliasRef.current?.focus();
      groupAliasRef.current?.select?.();
      setGroupAliasFocusKey("");
    }, 50);
    return () => window.clearTimeout(timer);
  }, [groupModalOpen, groupAliasFocusKey, groupNo]);

  async function saveGroupConfig() {
    await runAction("group", async () => {
      const normalizedGroupNo = normalizeGroupNo(groupNo);
      if (!normalizedGroupNo) {
        showNotice("error", "Vui lòng nhập số nhóm hợp lệ.");
        return;
      }
      const currentName = getConfigValue(config, `BTN_G${normalizedGroupNo}`);
      const currentNameEn = getConfigValue(config, `BTN_G${normalizedGroupNo}_EN`);
      const currentAliases = String(getConfigValue(config, `BTN_G${normalizedGroupNo}_ALIASES`, "") || "");
      const aliasValues = new Set(
        currentAliases
          .split(/[\n,;|]+/)
          .map((value) => value.trim())
          .filter(Boolean),
      );
      if (currentName && currentName.trim() && currentName.trim() !== groupName.trim()) aliasValues.add(currentName.trim());
      if (currentNameEn && currentNameEn.trim() && currentNameEn.trim() !== groupNameEn.trim()) aliasValues.add(currentNameEn.trim());
      String(groupAliases || "").split(/[\n,;|]+/).map((value) => value.trim()).filter(Boolean).forEach((value) => aliasValues.add(value));
      await updateConfigs(savedSecret, [
        { key: canonicalConfigKey(`BTN_G${normalizedGroupNo}`), value: groupName },
        { key: canonicalConfigKey(`BTN_G${normalizedGroupNo}_EN`), value: groupNameEn },
        { key: canonicalConfigKey(`BTN_G${normalizedGroupNo}_ALIASES`), value: Array.from(aliasValues).join("\n") },
        { key: canonicalConfigKey(`ID_G${normalizedGroupNo}`), value: groupId },
        { key: canonicalConfigKey(`PRICE_G${normalizedGroupNo}_1M`), value: groupPrice1m },
        { key: canonicalConfigKey(`PRICE_G${normalizedGroupNo}_LIFE`), value: groupPriceLife },
        { key: canonicalConfigKey(`PRICE_G${normalizedGroupNo}_1M_USD`), value: groupPrice1mUsd },
        { key: canonicalConfigKey(`PRICE_G${normalizedGroupNo}_LIFE_USD`), value: groupPriceLifeUsd },
      ]);
      clearGroupFields();
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
    if (live) showNotice("ok", "Đã kiểm tra live trạng thái nhóm hỗ trợ.");
    });
  }

  async function refreshVipMemberAudit(live = false, riskType: "ALL" | "NO_ORDER" | "EXPIRED_ORDER" = vipMemberAuditRiskType) {
    await runAction(live ? "vip-member-audit-live" : "vip-member-audit-refresh", async () => {
      const res = await getVipMemberAudit(savedSecret, live, riskType);
      setVipMemberAudit(res.data);
      if (live) showNotice("ok", "Đã quét live thành viên VIP đã ghi nhận.");
    });
  }

  async function cleanupVipInviteLinksAction(groupId = "", force = true) {
    await runAction(`vip-invite-cleanup-${groupId || "all"}`, async () => {
      const res = await cleanupVipInviteLinks(savedSecret, { group_id: groupId, force, only_used: false });
      const total = res.data.total || 0;
      const success = res.data.success || 0;
      const failed = res.data.failed || 0;
      setNotice({
        type: failed ? "error" : "ok",
        text: failed
          ? `Đã dọn ${success}/${total} link join, lỗi ${failed} lượt.`
          : `Đã dọn xong ${total} nhóm/link join.`,
      });
      await loadAll(savedSecret, { silent: true, scope: "vipAudit" });
    });
  }

  async function runSupportGroupCheck() {
    await runAction("support-check", async () => {
      const res = await checkSupportGroup(savedSecret);
      setSupportCheck(res.data);
      if (res.data.get_chat.ok && res.data.bot_member.ok && res.data.invite_link.ok) {
        showNotice("ok", "Nhóm hỗ trợ tạo link OK.");
      } else {
        showNotice("error", "Nhóm hỗ trợ chưa tạo được link. Xem chi tiết trong tab.");
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
      "Gói": resolveOrderLabel(item).displayLabel,
      "Số tiền": orderMoney(item),
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
        "Gói": resolveOrderLabel({ plan_name: item.plan_name }).displayLabel,
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

  function openAdminReply(entry: { id: string; userId: string; fullName: string; username: string; title: string; detail: string; ticketId?: string; initialMessages?: SupportMessage[] }) {
    if (!entry.userId) {
      showNotice("error", "Không có Telegram ID để trả lời khách.");
      return;
    }
    setAdminReplyTarget({
      id: entry.id,
      userId: entry.userId,
      fullName: entry.fullName,
      username: entry.username,
      sourceText: entry.title || entry.detail || "",
      ticketId: entry.ticketId,
    });
    setAdminReplyText("");
    setAdminReplyOptimisticMessage(null);
    if (adminReplyFallbackTimerRef.current) {
      window.clearTimeout(adminReplyFallbackTimerRef.current);
      adminReplyFallbackTimerRef.current = null;
    }
    setAdminReplyThread(null);
    setAdminReplyThreadMessageLimit(12);
    adminReplyStickToBottomRef.current = true;
    setAdminReplyOpen(true);
    if (entry.ticketId && entry.initialMessages?.length) {
      setAdminReplyThread({
        ticket: {
          id: entry.ticketId,
          ticket_no: "",
          telegram_user_id: entry.userId,
          username: entry.username || null,
          full_name: entry.fullName || null,
          subject: entry.title || entry.detail || null,
          status: "open",
          source: "support_inbox",
          updated_at: entry.initialMessages[entry.initialMessages.length - 1]?.created_at || new Date().toISOString(),
          created_at: entry.initialMessages[0]?.created_at || new Date().toISOString(),
        },
        messages: entry.initialMessages,
      });
    }
    void (async () => {
      setAdminReplyThreadLoading(true);
      try {
        if (!entry.ticketId) {
          const res = await getSupportCases(savedSecret, entry.userId, 1, "", 12);
          setAdminReplyThread(res.data?.[0] || null);
        }
      } catch (err) {
        console.warn("⚠️ Không tải được thread support:", err);
        setAdminReplyThread(null);
      } finally {
        setAdminReplyThreadLoading(false);
      }
    })();
  }

  async function submitAdminReply() {
    if (!adminReplyTarget || !savedSecret) return;
    const text = adminReplyText.trim();
    if (!text) {
      showNotice("error", "Nội dung trả lời đang trống.");
      return;
    }
    await runAction("admin-reply", async () => {
      if (adminReplyFallbackTimerRef.current) {
        window.clearTimeout(adminReplyFallbackTimerRef.current);
        adminReplyFallbackTimerRef.current = null;
      }
      const optimisticMessage: SupportMessage = {
        id: `optimistic:${Date.now()}`,
        ticket_id: adminReplyThread?.ticket?.id || adminReplyTarget.id,
        direction: "support_to_user",
        telegram_message_id: null,
        manager_group_message_id: null,
        manager_topic_message_id: null,
        reply_to_manager_message_id: null,
        text,
        payload: { optimistic: true },
        created_at: new Date().toISOString(),
      };
      setAdminReplyOptimisticMessage(optimisticMessage);
      adminReplyStickToBottomRef.current = true;
      console.info("[admin-reply] send start", {
        userId: adminReplyTarget.userId,
        sourceLogId: adminReplyTarget.id,
        messageId: optimisticMessage.id,
        preview: text.slice(0, 80),
      });
      const replyRes = await sendAdminReply(savedSecret, {
        ticket_id: adminReplyTarget.ticketId || adminReplyThread?.ticket?.id || undefined,
        telegram_user_id: adminReplyTarget.userId,
        text,
        source_log_id: adminReplyTarget.id,
        source_text: adminReplyTarget.sourceText,
        full_name: adminReplyTarget.fullName,
      });
      console.info("[admin-reply] send posted, waiting for thread confirm", {
        userId: adminReplyTarget.userId,
        messageId: optimisticMessage.id,
      });
      adminReplyFallbackTimerRef.current = window.setTimeout(() => {
        setAdminReplyOptimisticMessage((current) => {
          if (!current || current.id !== optimisticMessage.id) return current;
          console.warn("[admin-reply] confirm timeout fallback", {
            userId: adminReplyTarget.userId,
            messageId: optimisticMessage.id,
          });
          return { ...current, payload: { ...(current.payload || {}), optimistic: false, pending: false, timeoutFallback: true, confirmed: false }, telegram_message_id: current.telegram_message_id ?? null };
        });
      }, 8000);
      setAdminReplyText("");
      const returnedMessage = replyRes.data?.message || null;
      const returnedTicketId = String(replyRes.data?.ticket_id || "").trim();
      if (returnedMessage) {
        setAdminReplyThread((current) => {
          if (!current) {
            const fallbackTicket = returnedTicketId || adminReplyTarget.id;
            return {
              ticket: {
                id: fallbackTicket,
                ticket_no: "",
                telegram_user_id: adminReplyTarget.userId,
                username: adminReplyTarget.username || null,
                full_name: adminReplyTarget.fullName || null,
                subject: adminReplyTarget.sourceText || null,
                status: "open",
                source: "admin_reply",
                updated_at: returnedMessage.created_at,
                created_at: returnedMessage.created_at,
              },
              messages: [returnedMessage],
            };
          }
          const messages = [...(current.messages || [])];
          const exists = messages.some((item) => item.id === returnedMessage.id || (String(item.direction || "").toLowerCase().includes("support_to_user") && item.text === returnedMessage.text && Math.abs((safeDateMillis(item.created_at) ?? 0) - (safeDateMillis(returnedMessage.created_at) ?? 0)) < 120000));
          if (!exists) messages.push(returnedMessage);
          return { ...current, messages, ticket: { ...current.ticket, id: returnedTicketId || current.ticket.id } };
        });
      } else {
        const queryTarget = adminReplyTarget.ticketId || adminReplyTarget.userId;
        const res = await getSupportCases(savedSecret, queryTarget, 1, "", adminReplyThreadMessageLimit);
        setAdminReplyThread(res.data?.[0] || null);
      }
      const supportRes = await getSupportEvents(savedSecret);
      setSupportEvents(supportRes.data || []);
    });
  }

  async function loadAdminReplyThreadMore() {
    if (!adminReplyTarget || !savedSecret || adminReplyThreadLoading) return;
    const nextLimit = Math.min(adminReplyThreadMessageLimit + 12, 200);
    setAdminReplyThreadMessageLimit(nextLimit);
    adminReplyStickToBottomRef.current = false;
    setAdminReplyThreadLoading(true);
    try {
      const res = await getSupportCases(savedSecret, adminReplyTarget.userId, 1, "", nextLimit);
      setAdminReplyThread(res.data?.[0] || null);
    } catch (err) {
      console.warn("⚠️ Không tải thêm thread support:", err);
    } finally {
      setAdminReplyThreadLoading(false);
    }
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
    setSaleForm({ sale_id: "", price_key: "PRICE_COMBO_30D", discount_percent: "", sale_price: "", slot_limit: "", enabled: "ON", start_at: "", end_at: "" });
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
      throw new Error("Mã kích hoạt nên tối đa 32 ký tự để nút Telegram hoạt động ổn định.");
    }
    if (payload.Coupon_Type === "DISCOUNT") {
      const percent = Number(payload.Discount_Percent || 0);
      if (!Number.isFinite(percent) || percent <= 0 || percent >= 100) {
        throw new Error("Mã giảm giá cần phần trăm từ 1 đến 99. Muốn miễn phí hãy dùng loại Kích hoạt miễn phí.");
      }
      return payload;
    }

    if (isLifetimeCouponPlan(payload.Plan_Name)) {
      payload.Duration_Days = getConfigValue(config, "COUPON_LIFETIME_DAYS", DEFAULT_LIFETIME_DAYS) || DEFAULT_LIFETIME_DAYS;
      return payload;
    }

    const days = Number(payload.Duration_Days || 0);
    if (!Number.isFinite(days) || days <= 0) {
      throw new Error("Mã kích hoạt theo ngày cần số ngày sử dụng lớn hơn 0.");
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
          return (safeDateMillis(couponLastUsedAt(b) || b.created_at) ?? 0) - (safeDateMillis(couponLastUsedAt(a) || a.created_at) ?? 0);
        }
        if (tabKey === "expired") {
          return (safeDateMillis(b.expires_at || b.created_at) ?? 0) - (safeDateMillis(a.expires_at || a.created_at) ?? 0);
        }
        return (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0);
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
    if (!code || !window.confirm(`Xoá mã "${code}"? Lịch sử đã dùng vẫn được giữ riêng trong hệ thống.`)) return;
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
      const expired = (safeDateMillis(item.expire_at) ?? Number.POSITIVE_INFINITY) < now;
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
        const aTime = safeDateMillis(a.expire_at) ?? Number.MAX_SAFE_INTEGER;
        const bTime = safeDateMillis(b.expire_at) ?? Number.MAX_SAFE_INTEGER;
        return aTime - bTime;
      }
      if (activationCodeSort === "recently_used") {
        const aTime = safeDateMillis(a.used_at || a.activated_at) ?? 0;
        const bTime = safeDateMillis(b.used_at || b.activated_at) ?? 0;
        return bTime - aTime;
      }
      return (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0);
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

  function openSecurityTabForCustomer(customerId: string) {
    setTab("security");
    setSelectedCustomerId(customerId);
    setCustomerModalOpen(false);
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

  async function changeOrderNote(orderId: string, note: string) {
    await runAction(`order-note-${orderId}`, async () => {
      await updateOrder(savedSecret, orderId, { note });
      await loadAll();
    });
  }

  function openOrderEditor(order: Order) {
    setOrderEditorOrderId(order.order_id);
    setOrderEditorForm({
      status: String(order.status || "PENDING").toUpperCase(),
      plan_name: String(order.plan_name || ""),
      amount: String(order.amount ?? ""),
      payment_currency: String(order.payment_currency || inferOrderCurrency(order) || "VND").toUpperCase(),
      expire_at: orderExpireValue(order.expire_at || ""),
      paid_at: orderExpireValue(order.paid_at || ""),
      coupon_code: String(order.coupon_code || ""),
      note: orderNoteText(order),
    });
    setOrderEditorOpen(true);
  }

  useEffect(() => {
    if (!orderEditorOpen) return;
    window.setTimeout(() => {
      orderEditorPlanInputRef.current?.focus();
      orderEditorPlanInputRef.current?.select?.();
    }, 50);
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setOrderEditorOpen(false);
      }
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        void saveOrderEditor();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [orderEditorOpen, saveOrderEditor]);

  async function copyOrderId(orderId: string) {
    try {
      await navigator.clipboard.writeText(orderId);
      showNotice("ok", `Đã copy order ID ${orderId}.`);
    } catch {
      showNotice("error", "Không copy được order ID.");
    }
  }

  function parseManualActivationDetail(detail: string, title = "") {
    const text = String(detail || "").trim();
    const statusMatch = text.match(/Trạng thái:\s*([^•\n]+)/i) || text.match(/status:\s*([^•\n]+)/i);
    const planMatch = text.match(/(?:Gói|Plan):\s*([^•\n]+)/i);
    const orderMatch = text.match(/(?:Đơn|Order):\s*([^•\n]+)/i);
    const links = Array.from(text.matchAll(/'group_id':\s*'([^']+)'.*?'group_name':\s*'([^']+)'.*?'invite_link':\s*'([^']+)'/g)).map((match) => ({
      groupId: match[1],
      groupName: match[2],
      inviteLink: match[3],
    }));
    return {
      status: statusMatch?.[1]?.trim() || "",
      plan: planMatch?.[1]?.trim() || "",
      order: orderMatch?.[1]?.trim() || "",
      title: title || "Kích hoạt đơn",
      links,
    };
  }

  function detailStatusTone(status: string) {
    const normalized = String(status || "").trim().toUpperCase();
    if (["OK", "SUCCESS", "DONE", "ACTIVE"].includes(normalized)) return "success" as const;
    if (["ERROR", "FAIL", "FAILED", "LỖI"].includes(normalized)) return "error" as const;
    return "warning" as const;
  }

  function copyTextValue(value: string, label: string) {
    void navigator.clipboard.writeText(value).then(
      () => showNotice("ok", `Đã copy ${label}.`),
      () => showNotice("error", `Không copy được ${label}.`),
    );
  }

  function renderLogDetailCell(item: ActivityLogEntry) {
    const parsed = parseManualActivationDetail(item.detail, item.title);
    const detailText = activityLogDetailLabel(item.type, item.detail, item.title);
    if (item.type === "manual_activation_link_generated" || detailText !== item.detail) {
      return (
        <Box sx={{ display: "grid", gap: 0.75 }}>
          <Box sx={{ display: "flex", gap: 0.75, flexWrap: "wrap", alignItems: "center" }}>
            {parsed.status ? <Chip size="small" label={parsed.status} color={detailStatusTone(parsed.status)} variant="outlined" sx={{ height: 20, fontSize: 10.5, fontWeight: 800 }} /> : null}
            {parsed.plan ? <Chip size="small" label={parsed.plan} color="secondary" variant="outlined" sx={{ height: 20, fontSize: 10.5, fontWeight: 800 }} /> : null}
            {parsed.order ? <Chip size="small" label={parsed.order} color="info" variant="outlined" sx={{ height: 20, fontSize: 10.5, fontWeight: 800 }} /> : null}
          </Box>
          {parsed.links.length ? (
            <Box sx={{ display: "grid", gap: 0.75 }}>
              {parsed.links.map((link) => (
                <Box
                  key={`${item.id}-${link.groupId}`}
                  sx={{
                    display: "grid",
                    gap: 0.35,
                    p: 1,
                    borderRadius: 2,
                    border: "1px solid",
                    borderColor: "divider",
                    bgcolor: "rgba(15, 23, 42, 0.02)",
                  }}
                >
                  <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, justifyContent: "space-between", flexWrap: "wrap" }}>
                    <Typography sx={{ fontWeight: 800, lineHeight: 1.2 }}>{link.groupName}</Typography>
                    <Button variant="outlined" size="small" startIcon={<Copy size={14} />} onClick={() => copyTextValue(link.inviteLink, `${link.groupName} invite link`)}>
                      Copy link
                    </Button>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ wordBreak: "break-all" }}>
                    {link.inviteLink}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Group ID: {link.groupId}
                  </Typography>
                </Box>
              ))}
            </Box>
          ) : null}
        </Box>
      );
    }
    return <Box sx={{ whiteSpace: "pre-line" }}>{friendlyDetailText(detailText)}</Box>;
  }

  function orderEditorAmountPreview() {
    const raw = Number(String(orderEditorForm.amount || "").replace(/,/g, "."));
    if (!Number.isFinite(raw)) return "-";
    const fallbackCurrency = selectedOrderForEditor ? inferOrderCurrency(selectedOrderForEditor) : "VND";
    const currency = normalizeRevenueCurrency(orderEditorForm.payment_currency || fallbackCurrency);
    return formatRevenueCurrency(currency, raw);
  }

  function normalizeOrderEditorAmountInput(value: string, currency: string) {
    const normalizedCurrency = normalizeRevenueCurrency(currency);
    const cleaned = String(value || "").replace(/[^\d.,-]/g, "").replace(/,/g, ".");
    if (normalizedCurrency === "USD" || normalizedCurrency === "USDT" || normalizedCurrency === "CRYPTO") {
      const match = cleaned.match(/^-?\d*(?:\.\d{0,2})?/);
      return match ? match[0] : "";
    }
    const match = cleaned.match(/^-?\d*/);
    return match ? match[0] : "";
  }

  function normalizeMoneyInput(value: string, currency: string) {
    return normalizeOrderEditorAmountInput(value, currency);
  }

  function roundMoneyInput(value: string, currency: string) {
    const normalizedCurrency = normalizeRevenueCurrency(currency);
    const text = String(value || "").trim();
    if (!text) return "";
    const numeric = Number(text.replace(/,/g, "."));
    if (!Number.isFinite(numeric)) return value;
    if (normalizedCurrency === "USD" || normalizedCurrency === "USDT" || normalizedCurrency === "CRYPTO") {
      return String(Math.round(numeric * 100) / 100);
    }
    return String(Math.round(numeric));
  }

  function roundOrderEditorVndAmount() {
    const currency = normalizeRevenueCurrency(orderEditorForm.payment_currency || "VND");
    if (currency !== "VND") return;
    const text = String(orderEditorForm.amount || "").trim();
    if (!text) return;
    const numeric = Number(text.replace(/,/g, "."));
    if (!Number.isFinite(numeric)) return;
    setOrderEditorForm((current) => ({ ...current, amount: String(Math.round(numeric)) }));
  }

  async function saveOrderEditor() {
    if (!orderEditorOrderId) return;
    const nextPlanName = orderEditorForm.plan_name.trim();
    const nextCouponCode = orderEditorForm.coupon_code.trim().toUpperCase();
    const nextNote = orderEditorForm.note.trim();
    const nextStatus = String(orderEditorForm.status || "").toUpperCase();
    const payload: Parameters<typeof updateOrder>[2] = {
      status: nextStatus,
      plan_name: nextPlanName,
      coupon_code: nextCouponCode || null,
      payment_currency: String(orderEditorForm.payment_currency || "VND").toUpperCase(),
      note: nextNote,
    };
    if (String(orderEditorForm.amount || "").trim() !== "") payload.amount = Number(String(orderEditorForm.amount).replace(/,/g, "."));
    if (orderEditorForm.expire_at) payload.expire_at = orderEditorForm.expire_at;
    if (orderEditorForm.paid_at) payload.paid_at = orderEditorForm.paid_at;
    await runAction(`order-edit-${orderEditorOrderId}`, async () => {
      await updateOrder(savedSecret, orderEditorOrderId, payload);
      await loadAll();
      setOrderEditorOpen(false);
    });
  }

  function openCustomerRenewModal() {
    if (!selectedCustomer) return;
    const defaultOrder = selectedCustomerRenewTargetOrder || selectedCustomer.paidOrders[0] || null;
    const defaultPlanName = defaultOrder?.plan_name || selectedCustomerRenewPlanOptions[0] || "";
    const defaultDuration = isLifetimeText(defaultPlanName) ? "0" : "30";
    setCustomerRenewForm({
      order_id: defaultOrder?.order_id || "",
      plan_name: defaultPlanName,
      note: orderNoteText(defaultOrder || ({} as Order)),
      amount: defaultOrder ? String(defaultOrder.amount || "") : "",
      duration_days: defaultDuration,
      payment_currency: String(defaultOrder?.payment_currency || "VND").toUpperCase(),
      payment_provider: String(defaultOrder?.payment_provider || "MANUAL").toUpperCase(),
    });
    setCustomerRenewModalOpen(true);
  }

  function openCustomerCreateOrderModal() {
    if (!selectedCustomer) return;
    void ensureHiddenGroupsDataset();
    const defaultOrder = selectedCustomerRenewTargetOrder || selectedCustomer.paidOrders[0] || null;
    setManualOrderResult(null);
    setManualOrderForm({
      ...EMPTY_MANUAL_ORDER_FORM,
      telegram_user_id: selectedCustomer.id,
      full_name: selectedCustomer.name || selectedCustomer.id,
      plan_key: defaultOrder ? "CUSTOM" : "FULL_1M",
      plan_name: defaultOrder?.plan_name || manualPlanNameFromKey("FULL_1M"),
      special_group_id: "",
      special_group_duration: "1M",
      amount: defaultOrder ? String(defaultOrder.amount || "0") : (manualPriceFromKey("FULL_1M") || "0"),
      payment_currency: String(defaultOrder?.payment_currency || "VND").toUpperCase(),
      payment_provider: String(defaultOrder?.payment_provider || "MANUAL").toUpperCase(),
      expiry_mode: "days",
      duration_days: "30",
      expire_at: "",
    });
    setManualOrderModalOpen(true);
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
    showNotice("ok", `Đang tạo đơn gia hạn cho ${selectedCustomer.name || selectedCustomer.id}...`);
    const ok = await runAction(`customer-renew-${selectedCustomer.id}`, async () => {
      await createManualOrder(savedSecret, {
        telegram_user_id: selectedCustomer.id,
        full_name: selectedCustomer.name || selectedCustomer.id,
        plan_name: planName,
        note: customerRenewForm.note.trim(),
        amount: String(amount),
        duration_days: isLifetimeText(planName) ? "0" : String(days),
        sale_id: `RENEWAL_${customerRenewForm.order_id || "MANUAL"}`,
        payment_currency: String(customerRenewForm.payment_currency || "VND").toUpperCase(),
        payment_provider: String(customerRenewForm.payment_provider || "MANUAL").toUpperCase(),
        skip_active_code: true,
      });
      setCustomerRenewModalOpen(false);
      await loadAll();
    });
    if (ok) {
      showNotice("ok", `Đã tạo đơn gia hạn cho ${selectedCustomer.name || selectedCustomer.id}.`);
    }
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
      setWebhookMeta(res.meta);
    });
  }

  async function handleWebhookClearMaintenance() {
    await runAction("webhook-clear-maintenance", async () => {
      const res = await clearWebhookMaintenance(savedSecret);
      setWebhook(res.data);
      setWebhookMeta(res.meta);
    });
  }

  const metrics = useMemo(() => {
    const paid = orders.filter((item) => item.status === "PAID").length;
    const pending = orders.filter((item) => item.status === "PENDING").length;
    const revenue = orders.filter((item) => item.status === "PAID").reduce((sum, item) => sum + orderAmountValue(item), 0);
    return { paid, pending, revenue, users: users.length, coupons: coupons.length, menu: menuPages.length };
  }, [orders, users, coupons, menuPages]);
  const summaryCounts = useMemo(() => ({
    orders: dashboardSummary?.orders_total ?? orders.length,
    ordersPaid: dashboardSummary?.orders_paid ?? metrics.paid,
    ordersPending: dashboardSummary?.orders_pending ?? metrics.pending,
    activationCodes: dashboardSummary?.activation_codes ?? activationCodes.length,
    supportEvents: dashboardSummary?.support_events ?? supportEvents.length,
    activityEvents: dashboardSummary?.activity_events ?? activityEvents.length,
    coupons: dashboardSummary?.coupons ?? coupons.length,
    hiddenGroups: dashboardSummary?.hidden_groups ?? hiddenGroups.length,
    hiddenCodes: dashboardSummary?.hidden_codes ?? hiddenCodes.length,
    blacklist: dashboardSummary?.blacklist_active ?? blacklist.filter((item) => item.is_active).length,
    campaigns: dashboardSummary?.broadcast_campaigns ?? campaigns.length,
    channelPosts: dashboardSummary?.channel_posts ?? channelPosts.length,
  }), [activationCodes.length, activityEvents.length, blacklist, campaigns.length, channelPosts.length, coupons.length, dashboardSummary, hiddenCodes.length, hiddenGroups.length, metrics, orders.length, supportEvents.length]);
  const todayStats = useMemo(() => orderStats(orders.filter((item) => isWithinPeriod(item.created_at, "today"))), [orders]);
  const monthStats = useMemo(() => orderStats(orders.filter((item) => isWithinPeriod(item.created_at, "month"))), [orders]);
  const yearStats = useMemo(() => orderStats(orders.filter((item) => isWithinPeriod(item.created_at, "year"))), [orders]);
  const paidOrders = useMemo(() => orders.filter((item) => item.status === "PAID"), [orders]);
  const paidRevenueByCurrency = useMemo(() => groupRevenueByCurrency(paidOrders), [paidOrders]);
  const paidRevenueByProvider = useMemo(() => {
    return paidOrders.reduce((sum, order) => {
      const provider = inferOrderProvider(order);
      sum[provider] = (sum[provider] || 0) + orderAmountValue(order);
      return sum;
    }, {} as Record<string, number>);
  }, [paidOrders]);
  const webhookCooldownSeconds = Math.max(0, Number(webhookMeta?.reset_state?.wait_seconds ?? 0));
  const webhookCooldownLabel = webhookCooldownSeconds > 0 ? `${webhookCooldownSeconds}s` : "Đã hết";
  const hasPayosOrders = useMemo(() => paidOrders.some((item) => inferOrderProvider(item) === "PAYOS"), [paidOrders]);
  const overviewTrendPoints = useMemo(() => {
    const sourceOrders = orders.filter((item) => item.status === "PAID" && isWithinPeriod(item.created_at, overviewTrendRange));
    const groupMap = new Map<string, Order[]>();
    for (const order of sourceOrders) {
      const orderDate = safeDateMillis(order.created_at);
      const keyDate = orderDate ? new Date(orderDate) : null;
      const key = overviewTrendRange === "month"
        ? new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "2-digit" }).format(keyDate || new Date())
        : new Intl.DateTimeFormat("vi-VN", { month: "2-digit", year: "2-digit" }).format(keyDate || new Date());
      groupMap.set(key, [...(groupMap.get(key) || []), order]);
    }
    return Array.from(groupMap.entries()).map(([label, items]) => ({
      label,
      value: items.reduce((sum, item) => sum + orderAmountValue(item), 0),
      vip: new Set(items.map((item) => item.telegram_user_id)).size,
    }));
  }, [orders, overviewTrendRange]);
  const overviewVipPoints = useMemo(() => overviewTrendPoints.map((item) => ({ label: item.label, value: item.vip })), [overviewTrendPoints]);
  const maxGroups = useMemo(() => Math.max(Number(getConfigValue(config, "GROUP_COUNT", String(DEFAULT_GROUP_COUNT))) || DEFAULT_GROUP_COUNT, 1), [config]);
  const configuredGroups = useMemo(() => Array.from({ length: maxGroups }, (_, idx) => idx + 1).filter((item) => isGroupConfigured(config, item)), [config, maxGroups]);
  const visibleGroups = useMemo(() => Array.from({ length: maxGroups }, (_, idx) => idx + 1).filter((item) => hasAnyGroupConfig(config, item)), [config, maxGroups]);
  const groupQuickOptions = useMemo(() => {
    const values = new Set<string>(visibleGroups.map((item) => String(item)));
    const selected = String(groupNo || "").trim();
    if (selected) values.add(selected);
    return Array.from(values).sort((a, b) => Number(a) - Number(b));
  }, [groupNo, visibleGroups]);
  const activeSpecialGroups = useMemo(() => hiddenGroups.filter((item) => item.is_active).sort((a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name)), [hiddenGroups]);
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
  const customDurationEnabled = ["ON", "1", "TRUE", "YES"].includes(getConfigValue(config, "MANUAL_CUSTOM_DURATION_ENABLED", "ON").toUpperCase());
  const priceKeyOptions = useMemo(() => [
    ...PRICE_KEY_OPTIONS,
    ...configuredGroups.flatMap((item) => [`PRICE_G${item}_1M`, `PRICE_G${item}_LIFE`, `PRICE_G${item}_1M_USD`, `PRICE_G${item}_LIFE_USD`]),
  ], [configuredGroups]);
  const groupViContentFields = useMemo<ConfigField[]>(() => configuredGroups.flatMap((item) => [
    { key: `DESC_G${item}`, label: `G${item} - Mô tả tiếng Việt`, placeholder: "Mô tả nội dung nhóm", help: "Nội dung trang chi tiết nhóm tiếng Việt.", kind: "textarea" as const },
  ]), [configuredGroups]);
  const groupEnContentFields = useMemo<ConfigField[]>(() => configuredGroups.flatMap((item) => [
    { key: `DESC_G${item}_EN`, label: `G${item} - English description`, placeholder: "Short, sharp group description in English", help: "English content for the group detail page.", kind: "textarea" as const },
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

  const filteredOrdersBase = useMemo(() => {
    return orders.filter((order) => {
      const text = `${order.order_id} ${order.full_name || ""} ${order.telegram_user_id} ${order.plan_name} ${orderCouponCode(order)}`.toLowerCase();
      const matchQuery = !query || text.includes(query.toLowerCase());
      const matchPeriod = isWithinPeriod(order.created_at, orderPeriod);
      return matchQuery && matchPeriod;
    });
  }, [orders, query, orderPeriod]);
  const filteredOrders = useMemo(() => {
    return filteredOrdersBase.filter((order) => (orderTab === "paid" ? order.status === "PAID" : order.status !== "PAID"));
  }, [filteredOrdersBase, orderTab]);
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
        .sort((a, b) => (safeDateMillis(b) ?? 0) - (safeDateMillis(a) ?? 0))[0] || "";
      const coupons = uniqueValues(customer.orders.map(orderCouponCode));
      const groups = uniqueValues(customer.orders.flatMap(groupNamesForOrder));
      const plans = uniqueValues(customer.orders.map((item) => item.plan_name));
      const revenue = paidOrders.reduce((sum, item) => sum + orderAmountValue(item), 0);
      const lastOrderAt = customer.orders.map((item) => item.created_at).sort((a, b) => (safeDateMillis(b) ?? 0) - (safeDateMillis(a) ?? 0))[0] || "";
      const hasLifetimeSvip = customer.orders.some((item) => item.status === "PAID" && isLifetimeAllAccessText(item.plan_name));
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
    }).sort((a, b) => (safeDateMillis(b.lastOrderAt) ?? 0) - (safeDateMillis(a.lastOrderAt) ?? 0));
  }, [orders, reminderNoticeDays]);
  const customerSummaryById = useMemo(() => new Map(customerSummaries.map((item) => [item.id, item] as const)), [customerSummaries]);
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
  const selectedOrderForEditor = useMemo(() => {
    if (!orderEditorOrderId) return null;
    return orders.find((item) => item.order_id === orderEditorOrderId) || null;
  }, [orders, orderEditorOrderId]);
  const orderEditorHistoryRows = useMemo(() => {
    if (!selectedOrderForEditor) return [];
    const orderId = selectedOrderForEditor.order_id;
    const userId = String(selectedOrderForEditor.telegram_user_id || "").trim();
    const sameOrderEvents = supportEvents
      .filter((event) => {
        const rawData = (event.raw_data && typeof event.raw_data === "object") ? (event.raw_data as Record<string, unknown>) : null;
        return event.order_id === orderId || String(rawData?.order_id || "") === orderId || String(rawData?.source_order_id || "") === orderId;
      })
      .sort((a, b) => (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0));
    const timeline = [
      {
        at: selectedOrderForEditor.created_at,
        title: "Đơn được tạo",
        detail: `${selectedOrderForEditor.plan_name || "-"} • ${orderStatusLabel(selectedOrderForEditor.status)}${orderNoteText(selectedOrderForEditor) ? ` • ${orderNoteText(selectedOrderForEditor)}` : ""}`,
      },
      selectedOrderForEditor.paid_at ? {
        at: selectedOrderForEditor.paid_at,
        title: "Đã thanh toán",
        detail: `${orderMoney(selectedOrderForEditor)} • ${selectedOrderForEditor.payment_provider || "-"} • ${selectedOrderForEditor.payment_currency || "-"}`,
      } : null,
      selectedOrderForEditor.expire_at ? {
        at: selectedOrderForEditor.expire_at,
        title: "Hạn hiện tại",
        detail: dateText(selectedOrderForEditor.expire_at),
      } : null,
      ...sameOrderEvents.map((event) => ({
        at: event.created_at,
        title: event.event_type,
        detail: (() => {
          const rawData = (event.raw_data && typeof event.raw_data === "object") ? (event.raw_data as Record<string, unknown>) : null;
          const displayPlan = String(event.plan_name || "").trim();
          const parts = [displayPlan || "", String(rawData?.note || ""), String(rawData?.deleted_at || "")].filter(Boolean);
          return parts.join(" • ") || `${event.telegram_user_id || userId || "-"}${event.order_id ? ` • ${event.order_id}` : ""}`;
        })(),
      })),
    ].filter(Boolean) as { at: string; title: string; detail: string }[];
    return timeline.sort((a, b) => (safeDateMillis(b.at) ?? 0) - (safeDateMillis(a.at) ?? 0)).slice(0, 10);
  }, [orderEditorOrderId, orders, selectedOrderForEditor, supportEvents]);
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
      const aExpire = safeDateMillis(a.expire_at) ?? 0;
      const bExpire = safeDateMillis(b.expire_at) ?? 0;
      if (!Number.isNaN(aExpire) && !Number.isNaN(bExpire) && aExpire !== bExpire) return aExpire - bExpire;
      return (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0);
    });
  }, [selectedCustomer]);
  const selectedCustomerRenewTargetOrder = useMemo(() => {
    if (!selectedCustomer) return null;
    const candidates = selectedCustomer.activeOrders.length ? selectedCustomer.activeOrders : selectedCustomer.paidOrders;
    return [...candidates].sort((a, b) => {
      const aExpire = safeDateMillis(a.expire_at) ?? 0;
      const bExpire = safeDateMillis(b.expire_at) ?? 0;
      if (!Number.isNaN(aExpire) && !Number.isNaN(bExpire) && aExpire !== bExpire) return aExpire - bExpire;
      return (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0);
    })[0] || null;
  }, [selectedCustomer]);
  const selectedCustomerRenewPlanOptions = useMemo(() => {
    if (!selectedCustomer) return [];
    return uniqueValues(selectedCustomer.paidOrders.map((item) => item.plan_name)).sort((a, b) => a.localeCompare(b));
  }, [selectedCustomer]);
  const filteredBlacklist = useMemo(() => {
    const q = blacklistQuery.trim().toLowerCase();
    return blacklist.filter((item) => {
      const text = `${item.telegram_user_id} ${item.username || ""} ${item.full_name || ""} ${item.reason || ""} ${item.source || ""}`.toLowerCase();
      if (q && !text.includes(q)) return false;
      if (blacklistStatusFilter === "active" && !item.is_active) return false;
      if (blacklistStatusFilter === "inactive" && item.is_active) return false;
      if (blacklistStatusFilter === "reason" && !String(item.reason || "").trim()) return false;
      return true;
    });
  }, [blacklist, blacklistQuery, blacklistStatusFilter]);
  const customerQuickLookupResult = customerQuickLookupResults[0] || null;
  const selectedCustomerBlacklistEntry = useMemo(() => {
    if (!selectedCustomerId) return null;
    return blacklist.find((item) => item.telegram_user_id === selectedCustomerId && item.is_active) || null;
  }, [blacklist, selectedCustomerId]);
  const selectedCustomerIsBlacklisted = Boolean(selectedCustomerBlacklistEntry);
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
  const vipGroupAuditMismatchRows = useMemo(() => {
    return vipGroupAudit
      .filter((item) => item.status === "UNMAPPED" || Boolean(item.latest_error) || ((item.candidate_group_names || []).length > 0 && (item.current_group_ids || []).length === 0))
      .map((item) => ({
        auditId: item.audit_id,
        targetGroupNo: String(item.candidate_groups?.[0]?.group_no || item.current_group_ids?.[0] || ""),
        row: [
          <div key={`audit-customer-${item.audit_id}`}>
            <strong>{item.customer_name || "-"}</strong>
            <div className="muted">{item.telegram_user_id}</div>
          </div>,
          <div key={`audit-order-${item.audit_id}`}>
            <strong>{item.order_id || "-"}</strong>
            <div className="muted">{dateText(item.expire_at || "")}</div>
          </div>,
          <div key={`audit-plan-${item.audit_id}`}>
            <strong>{resolveOrderLabel({ plan_name: item.plan_name }).displayLabel}</strong>
            <div className="muted">{item.current_group_names?.join(" • ") || item.group_name || "-"}</div>
          </div>,
          <div key={`audit-group-${item.audit_id}`}>
            <strong>{item.group_name || "-"}</strong>
            <div className="muted">{item.group_id || "không có group_id"}</div>
          </div>,
          <div key={`audit-candidate-${item.audit_id}`}>
            <div>{(item.candidate_group_names || []).length ? (item.candidate_group_names || []).join(" • ") : "—"}</div>
            <div className="muted">{(item.candidate_groups || []).length ? (item.candidate_groups || []).map((group) => `${group.group_name}${group.alias_text ? ` [${group.alias_text}]` : ""}`).join(" • ") : "Không có gợi ý alias"}</div>
          </div>,
          <Tooltip key={`audit-error-${item.audit_id}`} title={item.latest_error || "Không có lỗi"} arrow>
            <span>{item.latest_error || item.status_label || item.status || "-"}</span>
          </Tooltip>,
        ],
      }));
  }, [vipGroupAudit]);
  const selectedCustomerGroupAuditRows = useMemo(() => {
    if (!selectedCustomer) return [];
    const customerId = selectedCustomer.id;
    const vipRows = vipGroupAudit
      .filter((item) => String(item.telegram_user_id || "").trim() === customerId)
      .map((item) => ({
        key: `vip-${item.audit_id}`,
        type: item.status,
        sortKey: safeDateMillis(item.latest_kick_at || item.expire_at) ?? 0,
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
          <><strong>{resolveOrderLabel({ plan_name: item.plan_name }).displayLabel}</strong><div className="muted">{item.order_id || "-"}</div></>,
          item.expire_at ? dateText(item.expire_at) : "-",
          <Tooltip key={`vip-${item.audit_id}-live-tip`} title={item.live_checked ? `Mã live: ${item.live_status || "-"}` : "Chưa kiểm tra live"} arrow>
            <span>{item.live_checked ? `${item.live_status || "-"}${item.live_present === true ? " / còn trong group" : item.live_present === false ? " / đã rời" : ""}` : "Chưa live"}</span>
          </Tooltip>,
          <Tooltip key={`vip-${item.audit_id}-err-tip`} title={item.latest_error || "Không có lỗi"} arrow>
            <Box component="span" sx={{ whiteSpace: "pre-line" }}>{friendlyDetailText(item.latest_error || "-")}</Box>
          </Tooltip>,
        ],
      }));
    const kickRows = kickAudit
      .filter((item) => String(item.telegram_user_id || "").trim() === customerId)
      .map((item) => ({
        key: `kick-${item.audit_id}`,
        type: item.status,
        sortKey: safeDateMillis(item.latest_kick_at || item.expire_at) ?? 0,
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
          <><strong>{resolveOrderLabel({ plan_name: item.plan_name }).displayLabel}</strong><div className="muted">{item.order_id || "-"}</div></>,
          item.expire_at ? dateText(item.expire_at) : "-",
          <Tooltip key={`kick-${item.audit_id}-live-tip`} title={item.live_checked ? `Mã live: ${item.live_status || "-"}` : "Chưa kiểm tra live"} arrow>
            <span>{item.live_checked ? `${item.live_status || "-"}${item.live_present === true ? " / còn trong group" : item.live_present === false ? " / đã rời" : ""}` : "Chưa live"}</span>
          </Tooltip>,
          <Tooltip key={`kick-${item.audit_id}-reason-tip`} title={kickAuditReason(item)} arrow>
            <Box component="span" sx={{ whiteSpace: "pre-line" }}>{friendlyDetailText(kickAuditReason(item))}</Box>
          </Tooltip>,
        ],
      }));
    return [...vipRows, ...kickRows]
      .sort((a, b) => (b.sortKey || 0) - (a.sortKey || 0))
      .map((item) => item.row);
  }, [selectedCustomer, vipGroupAudit, kickAudit]);
  const vipMemberAuditFiltered = useMemo(() => {
    if (vipMemberAuditRiskType === "ALL") return vipMemberAudit;
    return vipMemberAudit.filter((item) => item.risk_type === vipMemberAuditRiskType);
  }, [vipMemberAudit, vipMemberAuditRiskType]);
  const vipMemberAuditCounts = useMemo(() => ({
    all: vipMemberAudit.length,
    noOrder: vipMemberAudit.filter((item) => item.risk_type === "NO_ORDER").length,
    expired: vipMemberAudit.filter((item) => item.risk_type === "EXPIRED_ORDER").length,
  }), [vipMemberAudit]);
  const selectedCustomerSupportEvents = useMemo(() => {
    if (!selectedCustomer) return [];
    return supportEvents
      .filter((item) => String(item.telegram_user_id || "").trim() === selectedCustomer.id)
      .sort((a, b) => (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0));
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
        item.raw_data?.reason ? friendlyDetailText(String(item.raw_data.reason)) : "",
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
        detail: friendlyDetailText(item.latest_error || (item.live_checked ? `${item.live_status || "-"}` : "Chưa kiểm tra live") || "-"),
      }));

    const identityTrace: CustomerTraceEvent[] = customerIdentityHistory
      .filter((item) => String(item.telegram_user_id || "").trim() === customerId)
      .map((item) => ({
        key: `identity-${item.id}`,
        type: "identity_changed",
        group: item.source_event_type || "identity",
        order: item.source_order_id || "-",
        createdAt: item.created_at,
        detail: [
          item.previous_full_name && item.previous_full_name !== item.full_name ? `Tên: ${item.previous_full_name} → ${item.full_name || "-"}` : "",
          item.previous_username && item.previous_username !== item.username ? `Username: ${item.previous_username} → ${item.username || "-"}` : "",
          item.source_chat_id ? `Chat: ${item.source_chat_id}` : "",
        ].filter(Boolean).join(" • ") || "Identity snapshot",
      }));

    const rows = [...orderTrace, ...supportTrace, ...kickTrace, ...vipTrace, ...identityTrace]
      .filter((item) => item.createdAt)
      .sort((a, b) => (safeDateMillis(b.createdAt) ?? 0) - (safeDateMillis(a.createdAt) ?? 0))
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
    const joined = selectedCustomerSupportEvents.filter((item) => ["support_joined", "vip_joined"].includes(item.event_type)).length;
    const left = selectedCustomerSupportEvents.filter((item) => ["support_left", "vip_left"].includes(item.event_type)).length;
    const muted = selectedCustomerSupportEvents.filter((item) => ["member_muted", "vip_muted"].includes(item.event_type)).length;
    const kicked = selectedCustomerSupportEvents.filter((item) => ["member_kicked", "vip_kicked"].includes(item.event_type)).length;
    const orderKicked = kickAudit.filter((item) => String(item.telegram_user_id || "").trim() === selectedCustomer.id && item.status !== "ACTIVE_RETAINED").length;
    return {
      total: selectedCustomerTimelineRows.length,
      joined,
      left,
      muted,
      kicked: kicked + orderKicked,
    };
  }, [selectedCustomer, selectedCustomerSupportEvents, selectedCustomerTimelineRows, kickAudit]);
  const paidMemberOrders = useMemo(() => orders.filter((item) => item.status === "PAID" && item.expire_at), [orders]);
  const expiringToday = useMemo(() => paidMemberOrders.filter((item) => daysUntil(item.expire_at) === 0), [paidMemberOrders]);
  function renewalPriorityScore(item: Pick<Order, "telegram_user_id" | "expire_at" | "created_at" | "last_reminder_date"> | Pick<SupportEvent, "telegram_user_id" | "created_at">, options?: { reminderSentAt?: string; forceImportant?: boolean }) {
    const customerId = String(item.telegram_user_id || "").trim();
    const customer = customerSummaryById.get(customerId);
    const paidCount = customer?.paidOrders.length || 0;
    const firstPaidAt = customer?.paidOrders
      .map((order) => order.created_at)
      .filter(Boolean)
      .sort((a, b) => (safeDateMillis(a) ?? 0) - (safeDateMillis(b) ?? 0))[0] || "";
    const daysFromFirstPaid = firstPaidAt ? Math.max(0, Math.floor((Date.now() - (safeDateMillis(firstPaidAt) ?? Date.now())) / 86400000)) : Number.MAX_SAFE_INTEGER;
    const isNewCustomer = paidCount <= 1 || daysFromFirstPaid <= 14;
    const expireDays = "expire_at" in item ? daysUntil(item.expire_at) : Number.MAX_SAFE_INTEGER;
    const latestReminder = options?.reminderSentAt || ("last_reminder_date" in item ? item.last_reminder_date || "" : "");
    const needsUrgentAttention = Boolean(options?.forceImportant) || expireDays <= 1 || (!latestReminder && expireDays <= reminderNoticeDays);
    return [needsUrgentAttention ? 0 : 1, isNewCustomer ? 0 : 1] as const;
  }
  function sortRenewalOrders(items: Order[], options?: { useReminderMap?: boolean; forceImportant?: boolean }) {
    return [...items].sort((a, b) => {
      const aPriority = renewalPriorityScore(a, {
        reminderSentAt: options?.useReminderMap ? latestReminderByOrder.get(a.order_id)?.created_at || "" : "",
        forceImportant: options?.forceImportant,
      });
      const bPriority = renewalPriorityScore(b, {
        reminderSentAt: options?.useReminderMap ? latestReminderByOrder.get(b.order_id)?.created_at || "" : "",
        forceImportant: options?.forceImportant,
      });
      if (aPriority[0] !== bPriority[0]) return aPriority[0] - bPriority[0];
      if (aPriority[1] !== bPriority[1]) return aPriority[1] - bPriority[1];
      const expireDiff = (safeDateMillis(a.expire_at) ?? 0) - (safeDateMillis(b.expire_at) ?? 0);
      if (!Number.isNaN(expireDiff) && expireDiff !== 0) return expireDiff;
      return (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0);
    });
  }
  function sortRenewalEvents<T extends SupportEvent>(items: T[]) {
    return [...items].sort((a, b) => {
      const aPriority = renewalPriorityScore(a);
      const bPriority = renewalPriorityScore(b);
      if (aPriority[0] !== bPriority[0]) return aPriority[0] - bPriority[0];
      if (aPriority[1] !== bPriority[1]) return aPriority[1] - bPriority[1];
      return (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0);
    });
  }
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
  const latestReminderByOrder = useMemo(() => {
    const map = new Map<string, SupportEvent>();
    for (const event of renewalReminderEvents) {
      const orderId = event.order_id || "";
      if (!orderId) continue;
      const current = map.get(orderId);
      if (!current || (safeDateMillis(event.created_at) ?? 0) > (safeDateMillis(current.created_at) ?? 0)) {
        map.set(orderId, event);
      }
    }
    return map;
  }, [renewalReminderEvents]);
  const expiredNoticeEvents = useMemo(() => supportEvents.filter((item) => item.event_type === "expired_notice_sent"), [supportEvents]);
  const supportKickedToday = useMemo(() => supportGroupTodayEvents.filter((item) => item.event_type === "member_kicked"), [supportGroupTodayEvents]);
  const uniqueKickedEvents = useMemo(() => {
    const map = new Map<string, SupportEvent>();
    for (const item of supportEvents.filter((event) => event.event_type === "member_kicked")) {
      const key = [item.telegram_user_id || "", item.order_id || "", item.chat_id || ""].join("|");
      const current = map.get(key);
      if (!current || (safeDateMillis(item.created_at) ?? 0) > (safeDateMillis(current.created_at) ?? 0)) {
        map.set(key, item);
      }
    }
    return Array.from(map.values()).sort((a, b) => (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0));
  }, [supportEvents]);
  const sortedExpiringToday = useMemo(() => sortRenewalOrders(expiringToday, { forceImportant: true }), [expiringToday]);
  const sortedReminderEvents = useMemo(() => sortRenewalEvents(renewalReminderEvents), [renewalReminderEvents]);
  const sortedExpiredNoticeEvents = useMemo(() => sortRenewalEvents(expiredNoticeEvents), [expiredNoticeEvents]);
  const sortedUniqueKickedEvents = useMemo(() => sortRenewalEvents(uniqueKickedEvents), [uniqueKickedEvents]);
  const expiringSoon = useMemo(() => {
    return sortRenewalOrders(paidMemberOrders.filter((item) => {
      const days = daysUntil(item.expire_at);
      return !isLifetimeText(item.plan_name) && days >= 0 && days <= 5;
    }), { useReminderMap: true });
  }, [latestReminderByOrder, paidMemberOrders]);
  const expiredRenewalOrders = useMemo(() => {
    return [...orders]
      .filter((item) => ["PAID", "EXPIRED"].includes(String(item.status || "").toUpperCase()) && item.expire_at && !isLifetimeText(item.plan_name) && daysUntil(item.expire_at) < 0)
      .sort((a, b) => (safeDateMillis(b.expire_at || b.created_at) ?? 0) - (safeDateMillis(a.expire_at || a.created_at) ?? 0));
  }, [orders]);
  const lifetimeRenewalOrders = useMemo(() => {
    return [...orders]
      .filter((item) => String(item.status || "").toUpperCase() === "PAID" && isLifetimeText(item.plan_name))
      .sort((a, b) => (safeDateMillis(b.paid_at || b.created_at) ?? 0) - (safeDateMillis(a.paid_at || a.created_at) ?? 0));
  }, [orders]);
  const remindedToday = useMemo(() => paidMemberOrders.filter((item) => item.last_reminder_date && isTodayDate(item.last_reminder_date)), [paidMemberOrders]);
  function renewalCustomerName(item: Order | SupportEvent) {
    const telegramId = "telegram_user_id" in item ? String(item.telegram_user_id || "").trim() : "";
    const fromOrder = "full_name" in item ? displayText(item.full_name) : "";
    return fromOrder || customerNameById.get(telegramId) || telegramId || "-";
  }
  function telegramChatHref(telegramUserId: string, username?: string | null) {
    const handle = String(username || "").trim().replace(/^@/, "");
    if (handle) return `https://t.me/${handle}`;
    const id = String(telegramUserId || "").trim();
    if (!id) return "";
    return `tg://user?id=${encodeURIComponent(id)}`;
  }
  function telegramChatLink(label: ReactNode, telegramUserId: string, username?: string | null, color: string = "inherit") {
    const href = telegramChatHref(telegramUserId, username);
    const target = href.startsWith("https://") ? "_blank" : "_self";
    return href ? (
      <Box
        component="a"
        href={href}
        target={target}
        rel="noreferrer"
        onClick={(event) => event.stopPropagation()}
        sx={{
          color,
          textDecoration: "none",
          fontWeight: 800,
          display: "inline-flex",
          alignItems: "center",
          gap: 0.5,
          "&:hover": { textDecoration: "underline" },
        }}
      >
        {label}
      </Box>
    ) : (
      <Box component="span" sx={{ color, fontWeight: 800 }}>{label}</Box>
    );
  }
  function renewalRowFlags(telegramUserId: string, options?: { unreminded?: boolean }) {
    const customer = customerSummaryById.get(String(telegramUserId || "").trim());
    const paidCount = customer?.paidOrders.length || 0;
    const isNew = paidCount <= 1;
    const isSvip = customer?.paidOrders.some((order) => isLifetimeAllAccessText(order.plan_name)) || false;
    return {
      isNew,
      isSvip,
      isImportant: Boolean(options?.unreminded) || isNew || isSvip,
      isUnreminded: Boolean(options?.unreminded),
    };
  }
  function renewalBadgeRow(telegramUserId: string, options?: { unreminded?: boolean }) {
    const flags = renewalRowFlags(telegramUserId, options);
    const chips: ReactNode[] = [];
    if (flags.isImportant) chips.push(<Chip key="important" size="small" label="Ưu tiên" color="warning" variant="outlined" sx={{ height: 20, fontSize: 10.5, fontWeight: 800 }} />);
    if (flags.isNew) chips.push(<Chip key="new" size="small" label="Mới" color="info" variant="outlined" sx={{ height: 20, fontSize: 10.5, fontWeight: 800 }} />);
    if (flags.isSvip) chips.push(<Chip key="svip" size="small" label="Combo" color="secondary" variant="outlined" sx={{ height: 20, fontSize: 10.5, fontWeight: 800 }} />);
    if (options?.unreminded) chips.push(<Chip key="unreminded" size="small" label="Chưa nhắc" color="error" variant="outlined" sx={{ height: 20, fontSize: 10.5, fontWeight: 800 }} />);
    return chips;
  }
  function renewalStatusTone(status: string) {
    if (status === "Đã kick") return "success";
    if (status === "Bị giữ lại") return "info";
    if (status === "Lỗi") return "error";
    return "warning";
  }
  function renewalStatusLabel(status: string) {
    if (status === "Đã kick") return "Đã kick";
    if (status === "Bị giữ lại") return "Bị giữ lại";
    if (status === "Lỗi") return "Lỗi";
    if (status === "Chờ kick") return "Chờ kick";
    if (status === "Chờ audit") return "Chờ audit";
    return status || "-";
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
        <Box component="span" sx={{ display: "inline-grid", gap: 0.25 }}>
          {item.raw_data?.old_status || item.raw_data?.new_status ? (
            <Chip size="small" label={`${friendlyDetailText(String(item.raw_data?.old_status || "-"))} → ${friendlyDetailText(String(item.raw_data?.new_status || "-"))}`} color="info" variant="outlined" sx={{ height: 20, fontSize: 10.5, fontWeight: 800, width: "fit-content" }} />
          ) : null}
          {item.raw_data?.reason ? <Box sx={{ whiteSpace: "pre-line" }}>{friendlyDetailText(String(item.raw_data.reason))}</Box> : <Box sx={{ whiteSpace: "pre-line" }}>{friendlyDetailText(String(item.raw_data?.new_status || item.raw_data?.old_status || "-"))}</Box>}
        </Box>
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
  const renewalHeaders: Record<RenewalSubTab, string[]> = {
    soon: ["Khách", "Gói", "Hết hạn", "Nhắc gần nhất", "Trạng thái"],
    reminded: ["Khách", "Gói / Đơn", "Loại", "Lần thông báo", "Hạn dùng"],
    expired: ["Khách", "Gói / Đơn", "Hết hạn", "Xử lý kick", "Group đã kick", "Ghi chú"],
    lifetime: ["Khách", "Gói", "Ngày mua", "Nguồn", "Group"],
  };
  const renewalNoticeEvents = useMemo(() => {
    return [...renewalReminderEvents, ...expiredNoticeEvents].sort((a, b) => (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0));
  }, [renewalReminderEvents, expiredNoticeEvents]);
  function renewalNoticeLabel(event: SupportEvent) {
    return event.event_type === "expired_notice_sent" ? "Báo hết hạn" : "Nhắc gia hạn";
  }
  function renewalNoticeBatch(event: SupportEvent) {
    const rawExpire = String(event.raw_data?.expire_at || "");
    if (!rawExpire) return event.event_type === "expired_notice_sent" ? "Expired" : "Reminder";
    const diff = daysUntil(rawExpire);
    if (event.event_type === "expired_notice_sent" || diff < 0) return "Expired";
    return `T-${diff}`;
  }

  const kickAuditByOrder = useMemo(() => {
    const map = new Map<string, KickAuditRow[]>();
    for (const item of kickAudit) {
      const orderId = String(item.order_id || "");
      if (orderId) {
        if (!map.has(orderId)) map.set(orderId, []);
        map.get(orderId)!.push(item);
      }
      const userPlanKey = `${String(item.telegram_user_id || "")}|${String(item.plan_name || "")}`;
      if (userPlanKey !== "|") {
        if (!map.has(userPlanKey)) map.set(userPlanKey, []);
        map.get(userPlanKey)!.push(item);
      }
    }
    return map;
  }, [kickAudit]);

  const uniqueKickedEventsByOrder = useMemo(() => {
    const map = new Map<string, SupportEvent[]>();
    for (const item of uniqueKickedEvents) {
      const orderId = String(item.order_id || "");
      if (orderId) {
        if (!map.has(orderId)) map.set(orderId, []);
        map.get(orderId)!.push(item);
      }
      const userPlanKey = `${String(item.telegram_user_id || "")}|${String(item.plan_name || "")}`;
      if (userPlanKey !== "|") {
        if (!map.has(userPlanKey)) map.set(userPlanKey, []);
        map.get(userPlanKey)!.push(item);
      }
    }
    return map;
  }, [uniqueKickedEvents]);
  function expiredKickSummary(order: Order) {
    const orderId = String(order.order_id || "");
    const userPlanKey = `${String(order.telegram_user_id || "")}|${String(order.plan_name || "")}`;
    const audits = [
      ...(kickAuditByOrder.get(orderId) || []),
      ...(kickAuditByOrder.get(userPlanKey) || []),
    ].filter((item, index, self) => self.findIndex(t => t.audit_id === item.audit_id) === index);
    
    const kickedEvents = [
      ...(uniqueKickedEventsByOrder.get(orderId) || []),
      ...(uniqueKickedEventsByOrder.get(userPlanKey) || []),
    ].filter((item, index, self) => self.findIndex(t => t.id === item.id) === index);

    const groupDetails = audits.map((audit) => {
      const isKickedEvent = kickedEvents.some(k => String(k.chat_id || "") === String(audit.group_id || ""));
      const isKickedAudit = ["MEMBER_KICKED", "KICKED", "EXPIRED_KICKED"].includes(String(audit.status || "").toUpperCase());
      const isRetained = audit.status === "ACTIVE_RETAINED";
      const hasError = Boolean(audit.latest_error);
      const isPending = audit.needs_action || (!isKickedEvent && !isKickedAudit && !isRetained && !hasError);
      
      let groupStatus: "Đã kick" | "Bị giữ lại" | "Lỗi" | "Chờ kick" = "Chờ kick";
      if (isKickedEvent || isKickedAudit) groupStatus = "Đã kick";
      else if (isRetained) groupStatus = "Bị giữ lại";
      else if (hasError) groupStatus = "Lỗi";

      const note = audit.latest_error || audit.retained_reason || (audit.retained_orders?.length ? `Còn đơn active: ${audit.retained_orders.join(", ")}` : "") || kickAuditReason(audit);
      
      return {
        groupId: audit.group_id,
        groupName: audit.group_name || audit.group_id,
        status: groupStatus,
        note: note,
        auditId: audit.audit_id,
      };
    });

    const latestKickAt = kickedEvents.map((item) => item.created_at).sort((a, b) => (safeDateMillis(b) ?? 0) - (safeDateMillis(a) ?? 0))[0] || "";
    
    // Overall status logic
    let overallStatus: "Đã kick" | "Bị giữ lại" | "Lỗi" | "Chờ kick" | "Chờ audit" = "Chờ audit";
    if (groupDetails.length > 0) {
      if (groupDetails.every(g => g.status === "Đã kick" || g.status === "Bị giữ lại")) overallStatus = "Đã kick"; // Or considered complete
      else if (groupDetails.some(g => g.status === "Lỗi")) overallStatus = "Lỗi";
      else if (groupDetails.every(g => g.status === "Bị giữ lại")) overallStatus = "Bị giữ lại";
      else overallStatus = "Chờ kick";
    }

    const kickedCount = groupDetails.filter(g => g.status === "Đã kick").length;
    const errorCount = groupDetails.filter(g => g.status === "Lỗi").length;
    const retainedCount = groupDetails.filter(g => g.status === "Bị giữ lại").length;
    
    const overallNote = groupDetails.length === 0 ? "Chưa có audit kick gần nhất" : `Kick: ${kickedCount}/${groupDetails.length}` + (errorCount ? `, Lỗi: ${errorCount}` : "") + (retainedCount ? `, Giữ lại: ${retainedCount}` : "");

    return { 
      groups: groupDetails.map(g => g.groupName).filter(Boolean), 
      groupDetails,
      latestKickAt, 
      note: overallNote, 
      status: overallStatus 
    };
  }
  type RenewalOpsRow = {
    key: string;
    telegramId: string;
    searchText: string;
    flags: { isImportant: boolean; isNew: boolean; isSvip: boolean; isUnreminded: boolean };
    cells: ReactNode[];
    orderId?: string;
    planName?: string;
    customerName?: string;
    groupsToKick?: string[];
    groupsToReview?: string[];
    renewalStatus?: string;
    renewalNote?: string;
  };
  const renewalOpsRows = useMemo(() => {
    return {
      soon: expiringSoon.map((item) => {
        const reminderEvent = latestReminderByOrder.get(item.order_id);
        const unreminded = !reminderEvent && !item.last_reminder_date;
        return {
          key: `soon-${item.order_id}`,
          telegramId: String(item.telegram_user_id || "").trim(),
          searchText: `${renewalCustomerName(item)} ${item.telegram_user_id || ""} ${item.plan_name || ""} ${item.order_id || ""}`.toLowerCase(),
          flags: renewalRowFlags(String(item.telegram_user_id || ""), { unreminded }),
          cells: [
            <Fragment key="customer">
              {telegramChatLink(renewalCustomerName(item), String(item.telegram_user_id || "").trim(), undefined, "var(--ink)")}
              <div className="muted">{item.telegram_user_id || "-"}</div>
            </Fragment>,
            <Fragment key="plan"><strong>{resolveOrderLabel({ plan_name: item.plan_name }).displayLabel}</strong><div className="muted">Đơn {item.order_id || "-"}</div></Fragment>,
            <Fragment key="expire"><strong>{dateText(item.expire_at)}</strong><div className="muted">Còn {daysUntil(item.expire_at)} ngày</div></Fragment>,
            reminderEvent ? <Fragment key="reminder"><strong>{dateText(reminderEvent.created_at)}</strong><div className="muted">{renewalNoticeBatch(reminderEvent)}</div></Fragment> : item.last_reminder_date || "Chưa nhắc",
            <Chip key="status" size="small" label={unreminded ? "Chưa nhắc" : "Đã nhắc"} color={unreminded ? "warning" : "success"} variant="outlined" />,
          ] as ReactNode[],
        };
      }),
      reminded: renewalNoticeEvents.map((item) => ({
        key: `notice-${item.id}`,
        telegramId: String(item.telegram_user_id || "").trim(),
        searchText: `${renewalCustomerName(item)} ${item.telegram_user_id || ""} ${item.plan_name || ""} ${item.order_id || ""}`.toLowerCase(),
        flags: renewalRowFlags(String(item.telegram_user_id || "")),
        cells: [
          <Fragment key="customer">
            {telegramChatLink(renewalCustomerName(item), String(item.telegram_user_id || "").trim(), item.username, "var(--ink)")}
            <div className="muted">{item.telegram_user_id || "-"}</div>
          </Fragment>,
          <Fragment key="plan"><strong>{resolveOrderLabel({ plan_name: item.plan_name }).displayLabel}</strong><div className="muted">Đơn {item.order_id || "-"}</div></Fragment>,
          <Fragment key="type"><strong>{renewalNoticeLabel(item)}</strong><div className="muted">{renewalNoticeBatch(item)}</div></Fragment>,
          <Fragment key="at"><strong>{dateText(item.created_at)}</strong><div className="muted">{isTodayDate(item.created_at) ? "Hôm nay" : "Đã gửi"}</div></Fragment>,
          item.raw_data?.expire_at ? dateText(String(item.raw_data.expire_at)) : "-",
        ] as ReactNode[],
      })),
      expired: expiredRenewalOrders.map((item) => {
        const summary = expiredKickSummary(item);
        const tone = renewalStatusTone(summary.status);
        return {
          key: `expired-${item.order_id}`,
          telegramId: String(item.telegram_user_id || "").trim(),
          orderId: item.order_id,
          planName: item.plan_name,
          customerName: renewalCustomerName(item),
          groupsToKick: summary.groupDetails.filter(g => g.status === "Lỗi" || g.status === "Chờ kick").map(g => g.groupId),
          groupsToReview: summary.groupDetails.filter(g => g.status !== "Đã kick").map(g => g.groupId),
          renewalStatus: summary.status,
          renewalNote: summary.note,
          searchText: `${renewalCustomerName(item)} ${item.telegram_user_id || ""} ${item.plan_name || ""} ${item.order_id || ""} ${summary.groups.join(" ")} ${summary.note}`.toLowerCase(),
          flags: renewalRowFlags(String(item.telegram_user_id || ""), { unreminded: summary.status !== "Đã kick" }),
          cells: [
            <Fragment key="customer">
              {telegramChatLink(renewalCustomerName(item), String(item.telegram_user_id || "").trim(), undefined, "var(--ink)")}
              <div className="muted">{item.telegram_user_id || "-"}</div>
            </Fragment>,
            <Fragment key="plan"><strong>{resolveOrderLabel({ plan_name: item.plan_name }).displayLabel}</strong><div className="muted">Đơn {item.order_id || "-"}</div></Fragment>,
            <Fragment key="expire"><strong>{dateText(item.expire_at)}</strong><div className="muted">Quá {Math.abs(daysUntil(item.expire_at))} ngày</div></Fragment>,
            <Fragment key="status">
              <Stack spacing={0.75}>
                <Chip size="small" label={renewalStatusLabel(summary.status)} color={tone} variant="outlined" />
                {summary.latestKickAt ? <div className="muted">{dateText(summary.latestKickAt)}</div> : null}
              </Stack>
            </Fragment>,
            <Box key="groups" sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
              {summary.groupDetails.length ? summary.groupDetails.map((g, i) => (
                <Tooltip key={i} title={g.note || "Không có ghi chú"} arrow placement="left">
                  <Chip 
                    size="small" 
                    label={g.groupName} 
                    color={g.status === "Đã kick" ? "success" : g.status === "Lỗi" ? "error" : g.status === "Bị giữ lại" ? "info" : "warning"} 
                    variant="outlined" 
                    sx={{ height: 20, fontSize: 11 }} 
                  />
                </Tooltip>
              )) : "-"}
            </Box>,
            <Box key="notes" sx={{ display: "flex", flexDirection: "column", gap: 0.5, maxWidth: 200 }}>
              {summary.groupDetails.length ? summary.groupDetails.map((g, i) => {
                if (g.status === "Đã kick") return null;
                return (
                  <Typography key={i} variant="caption" sx={{ color: g.status === "Lỗi" ? "error.main" : "text.secondary", display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden", lineHeight: 1.2 }}>
                    <strong style={{ opacity: 0.7 }}>{g.groupName}</strong>: {g.note || g.status}
                  </Typography>
                );
              }) : summary.note}
            </Box>,
          ] as ReactNode[],
        };
      }),
      lifetime: lifetimeRenewalOrders.map((item) => ({
        key: `lifetime-${item.order_id}`,
        telegramId: String(item.telegram_user_id || "").trim(),
        searchText: `${renewalCustomerName(item)} ${item.telegram_user_id || ""} ${item.plan_name || ""} ${item.order_id || ""}`.toLowerCase(),
        flags: renewalRowFlags(String(item.telegram_user_id || "")),
        cells: [
          <Fragment key="customer">
            {telegramChatLink(renewalCustomerName(item), String(item.telegram_user_id || "").trim(), undefined, "var(--ink)")}
            <div className="muted">{item.telegram_user_id || "-"}</div>
          </Fragment>,
          <Fragment key="plan"><strong>{resolveOrderLabel({ plan_name: item.plan_name }).displayLabel}</strong><div className="muted">Đơn {item.order_id || "-"}</div></Fragment>,
          dateText(item.paid_at || item.created_at),
          [item.payment_provider || item.source_type || "PAID", inferOrderCurrency(item)].filter(Boolean).join(" / "),
          groupNamesForOrder(item).join(", ") || "Combo / trọn đời",
        ] as ReactNode[],
      })),
    } satisfies Record<RenewalSubTab, RenewalOpsRow[]>;
  }, [expiringSoon, latestReminderByOrder, renewalNoticeEvents, expiredRenewalOrders, lifetimeRenewalOrders, kickAudit, uniqueKickedEvents, renewalCustomerName]);
  const currentRenewalOpsRows = useMemo(() => {
    const source = (renewalOpsRows[renewalTab] || []) as RenewalOpsRow[];
    const q = renewalQuery.trim().toLowerCase();
    return source.filter((item) => {
      if (q && !item.searchText.includes(q)) return false;
      if (renewalTab === "expired" && renewalFocusFilter !== "all") {
        const status = String(item.renewalStatus || "");
        if (renewalFocusFilter === "chokick" && !["Chờ kick", "Chờ audit"].includes(status)) return false;
        if (renewalFocusFilter === "kicked" && status !== "Đã kick") return false;
        if (renewalFocusFilter === "retained" && status !== "Bị giữ lại") return false;
        if (renewalFocusFilter === "error" && status !== "Lỗi") return false;
        if (renewalFocusFilter === "review" && status === "Đã kick") return false;
      }
      return true;
    });
  }, [renewalFocusFilter, renewalOpsRows, renewalQuery, renewalTab]);
  const totalRenewalPages = Math.max(1, Math.ceil(currentRenewalOpsRows.length / RENEWAL_PAGE_SIZE));
  const pagedRenewalRows = useMemo(() => {
    const safePage = Math.min(renewalPage, totalRenewalPages);
    const start = (safePage - 1) * RENEWAL_PAGE_SIZE;
    return currentRenewalOpsRows.map((item) => item.cells).slice(start, start + RENEWAL_PAGE_SIZE);
  }, [currentRenewalOpsRows, renewalPage, totalRenewalPages]);
  const activityLogRows = activityLogResponse?.data || [];
  const activityLogSummary = activityLogResponse?.summary || { user: 0, bot: 0, today: 0 };
  const activityLogTotal = activityLogResponse?.total || 0;
  const logTypeOptions = useMemo(() => {
    const values = uniqueValues(activityLogResponse?.facets?.types || []);
    return values.sort((a, b) => a.localeCompare(b));
  }, [activityLogResponse?.facets?.types]);
  const logDateOptions = useMemo(() => {
    const values = uniqueValues(activityLogResponse?.facets?.dates || []);
    return values.sort((a, b) => {
      if (a === "UNKNOWN") return 1;
      if (b === "UNKNOWN") return -1;
      return b.localeCompare(a);
    });
  }, [activityLogResponse?.facets?.dates]);
  const campaignPlanOptions = useMemo(() => {
    return uniqueValues(orders.filter((item) => item.status === "PAID").map((item) => item.plan_name)).sort((a, b) => a.localeCompare(b));
  }, [orders]);
  const totalLogPages = Math.max(1, Math.ceil(activityLogTotal / LOG_PAGE_SIZE));
  const pagedLogEntries = activityLogRows;
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
  const overviewRecentOrders = useMemo(() => {
    if (dashboardOverview?.recent_orders?.length) return dashboardOverview.recent_orders as Order[];
    return [...orders]
      .sort((a, b) => (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0))
      .slice(0, 10);
  }, [dashboardOverview?.recent_orders, orders]);
  const overviewNewCustomers = useMemo(() => {
    if (dashboardOverview?.expiring_customers?.length) {
      return dashboardOverview.expiring_customers.map((item) => {
        const raw = item as { telegram_user_id?: string; order_id?: string; full_name?: string };
        return {
        id: String(raw.telegram_user_id || raw.order_id || ""),
        name: String(raw.full_name || raw.telegram_user_id || ""),
        orders: [],
        };
      }) as Array<{ id: string; name: string; orders: Order[] }>;
    }
    return [...customerSummaries]
      .filter((item) => item.lastOrderAt || item.hasAnyPaidOrder || item.orders.length)
      .sort((a, b) => (safeDateMillis(b.lastOrderAt) ?? 0) - (safeDateMillis(a.lastOrderAt) ?? 0))
      .slice(0, 10);
  }, [customerSummaries, dashboardOverview?.expiring_customers]);
  const overviewRecentUserActivity = useMemo(() => {
    if (dashboardOverview?.recent_user_activity?.length) return dashboardOverview.recent_user_activity as ActivityEvent[];
    return [...activityEvents]
      .filter((event) => {
        const chatType = payloadText(event.payload || {}, "chat_type").toLowerCase();
        return chatType !== "group" && chatType !== "supergroup" && chatType !== "channel";
      })
      .sort((a, b) => (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0))
      .slice(0, 10);
  }, [activityEvents, dashboardOverview?.recent_user_activity]);
  const overviewRecentNotifications = useMemo(() => {
    if (dashboardOverview?.recent_notifications?.length) {
      return dashboardOverview.recent_notifications.map((item) => ({
        key: `support-${String(item.id || "")}`,
        kind: "bot" as const,
        title: supportEventLabel(String(item.event_type || "")),
        detail: (() => {
          const raw = item as { full_name?: string; plan_name?: string; order_id?: string; raw_data?: { reason?: string } };
          return [String(raw.full_name || ""), String(raw.plan_name || ""), String(raw.order_id || "")].filter(Boolean).join(" • ") || String(raw.raw_data?.reason || "-");
        })(),
        createdAt: String((item as { created_at?: string }).created_at || ""),
        userId: String((item as { telegram_user_id?: string }).telegram_user_id || ""),
      }));
    }
    const userEvents = activityEvents
      .filter((event) => {
        const chatType = payloadText(event.payload || {}, "chat_type").toLowerCase();
        return chatType !== "group" && chatType !== "supergroup" && chatType !== "channel";
      })
      .map((event) => {
        const payload = event.payload || {};
        const messageText = payloadText(payload, "message_text");
        const title = messageText ? `Khách nhắn: ${messageText}` : payloadText(payload, "source_ref") || payloadText(payload, "activation_code") || activityEventLabel(payloadText(payload, "event_type") || event.event_name || "event");
        const detail = messageText ? [payloadText(payload, "message_kind"), payloadText(payload, "chat_type")].filter(Boolean).join(" • ") : payloadText(payload, "start_payload") || payloadText(payload, "callback_data") || payloadText(payload, "command") || "-";
        return {
          key: `activity-${event.id}`,
          kind: "user" as const,
          title,
          detail,
          createdAt: event.created_at,
          userId: event.telegram_user_id || payloadText(payload, "user_id") || "",
        };
      });
    const botEvents = supportEvents
      .filter((event) => [
        "manual_order_created",
        "manual_activation_link_generated",
        "manual_activation_link_failed",
        "activation_link_cleanup_done",
        "activation_link_cleanup_failed",
        "expired_notice_sent",
        "renewal_reminder_sent",
        "member_kicked",
        "member_muted",
        "member_unmuted",
        "support_joined",
        "support_left",
        "vip_joined",
        "vip_left",
      ].includes(event.event_type))
      .map((event) => ({
        key: `support-${event.id}`,
        kind: "bot" as const,
        title: supportEventLabel(event.event_type),
        detail: [event.full_name, event.plan_name, event.order_id].filter(Boolean).join(" • ") || event.raw_data?.reason || "-",
        createdAt: event.created_at,
        userId: event.telegram_user_id || "",
      }));
    return [...userEvents, ...botEvents].sort((a, b) => (safeDateMillis(b.createdAt) ?? 0) - (safeDateMillis(a.createdAt) ?? 0)).slice(0, 10);
  }, [activityEvents, dashboardOverview?.recent_notifications, supportEvents]);
  const overviewExpiringCustomers = useMemo(() => {
    if (dashboardOverview?.expiring_customers?.length) {
      return dashboardOverview.expiring_customers.map((item) => {
        const raw = item as { order_id?: string; telegram_user_id?: string; full_name?: string; plan_name?: string; expire_at?: string; days_remaining?: number };
        return {
          order_id: String(raw.order_id || ""),
          telegram_user_id: String(raw.telegram_user_id || ""),
          full_name: String(raw.full_name || ""),
          plan_name: String(raw.plan_name || ""),
          expire_at: String(raw.expire_at || ""),
          daysRemaining: Number(raw.days_remaining || 0),
        };
      });
    }
    return [...customerSummaries]
      .filter((item) => item.expiringWithinWindow || item.activeOrders.some((order) => daysUntil(order.expire_at) >= 0 && daysUntil(order.expire_at) <= reminderNoticeDays))
      .sort((a, b) => {
        const aDays = a.activeOrders.length ? Math.min(...a.activeOrders.map((order) => daysUntil(order.expire_at)).filter((days) => Number.isFinite(days))) : 9999;
        const bDays = b.activeOrders.length ? Math.min(...b.activeOrders.map((order) => daysUntil(order.expire_at)).filter((days) => Number.isFinite(days))) : 9999;
        return aDays - bDays;
      })
      .slice(0, 10);
  }, [customerSummaries, dashboardOverview?.expiring_customers, reminderNoticeDays]);
  const overviewHealthAlerts = useMemo(() => {
    if (dashboardOverview?.health_alerts?.length) return dashboardOverview.health_alerts;
    const alerts: { title: string; detail: string; tone: "good" | "warning" | "bad" }[] = [];
    if (webhookMeta?.maintenance_override?.active) alerts.push({ title: "Webhook", detail: webhookMeta.maintenance_override.reason || "Bot đang bảo trì do webhook lỗi", tone: "bad" });
    else if (!webhook?.url) alerts.push({ title: "Webhook", detail: "Chưa có URL webhook đang hoạt động", tone: "bad" });
    else if (webhookMeta?.problem_reason) alerts.push({ title: "Webhook", detail: `Webhook có lỗi: ${webhookMeta.problem_reason}`, tone: "warning" });
    else alerts.push({ title: "Webhook", detail: "Webhook đang hoạt động", tone: "good" });
    if (botScheduleStatus?.active) alerts.push({ title: "Bot", detail: botScheduleStatus.title || "Bot đang hoạt động", tone: "good" });
    else alerts.push({ title: "Bot", detail: botScheduleStatus?.title || "Bot đang tạm dừng", tone: "warning" });
    alerts.push({ title: "Đơn chờ", detail: `${metrics.pending} đơn đang chờ`, tone: metrics.pending > 0 ? "warning" : "good" });
    alerts.push({ title: "Sắp hết hạn", detail: `${expiringSoon.length} khách trong khung nhắc`, tone: expiringSoon.length > 0 ? "warning" : "good" });
    if (missingCore.length) {
      alerts.push({ title: "Thiếu cấu hình", detail: missingCore[0], tone: "bad" });
    }
    return alerts.slice(0, 5);
  }, [botScheduleStatus, dashboardOverview?.health_alerts, expiringSoon.length, metrics.pending, missingCore, webhook]);
  const overviewPriorityAlerts = useMemo(() => {
    if (dashboardOverview?.priority_alerts?.length) return dashboardOverview.priority_alerts;
    const rows: { title: string; detail: string; tone: "warning" | "bad" }[] = [];
    if (expiringSoon.length) rows.push({ title: "Khách sắp hết hạn", detail: `${expiringSoon.length} khách cần nhắc gia hạn`, tone: "warning" });
    if (metrics.pending) rows.push({ title: "Đơn đang chờ", detail: `${metrics.pending} đơn chưa chốt trạng thái`, tone: "warning" });
    if (missingCore.length) rows.push({ title: "Thiếu cấu hình", detail: missingCore.join(" • "), tone: "bad" });
    if (supportGroupEvents.length && supportGroupTodayEvents.length) rows.push({ title: "Nhóm hỗ trợ", detail: `${supportGroupTodayEvents.length} sự kiện hôm nay`, tone: "warning" });
    return rows.slice(0, 4);
  }, [dashboardOverview?.priority_alerts, expiringSoon.length, metrics.pending, missingCore, supportGroupEvents.length, supportGroupTodayEvents.length]);

  const visibleAdminNotifications = useMemo(() => {
    return adminNotifications.filter((item) => {
      if (item.kind === "order" && !notificationOrdersEnabled) return false;
      if (item.kind === "message") return false;
      return true;
    });
  }, [adminNotifications, notificationOrdersEnabled]);

  const unreadAdminNotifications = useMemo(() => {
    const seen = new Set(notificationSeenIds);
    return visibleAdminNotifications.filter((item) => !seen.has(item.id));
  }, [notificationSeenIds, visibleAdminNotifications]);

  const unreadAdminNotificationCount = unreadAdminNotifications.length;
  const previousUnreadCountRef = useRef(0);
  const previousSupportUnreadCountRef = useRef(0);

  const supportInboxItems = useMemo(() => {
    return [...supportInboxCases]
      .map((item) => {
        const ticket = item.ticket;
        const messages = [...(item.messages || [])].sort((a, b) => (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0));
        const latestMessage = messages[0] || null;
        const latestUserMessage = messages.find((message) => String(message.direction || "").toLowerCase().includes("user")) || latestMessage;
        const previewText = displayText(
          String(latestUserMessage?.text || latestMessage?.text || ticket.subject || ticket.full_name || ticket.telegram_user_id || "")
        );
        const hasExtraMessages = messages.length > 1;
        return {
          id: ticket.id,
          event_type: "support_case",
          telegram_user_id: String(ticket.telegram_user_id || "").trim(),
          username: String(ticket.username || "").trim(),
          full_name: String(ticket.full_name || "").trim(),
          title: displayText(ticket.full_name || ticket.username) || String(ticket.telegram_user_id || "Khách"),
          detail: previewText || "Tin nhắn riêng",
          created_at: latestMessage?.created_at || ticket.updated_at || ticket.created_at,
          ticket_id: ticket.id,
          ticket_no: String(ticket.ticket_no || "").trim(),
          order_id: String(ticket.subject || "").trim(),
          plan_name: String(ticket.source || "").trim(),
          latestMessageText: previewText,
          messageCount: messages.length,
          hasExtraMessages,
          latestMessageId: latestMessage?.id || "",
          unreadKey: `${ticket.id}:${latestMessage?.id || "none"}`,
          messages,
        };
      })
      .sort((a, b) => (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0));
  }, [supportInboxCases]);

  const unreadSupportInboxItems = useMemo(() => {
    const seen = new Set(supportInboxSeenIds);
    return supportInboxItems.filter((item) => !seen.has(item.unreadKey || item.id));
  }, [supportInboxItems, supportInboxSeenIds]);

  const unreadSupportInboxCount = unreadSupportInboxItems.length;

  const adminReplyThreadMessages = useMemo(() => {
    const messages = [...(adminReplyThread?.messages || [])]
      .sort((a, b) => (safeDateMillis(a.created_at) ?? 0) - (safeDateMillis(b.created_at) ?? 0));
    if (adminReplyOptimisticMessage) {
      const optimisticKey = adminReplyOptimisticMessage.id;
      const duplicate = messages.some((item) => item.id === optimisticKey || (String(item.direction || "").toLowerCase().includes("support_to_user") && item.text === adminReplyOptimisticMessage.text && Math.abs((safeDateMillis(item.created_at) ?? 0) - (safeDateMillis(adminReplyOptimisticMessage.created_at) ?? 0)) < 60000));
      if (!duplicate) messages.push(adminReplyOptimisticMessage);
    }
    return messages;
  }, [adminReplyOptimisticMessage, adminReplyThread]);

  useEffect(() => {
    if (!adminReplyOptimisticMessage) return;
    const messages = adminReplyThread?.messages || [];
    const confirmed = messages.some((item) => {
      if (item.id === adminReplyOptimisticMessage.id) return true;
      const sameDirection = String(item.direction || "").toLowerCase().includes("support_to_user") || String(item.direction || "").toLowerCase().includes("manager");
      const sameText = String(item.text || "").trim() === String(adminReplyOptimisticMessage.text || "").trim();
      const closeTime = Math.abs((safeDateMillis(item.created_at) ?? 0) - (safeDateMillis(adminReplyOptimisticMessage.created_at) ?? 0)) < 120000;
      return sameDirection && sameText && closeTime;
    });
    if (confirmed) {
      if (adminReplyFallbackTimerRef.current) {
        window.clearTimeout(adminReplyFallbackTimerRef.current);
        adminReplyFallbackTimerRef.current = null;
      }
      console.info("[admin-reply] thread confirmed", {
        userId: adminReplyTarget?.userId,
        messageId: adminReplyOptimisticMessage.id,
      });
      setAdminReplyOptimisticMessage(null);
    }
  }, [adminReplyOptimisticMessage, adminReplyThread]);

  useEffect(() => {
    return () => {
      if (adminReplyFallbackTimerRef.current) {
        window.clearTimeout(adminReplyFallbackTimerRef.current);
        adminReplyFallbackTimerRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!adminReplyOpen) return;
    if (!adminReplyThreadMessages.length) return;
    if (!adminReplyStickToBottomRef.current) return;
    const raf = window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        adminReplyThreadBottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
      });
    });
    adminReplyStickToBottomRef.current = false;
    return () => window.cancelAnimationFrame(raf);
  }, [adminReplyOpen, adminReplyThreadMessages.length]);

  const markAllNotificationsRead = useCallback(() => {
    setNotificationSeenIds((current) => {
      const seen = new Set(current);
      visibleAdminNotifications.forEach((item) => seen.add(item.id));
      return Array.from(seen);
    });
  }, [visibleAdminNotifications]);

  const markAllSupportInboxRead = useCallback(() => {
    setSupportInboxSeenIds((current) => {
      const seen = new Set(current);
      supportInboxItems.forEach((item) => seen.add(item.unreadKey || item.id));
      return Array.from(seen);
    });
  }, [supportInboxItems]);

  const openNotificationMenu = useCallback((event: MouseEvent<HTMLElement>) => {
    setNotificationMenuAnchorEl(event.currentTarget);
  }, []);

  const closeNotificationMenu = useCallback(() => {
    setNotificationMenuAnchorEl(null);
  }, []);

  const openSupportInboxMenu = useCallback((event: MouseEvent<HTMLElement>) => {
    setSupportInboxMenuAnchorEl(event.currentTarget);
  }, []);

  const closeSupportInboxMenu = useCallback(() => {
    setSupportInboxMenuAnchorEl(null);
  }, []);

  const toggleNotificationExpanded = useCallback((id: string) => {
    setNotificationExpandedIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]);
  }, []);

  const openSupportInboxItem = useCallback((item: {
    id: string;
    ticket_id?: string;
    telegram_user_id: string;
    title: string;
    detail: string;
    full_name: string;
    username: string;
    order_id: string;
    plan_name: string;
    unreadKey?: string;
    messages?: SupportMessage[];
  }) => {
    setSupportInboxSeenIds((current) => uniqueValues([...current, item.unreadKey || item.id]));
    closeSupportInboxMenu();
    selectTab("supportGroup");
    setSupportTab("all");
    if (item.telegram_user_id) setQuery(item.telegram_user_id);
    openAdminReply({
      id: item.id,
      userId: item.telegram_user_id,
      fullName: item.full_name || item.title || item.telegram_user_id,
      username: item.username || "",
      title: item.title,
      detail: item.detail,
      ticketId: item.ticket_id,
      initialMessages: item.messages,
    });
  }, [closeSupportInboxMenu, openAdminReply, selectTab, setQuery, setSupportTab]);

  const openNotificationItem = useCallback((item: AdminNotificationItem) => {
    setNotificationSeenIds((current) => uniqueValues([...current, item.id]));
    closeNotificationMenu();

    if (item.kind === "order") {
      selectTab("orders");
      setOrderPage(1);
      if (item.order_id) {
        const matchedOrder = orders.find((order) => order.order_id === item.order_id);
        if (matchedOrder) {
          requestAnimationFrame(() => {
            openOrderEditor(matchedOrder);
          });
        } else if (item.telegram_user_id) {
          setQuery(item.telegram_user_id);
        }
      } else if (item.telegram_user_id) {
        setQuery(item.telegram_user_id);
      }
      return;
    }

    selectTab("supportGroup");
    setSupportTab("all");
    if (item.telegram_user_id) {
      setQuery(item.telegram_user_id);
    }
    if (item.telegram_user_id) {
      openAdminReply({
        id: item.id,
        userId: item.telegram_user_id,
        fullName: item.full_name || item.telegram_user_id,
        username: "",
        title: item.title,
        detail: item.detail,
      });
    }
  }, [closeNotificationMenu, openAdminReply, openOrderEditor, orders, selectTab, setOrderPage, setQuery, setSupportTab]);

  const notificationChipText = useCallback((item: AdminNotificationItem) => {
    const chips: string[] = [];
    const amount = String(item.amount || "").trim();
    const currency = String(item.payment_currency || "").trim();
    if (amount) {
      const numericAmount = Number(String(amount).replace(/,/g, "").trim());
      if (!Number.isNaN(numericAmount)) chips.push(formatDisplayCurrency(numericAmount, currency || "VND"));
    }
    if (item.payment_provider) chips.push(item.payment_provider);
    if (item.status) chips.push(item.status);
    if (item.expire_at) chips.push(dateTextShort(item.expire_at));
    return chips;
  }, []);

  const playNotificationSound = useCallback(() => {
    if (typeof window === "undefined") return;
    const now = Date.now();
    if (now - notificationSoundRef.current.playedAt < 1800) return;
    notificationSoundRef.current.playedAt = now;
    try {
      const AudioContextCtor = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AudioContextCtor) return;
      const audioContext = new AudioContextCtor();
      const gain = audioContext.createGain();
      gain.gain.value = 0.0001;
      gain.connect(audioContext.destination);
      const attack = audioContext.currentTime;
      const tones = [880, 1174.66];
      tones.forEach((frequency, index) => {
        const oscillator = audioContext.createOscillator();
        oscillator.type = index === 0 ? "sine" : "triangle";
        oscillator.frequency.value = frequency;
        oscillator.connect(gain);
        oscillator.start(attack + index * 0.04);
        oscillator.stop(attack + 0.25 + index * 0.04);
      });
      gain.gain.exponentialRampToValueAtTime(0.08, attack + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, attack + 0.32);
      window.setTimeout(() => {
        void audioContext.close().catch(() => undefined);
      }, 450);
    } catch {
      // ignore autoplay / browser audio errors
    }
  }, []);

  useEffect(() => {
    const previous = previousUnreadCountRef.current;
    if (unreadAdminNotificationCount > previous && previous >= 0) {
      playNotificationSound();
    }
    previousUnreadCountRef.current = unreadAdminNotificationCount;
  }, [playNotificationSound, unreadAdminNotificationCount]);

  const playSupportInboxSound = useCallback(() => {
    if (typeof window === "undefined") return;
    const now = Date.now();
    if (now - notificationSoundRef.current.playedAt < 1400) return;
    notificationSoundRef.current.playedAt = now;
    try {
      const AudioContextCtor = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AudioContextCtor) return;
      const audioContext = new AudioContextCtor();
      const gain = audioContext.createGain();
      gain.gain.value = 0.0001;
      gain.connect(audioContext.destination);
      const attack = audioContext.currentTime;
      const tones = [659.25, 988];
      tones.forEach((frequency, index) => {
        const oscillator = audioContext.createOscillator();
        oscillator.type = index === 0 ? "sine" : "triangle";
        oscillator.frequency.value = frequency;
        oscillator.connect(gain);
        oscillator.start(attack + index * 0.035);
        oscillator.stop(attack + 0.22 + index * 0.035);
      });
      gain.gain.exponentialRampToValueAtTime(0.07, attack + 0.015);
      gain.gain.exponentialRampToValueAtTime(0.0001, attack + 0.28);
      window.setTimeout(() => {
        void audioContext.close().catch(() => undefined);
      }, 380);
    } catch {
      // ignore autoplay / browser audio errors
    }
  }, []);

  useEffect(() => {
    const previous = previousSupportUnreadCountRef.current;
    if (unreadSupportInboxCount > previous && previous >= 0) {
      playSupportInboxSound();
    }
    previousSupportUnreadCountRef.current = unreadSupportInboxCount;
  }, [playSupportInboxSound, unreadSupportInboxCount]);

  const actionableFeed = useMemo(() => {
    if (dashboardOverview?.priority_alerts?.length || dashboardOverview?.recent_orders?.length || dashboardOverview?.recent_notifications?.length || dashboardOverview?.recent_user_activity?.length) {
      const overview = dashboardOverview!;
      const feed: { type: string; id: string; priority: number; title: string; detail: string; time: string; tone: "critical" | "warning" | "good" }[] = [];
      overview.priority_alerts.forEach((item, idx) => feed.push({ type: "alert", id: `summary-alert-${idx}`, priority: item.tone === "bad" ? 10 : 8, title: item.title, detail: item.detail, time: new Date().toISOString(), tone: item.tone === "bad" ? "critical" : "warning" }));
      overview.recent_notifications.slice(0, 5).forEach((item, idx) => {
        const raw = item as { event_type?: string; full_name?: string; plan_name?: string; order_id?: string; created_at?: string };
        feed.push({ type: "bot", id: `summary-bot-${idx}`, priority: 4, title: supportEventLabel(String(raw.event_type || "")), detail: [String(raw.full_name || ""), String(raw.plan_name || ""), String(raw.order_id || "")].filter(Boolean).join(" • ") || "-", time: String(raw.created_at || new Date().toISOString()), tone: "good" });
      });
      overview.recent_orders.slice(0, 5).forEach((item, idx) => {
        const raw = item as { order_id?: string; full_name?: string; plan_name?: string; created_at?: string };
        feed.push({ type: "order", id: `summary-order-${idx}`, priority: 2, title: `Đơn mới: ${String(raw.order_id || "")}`, detail: `${String(raw.full_name || "Khách ẩn danh")} • ${resolveOrderLabel({ plan_name: raw.plan_name }).displayLabel}`, time: String(raw.created_at || new Date().toISOString()), tone: "good" });
      });
      return feed.sort((a, b) => b.priority - a.priority || (safeDateMillis(b.time) ?? 0) - (safeDateMillis(a.time) ?? 0)).slice(0, 10);
    }
    const feed: { type: string; id: string; priority: number; title: string; detail: string; time: string; tone: "critical" | "warning" | "good" }[] = [];
    
    // Priority Alerts (Critical)
    if (missingCore.length) feed.push({ type: "alert", id: "missing-core", priority: 10, title: "Thiếu cấu hình hệ thống", detail: missingCore.join(" • "), time: new Date().toISOString(), tone: "critical" });
    if (webhookMeta?.maintenance_override?.active) feed.push({ type: "alert", id: "webhook-maint", priority: 9, title: "Webhook đang bảo trì", detail: webhookMeta.maintenance_override.reason || "Bot đang bảo trì do webhook", time: new Date().toISOString(), tone: "critical" });
    else if (!webhook?.url || webhookMeta?.problem_reason) feed.push({ type: "alert", id: "webhook-prob", priority: 9, title: "Lỗi Webhook", detail: webhookMeta?.problem_reason || "Chưa có URL webhook", time: new Date().toISOString(), tone: "critical" });
    else if (botScheduleStatus && !botScheduleStatus.active) feed.push({ type: "alert", id: "bot-offline", priority: 8, title: "Bot đang Offline", detail: botScheduleStatus.title, time: new Date().toISOString(), tone: "critical" });
    
    // Pending Orders (High)
    const pendingOrders = orders.filter((o) => o.status === "PENDING").slice(0, 10);
    pendingOrders.forEach((o) => {
      feed.push({ type: "order", id: `order-${o.order_id}`, priority: 5, title: `Đơn chờ duyệt: ${o.order_id}`, detail: `${o.full_name || "Khách ẩn danh"} • ${o.plan_name}`, time: o.created_at, tone: "warning" });
    });

    // Expiring Customers (Medium)
    expiringSoon.slice(0, 10).forEach((c) => {
      feed.push({ type: "customer", id: `exp-${c.order_id}`, priority: 3, title: `Khách sắp hết hạn: ${c.full_name || "Không rõ"}`, detail: `Còn ${daysUntil(c.expire_at)} ngày • ${c.plan_name}`, time: new Date().toISOString(), tone: "warning" });
    });

    // Just added orders (Low)
    const paidOrders = orders.filter((o) => o.status === "PAID").slice(0, 5);
    paidOrders.forEach((o) => {
      feed.push({ type: "order", id: `order-paid-${o.order_id}`, priority: 1, title: `Đơn mới: ${o.order_id}`, detail: `${o.full_name || "Khách ẩn danh"} • ${o.plan_name}`, time: o.created_at, tone: "good" });
    });

    return feed.sort((a, b) => b.priority - a.priority || (safeDateMillis(b.time) ?? 0) - (safeDateMillis(a.time) ?? 0));
  }, [missingCore, webhookMeta, webhook, botScheduleStatus, orders, expiringSoon]);

  const activityStream = useMemo(() => {
    if (dashboardOverview?.recent_user_activity?.length) {
      return dashboardOverview.recent_user_activity.slice(0, 20).map((e) => ({
        id: `act-${String(e.id || "")}`,
        type: String(e.event_name || "event"),
        title: activityEventLabel(String(e.event_name || "event")),
        detail: String(e.telegram_user_id || "Không rõ"),
        time: String(e.created_at || new Date().toISOString()),
      }));
    }
    const stream: { id: string; type: string; title: string; detail: string; time: string }[] = [];
    overviewRecentUserActivity.slice(0, 20).forEach((e) => {
      stream.push({
        id: `act-${e.id}`,
        type: payloadText(e.payload || {}, "event_type") || e.event_name || "event",
        title: activityEventLabel(payloadText(e.payload || {}, "event_type") || e.event_name || "event"),
        detail: customerNameById.get(e.telegram_user_id || payloadText(e.payload || {}, "user_id")) || payloadText(e.payload || {}, "full_name") || payloadText(e.payload || {}, "username") || e.telegram_user_id || "Không rõ",
        time: e.created_at,
      });
    });
    return stream.sort((a, b) => (safeDateMillis(b.time) ?? 0) - (safeDateMillis(a.time) ?? 0));
  }, [dashboardOverview?.recent_user_activity, overviewRecentUserActivity, customerNameById]);
  const visibleChannelPosts = useMemo(() => {
    return channelPosts
      .filter((item) => channelPostTabFor(item) === channelPostTab)
      .sort((a, b) => (safeDateMillis(b.updated_at || b.created_at) ?? 0) - (safeDateMillis(a.updated_at || a.created_at) ?? 0));
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
  }, [query, orderTab, orderPeriod]);

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
    if (value === "FULL_1M") return "Combo - 30 ngày";
    if (value === "FULL_LIFE") return "Combo - trọn đời";
    if (value === "SELECT_GROUP_1M") return "Khách tự chọn collection lẻ - 30 ngày";
    if (value === "SELECT_GROUP_LIFE") return "Khách tự chọn collection lẻ - trọn đời";
    const match = value.match(/^G(\d+)_(1M|LIFE)$/);
    if (!match) return value;
    const name = getConfigValue(config, `BTN_G${match[1]}`) || `Nhóm G${match[1]}`;
    return `${name} - ${match[2] === "1M" ? "30 ngày" : "trọn đời"}`;
  }

  function priceOptionLabel(value: string) {
    if (value === "PRICE_COMBO_30D") return "Giá Combo - 30 ngày";
    if (value === "PRICE_COMBO_LIFE") return "Giá Combo - trọn đời";
    if (value === "PRICE_COMBO_30D_USD") return "Giá USD Combo - 30 ngày";
    if (value === "PRICE_COMBO_LIFE_USD") return "Giá USD Combo - trọn đời";
    const match = value.match(/^PRICE_G(\d+)_(1M|LIFE)(_USD)?$/);
    if (!match) return value;
    const name = getConfigValue(config, `BTN_G${match[1]}`) || `Nhóm G${match[1]}`;
    return `${name} - ${match[2] === "1M" ? "giá 30 ngày" : "giá trọn đời"}${match[3] ? " (USD)" : " (VNĐ)"}`;
  }

  function manualPlanNameFromKey(value: string) {
    if (value === "FULL_1M") return getConfigValue(config, "PLAN_COMBO_30D", getConfigValue(config, "PLAN_ALL_ACCESS_30D", "Combo 30 Ngày")) || "Combo 30 Ngày";
    if (value === "FULL_LIFE") return getConfigValue(config, "PLAN_COMBO_LIFE", getConfigValue(config, "PLAN_ALL_ACCESS_LIFE", "Combo Trọn Đời")) || "Combo Trọn Đời";
    const match = value.match(/^G(\d+)_(1M|LIFE)$/);
    if (!match) return "";
    const prefixKey = match[2] === "1M" ? "PLAN_COLLECTION_30D" : "PLAN_COLLECTION_LIFE";
    const fallbackPrefix = match[2] === "1M" ? "Collection 30 Ngày" : "Collection Trọn Đời";
    const prefix = getConfigValue(config, prefixKey, fallbackPrefix) || fallbackPrefix;
    const groupName = getConfigValue(config, `BTN_G${match[1]}`) || `G${match[1]}`;
    return `${prefix} - ${groupName}`;
  }

  function manualPriceFromKey(value: string) {
    if (value === "FULL_1M") return getConfigValue(config, "PRICE_COMBO_30D", "0");
    if (value === "FULL_LIFE") return getConfigValue(config, "PRICE_COMBO_LIFE", "0");
    const match = value.match(/^G(\d+)_(1M|LIFE)$/);
    if (!match) return "";
    return getConfigValue(config, `PRICE_G${match[1]}_${match[2]}`, "0");
  }

  function hiddenGroupDurationLabel(group: HiddenGroup, durationKey: string) {
    return String(durationKey).toUpperCase() === "LIFE"
      ? "Trọn đời"
      : `${group.duration_1m_days || 30} Ngày`;
  }

  function hiddenGroupManualPrice(group: HiddenGroup, durationKey: string, currency: string) {
    const useUsd = String(currency || "VND").toUpperCase() === "USD";
    if (String(durationKey).toUpperCase() === "LIFE") return useUsd ? group.price_life_usd : group.price_life_vnd;
    return useUsd ? group.price_1m_usd : group.price_1m_vnd;
  }

  function hiddenGroupManualPlanName(group: HiddenGroup, durationKey: string) {
    const durationLabel = hiddenGroupDurationLabel(group, durationKey);
    return `Hidden - ${group.name} - ${durationLabel} [PT:HG:${group.id}:${String(durationKey).toUpperCase() === "LIFE" ? "LIFE" : "1M"}]`;
  }

  function changeManualPlanKey(value: string) {
    const lifetime = isLifetimePlanKey(value);
    const customDuration = value === "CUSTOM_DURATION";
    const nextPlanName = value === "CUSTOM"
      ? (manualOrderForm.plan_name.trim() || manualPlanNameFromKey("FULL_1M"))
      : manualPlanNameFromKey(value);
    setManualOrderForm({
      ...manualOrderForm,
      plan_key: value,
      plan_name: nextPlanName,
      plan_mode: customDuration ? "CUSTOM_DURATION" : "",
      entitlement_type: customDuration ? "ALL_ACCESS" : manualOrderForm.entitlement_type,
      entitlement_key: customDuration ? "" : manualOrderForm.entitlement_key,
  
      amount: manualPriceFromKey(value) || manualOrderForm.amount,
      expiry_mode: lifetime ? "days" : manualOrderForm.expiry_mode || "days",
      duration_days: customDuration ? "1" : (lifetime ? String(lifetimeCouponDays || 3650) : "30"),
      expire_at: lifetime ? "" : manualOrderForm.expire_at,
      special_group_id: value === "CUSTOM" ? manualOrderForm.special_group_id : "",
      special_group_duration: value === "CUSTOM" ? manualOrderForm.special_group_duration : "1M",
    });
  }

  function changeManualSpecialGroup(groupId: string, durationKey = manualOrderForm.special_group_duration || "1M") {
    const group = activeSpecialGroups.find((item) => item.id === groupId) || null;
    const normalizedDuration = String(durationKey || "1M").toUpperCase() === "LIFE" ? "LIFE" : "1M";
    const nextPlanName = group ? hiddenGroupManualPlanName(group, normalizedDuration) : "";
    const nextAmount = group ? String(hiddenGroupManualPrice(group, normalizedDuration, manualOrderForm.payment_currency) || "0") : manualOrderForm.amount;
    setManualOrderForm({
      ...manualOrderForm,
      plan_key: group ? "CUSTOM" : manualOrderForm.plan_key,
      special_group_id: groupId,
      special_group_duration: normalizedDuration,
      plan_name: nextPlanName || manualOrderForm.plan_name || manualPlanNameFromKey("FULL_1M"),
      
      amount: nextAmount,
      expiry_mode: "days",
      duration_days: normalizedDuration === "LIFE"
        ? String(group?.lifetime_days || lifetimeCouponDays || 3650)
        : String(group?.duration_1m_days || manualOrderForm.duration_days || 30),
    });
  }

  function manualOrderTechnicalPlanName() {
    const group = manualOrderForm.special_group_id ? activeSpecialGroups.find((item) => item.id === manualOrderForm.special_group_id) || null : null;
    if (group) return hiddenGroupManualPlanName(group, manualOrderForm.special_group_duration || "1M");
    if (manualOrderForm.plan_key === "CUSTOM") return manualOrderForm.plan_name.trim() || manualPlanNameFromKey("FULL_1M");
    return manualPlanNameFromKey(manualOrderForm.plan_key);
  }

  function manualOrderPlanNameDisplay() {
    const group = manualOrderForm.special_group_id ? activeSpecialGroups.find((item) => item.id === manualOrderForm.special_group_id) || null : null;
    if (group) return hiddenGroupManualPlanName(group, manualOrderForm.special_group_duration || "1M");
    return manualOrderTechnicalPlanName();
  }

  function manualExpiryPreview() {
    if (manualOrderForm.expiry_mode === "date") {
      return `Sẽ áp dụng: ${dateTimePreviewText(manualOrderForm.expire_at, "Chưa chọn ngày hết hạn")}`;
    }
    if (isLifetimeText(manualOrderPlanNameDisplay())) {
      return `Sẽ áp dụng: ${manualOrderForm.duration_days || lifetimeCouponDays || "3650"} ngày (lifetime)`;
    }
    return `Sẽ áp dụng: ${manualOrderForm.duration_days || "30"} ngày`;
  }

  function syncCustomerRenewPlan(nextPlan: string) {
    const matchedOrder = selectedCustomer?.paidOrders.find((item) => item.plan_name === nextPlan) || null;
    const lifetime = isLifetimeText(nextPlan);
    setCustomerRenewForm((current) => ({
      ...current,
      order_id: matchedOrder?.order_id || "",
      plan_name: nextPlan,
      note: matchedOrder ? orderNoteText(matchedOrder) : current.note,
      amount: matchedOrder ? String(matchedOrder.amount || "") : current.amount,
      duration_days: lifetime ? "0" : "30",
      payment_currency: String(matchedOrder?.payment_currency || current.payment_currency || "VND").toUpperCase(),
      payment_provider: String(matchedOrder?.payment_provider || current.payment_provider || "MANUAL").toUpperCase(),
    }));
  }

  async function retryKickUserHandler(telegramId: string, orderId: string, planName: string, customerName: string, groupsToKick: string[]) {
    await runAction(`retry-kick-${orderId}`, async () => {
      let successCount = 0;
      let errorCount = 0;
      for (const groupId of groupsToKick) {
        try {
          await kickAuditMember(savedSecret, {
            telegram_user_id: telegramId,
            order_id: orderId,
            group_id: groupId,
            plan_name: planName,
            customer_name: customerName,
          });
          successCount++;
        } catch (err) {
          console.error("Retry kick error for group", groupId, err);
          errorCount++;
        }
      }
      if (errorCount === 0 && successCount > 0) {
        showNotice("ok", `Đã kick thành công khỏi ${successCount} nhóm.`);
      } else if (successCount > 0) {
        showNotice("error", `Đã kick thành công ${successCount} nhóm. Lỗi ${errorCount} nhóm.`);
      } else {
        showNotice("error", `Lỗi kick lại cho ${groupsToKick.length} nhóm. Vui lòng kiểm tra log.`);
      }
      await refreshKickAudit(true);
    });
  }

  async function saveManualOrder() {
    const specialGroup = activeSpecialGroups.find((item) => item.id === manualOrderForm.special_group_id) || null;
    const specialPlanName = specialGroup ? hiddenGroupManualPlanName(specialGroup, manualOrderForm.special_group_duration || "1M") : "";
    const planName = specialPlanName || (manualOrderForm.plan_mode === "CUSTOM_DURATION" ? "Tùy chỉnh" : manualOrderTechnicalPlanName());
    const paymentCurrency = String(manualOrderForm.payment_currency || "VND").toUpperCase();
    const paymentProvider = String(manualOrderForm.payment_provider || "MANUAL").toUpperCase();
    const isLifetime = isLifetimeText(planName);
    const durationDays = manualOrderForm.expiry_mode === "days" || isLifetime ? (manualOrderForm.duration_days || String(lifetimeCouponDays || 3650)) : "";
    const expireAt = manualOrderForm.expiry_mode === "date" && !isLifetime ? manualOrderForm.expire_at : "";
    await runAction("manual-order", async () => {
      const res = await createManualOrder(savedSecret, {
        telegram_user_id: manualOrderForm.telegram_user_id.trim(),
        full_name: manualOrderForm.full_name.trim(),
        plan_name: planName,
        plan_mode: manualOrderForm.plan_mode || undefined,
        entitlement_type: manualOrderForm.plan_mode === "CUSTOM_DURATION" ? manualOrderForm.entitlement_type : undefined,
        entitlement_key: manualOrderForm.plan_mode === "CUSTOM_DURATION" ? manualOrderForm.entitlement_key : undefined,
        note: manualOrderForm.note.trim(),
        amount: manualOrderForm.amount,
        duration_days: durationDays,
        expire_at: expireAt,
        coupon_code: manualOrderForm.coupon_code.trim(),
        sale_id: "MANUAL",
        payment_currency: paymentCurrency,
        payment_provider: paymentProvider,
        skip_join_link: true,
        skip_active_code: true,
      });
      setManualOrderResult(res.data);
      setManualOrderForm({ ...EMPTY_MANUAL_ORDER_FORM, plan_name: manualPlanNameFromKey("FULL_1M"), amount: manualPriceFromKey("FULL_1M") || "0" });
      await loadAll();
    });
  }

  async function generateManualActiveCodeHandler() {
    if (!manualOrderResult) return;
    await runAction("generate-active-code", async () => {
      const res = await generateManualActiveCode(savedSecret, {
        order_id: manualOrderResult.order_id,
        telegram_user_id: manualOrderResult.telegram_user_id,
        full_name: manualOrderResult.full_name,
        plan_name: manualOrderResult.plan_name,
        expire_at: manualOrderResult.expire_at,
        expire_at_iso: manualOrderResult.expire_at_iso,
      });
      
      setManualOrderResult(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          activation_code: res.data.activation_code,
          activation_url: res.data.activation_url,
          manual_order_message_url: res.data.manual_order_message_url,
          manual_order_text: res.data.manual_order_text,
        };
      });
      showNotice("ok", "Đã tạo link active code thành công.");
    });
  }

  async function generateManualJoinLinkHandler() {
    if (!manualOrderResult) return;
    await runAction("generate-join-link", async () => {
      const res = await generateManualJoinLink(savedSecret, {
        order_id: manualOrderResult.order_id,
        telegram_user_id: manualOrderResult.telegram_user_id,
        plan_name: manualOrderResult.plan_name,
        full_name: manualOrderResult.full_name,
        expire_at: manualOrderResult.expire_at,
      });
      
      setManualOrderResult(prev => {
        if (!prev) return prev;
        return {
          ...prev,
          links_text: res.data.links_text,
          support_text: res.data.support_text,
          support_link: res.data.support_link,
          support_error: res.data.support_error,
          manual_order_join_text: res.data.manual_order_join_text,
        };
      });
      showNotice("ok", "Đã tạo link tham gia nhóm thành công.");
    });
  }

  async function openCustomerQuickLookup() {
    setCustomerQuickLookupQuery(selectedCustomerId || "");
    setCustomerQuickLookupResults([]);
    setCustomerQuickLookupSearched(false);
    setCustomerQuickLookupOpen(true);
  }

  function lookupCustomerByTelegramId(rawId: string) {
    const telegramId = rawId.trim();
    if (!telegramId) return null;
    return customerSummaries.find((item) => item.id === telegramId) || customerQuickLookupResults.find((item) => item.id === telegramId) || null;
  }

  async function ensureCustomerDataset(customerId: string) {
    let customer = lookupCustomerByTelegramId(customerId);
    if (!customer) return;
    const lookupId = customer.id;
    if (!customerSummaries.some((item) => item.id === lookupId) && savedSecret) {
      await loadAll(savedSecret, { silent: true, resetPages: false, scope: "all" });
      customer = lookupCustomerByTelegramId(customerId);
    }
    return customer;
  }

  async function ensureHiddenGroupsDataset() {
    if (!savedSecret) return;
    if (hiddenGroups.length > 0) return;
    await loadAll(savedSecret, { silent: true, resetPages: false, scope: "specialGroups" });
  }

  async function openCustomerFromLookup(customerId: string) {
    const customer = await ensureCustomerDataset(customerId);
    if (!customer) return;
    await ensureHiddenGroupsDataset();
    setSelectedCustomerId(customer.id);
    setCustomerOrderTab("paid");
    setCustomerDetailTab("orders");
    setCustomerTimelineSubTab("all");
    setCustomerModalOpen(true);
  }

  async function openCustomerRenewFromLookup(customerId: string) {
    const customer = await ensureCustomerDataset(customerId);
    if (!customer) return;
    await ensureHiddenGroupsDataset();
    setSelectedCustomerId(customer.id);
    setCustomerOrderTab("paid");
    setCustomerDetailTab("orders");
    setCustomerTimelineSubTab("all");
    setCustomerModalOpen(true);
    requestAnimationFrame(() => {
      setCustomerRenewModalOpen(true);
    });
  }

  async function openQuickLookupPrimaryAction(customerId: string) {
    const customer = lookupCustomerByTelegramId(customerId);
    if (!customer) return;
    const lookupBlacklistEntry = "blacklistEntry" in customer ? customer.blacklistEntry : null;
    const blacklistEntry = lookupBlacklistEntry || blacklist.find((item) => item.telegram_user_id === customer.id && item.is_active) || null;
    if (blacklistEntry) {
      showNotice("error", `Khách ${customer.id} đang blacklist: ${blacklistEntry.reason || "không có lý do"}`);
      return;
    }
    if (customer.activeOrders.length > 0) {
      await openCustomerRenewFromLookup(customer.id);
      return;
    }
    openManualOrderFromLookup(customer.id);
  }

  function openManualOrderFromLookup(customerId: string) {
    const customer = lookupCustomerByTelegramId(customerId);
    const nextCustomerId = customer?.id || customerId.trim();
    if (!nextCustomerId) return;
    void ensureHiddenGroupsDataset();
    setManualOrderForm((current) => ({
      ...current,
      telegram_user_id: nextCustomerId,
      full_name: customer?.name && customer.name !== "-" ? customer.name : current.full_name,
      plan_name: customer?.paidOrders.length ? current.plan_name : manualPlanNameFromKey("FULL_1M"),
      special_group_id: "",
      special_group_duration: "1M",
      expiry_mode: "days",
      duration_days: "30",
      expire_at: "",
    }));
    setManualOrderModalOpen(true);
    setCustomerQuickLookupOpen(false);
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
              <Typography variant="h4" sx={{ fontWeight: 800 }}>Hang Cú VIP Admin</Typography>
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
              Hang Cú VIP
            </Typography>
            <Typography variant="body2" color="text.secondary" noWrap sx={{ display: { xs: "none", sm: "block" } }}>
              {ui("Dashboard vận hành: nhóm nhận link, đơn hàng, mã, sale và nội dung bot.", "Operations dashboard for groups, orders, codes, sales, and bot content.")}
            </Typography>
          </Box>
          <Box sx={{ minWidth: 0, display: "flex", alignItems: "center", gap: 1.25, flexWrap: "nowrap", justifyContent: "flex-end" }}>
            <Tooltip title="Inbox hỗ trợ" placement="bottom">
              <IconButton
                onClick={openSupportInboxMenu}
                aria-label="Inbox hỗ trợ"
                sx={{
                  width: 42,
                  height: 42,
                  border: unreadSupportInboxCount > 0 ? "1px solid rgba(14,165,233,0.30)" : "1px solid rgba(148,163,184,0.18)",
                  bgcolor: unreadSupportInboxCount > 0 ? "rgba(14,165,233,0.12)" : "rgba(15,23,42,0.03)",
                  color: unreadSupportInboxCount > 0 ? "info.main" : "text.secondary",
                  boxShadow: unreadSupportInboxCount > 0 ? "0 14px 30px rgba(14,165,233,0.24), 0 0 0 6px rgba(14,165,233,0.08)" : "inset 0 1px 0 rgba(255,255,255,0.76)",
                  animation: unreadSupportInboxCount > 0 ? "supportInboxPing 1.1s ease-in-out infinite" : "none",
                  transition: "transform 160ms ease, box-shadow 160ms ease, background-color 160ms ease, color 160ms ease",
                  "@keyframes supportInboxPing": {
                    "0%, 100%": { transform: "translateY(0px) scale(1)" },
                    "18%": { transform: "translateY(-2px) scale(1.08)" },
                    "42%": { transform: "translateY(0px) scale(0.98)" },
                    "68%": { transform: "translateY(-1px) scale(1.05)" },
                  },
                  "&:hover": {
                    bgcolor: unreadSupportInboxCount > 0 ? "rgba(14,165,233,0.16)" : "rgba(59,130,246,0.12)",
                    boxShadow: unreadSupportInboxCount > 0 ? "0 16px 34px rgba(14,165,233,0.28)" : "0 14px 28px rgba(59,130,246,0.16)",
                  },
                }}
              >
                <Badge
                  badgeContent={unreadSupportInboxCount}
                  color={unreadSupportInboxCount > 0 ? "info" : "primary"}
                  overlap="circular"
                  sx={{
                    "& .MuiBadge-badge": {
                      fontWeight: 800,
                      minWidth: unreadSupportInboxCount > 0 ? 20 : 18,
                      height: unreadSupportInboxCount > 0 ? 20 : 18,
                      px: 0.45,
                      bgcolor: unreadSupportInboxCount > 0 ? "#0ea5e9" : undefined,
                      color: "#fff",
                      animation: unreadSupportInboxCount > 0 ? "supportInboxBadgePop 0.8s ease-in-out infinite" : "none",
                      "@keyframes supportInboxBadgePop": {
                        "0%, 100%": { transform: "scale(1)" },
                        "20%": { transform: "scale(1.2)" },
                        "55%": { transform: "scale(0.96)" },
                        "80%": { transform: "scale(1.12)" },
                      },
                    },
                  }}
                >
                  <MessagesSquare size={18} />
                </Badge>
              </IconButton>
            </Tooltip>
            <Tooltip title="Thông báo" placement="bottom">
              <IconButton
                onClick={openNotificationMenu}
                aria-label="Thông báo"
                sx={{
                  width: 42,
                  height: 42,
                  border: unreadAdminNotificationCount > 0 ? "1px solid rgba(239,68,68,0.28)" : "1px solid rgba(148,163,184,0.18)",
                  bgcolor: unreadAdminNotificationCount > 0 ? "rgba(239,68,68,0.12)" : "rgba(15,23,42,0.03)",
                  color: unreadAdminNotificationCount > 0 ? "error.main" : "text.secondary",
                  boxShadow: unreadAdminNotificationCount > 0 ? "0 14px 30px rgba(239,68,68,0.22), 0 0 0 6px rgba(239,68,68,0.08)" : "inset 0 1px 0 rgba(255,255,255,0.76)",
                  animation: unreadAdminNotificationCount > 0 ? "notifHeaderBounce 0.95s ease-in-out infinite" : "none",
                  transition: "transform 160ms ease, box-shadow 160ms ease, background-color 160ms ease, color 160ms ease",
                  "@keyframes notifHeaderBounce": {
                    "0%, 100%": { transform: "translateY(0px) scale(1)" },
                    "20%": { transform: "translateY(-2px) scale(1.12)" },
                    "45%": { transform: "translateY(0px) scale(0.98)" },
                    "70%": { transform: "translateY(-1px) scale(1.08)" },
                  },
                  "&:hover": {
                    bgcolor: unreadAdminNotificationCount > 0 ? "rgba(239,68,68,0.16)" : "rgba(59,130,246,0.12)",
                    boxShadow: unreadAdminNotificationCount > 0 ? "0 16px 34px rgba(239,68,68,0.28)" : "0 14px 28px rgba(59,130,246,0.16)",
                  },
                }}
              >
                <Badge
                  badgeContent={unreadAdminNotificationCount}
                  color={unreadAdminNotificationCount > 0 ? "error" : "primary"}
                  overlap="circular"
                  sx={{
                    "& .MuiBadge-badge": {
                      fontWeight: 800,
                      minWidth: unreadAdminNotificationCount > 0 ? 20 : 18,
                      height: unreadAdminNotificationCount > 0 ? 20 : 18,
                      px: 0.45,
                      bgcolor: unreadAdminNotificationCount > 0 ? "#ef4444" : undefined,
                      color: "#fff",
                      animation: unreadAdminNotificationCount > 0 ? "notifBadgePop 0.75s ease-in-out infinite" : "none",
                      "@keyframes notifBadgePop": {
                        "0%, 100%": { transform: "scale(1)" },
                        "20%": { transform: "scale(1.22)" },
                        "55%": { transform: "scale(0.96)" },
                        "80%": { transform: "scale(1.14)" },
                      },
                    },
                  }}
                >
                  <BellRing size={18} />
                </Badge>
              </IconButton>
            </Tooltip>
            <Menu
              anchorEl={supportInboxMenuAnchorEl}
              open={Boolean(supportInboxMenuAnchorEl)}
              onClose={closeSupportInboxMenu}
              transformOrigin={{ horizontal: "right", vertical: "top" }}
              anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
              slotProps={{
                paper: {
                  sx: {
                    mt: 1,
                    width: { xs: "min(356px, calc(100vw - 24px))", sm: 400 },
                    maxWidth: "calc(100vw - 24px)",
                    borderRadius: 3,
                    boxShadow: "0 18px 48px rgba(15,23,42,0.16)",
                    overflow: "hidden",
                  },
                },
              }}
            >
              <Box sx={{ px: 1.25, py: 1.1, bgcolor: "rgba(14,165,233,0.06)", borderBottom: 1, borderColor: "divider", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}>
                <Box sx={{ minWidth: 0 }}>
                  <Typography sx={{ fontWeight: 800, lineHeight: 1.15, fontSize: 17 }}>Inbox hỗ trợ</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {unreadSupportInboxCount} mới · {supportInboxItems.length} tổng
                  </Typography>
                </Box>
                <Stack direction="row" spacing={0.25} sx={{ flexShrink: 0 }}>
                  <Tooltip title="Đánh dấu đã đọc">
                    <IconButton
                      size="small"
                      onClick={() => {
                        markAllSupportInboxRead();
                        closeSupportInboxMenu();
                      }}
                    >
                      <CheckCircle2 size={17} />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Làm mới">
                    <IconButton
                      size="small"
                      onClick={() => void refreshSupportInboxCases()}
                    >
                      <RefreshCw size={17} />
                    </IconButton>
                  </Tooltip>
                </Stack>
              </Box>
              <Box sx={{ maxHeight: 420, overflowY: "auto" }}>
                {supportInboxCasesLoading && !supportInboxItems.length ? (
                  <Box sx={{ px: 1.5, py: 2.5, textAlign: "center", color: "text.secondary" }}>
                    Đang tải inbox hỗ trợ...
                  </Box>
                ) : supportInboxItems.length ? supportInboxItems.map((item) => {
                  const unread = !supportInboxSeenIds.includes(item.unreadKey || item.id);
                  return (
                    <Box key={item.id} sx={{ borderBottom: 1, borderColor: "rgba(148,163,184,0.10)", bgcolor: unread ? "rgba(14,165,233,0.03)" : "background.paper" }}>
                      <MenuItem
                        onClick={() => openSupportInboxItem(item)}
                        sx={{
                          alignItems: "flex-start",
                          gap: 1,
                          py: 0.95,
                          px: 1.25,
                          minWidth: 0,
                        }}
                      >
                        <Box sx={{
                          width: 30,
                          height: 30,
                          borderRadius: "50%",
                          display: "grid",
                          placeItems: "center",
                          flexShrink: 0,
                          bgcolor: "rgba(14,165,233,0.14)",
                          color: "#0284c7",
                          mt: 0.1,
                          boxShadow: "0 0 0 1px rgba(14,165,233,0.10) inset",
                        }}>
                          <MessageSquare size={15} />
                        </Box>
                        <Box sx={{ minWidth: 0, flex: 1 }}>
                          <Typography sx={{ fontWeight: unread ? 900 : 700, lineHeight: 1.15, fontSize: 14.5, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {item.title}
                            {unread ? <Box component="span" sx={{ ml: 0.75, display: "inline-block", width: 8, height: 8, borderRadius: "50%", bgcolor: "info.main", boxShadow: "0 0 0 5px rgba(14,165,233,0.10)" }} /> : null}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.35, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            ID: {item.telegram_user_id || "-"}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.1, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {item.detail || "Tin nhắn riêng"} · {dateText(item.created_at)}
                          </Typography>
                        </Box>
                        <Button
                          variant="text"
                          size="small"
                          onClick={(event) => {
                            event.preventDefault();
                            event.stopPropagation();
                            openSupportInboxItem(item);
                          }}
                          sx={{ flexShrink: 0, mt: 0.05 }}
                        >
                          Trả lời
                        </Button>
                      </MenuItem>
                    </Box>
                  );
                }) : (
                  <Box sx={{ px: 1.5, py: 2.5, textAlign: "center", color: "text.secondary" }}>
                    Chưa có tin nhắn hỗ trợ mới.
                  </Box>
                )}
              </Box>
            </Menu>
            <Menu
              anchorEl={notificationMenuAnchorEl}
              open={Boolean(notificationMenuAnchorEl)}
              onClose={closeNotificationMenu}
              transformOrigin={{ horizontal: "right", vertical: "top" }}
              anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
              slotProps={{
                paper: {
                  sx: {
                    mt: 1,
                    width: { xs: "min(356px, calc(100vw - 24px))", sm: 400 },
                    maxWidth: "calc(100vw - 24px)",
                    borderRadius: 3,
                    boxShadow: "0 18px 48px rgba(15,23,42,0.16)",
                    overflow: "hidden",
                  },
                },
              }}
            >
              <Box sx={{ px: 1.25, py: 1.1, bgcolor: "rgba(59,130,246,0.06)", borderBottom: 1, borderColor: "divider", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}>
                <Box sx={{ minWidth: 0 }}>
                  <Typography sx={{ fontWeight: 800, lineHeight: 1.15, fontSize: 17 }}>Thông báo</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {unreadAdminNotificationCount} mới · {visibleAdminNotifications.length} tổng
                  </Typography>
                </Box>
                <Stack direction="row" spacing={0.25} sx={{ flexShrink: 0 }}>
                  <Tooltip title="Đánh dấu đã đọc">
                    <IconButton
                      size="small"
                      onClick={() => {
                        markAllNotificationsRead();
                        closeNotificationMenu();
                      }}
                    >
                      <CheckCircle2 size={17} />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Làm mới">
                    <IconButton
                      size="small"
                      onClick={() => {
                        void loadAdminNotifications(savedSecret, { silent: true });
                      }}
                    >
                      <RefreshCw size={17} />
                    </IconButton>
                  </Tooltip>
                </Stack>
              </Box>
              <Box sx={{ maxHeight: 420, overflowY: "auto" }}>
                {visibleAdminNotifications.length ? visibleAdminNotifications.map((item) => {
                  const unread = !notificationSeenIds.includes(item.id);
                  const expanded = notificationExpandedIds.includes(item.id);
                  const chips = notificationChipText(item);
                  return (
                    <Box key={item.id} sx={{ borderBottom: 1, borderColor: "rgba(148,163,184,0.10)", bgcolor: unread ? "rgba(239,68,68,0.03)" : "background.paper" }}>
                      <MenuItem
                        onClick={() => openNotificationItem(item)}
                        sx={{
                          alignItems: "flex-start",
                          gap: 1,
                          py: 0.95,
                          px: 1.25,
                          minWidth: 0,
                        }}
                      >
                        <Box sx={{
                          width: 30,
                          height: 30,
                          borderRadius: "50%",
                          display: "grid",
                          placeItems: "center",
                          flexShrink: 0,
                          bgcolor: item.kind === "order" ? "rgba(37,99,235,0.14)" : "rgba(16,185,129,0.14)",
                          color: item.kind === "order" ? "#2563eb" : "#059669",
                          mt: 0.1,
                          boxShadow: item.kind === "order" ? "0 0 0 1px rgba(37,99,235,0.10) inset" : "0 0 0 1px rgba(16,185,129,0.10) inset",
                        }}>
                          {item.kind === "order" ? <ClipboardList size={15} /> : <MessageSquare size={15} />}
                        </Box>
                        <Box sx={{ minWidth: 0, flex: 1 }}>
                          <Typography sx={{ fontWeight: unread ? 900 : 700, lineHeight: 1.15, fontSize: 14.5, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {item.title}
                            {unread ? <Box component="span" sx={{ ml: 0.75, display: "inline-block", width: 8, height: 8, borderRadius: "50%", bgcolor: "error.main", boxShadow: "0 0 0 5px rgba(239,68,68,0.10)" }} /> : null}
                          </Typography>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{
                              mt: 0.25,
                              lineHeight: 1.25,
                              display: "-webkit-box",
                              WebkitLineClamp: 2,
                              WebkitBoxOrient: "vertical",
                              overflow: "hidden",
                              wordBreak: "break-word",
                            }}
                          >
                            {item.detail || "-"}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.25, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                            {dateText(item.created_at)}
                            {item.plan_name ? ` · ${resolveOrderLabel({ plan_name: item.plan_name }).displayLabel}` : ""}
                          </Typography>
                        </Box>
                        <IconButton
                          size="small"
                          onClick={(event) => {
                            event.stopPropagation();
                            toggleNotificationExpanded(item.id);
                          }}
                          sx={{ mt: -0.2 }}
                        >
                          <ChevronRight size={16} style={{ transform: expanded ? "rotate(90deg)" : "rotate(0deg)", transition: "transform 160ms ease" }} />
                        </IconButton>
                      </MenuItem>
                      {expanded ? (
                        <Box sx={{ px: 1.25, pb: 1.1, pl: 5.25, pr: 1.25 }}>
                          {chips.length ? (
                            <Stack direction="row" spacing={0.5} useFlexGap sx={{ mb: 0.75, flexWrap: "wrap", maxWidth: "100%" }}>
                              {chips.map((chip) => (
                                <Chip key={`${item.id}-${chip}`} size="small" label={chip} variant="outlined" sx={{ height: 22, fontSize: 10.8, fontWeight: 700, maxWidth: "100%" }} />
                              ))}
                            </Stack>
                          ) : null}
                          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mb: 0.75, wordBreak: "break-word", lineHeight: 1.25 }}>
                            {item.telegram_user_id ? `Telegram ID: ${item.telegram_user_id}` : "Chưa có Telegram ID"}
                            {item.order_id ? ` · Order: ${item.order_id}` : ""}
                          </Typography>
                          <Stack direction="row" spacing={0.5} sx={{ flexWrap: "wrap", maxWidth: "100%" }}>
                            <Button
                              size="small"
                              variant="contained"
                              onClick={(event) => {
                                event.stopPropagation();
                                openNotificationItem(item);
                              }}
                              sx={{ borderRadius: 999, textTransform: "none", whiteSpace: "nowrap", py: 0.35, px: 1.15, minHeight: 30 }}
                            >
                              {item.kind === "order" ? "Xem đơn" : "Mở hỗ trợ"}
                            </Button>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={async (event) => {
                                event.stopPropagation();
                                const text = item.kind === "order" ? item.order_id || item.telegram_user_id : item.telegram_user_id || item.order_id;
                                if (!text) return;
                                await navigator.clipboard.writeText(text);
                                showNotice("ok", `Đã copy ${text}.`);
                              }}
                              sx={{ borderRadius: 999, textTransform: "none", whiteSpace: "nowrap", py: 0.35, px: 1.15, minHeight: 30 }}
                            >
                              {item.kind === "order" ? "Copy order ID" : "Copy Telegram ID"}
                            </Button>
                            {item.kind === "message" ? (
                              <Button
                                size="small"
                                variant="outlined"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  openAdminReply({
                                    id: item.id,
                                    userId: item.telegram_user_id,
                                    fullName: item.full_name || item.telegram_user_id,
                                    username: "",
                                    title: item.title,
                                    detail: item.detail,
                                  });
                                }}
                                sx={{ borderRadius: 999, textTransform: "none", whiteSpace: "nowrap", py: 0.35, px: 1.15, minHeight: 30 }}
                              >
                                Trả lời ngay
                              </Button>
                            ) : null}
                          </Stack>
                        </Box>
                      ) : null}
                    </Box>
                  );
                }) : (
                  <Box sx={{ p: 1.5 }}>
                    <Alert severity="info" variant="outlined">Chưa có thông báo phù hợp.</Alert>
                  </Box>
                )}
              </Box>
            </Menu>
            <Button variant="outlined" onClick={() => void openCustomerQuickLookup()} size="small" startIcon={<Search size={16} />}>
              Tra cứu khách
            </Button>
            <Button
              variant="contained"
              size="small"
              onClick={() => {
                setManualOrderResult(null);
                setManualOrderForm({
                  ...EMPTY_MANUAL_ORDER_FORM,
                  plan_key: "FULL_1M",
                  plan_name: manualPlanNameFromKey("FULL_1M"),
                  amount: manualPriceFromKey("FULL_1M") || "0",
                  expiry_mode: "days",
                  duration_days: "30",
                  expire_at: "",
                });
                setManualOrderModalOpen(true);
              }}
              startIcon={<Plus size={16} />}
            >
              Tạo đơn
            </Button>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1, whiteSpace: "nowrap", px: 1.15, py: 0.7, borderRadius: 999, border: "1px solid rgba(148, 163, 184, 0.16)", bgcolor: "rgba(15,23,42,0.03)", boxShadow: "inset 0 1px 0 rgba(255,255,255,0.76)" }}>
              <Box sx={{ width: 8, height: 8, borderRadius: "50%", bgcolor: webhookMeta?.maintenance_override?.active ? "#ef4444" : webhook?.url ? "#22c55e" : "#ef4444", boxShadow: webhookMeta?.maintenance_override?.active ? "0 0 0 5px rgba(239,68,68,0.12)" : webhook?.url ? "0 0 0 5px rgba(34,197,94,0.12)" : "0 0 0 5px rgba(239,68,68,0.12)" }} />
              <Typography variant="caption" sx={{ color: "text.secondary", fontWeight: 700, lineHeight: 1 }}>
                {webhookMeta?.maintenance_override?.active ? ui("Bảo trì do webhook", "Maintenance by webhook") : webhook?.url ? ui("Webhook đang bật", "Webhook active") : ui("Webhook cần kiểm tra", "Check webhook")}
              </Typography>
            </Box>
            <Button
              variant="outlined"
              onClick={() => {
                if (tab === "activityLog") {
                  void loadActivityLogPage(savedSecret, { page: logPage });
                  return;
                }
                loadAll();
              }}
              disabled={loading || activityLogLoading}
              startIcon={loading || activityLogLoading ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}
            >
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
            borderColor: "rgba(255,255,255,0.06)",
            bgcolor: "rgba(15, 23, 42, 0.95)",
            backdropFilter: "blur(16px)",
            color: "#f9fafb",
            top: "68px",
            height: "calc(100vh - 68px)",
          },
        }}
      >
        <Box sx={{ px: 1.5, pt: 0.75, pb: 2, display: "flex", flexDirection: "column", minHeight: 0 }}>
        <Box sx={{ mt: 1, pr: 0.5, display: "grid", gap: 1.25, overflow: "visible" }}>
          <Box>
            <Typography variant="overline" sx={{ px: 1, color: "rgba(255,255,255,0.55)", fontWeight: 800, letterSpacing: 1.2 }}>
              Vận hành
            </Typography>
            <Tabs
              orientation="vertical"
              value={tab}
              onChange={(_, next) => selectTab(next)}
              variant="scrollable"
              scrollButtons={false}
              textColor="inherit"
              sx={sidebarTabSx}
            >
              <Tab value="overview" icon={<Activity size={16} />} iconPosition="start" label={<Box sx={sidebarTabLabelSx}><span>{ui("Tổng quan", "Overview")}</span><Chip size="small" label={String(summaryCounts.orders)} sx={sidebarTabChipSx} variant="outlined" /></Box>} />
              <Tab value="analytics" icon={<BarChart3 size={16} />} iconPosition="start" label={ui("Thống kê", "Analytics")} />
              <Tab value="setup" icon={<ShieldCheck size={16} />} iconPosition="start" label={ui("Nhóm & giá", "Groups & pricing")} />
              <Tab value="orders" icon={<ShoppingCart size={16} />} iconPosition="start" label={<Box sx={sidebarTabLabelSx}><span>{ui("Đơn hàng", "Orders")}</span><Chip size="small" label={String(summaryCounts.ordersPending)} sx={sidebarTabChipSx} variant="outlined" /></Box>} />
              <Tab value="customers" icon={<Users size={16} />} iconPosition="start" label={<Box sx={sidebarTabLabelSx}><span>{ui("Khách hàng", "Customers")}</span><Chip size="small" label={String(customerSummaries.length || summaryCounts.orders)} sx={sidebarTabChipSx} variant="outlined" /></Box>} />
              <Tab value="activityLog" icon={<ClipboardList size={16} />} iconPosition="start" label={ui("Nhật ký", "Activity log")} />
              <Tab value="campaigns" icon={<Megaphone size={16} />} iconPosition="start" label={<Box sx={sidebarTabLabelSx}><span>Campaign</span><Chip size="small" label={String(summaryCounts.campaigns)} sx={sidebarTabChipSx} variant="outlined" /></Box>} />
              <Tab value="channelPosts" icon={<Send size={16} />} iconPosition="start" label={<Box sx={sidebarTabLabelSx}><span>Đăng channel</span><Chip size="small" label={String(summaryCounts.channelPosts)} sx={sidebarTabChipSx} variant="outlined" /></Box>} />
              <Tab value="renewals" icon={<RefreshCw size={16} />} iconPosition="start" label={ui("Gia hạn", "Renewals")} />
            </Tabs>
          </Box>
          <Box>
            <Typography variant="overline" sx={{ px: 1, color: "rgba(255,255,255,0.55)", fontWeight: 800, letterSpacing: 1.2 }}>
              Cấu hình
            </Typography>
            <Tabs
              orientation="vertical"
              value={tab}
              onChange={(_, next) => selectTab(next)}
              variant="scrollable"
              scrollButtons={false}
              textColor="inherit"
              sx={sidebarTabSx}
            >
              <Tab value="supportGroup" icon={<ShieldCheck size={16} />} iconPosition="start" label={ui("Khu vực hỗ trợ", "Support area")} />
              <Tab value="content" icon={<Settings size={16} />} iconPosition="start" label={ui("Cấu hình bot", "Bot config")} />
              <Tab value="autoPayment" icon={<CalendarClock size={16} />} iconPosition="start" label="Auto payment" />
              <Tab value="botVi" icon={<FileText size={16} />} iconPosition="start" label="UI Bot tiếng Việt" />
              <Tab value="botEn" icon={<FileText size={16} />} iconPosition="start" label="UI Bot tiếng Anh" />
              <Tab value="botTools" icon={<ClipboardList size={16} />} iconPosition="start" label="Phản hồi & cảnh báo" />
              <Tab value="specialGroups" icon={<Ticket size={16} />} iconPosition="start" label={<Box sx={sidebarTabLabelSx}><span>Special Group</span><Chip size="small" label={String(summaryCounts.hiddenGroups)} sx={sidebarTabChipSx} variant="outlined" /></Box>} />
              <Tab value="menuBot" icon={<FileText size={16} />} iconPosition="start" label="Menu Bot" />
              <Tab value="coupons" icon={<Ticket size={16} />} iconPosition="start" label={<Box sx={sidebarTabLabelSx}><span>Coupon</span><Chip size="small" label={String(summaryCounts.coupons)} sx={sidebarTabChipSx} variant="outlined" /></Box>} />
              <Tab value="activationCodes" icon={<Ticket size={16} />} iconPosition="start" label={<Box sx={sidebarTabLabelSx}><span>Activation code</span><Chip size="small" label={String(summaryCounts.activationCodes)} sx={sidebarTabChipSx} variant="outlined" /></Box>} />
              <Tab value="security" icon={<ShieldCheck size={16} />} iconPosition="start" label={ui("Bảo mật", "Security")} />
              <Tab value="vipAudit" icon={<Users size={16} />} iconPosition="start" label={<Box sx={sidebarTabLabelSx}><span>VIP audit</span><Chip size="small" label={String(summaryCounts.blacklist)} sx={sidebarTabChipSx} variant="outlined" /></Box>} />
              <Tab value="sales" icon={<BadgePercent size={16} />} iconPosition="start" label="Sale" />
              <Tab value="system" icon={<Settings size={16} />} iconPosition="start" label={ui("Hệ thống", "System")} />
              <Tab value="license" icon={<ShieldCheck size={16} />} iconPosition="start" label={ui("License", "License")} />
            </Tabs>
          </Box>
        </Box>
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
              zIndex: (theme) => theme.zIndex.modal + 1000,
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
          <Stack spacing={3}>
            {/* VITAL SIGNS (Top Bar) */}
            <Card variant="outlined" sx={{ ...sectionCardSx, p: 2.5, display: "flex", flexWrap: "wrap", gap: 3, alignItems: "center", justifyContent: "space-between" }}>
              <Box sx={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
                <HealthItem ok={Boolean(webhook?.url) && !webhookMeta?.maintenance_override?.active && !webhookMeta?.problem_reason} title="Webhook" detail={webhookMeta?.maintenance_override?.active ? "Đang bảo trì" : webhookMeta?.problem_reason ? "Lỗi kết nối" : "Hoạt động tốt"} />
                <HealthItem ok={botScheduleStatus?.active ?? true} title="Bot Runtime" detail={botScheduleStatus?.title || "Hoạt động tốt"} />
                <HealthItem ok={metrics.pending === 0} title="Đơn đang chờ" detail={`${metrics.pending} đơn chờ duyệt`} />
                <HealthItem ok={expiringSoon.length === 0} title="Sắp hết hạn" detail={`${expiringSoon.length} khách chờ gia hạn`} />
              </Box>
              <Stack direction="row" spacing={1.5}>
                <Button variant="outlined" onClick={() => selectTab("analytics")}>Xem thống kê</Button>
                <Button variant="contained" onClick={() => loadAll(savedSecret, { silent: false, resetPages: false, scope: "overview" })} startIcon={<RefreshCw size={16} />}>Tải lại dữ liệu</Button>
              </Stack>
            </Card>

            <Box sx={{ display: "grid", gap: 4, gridTemplateColumns: { xs: "1fr", lg: "6.5fr 3.5fr" }, alignItems: "start" }}>
              {/* LEFT: NOTIFICATION FEED */}
              <Stack spacing={2.5}>
                <Typography variant="h6" sx={{ fontWeight: 800, color: "var(--ink)", display: "flex", alignItems: "center", gap: 1 }}>
                  <Activity size={20} className="text-primary" />
                  Trung tâm thông báo
                </Typography>
                <Stack spacing={2}>
                  {actionableFeed.length ? actionableFeed.map((item, idx) => {
                    const isNew = Date.now() - (safeDateMillis(item.time) ?? 0) < 24 * 60 * 60 * 1000;
                    
                    // Determine elegant icon styling
                    let iconBg = "rgba(16, 185, 129, 0.1)";
                    let iconColor = "#10b981";
                    if (item.tone === "critical") {
                      iconBg = "rgba(239, 68, 68, 0.1)";
                      iconColor = "#ef4444";
                    } else if (item.tone === "warning") {
                      iconBg = "rgba(245, 158, 11, 0.1)";
                      iconColor = "#f59e0b";
                    }

                    const handleFeedClick = () => {
                      if (item.type === "order") {
                        setQuery(item.id.replace("order-", "").replace("paid-", ""));
                        selectTab("orders");
                      } else if (item.type === "customer") {
                        setQuery(item.id.replace("exp-", ""));
                        selectTab("customers");
                      } else if (item.type === "alert") {
                        selectTab("setup");
                      }
                    };

                    return (
                      <Box key={`${item.id}-${idx}`} className={`feed-item ${isNew ? "unread" : ""}`} sx={{ animationDelay: `${idx * 0.05}s`, cursor: "pointer" }} onClick={handleFeedClick}>
                        {isNew && <div className={`feed-dot tone-${item.tone}`} />}
                        <div className="feed-icon" style={{ background: iconBg, color: iconColor }}>
                          {item.type === "alert" ? <ShieldCheck size={20} /> : item.type === "order" ? <ClipboardList size={20} /> : <Users size={20} />}
                        </div>
                        <div className="feed-content">
                          <div className="feed-title">{item.title}</div>
                          <div className="feed-time">{item.detail} • <span style={{ opacity: 0.7 }}>{dateText(item.time)}</span></div>
                        </div>
                        <div className="feed-action" style={{ display: "flex", alignItems: "center", opacity: 0.6 }}>
                          <ChevronRight size={20} />
                        </div>
                      </Box>
                    );
                  }) : (
                    <div className="overview-empty">Tuyệt vời! Không có thông báo hay công việc nào đang chờ xử lý.</div>
                  )}
                </Stack>
              </Stack>

              {/* RIGHT: LIVE ACTIVITY STREAM */}
              <Stack spacing={2.5}>
                <Typography variant="h6" sx={{ fontWeight: 800, color: "var(--ink)", display: "flex", alignItems: "center", gap: 1 }}>
                  <History size={20} className="text-primary" />
                  Live Activity
                </Typography>
                <Card variant="outlined" sx={{ ...sectionCardSx, p: 3 }}>
                  {activityStream.length ? (
                    <div className="timeline-container">
                      {activityStream.map((item, idx) => (
                        <div key={`${item.id}-${idx}`} className="timeline-item" style={{ animationDelay: `${idx * 0.05 + 0.2}s` }}>
                          <div className="timeline-node" />
                          <div className="feed-title" style={{ fontSize: "14px" }}>{item.title}</div>
                          <div className="feed-time" style={{ fontSize: "13px", marginBottom: "4px", color: "var(--ink)" }}>{item.detail}</div>
                          <div className="muted" style={{ fontSize: "12px", opacity: 0.7 }}>{dateText(item.time)}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="overview-empty overview-empty-compact">Chưa có hoạt động nào của user/bot gần đây.</div>
                  )}
                </Card>
              </Stack>
            </Box>
          </Stack>
        ) : null}

        {tab === "analytics" ? (
          <AnalyticsSection
            orders={orders}
            yearStats={yearStats}
            monthStats={monthStats}
            paidRevenueByCurrency={paidRevenueByCurrency}
            paidRevenueByProvider={paidRevenueByProvider}
            marketingStats={marketingStats}
            marketingRange={marketingRange}
            setMarketingRange={setMarketingRange}
            refreshMarketingStats={refreshMarketingStatsDebounced}
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
                title="Bảng giá Combo"
                subtitle="Bấm trực tiếp vào từng card để sửa đúng gói đó trong popup."
              />
              <div className="pricing-grid">
                <Box
                  sx={{
                    gridColumn: "1 / -1",
                    display: "grid",
                    gap: 1.5,
                    gridTemplateColumns: { xs: "1fr", lg: "repeat(2, minmax(0, 1fr))" },
                  }}
                >
                  {[
                    {
                      variant: "30d" as const,
                      title: getConfigValue(config, "PLAN_COMBO_30D", "Combo 30 Ngày"),
                      aliases: String(getConfigValue(config, "PLAN_COMBO_30D_ALIASES", "All Access 30 Ngày, SVIP 30 Ngày, FULL 30D"))
                        .split(/[\n,;|]+/)
                        .map((item) => item.trim())
                        .filter(Boolean),
                      priceVnd: formatDisplayCurrency(Number(getConfigValue(config, "PRICE_COMBO_30D", "0") || 0), "VND"),
                      priceUsd: formatDisplayCurrency(Number(getConfigValue(config, "PRICE_COMBO_30D_USD", "0") || 0), "USD"),
                      accent: "#10b981",
                      softBg: "linear-gradient(135deg, rgba(16,185,129,0.10), rgba(255,255,255,0.92))",
                    },
                    {
                      variant: "life" as const,
                      title: getConfigValue(config, "PLAN_COMBO_LIFE", "Combo Trọn Đời"),
                      aliases: String(getConfigValue(config, "PLAN_COMBO_LIFE_ALIASES", "All Access Trọn Đời, SVIP Trọn Đời, FULL LIFE"))
                        .split(/[\n,;|]+/)
                        .map((item) => item.trim())
                        .filter(Boolean),
                      priceVnd: formatDisplayCurrency(Number(getConfigValue(config, "PRICE_COMBO_LIFE", "0") || 0), "VND"),
                      priceUsd: formatDisplayCurrency(Number(getConfigValue(config, "PRICE_COMBO_LIFE_USD", "0") || 0), "USD"),
                      accent: "#2563eb",
                      softBg: "linear-gradient(135deg, rgba(37,99,235,0.10), rgba(255,255,255,0.92))",
                    },
                  ].map((item) => (
                    <Card
                      key={item.title}
                      variant="outlined"
                      onClick={() => { setComboSettingsVariant(item.variant); setComboSettingsTab("name"); setComboSettingsOpen(true); }}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          setComboSettingsVariant(item.variant);
                          setComboSettingsTab("name");
                          setComboSettingsOpen(true);
                        }
                      }}
                      sx={{
                        borderRadius: 3,
                        overflow: "hidden",
                        borderColor: "rgba(37,99,235,0.12)",
                        background: item.softBg,
                        boxShadow: "0 10px 28px rgba(15, 23, 42, 0.05)",
                        cursor: "pointer",
                        transition: "transform 140ms ease, box-shadow 140ms ease, border-color 140ms ease",
                        "&:hover": {
                          transform: "translateY(-1px)",
                          boxShadow: "0 14px 34px rgba(15, 23, 42, 0.08)",
                          borderColor: "rgba(37,99,235,0.20)",
                        },
                      }}
                    >
                      <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                        <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 1.5 }}>
                          <Box sx={{ display: "flex", gap: 1.25, minWidth: 0, flex: 1 }}>
                            <Box sx={{ width: 40, height: 40, borderRadius: "50%", display: "grid", placeItems: "center", flex: "0 0 auto", bgcolor: `${item.accent}18`, color: item.accent }}>
                              <ShieldCheck size={20} />
                            </Box>
                            <Box sx={{ minWidth: 0 }}>
                              <Typography sx={{ fontSize: 16.5, fontWeight: 900, lineHeight: 1.15 }}>
                                {item.title}
                              </Typography>
                              <Typography variant="body2" color="text.secondary" sx={{ mt: 0.45, lineHeight: 1.4, maxWidth: 440 }}>
                                1 hub duy nhất: tên hiển thị, alias, giá VNĐ/USD và cổng thanh toán đều chỉnh từ đây.
                              </Typography>
                            </Box>
                          </Box>
                          <Typography sx={{ fontSize: 24, fontWeight: 900, lineHeight: 1, whiteSpace: "nowrap", color: "text.primary", pt: 0.1 }}>
                            {item.priceVnd}
                          </Typography>
                        </Box>

                        <Box sx={{ display: "flex", gap: 0.75, flexWrap: "wrap", mt: 1.25 }}>
                          <Chip size="small" label={`VNĐ ${item.priceVnd}`} variant="outlined" sx={{ bgcolor: "rgba(255,255,255,0.84)", fontWeight: 700 }} />
                          <Chip size="small" label={`USD ${item.priceUsd}`} variant="outlined" sx={{ bgcolor: "rgba(255,255,255,0.84)", fontWeight: 700 }} />
                          {item.aliases.slice(0, 2).map((alias) => (
                            <Chip key={`${item.title}-${alias}`} size="small" label={alias} variant="outlined" sx={{ bgcolor: "rgba(255,255,255,0.84)", maxWidth: "100%", "& .MuiChip-label": { maxWidth: 180, overflow: "hidden", textOverflow: "ellipsis" } }} />
                          ))}
                          {item.aliases.length > 2 ? <Chip size="small" label={`+${item.aliases.length - 2}`} variant="outlined" sx={{ bgcolor: "rgba(255,255,255,0.84)", fontWeight: 700 }} /> : null}
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
                <Box sx={{ gridColumn: "1 / -1", display: "flex", justifyContent: "flex-end", gap: 1, flexWrap: "wrap", pt: 0.25 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ alignSelf: "center" }}>
                    Bấm card để sửa
                  </Typography>
                </Box>
              </div>
            </section>
            <section className="panel">
              <PanelHead
                title="Collection & bảng giá"
                subtitle="Bấm một nhóm để sửa trong popup. Không còn form dài nằm sẵn trên trang."
                action={<Button variant="contained" size="small" onClick={openNewGroupModal} startIcon={<Plus size={16} />}>Thêm nhóm mới</Button>}
              />
              <div className="hint">
                Giá chỉ chỉnh tại màn hình này. UI Bot chỉ quản lý nội dung hiển thị, không còn trường giá trùng lặp.
              </div>
              <div className="bento-grid">
                {visibleGroups.length ? visibleGroups.map((item) => {
                  const name = getConfigValue(config, `BTN_G${item}`);
                  const id = getConfigValue(config, `ID_G${item}`);
                  const aliases = String(getConfigValue(config, `BTN_G${item}_ALIASES`, "") || "").split(/[\n,;|]+/).map((value) => value.trim()).filter(Boolean);
                  const isOk = name && id;
                  return (
                    <button className="bento-card" key={item} onClick={() => openEditGroupModal(String(item))}>
                      <div className="bento-top">

                        <div className="bento-status">
                          {isOk ? <CheckCircle2 size={14} className="icon-success" /> : <XCircle size={14} className="icon-error" />}
                          <span className={isOk ? "text-success" : "text-error"}>{isOk ? "Active" : "Cần thiết lập"}</span>
                        </div>
                        <h4 className="bento-title">{name || "Chưa đặt tên nhóm"}</h4>
                        <div className="bento-id"><Users size={14} /> ID: {id || "---"}</div>
                        <div className="bento-id" style={{ whiteSpace: "normal", lineHeight: 1.4 }}>
                          <ClipboardList size={14} />
                          Alias: {aliases.length ? aliases.join(" • ") : "—"}
                        </div>
                        
                        <div className="bento-action" onClick={(event) => { event.stopPropagation(); openEditGroupModal(String(item)); setTimeout(() => groupAliasRef.current?.focus(), 50); }}>
                          <Settings size={16} /> Cấu hình / Thêm alias
                        </div>
                      </div>
                      
                      <div className="bento-bottom">
                        <div className="bento-price-row">
                          <span className="price-label">Gói 30 ngày</span>
                          <span className="price-value">{formatDisplayCurrency(Number(getConfigValue(config, `PRICE_G${item}_1M`, "0") || 0), "VND")}</span>
                        </div>
                        <div className="bento-price-row">
                          <span className="price-label">Gói Trọn đời</span>
                          <span className="price-value">{formatDisplayCurrency(Number(getConfigValue(config, `PRICE_G${item}_LIFE`, "0") || 0), "VND")}</span>
                        </div>
                      </div>
                    </button>
                  );
                }) : <div className="empty-card">Chưa có nhóm nào. Bấm <strong>Thêm nhóm mới</strong>, nhập tên nhóm và Telegram group ID rồi lưu.</div>}
              </div>
            </section>
          </div>
        ) : null}

        {tab === "orders" ? (
          <OrdersSection
            orders={orders}
            filteredOrders={filteredOrders}
            filteredOrdersBase={filteredOrdersBase}
            exportOrdersCsv={exportOrdersCsv}
            query={query}
            setQuery={setQuery}
            orderTab={orderTab}
            setOrderTab={setOrderTab}
            orderPeriod={orderPeriod}
            setOrderPeriod={setOrderPeriod}
            pagedOrders={pagedOrders}
            changeOrderStatus={changeOrderStatus}
            removeOrder={removeOrder}
            openOrderEditor={openOrderEditor}
            saving={saving}
            orderPage={orderPage}
            totalOrderPages={totalOrderPages}
            setOrderPage={setOrderPage}
            ordersMoney={ordersMoney}
            isWithinPeriod={isWithinPeriod}
            openOrderSettings={() => setOrderSettingsOpen(true)}
            openManualOrder={() => { setManualOrderResult(null); setManualOrderModalOpen(true); }}
          />
        ) : null}

        {tab === "customers" ? (
          <CustomersSection
            filteredCustomers={filteredCustomers}
            customerSummaries={customerSummaries}
            blacklist={blacklist}
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
              <Metric label="Event gần đây" value={activityLogTotal === 3000 ? "3000+" : String(activityLogTotal)} accent="blue" icon={<Activity size={16} />} />
              <Metric label="User → Bot" value={String(activityLogSummary.user)} accent="cyan" icon={<Users size={16} />} />
              <Metric label="Bot → User" value={String(activityLogSummary.bot)} accent="emerald" icon={<Send size={16} />} />
              <Metric label="Hôm nay" value={String(activityLogSummary.today)} accent="amber" icon={<CalendarClock size={16} />} />
            </div>
            <section className="panel">
              <PanelHead title="Nhật ký tương tác" subtitle="Tải theo trang từ backend, không còn phụ thuộc vào mớ event đã nạp sẵn." />
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
                  <Box key={`detail-${item.id}`}>{renderLogDetailCell(item)}</Box>,
                ])}
                actions={(idx) => {
                  const item = pagedLogEntries[idx];
                  if (!item || item.direction !== "user" || !item.userId) return null;
                  return (
                    <Button variant="text" size="small" onClick={() => openAdminReply(item)} startIcon={<Send size={14} />}>
                      Trả lời
                    </Button>
                  );
                }}
              />
              <Pagination page={logPage} totalPages={totalLogPages} totalItems={activityLogTotal} onPage={setLogPage} label="event" />
              {activityLogLoading ? <div className="hint compact">Đang tải trang nhật ký...</div> : null}
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
	              {[
	                { key: "soon" as RenewalSubTab, label: "Sắp hết hạn", value: String(expiringSoon.length), accent: "amber" as const, note: "5 ngày tới" },
	                { key: "reminded" as RenewalSubTab, label: "Đã thông báo", value: String(renewalNoticeEvents.length), accent: "cyan" as const, note: "Nhắc / báo hết hạn" },
	                { key: "expired" as RenewalSubTab, label: "Đã hết hạn", value: String(expiredRenewalOrders.length), accent: "rose" as const, note: "Theo trạng thái kick" },
                { key: "lifetime" as RenewalSubTab, label: "Trọn đời", value: String(lifetimeRenewalOrders.length), accent: "indigo" as const, note: "Không cần nhắc/kick" },
	              ].map((item) => (
                <ButtonBase
                  key={item.key}
                  onClick={() => { setRenewalTab(item.key); setRenewalPage(1); }}
                  sx={{ display: "block", textAlign: "inherit", borderRadius: 4 }}
                >
                  <Metric label={item.label} value={item.value} accent={item.accent} note={item.note} icon={<Activity size={16} />} />
                </ButtonBase>
              ))}
            </div>
            <section className="panel">
	              <PanelHead
	                title="Quản lý gia hạn"
	                subtitle="Gọn lại theo 4 khối. Dòng nào cần xử lý thì bấm đúng nút ngay trên dòng đó."
	                action={
	                  <div className="panel-actions">
                    <Button variant="outlined" size="small" onClick={() => refreshKickAudit(renewalLiveCheck)} disabled={saving === "kick-audit-live"} startIcon={saving === "kick-audit-live" ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}>
	                      {renewalLiveCheck ? "Kiểm tra live" : "Kiểm tra log"}
                    </Button>
                    <Button variant="outlined" size="small" onClick={() => setRenewalLiveCheck((current) => !current)} startIcon={<ShieldCheck size={16} />}>
                      Live check: {renewalLiveCheck ? "Bật" : "Tắt"}
                    </Button>
                    <Button variant="contained" size="small" onClick={() => setRenewalSettingsOpen(true)} startIcon={<Settings size={16} />}>Cài đặt</Button>
                  </div>
                }
              />
	              <Box sx={{ display: "grid", gap: 1.25, p: 2, pb: 1 }}>
	                <TextField value={renewalQuery} onChange={(event) => { setRenewalQuery(event.target.value); setRenewalPage(1); }} placeholder="Tìm tên khách, Telegram ID, gói, order..." size="small" fullWidth />
                  {renewalTab === "expired" ? (
                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
                      {[
                        { key: "all", label: "Tất cả" },
                        { key: "chokick", label: "Chờ kick / audit" },
                        { key: "review", label: "Cần soi" },
                        { key: "kicked", label: "Đã kick" },
                        { key: "retained", label: "Bị giữ lại" },
                        { key: "error", label: "Có lỗi" },
                      ].map((item) => (
                        <Chip
                          key={item.key}
                          label={item.label}
                          clickable
                          color={renewalFocusFilter === item.key ? "primary" : "default"}
                          variant={renewalFocusFilter === item.key ? "filled" : "outlined"}
                          onClick={() => {
                            setRenewalFocusFilter(item.key as RenewalFocusFilter);
                            setRenewalPage(1);
                          }}
                          sx={{ fontWeight: 800 }}
                        />
                      ))}
                    </Box>
                  ) : null}
	              </Box>
	              <Tabs value={renewalTab} onChange={(_, next) => { setRenewalTab(next); setRenewalPage(1); }} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
	                <Tab value="soon" label={`Sắp hết hạn (${expiringSoon.length})`} />
	                <Tab value="reminded" label={`Đã thông báo (${renewalNoticeEvents.length})`} />
	                <Tab value="expired" label={`Đã hết hạn (${expiredRenewalOrders.length})`} />
	                <Tab value="lifetime" label={`Trọn đời (${lifetimeRenewalOrders.length})`} />
	              </Tabs>
	              <SimpleTable
	                headers={renewalHeaders[renewalTab]}
	                rows={pagedRenewalRows}
	                rowSx={(idx) => {
	                  const row = currentRenewalOpsRows[(Math.min(renewalPage, totalRenewalPages) - 1) * RENEWAL_PAGE_SIZE + idx];
	                  return row?.flags.isImportant ? { bgcolor: "rgba(245, 158, 11, 0.08)" } : row?.flags.isNew ? { bgcolor: "rgba(59, 130, 246, 0.05)" } : {};
	                }}
	                actions={(idx) => {
	                  const row = currentRenewalOpsRows[(Math.min(renewalPage, totalRenewalPages) - 1) * RENEWAL_PAGE_SIZE + idx] as (typeof currentRenewalOpsRows)[number] & { orderId?: string, planName?: string, customerName?: string, groupsToKick?: string[], groupsToReview?: string[], renewalStatus?: string, renewalNote?: string };
	                  if (!row?.telegramId) return null;
                      const groupsToKick = row.groupsToKick || [];
                      const groupsToReview = row.groupsToReview || [];
                      const status = String(row.renewalStatus || "");
	                  return (
	                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
	                      <Button variant="text" size="small" onClick={(event) => { event.stopPropagation(); void openCustomerFromLookup(row.telegramId); }} startIcon={<Search size={14} />}>Mở</Button>
	                      {renewalTab === "soon" ? <Button variant="text" size="small" onClick={(event) => { event.stopPropagation(); void openCustomerRenewFromLookup(row.telegramId); }} startIcon={<RefreshCw size={14} />}>Gia hạn</Button> : null}
                          {renewalTab === "expired" && row.orderId ? (
                            <>
                              {(status === "Chờ kick" || status === "Chờ audit" || status === "Lỗi" || renewalFocusFilter === "review") && groupsToKick.length > 0 ? (
                                <Button variant="text" size="small" onClick={(event) => { event.stopPropagation(); void retryKickUserHandler(row.telegramId, row.orderId as string, row.planName || "", row.customerName || "", groupsToKick); }} disabled={saving === `retry-kick-${row.orderId}`} startIcon={saving === `retry-kick-${row.orderId}` ? <Loader2 size={14} className="spin" /> : <RefreshCw size={14} />}>Kick lại ({groupsToKick.length})</Button>
                              ) : null}
                              {(status === "Bị giữ lại" || renewalFocusFilter === "retained") && groupsToReview.length > 0 ? (
                                <Button variant="text" size="small" onClick={(event) => { event.stopPropagation(); void openCustomerFromLookup(row.telegramId); }} startIcon={<ShieldCheck size={14} />}>Soi giữ lại ({groupsToReview.length})</Button>
                              ) : null}
                              {status === "Đã kick" ? (
                                <Button variant="text" size="small" onClick={(event) => { event.stopPropagation(); void openCustomerFromLookup(row.telegramId); }} startIcon={<CheckCircle2 size={14} />}>Đã xong</Button>
                              ) : null}
                            </>
                          ) : null}
	                    </Box>
	                  );
	                }}
	              />
	              <Pagination page={renewalPage} totalPages={totalRenewalPages} totalItems={currentRenewalOpsRows.length} onPage={setRenewalPage} label="dòng" />
            </section>
          </div>
        ) : null}

        {tab === "supportGroup" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Join hôm nay" value={String(supportGroupTodayEvents.filter((item) => item.event_type === "support_joined").length)} accent="emerald" icon={<Plus size={16} />} />
              <Metric label="Rời hôm nay" value={String(supportGroupTodayEvents.filter((item) => item.event_type === "support_left").length)} accent="rose" icon={<TrendingUp size={16} />} />
              <Metric label="Mute hôm nay" value={String(supportGroupTodayEvents.filter((item) => item.event_type === "member_muted").length)} accent="amber" icon={<XCircle size={16} />} />
              <Metric label="Kick hôm nay" value={String(supportKickedToday.length)} accent="violet" icon={<ShieldCheck size={16} />} />
              <Metric label="Sự kiện nhóm hỗ trợ" value={String(supportGroupEvents.length)} accent="blue" icon={<Activity size={16} />} />
              <Metric label="Tên group hỗ trợ" value={getConfigValue(config, "SUPPORT_GROUP_NAME", "Nhóm hỗ trợ")} accent="cyan" icon={<Users size={16} />} />
              <Metric label="Mode hỗ trợ" value={String(getConfigValue(config, "SUPPORT_GROUP_MODE", "group")).toUpperCase()} accent="indigo" icon={<Settings size={16} />} />
            </div>
            <section className="panel">
              <PanelHead
                title="Khu vực hỗ trợ"
                subtitle="Chỉ hiển thị sự kiện của group hỗ trợ theo SUPPORT_GROUP_ID. Không trộn với inbox tin nhắn bot."
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
                <div className="muted">Bấm kiểm tra sau khi lưu ID group chăm sóc khách hàng.</div>
              )}
            </section>
            <section className="panel">
              <PanelHead
                title="Sự kiện nhóm hỗ trợ"
                subtitle="Theo tab để dễ lọc, chỉ hiển thị dữ liệu của nhóm hỗ trợ."
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
              <PanelHead title="Cấu hình vận hành Bot" subtitle="Thiết lập hệ thống bot." />
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
                  <div className="grid" style={{ padding: "0 16px 8px" }}>
                    <Metric label={botScheduleStatus ? (botScheduleStatus.active ? "Bot đang hoạt động" : "Bot đang offline") : "Không đọc được runtime"} value={botScheduleStatus?.title || "Không có dữ liệu runtime"} accent={botScheduleStatus?.active ? "emerald" : "rose"} icon={<Activity size={16} />} />
                    {botScheduleStatus ? (
                      <>
                        <Metric label="Nguồn hiện tại" value={botScheduleStatus?.source === "fixed" ? "Theo BOT_ACTIVE_HOURS" : botScheduleStatus?.source === "maintenance" ? "Bảo trì thủ công" : "Luôn hoạt động"} accent="blue" icon={<Settings size={16} />} />
                        <Metric label="Khung giờ / lý do" value={botScheduleStatus?.window || "Không có khung giờ runtime"} accent="cyan" icon={<Send size={16} />} />
                        <Metric label="Lặp bài channel" value="Độc lập với giờ hoạt động bot" accent="amber" icon={<ClipboardList size={16} />} />
                      </>
                    ) : (
                      <Metric label="Runtime" value="Không đọc được trạng thái giờ bot từ API" accent="rose" icon={<Settings size={16} />} />
                    )}
                  </div>
                  {botScheduleStatus ? (
                    <div className="hint compact" style={{ padding: "0 16px 16px" }}>
                      Múi giờ bot: <strong>{botScheduleStatus?.timezone || "-"}</strong> • Bảo trì thủ công: <strong>{botScheduleStatus?.maintenanceMode ? "ON" : "OFF"}</strong>
                    </div>
                  ) : (
                    <div className="hint compact" style={{ padding: "0 16px 16px" }}>
                      Không đọc được runtime từ API.
                    </div>
                  )}
                </section>
                <ConfigEditor title="Cài đặt bot" subtitle="Bảo trì thủ công, lịch hoạt động giờ Việt Nam, QR và tần suất kiểm tra thanh toán." fields={BOT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} />
                <ConfigEditor title="Inbox hỗ trợ" subtitle="Luồng tin nhắn riêng từ khách vào bot, group inbox, tên admin và quyền xoá inbox." fields={SUPPORT_INBOX_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} />
              </>
            ) : null}
            {contentTab === "payment" ? (
              <Stack spacing={2.5}>
                <section className="panel">
                  <PanelHead
                    title="Payment rails"
                    subtitle="Danh sách cổng thanh toán thật."
                    action={
                      <Tooltip title="Rail là cổng xử lý tiền và đối soát. Action chỉ mở luồng phụ như web checkout." arrow>
                        <Chip size="small" label="Rail / Action" variant="outlined" />
                      </Tooltip>
                    }
                  />
                  <div style={{ display: "grid", gap: 10, padding: "0 16px 16px" }}>
                    {(paymentSchema?.rails?.length ? paymentSchema.rails : [{ provider: "PAYOS", kind: "rail", enabledKey: "PAYOS_PAYMENT_ENABLED", enabledDefault: "ON", currency: "VND", priority: 10, fields: PAYMENT_RAIL_FIELDS.slice(0, 1) } as PaymentSchemaGroup]).map((rail) => {
                      const field = rail.fields?.[0];
                      const currentValue = String(field ? fieldValues[field.key] || "" : "").trim().toUpperCase();
                      const enabled = currentValue === "ON" || currentValue === "TRUE" || currentValue === "YES" || currentValue === "1";
                      const providerIcon = rail.provider === "PAYOS" ? <CreditCard size={18} /> : rail.provider === "PAYPAL" ? <BadgeDollarSign size={18} /> : rail.provider === "NOWPAYMENTS" ? <Coins size={18} /> : rail.provider === "TRON_USDT" ? <Coins size={18} /> : <ShoppingCart size={18} />;
                      const providerLabel = rail.provider === "PAYOS" ? "PayOS / VietQR" : rail.provider === "PAYPAL" ? "PayPal" : rail.provider === "NOWPAYMENTS" ? "NOWPayments" : rail.provider === "TRON_USDT" ? "USDT TRC20" : "Binance Pay";
                      return (
                        <Box
                          key={rail.provider}
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            gap: 1.5,
                            flexWrap: "wrap",
                            px: 1.75,
                            py: 1.5,
                            borderRadius: 3,
                            border: "1px solid",
                            borderColor: enabled ? "rgba(34,197,94,0.28)" : "rgba(148,163,184,0.22)",
                            bgcolor: enabled ? "rgba(240,253,244,0.55)" : "rgba(255,255,255,0.88)",
                          }}
                        >
                          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1.5, flexWrap: "wrap", width: "100%" }}>
                            <Box sx={{ display: "flex", alignItems: "center", gap: 1.25, minWidth: 0 }}>
                              <Box sx={{ width: 34, height: 34, borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: enabled ? "rgba(16,185,129,0.12)" : "rgba(59,130,246,0.10)", color: enabled ? "success.main" : "primary.main" }}>
                                {providerIcon}
                              </Box>
                              <Box sx={{ minWidth: 0 }}>
                                <Typography sx={{ fontWeight: 800, lineHeight: 1.15 }}>{providerLabel}</Typography>
                              </Box>
                            </Box>
                            <Chip size="small" label={enabled ? "Active" : "Off"} color={enabled ? "success" : "default"} variant={enabled ? "filled" : "outlined"} />
                          </Box>
                          <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.4, flex: "1 1 100%", mt: 0.25 }}>
                            {field ? field.help : "Chưa có field schema"}.
                          </Typography>
                        </Box>
                      );
                    })}
                  </div>
                </section>
                <ConfigEditor
                  title="Cài đặt payment rails"
                  subtitle="Bật/tắt và chỉnh field cổng thanh toán thật."
                  fields={paymentRailFields.length ? paymentRailFields : PAYMENT_RAIL_FIELDS}
                  values={fieldValues}
                  setValues={setFieldValues}
                  onSave={saveFields}
                />
                <section className="panel">
                  <PanelHead
                    title="Payment actions"
                    subtitle="Danh sách action phụ."
                  />
                  <div className="hint compact" style={{ margin: "0 16px 16px" }}>
                    <strong>WEB</strong> chỉ mở luồng phụ, không đối soát tiền.
                  </div>
                  <div style={{ display: "grid", gap: 10, padding: "0 16px 16px" }}>
                    {(paymentSchema?.actions?.length ? paymentSchema.actions : [{ provider: "WEB", kind: "action", enabledKey: "WEB_PAYMENT_ENABLED", enabledDefault: "ON", currency: "VND", priority: 99, fields: PAYMENT_ACTION_FIELDS } as PaymentSchemaGroup]).map((action) => {
                      const field = action.fields?.[0];
                      const currentValue = String(field ? fieldValues[field.key] || "" : "").trim().toUpperCase();
                      const enabled = currentValue === "ON" || currentValue === "TRUE" || currentValue === "YES" || currentValue === "1";
                      return (
                        <Box
                          key={action.provider}
                          sx={{
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            gap: 1.5,
                            flexWrap: "wrap",
                            px: 1.75,
                            py: 1.5,
                            borderRadius: 3,
                            border: "1px solid",
                            borderColor: enabled ? "rgba(59,130,246,0.25)" : "rgba(148,163,184,0.22)",
                            bgcolor: enabled ? "rgba(239,246,255,0.56)" : "rgba(255,255,255,0.88)",
                          }}
                        >
                          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1.5, flexWrap: "wrap", width: "100%" }}>
                            <Box sx={{ display: "flex", alignItems: "center", gap: 1.25, minWidth: 0 }}>
                              <Box sx={{ width: 34, height: 34, borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: enabled ? "rgba(59,130,246,0.12)" : "rgba(148,163,184,0.10)", color: enabled ? "primary.main" : "text.secondary" }}>
                                <Pencil size={18} />
                              </Box>
                              <Box sx={{ minWidth: 0 }}>
                                <Typography sx={{ fontWeight: 800, lineHeight: 1.15 }}>WEB checkout</Typography>
                              </Box>
                            </Box>
                            <Chip size="small" label={enabled ? "Active" : "Off"} color={enabled ? "primary" : "default"} variant={enabled ? "filled" : "outlined"} />
                          </Box>
                          <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.4, flex: "1 1 100%", mt: 0.25 }}>
                            {field ? field.help : "Chưa có field schema"}.
                          </Typography>
                        </Box>
                      );
                    })}
                  </div>
                </section>
                <ConfigEditor
                  title="Cài đặt payment actions"
                  subtitle="Bật/tắt và chỉnh field cho action mở web thanh toán."
                  fields={paymentActionFields.length ? paymentActionFields : PAYMENT_ACTION_FIELDS}
                  values={fieldValues}
                  setValues={setFieldValues}
                  onSave={saveFields}
                />
              </Stack>
            ) : null}
            {contentTab === "currency" ? <ConfigEditor title="Tiền tệ hiển thị" subtitle="Chỉ đổi cách hiển thị trong bot/UI. Số tiền QR PayOS vẫn giữ nguyên VND." fields={CURRENCY_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {contentTab === "admin" ? <ConfigEditor title="Setup Admin ID" subtitle="Quản lý Telegram ID có quyền admin. Nhiều ID thì cách nhau bằng dấu phẩy." fields={ADMIN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
          </div>
        ) : null}

        {tab === "autoPayment" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead
                title="Auto payment"
                subtitle="Tách riêng theo ngôn ngữ và tệp khách: khách Việt, khách nước ngoài, cùng bot hỗ trợ và audit gần nhất."
              />
              <div className="hint">
                Khách Việt dùng bộ config VI, khách nước ngoài dùng bộ config EN. Mỗi bộ có cờ bật/tắt và khung giờ riêng cho khách mới và khách cũ.
              </div>
              <div className="panel-actions" style={{ padding: "0 16px 16px", flexWrap: "wrap" }}>
                <Button variant="contained" size="small" onClick={() => quickSetAutoPaymentWindow(true)} startIcon={<CalendarClock size={16} />}>
                  Bật nhanh lịch VI
                </Button>
                <Button variant="outlined" size="small" onClick={() => quickSetAutoPaymentWindow(false)} startIcon={<Settings size={16} />}>
                  Tắt lịch VI
                </Button>
                <Button variant="contained" size="small" color="secondary" onClick={() => quickSetAutoPaymentWindowEn(true)} startIcon={<CalendarClock size={16} />}>
                  Bật nhanh lịch EN
                </Button>
                <Button variant="outlined" size="small" color="secondary" onClick={() => quickSetAutoPaymentWindowEn(false)} startIcon={<Settings size={16} />}>
                  Tắt lịch EN
                </Button>
              </div>
            </section>
            <div className="grid">
              <Metric label="VI khách mới" value={autoPaymentUiValue("AUTO_PAYMENT_VI_NEW_ENABLED", "OFF", "AUTO_PAYMENT_NEW_ENABLED")} accent="blue" icon={<CalendarClock size={16} />} />
              <Metric label="VI khách cũ" value={autoPaymentUiValue("AUTO_PAYMENT_VI_RETURNING_ENABLED", "ON", "AUTO_PAYMENT_RETURNING_ENABLED")} accent="emerald" icon={<Settings size={16} />} />
              <Metric label="EN khách mới" value={autoPaymentUiValue("AUTO_PAYMENT_EN_NEW_ENABLED", "OFF")} accent="amber" icon={<Clock3 size={16} />} />
              <Metric label="EN khách cũ" value={autoPaymentUiValue("AUTO_PAYMENT_EN_RETURNING_ENABLED", "ON")} accent="violet" icon={<CheckCircle2 size={16} />} />
            </div>
            <section className="panel">
              <PanelHead title="Audit gần nhất" subtitle="Worker ghi lại trạng thái mới nhất của từng tệp theo ngôn ngữ để admin kiểm tra nhanh." />
              <SimpleTable
                headers={["Key", "Giá trị"]}
                rows={[
                  ["AUTO_PAYMENT_VI_NEW_LAST_CHECK_AT", getConfigValue(config, "AUTO_PAYMENT_VI_NEW_LAST_CHECK_AT", getConfigValue(config, "AUTO_PAYMENT_NEW_LAST_CHECK_AT", "-")) || "-"],
                  ["AUTO_PAYMENT_VI_NEW_LAST_CHECK_RESULT", getConfigValue(config, "AUTO_PAYMENT_VI_NEW_LAST_CHECK_RESULT", getConfigValue(config, "AUTO_PAYMENT_NEW_LAST_CHECK_RESULT", "-")) || "-"],
                  ["AUTO_PAYMENT_VI_RETURNING_LAST_CHECK_AT", getConfigValue(config, "AUTO_PAYMENT_VI_RETURNING_LAST_CHECK_AT", getConfigValue(config, "AUTO_PAYMENT_RETURNING_LAST_CHECK_AT", "-")) || "-"],
                  ["AUTO_PAYMENT_VI_RETURNING_LAST_CHECK_RESULT", getConfigValue(config, "AUTO_PAYMENT_VI_RETURNING_LAST_CHECK_RESULT", getConfigValue(config, "AUTO_PAYMENT_RETURNING_LAST_CHECK_RESULT", "-")) || "-"],
                  ["AUTO_PAYMENT_EN_NEW_LAST_CHECK_AT", getConfigValue(config, "AUTO_PAYMENT_EN_NEW_LAST_CHECK_AT", "-") || "-"],
                  ["AUTO_PAYMENT_EN_NEW_LAST_CHECK_RESULT", getConfigValue(config, "AUTO_PAYMENT_EN_NEW_LAST_CHECK_RESULT", "-") || "-"],
                  ["AUTO_PAYMENT_EN_RETURNING_LAST_CHECK_AT", getConfigValue(config, "AUTO_PAYMENT_EN_RETURNING_LAST_CHECK_AT", "-") || "-"],
                  ["AUTO_PAYMENT_EN_RETURNING_LAST_CHECK_RESULT", getConfigValue(config, "AUTO_PAYMENT_EN_RETURNING_LAST_CHECK_RESULT", "-") || "-"],
                ]}
              />
            </section>
            <div className="two-col">
              <ConfigEditor
                title="Khách Việt"
                subtitle="Bộ riêng cho khách nội địa, giữ tương thích với cấu hình cũ trong giai đoạn chuyển đổi."
                fields={[...AUTO_PAYMENT_VI_NEW_FIELDS, ...AUTO_PAYMENT_VI_RETURNING_FIELDS]}
                values={fieldValues}
                setValues={setFieldValues}
                onSave={saveFields}
              />
              <ConfigEditor
                title="Khách nước ngoài"
                subtitle="Bộ riêng cho khách tiếng Anh, không dùng chung lịch với khách Việt."
                fields={[...AUTO_PAYMENT_EN_NEW_FIELDS, ...AUTO_PAYMENT_EN_RETURNING_FIELDS]}
                values={fieldValues}
                setValues={setFieldValues}
                onSave={saveFields}
              />
            </div>
            <div className="two-col">
              <ConfigEditor
                title="Bot hỗ trợ"
                subtitle="Link bot và toàn bộ tin nhắn auto payment cho khách Việt."
                fields={AUTO_PAYMENT_SUPPORT_FIELDS}
                values={fieldValues}
                setValues={setFieldValues}
                onSave={saveFields}
              />
              <ConfigEditor
                title="Bot hỗ trợ tiếng Anh"
                subtitle="Link bot và toàn bộ tin nhắn auto payment cho khách nước ngoài."
                fields={AUTO_PAYMENT_SUPPORT_EN_FIELDS}
                values={fieldValues}
                setValues={setFieldValues}
                onSave={saveFields}
              />
            </div>
          </div>
        ) : null}

        {tab === "botVi" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="UI Bot tiếng Việt" subtitle="Chỉ quản lý tên gói và nội dung khách Việt nhìn thấy. Giá được quản lý tập trung tại Nhóm & giá." />
              <Tabs value={botViTab} onChange={(_, next) => setBotViTab(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="plans" label="Tên gói & nút mua" />
                <Tab value="groups" label="Mô tả collection" />
                <Tab value="buttons" label="Nút bấm" />
                <Tab value="messages" label="Tin nhắn" />
                <Tab value="saleContent" label="Flash sale" />
              </Tabs>
            </section>
            {botViTab === "plans" ? <ConfigEditor title="Tên gói và nút mua tiếng Việt" subtitle="Không chứa giá. Giá bán được quản lý tập trung tại Nhóm & giá." fields={PLAN_VI_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botViTab === "groups" ? <ConfigEditor title="Mô tả collection tiếng Việt" subtitle="Chỉ chỉnh nội dung mô tả. Tên collection và giá nằm tại Nhóm & giá." fields={groupViContentFields} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botViTab === "buttons" ? <ConfigEditor title="Nút bấm tiếng Việt" subtitle="Text nút Telegram dành cho khách Việt." fields={BUTTON_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botViTab === "messages" ? <ConfigEditor title="Tin nhắn tiếng Việt" subtitle="Các mẫu tin Bot gửi cho khách Việt." fields={VISIBLE_MESSAGE_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botViTab === "saleContent" ? <ConfigEditor title="Flash sale tiếng Việt" subtitle="Nội dung flash sale dành cho khách Việt." fields={SALE_CONTENT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
          </div>
        ) : null}

        {tab === "specialGroups" ? (
          <div className="stack">
            <div className="grid">
              <Metric label="Special group" value={String(hiddenGroups.length)} accent="blue" icon={<Users size={20} />} />
              <Metric label="Đang hoạt động" value={String(hiddenGroups.filter((item) => item.is_active).length)} accent="emerald" icon={<CheckCircle2 size={20} />} />
              <Metric label="Special code" value={String(hiddenCodes.length)} accent="amber" icon={<Ticket size={20} />} />
              <Metric label="Lượt mở catalog" value={String(hiddenRedemptions.length)} accent="violet" icon={<Activity size={20} />} />
            </div>
            <section className="panel">
              <PanelHead
                title="Special Group"
                subtitle="Quản lý nhóm đặc biệt ẩn, mã reveal và lịch sử người đã mở catalog."
                action={(
                  <div className="panel-actions">
                    <IconButton onClick={() => setSpecialGroupSettingsOpen(true)} color="primary" sx={{ mr: 1 }} title="Cài đặt tin nhắn Special Group"><Settings size={18} /></IconButton>
                    {hiddenSetupView === "groups" ? <Button variant="contained" size="small" onClick={openNewHiddenGroupModal} startIcon={<Plus size={16} />}>Thêm Special Group</Button> : null}
                    {hiddenSetupView === "codes" ? <Button variant="contained" size="small" onClick={openNewHiddenCodeModal} startIcon={<Plus size={16} />}>Thêm Special Code</Button> : null}
                  </div>
                )}
              />
              <Tabs value={hiddenSetupView} onChange={(_, next) => setHiddenSetupView(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="groups" label="Nhóm đặc biệt" />
                <Tab value="codes" label="Mã reveal" />
                <Tab value="activity" label="Lịch sử mở mã" />
              </Tabs>
              {hiddenSetupView === "groups" ? (
                <>
                  <div className="hint compact">
                    Mỗi Special Group là một entitlement riêng. ID nên ngắn gọn, ổn định như <code>prime_alpha</code> vì nó đi vào plan token và scheduler.
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
                            <span>30 ngày {formatDisplayCurrency(Number(item.price_1m_vnd || 0), "VND")}</span>
                            <span>Trọn đời {formatDisplayCurrency(Number(item.price_life_vnd || 0), "VND")}</span>
                            <span>{formatDisplayCurrency(Number(item.price_1m_usd || 0), "USD")} / {formatDisplayCurrency(Number(item.price_life_usd || 0), "USD")}</span>
                            <span>{item.duration_1m_days}d / {item.lifetime_days}d</span>
                          </div>
                        </div>
                        <div className="coupon-row-actions">
                          <Button variant="outlined" size="small" onClick={() => openEditHiddenGroupModal(item)} disabled={saving === `hidden-group-${item.id}`}>Sửa</Button>
                          <Button variant="outlined" color="error" size="small" onClick={() => removeHiddenGroupAction(item.id)} disabled={saving === `hidden-group-delete-${item.id}`}>Xóa</Button>
                        </div>
                      </div>
                    )) : <div className="empty-card">Chưa có Special Group khớp bộ lọc.</div>}
                  </div>
                </>
              ) : null}
              {hiddenSetupView === "codes" ? (
                <>
                  <div className="hint compact">
                    Special Code chỉ dùng để reveal catalog, không phải mã. Bạn có thể giới hạn thời gian, số lượt và điều kiện như <code>COMBO_LIFETIME</code> (legacy key vẫn hỗ trợ <code>SVIP_LIFETIME</code>).
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
                            <span>{item.scope_type === "ALL_ACTIVE_HIDDEN_GROUPS" ? "Toàn bộ Special Group active" : `${item.group_ids.length} group cụ thể`}</span>
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
                    )) : <div className="empty-card">Chưa có Special Code khớp bộ lọc.</div>}
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

        {tab === "botEn" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="UI Bot tiếng Anh" subtitle="Chỉ quản lý tên gói và nội dung tiếng Anh. Giá USD PayPal được quản lý tập trung tại Nhóm & giá." />
              <Tabs value={botEnTab} onChange={(_, next) => setBotEnTab(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="plans" label="Tên gói & nút mua" />
                <Tab value="groups" label="Mô tả collection" />
                <Tab value="buttons" label="Nút bấm" />
                <Tab value="messages" label="Tin nhắn" />
                <Tab value="saleContent" label="Flash sale" />
              </Tabs>
            </section>
            {botEnTab === "plans" ? <ConfigEditor title="Tên gói và nút mua tiếng Anh" subtitle="Không chứa giá. Giá USD PayPal được quản lý tập trung tại Nhóm & giá." fields={PLAN_EN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botEnTab === "groups" ? <ConfigEditor title="Mô tả collection tiếng Anh" subtitle="Chỉ chỉnh nội dung mô tả. Tên tiếng Anh và giá USD nằm tại Nhóm & giá." fields={groupEnContentFields} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botEnTab === "buttons" ? <ConfigEditor title="Nút bấm tiếng Anh" subtitle="Các key BTN_*_EN dành riêng cho khách tiếng Anh." fields={BUTTON_EN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botEnTab === "messages" ? <ConfigEditor title="Tin nhắn tiếng Anh" subtitle="Các key MSG_*_EN dành riêng cho khách tiếng Anh, không gồm các tin auto payment đã gom về tab Auto payment." fields={VISIBLE_MESSAGE_EN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botEnTab === "saleContent" ? <ConfigEditor title="Flash sale tiếng Anh" subtitle="Nội dung sale tiếng Anh, dùng giá USD." fields={SALE_CONTENT_EN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
          </div>
        ) : null}

        {tab === "botTools" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="Phản hồi & cảnh báo" subtitle="Chỉ giữ phản hồi lệnh trong group và các alert ngắn. Command menu được quản lý ở Menu Bot." />
              <Tabs value={botToolsTab} onChange={(_, next) => setBotToolsTab(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="groupReplies" label="Group replies" />
                <Tab value="alerts" label="Cảnh báo" />
              </Tabs>
            </section>
            {botToolsTab === "groupReplies" ? <ConfigEditor title="Phản hồi lệnh trong group" subtitle="Bật/tắt và chỉnh câu nhắc cuối cho các lệnh group. Command menu riêng được đặt ở Menu Bot." fields={GROUP_COMMAND_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} /> : null}
            {botToolsTab === "alerts" ? (
              <div className="stack">
                <ConfigEditor title="Cảnh báo tiếng Việt" subtitle="Alert ngắn khi khách Việt thao tác." fields={ALERT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} />
                <ConfigEditor title="Cảnh báo tiếng Anh" subtitle="Alert ngắn khi khách tiếng Anh thao tác." fields={ALERT_EN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} />
              </div>
            ) : null}
          </div>
        ) : null}

        {tab === "menuBot" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="Menu Bot" subtitle="Một nơi để quản lý page menu, nút đổi ngôn ngữ và command menu riêng cho private/group." />
              <Tabs value={menuBotTab} onChange={(_, next) => setMenuBotTab(next)} variant="scrollable" scrollButtons="auto" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="pages" label="Trang menu" />
                <Tab value="language" label="Ngôn ngữ" />
                <Tab value="commands" label="Command menu" />
              </Tabs>
            </section>
            {menuBotTab === "pages" ? (
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
            {menuBotTab === "language" ? (
              <ConfigEditor title="Ngôn ngữ menu bot" subtitle="Bật/tắt nút đổi ngôn ngữ và chọn ngôn ngữ mặc định cho user mới." fields={MENU_LANGUAGE_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} />
            ) : null}
            {menuBotTab === "commands" ? (
              <div className="stack">
                <ConfigEditor title="Menu private" subtitle="Bật/tắt từng lệnh hiển thị khi chat riêng với bot. Đây là menu quan trọng nhất cho khách." fields={PRIVATE_MENU_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} />
                <ConfigEditor title="Menu group" subtitle="Bật/tắt từng lệnh hiển thị trong group công khai. Chỉ giữ các lệnh cần cho nhóm." fields={GROUP_MENU_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} />
                <ConfigEditor title="Mô tả lệnh tiếng Việt" subtitle="Mô tả command hiển thị trong Telegram menu cho khách Việt." fields={COMMAND_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} />
                <ConfigEditor title="Mô tả lệnh tiếng Anh" subtitle="Mô tả command hiển thị trong Telegram menu cho khách tiếng Anh." fields={COMMAND_EN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} />
              </div>
            ) : null}
          </div>
        ) : null}

        {tab === "coupons" ? (
          <section className="panel">
            <PanelHead
              title="Mã"
              subtitle="Danh sách mã được tách theo trạng thái. Bấm mã để copy và đánh dấu đã gửi, bấm dòng để chỉnh sửa trong popup."
              action={
                  <div className="panel-actions">
                  <Button variant="contained" size="small" onClick={openNewCouponModal} startIcon={<Plus size={16} />}>Thêm mã</Button>
                </div>
              }
            />
            <div className="grid">
              <Metric label="Chưa gửi" value={String(couponTabCounts.unsent)} accent="blue" icon={<Ticket size={16} />} />
              <Metric label="Đã gửi" value={String(couponTabCounts.sent)} accent="cyan" icon={<Send size={16} />} />
              <Metric label="Đã sử dụng" value={String(couponTabCounts.used)} accent="emerald" icon={<CheckCircle2 size={16} />} />
              <Metric label="Đã hết hạn" value={String(couponTabCounts.expired)} accent="rose" icon={<Clock3 size={16} />} />
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
                  <IconButton color="error" size="small" onClick={(event) => { event.stopPropagation(); removeCoupon(pagedCoupons[idx].code); }} title="Xoá mã">
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
              <Metric label="Tổng mã" value={String(activationCodesByStatus.ALL.length)} accent="blue" icon={<ClipboardList size={16} />} />
              <Metric label="Chờ kích hoạt" value={String(activationCodesByStatus.PENDING.length)} accent="amber" icon={<Clock3 size={16} />} />
              <Metric label="Đã dùng" value={String(activationCodesByStatus.USED.length)} accent="emerald" icon={<CheckCircle2 size={16} />} />
              <Metric label="Đã vô hiệu" value={String(activationCodesByStatus.DISABLED.length)} accent="rose" icon={<XCircle size={16} />} />
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
                title="Bảo mật bot và mã kích hoạt"
                subtitle="Chặn seller, ẩn menu nhập mã và chống dò mã. Mặc định khách chỉ cần nhắn mã bắt đầu bằng HANGCU_."
                action={
                  <div className="panel-actions">
                    <Button variant="outlined" size="small" onClick={() => setSecuritySettingsOpen(true)} startIcon={<Settings size={16} />}>Cài đặt</Button>
                    <Button variant="contained" size="small" onClick={() => { setBlacklistForm({ telegram_user_id: "", username: "", full_name: "", reason: "" }); setBlacklistModalOpen(true); }} startIcon={<Plus size={16} />}>Thêm blacklist</Button>
                  </div>
                }
              />
              <div className="hint compact">Cấu hình bảo mật được tách vào popup để phần blacklist luôn gọn và dễ thao tác.</div>
              <Box sx={{ display: "grid", gap: 1.25, gridTemplateColumns: { xs: "1fr", md: "minmax(0, 1fr) 220px 220px" }, p: 2 }}>
                <TextField size="small" value={blacklistQuery} onChange={(event) => setBlacklistQuery(event.target.value)} placeholder="Tìm Telegram ID, username, tên, lý do..." />
                <TextField select size="small" value={blacklistStatusFilter} onChange={(event) => setBlacklistStatusFilter(event.target.value as "all" | "active" | "inactive" | "reason")}>
                  <MenuItem value="all">Tất cả blacklist</MenuItem>
                  <MenuItem value="active">Đang chặn</MenuItem>
                  <MenuItem value="inactive">Đã tắt</MenuItem>
                  <MenuItem value="reason">Có lý do</MenuItem>
                </TextField>
                <Box sx={{ display: "flex", alignItems: "center", justifyContent: { xs: "flex-start", md: "flex-end" }, gap: 1, color: "text.secondary" }}>
                  <Typography variant="body2" sx={{ fontWeight: 700 }}>Hiển thị {filteredBlacklist.length}/{blacklist.length}</Typography>
                </Box>
              </Box>
              <SimpleTable
                headers={["Telegram ID", "Username", "Tên", "Nguồn", "Lý do", "Trạng thái"]}
                rows={filteredBlacklist.map((item) => [
                  item.telegram_user_id,
                  item.username || "-",
                  item.full_name || "-",
                  item.source || "-",
                  item.reason || "-",
                  item.is_active ? "Đang chặn" : "Tắt",
                ])}
                onRow={(idx) => {
                  const item = filteredBlacklist[idx];
                  setBlacklistForm({
                    telegram_user_id: item.telegram_user_id,
                    username: item.username || "",
                    full_name: item.full_name || "",
                    reason: item.reason || "",
                  });
                  setBlacklistModalOpen(true);
                }}
                actions={(idx) => (
                  <IconButton color="error" size="small" onClick={(event) => { event.stopPropagation(); removeBlacklistEntry(filteredBlacklist[idx].telegram_user_id); }} title="Gỡ blacklist">
                    <Trash2 size={16} />
                  </IconButton>
                )}
              />
            </section>
          </div>
        ) : null}

        {tab === "vipAudit" ? (
          <div className="stack">
            <section className="panel">
              <PanelHead
                title="VIP audit"
                subtitle="Dò những member VIP bot đã ghi nhận nhưng không còn đơn active hoặc chưa từng có đơn. Dùng live check để bỏ qua member đã out group."
                action={(
                  <div className="panel-actions">
                    <Button variant="outlined" size="small" onClick={() => refreshVipMemberAudit(false)} disabled={saving === "vip-member-audit-refresh"} startIcon={saving === "vip-member-audit-refresh" ? <Loader2 size={16} className="spin" /> : <RefreshCw size={16} />}>
                      Quét lại
                    </Button>
                    <Button variant="contained" size="small" onClick={() => refreshVipMemberAudit(true)} disabled={saving === "vip-member-audit-live"} startIcon={saving === "vip-member-audit-live" ? <Loader2 size={16} className="spin" /> : <Search size={16} />}>
                      Quét live
                    </Button>
                    <Button variant="outlined" color="warning" size="small" onClick={() => cleanupVipInviteLinksAction("", true)} disabled={saving === "vip-invite-cleanup-all"} startIcon={saving === "vip-invite-cleanup-all" ? <Loader2 size={16} className="spin" /> : <Trash2 size={16} />}>
                      Dọn toàn bộ link join
                    </Button>
                  </div>
                )}
              />
              <div className="hint compact">
                Công cụ này chỉ quét member VIP mà bot đã ghi nhận qua sự kiện join/left/kick. Telegram Bot API không cho phép liệt kê toàn bộ member ẩn của group từ con số 0.
              </div>
              <div className="grid" style={{ padding: "0 16px 12px" }}>
                <Metric label="Rows" value={String(vipMemberAuditCounts.all)} accent="blue" icon={<Users size={16} />} />
                <Metric label="Không có đơn" value={String(vipMemberAuditCounts.noOrder)} accent="amber" icon={<Ticket size={16} />} />
                <Metric label="Đơn hết hạn" value={String(vipMemberAuditCounts.expired)} accent="rose" icon={<Clock3 size={16} />} />
                <Metric label="Live checked" value={String(vipMemberAudit.filter((item) => item.live_checked).length)} accent="emerald" icon={<CheckCircle2 size={16} />} />
              </div>
              <div className="panel-actions" style={{ padding: "0 16px 10px", flexWrap: "wrap" }}>
                <Button
                  variant={vipMemberAuditRiskType === "ALL" ? "contained" : "outlined"}
                  size="small"
                  onClick={() => { setVipMemberAuditRiskType("ALL"); void refreshVipMemberAudit(false, "ALL"); }}
                  startIcon={<Users size={16} />}
                >
                  Tất cả ({vipMemberAuditCounts.all})
                </Button>
                <Button
                  variant={vipMemberAuditRiskType === "NO_ORDER" ? "contained" : "outlined"}
                  size="small"
                  onClick={() => { setVipMemberAuditRiskType("NO_ORDER"); void refreshVipMemberAudit(false, "NO_ORDER"); }}
                  startIcon={<Ticket size={16} />}
                >
                  Chỉ không có đơn ({vipMemberAuditCounts.noOrder})
                </Button>
                <Button
                  variant={vipMemberAuditRiskType === "EXPIRED_ORDER" ? "contained" : "outlined"}
                  size="small"
                  onClick={() => { setVipMemberAuditRiskType("EXPIRED_ORDER"); void refreshVipMemberAudit(false, "EXPIRED_ORDER"); }}
                  startIcon={<Clock3 size={16} />}
                >
                  Chỉ hết hạn ({vipMemberAuditCounts.expired})
                </Button>
              </div>
              <SimpleTable
                headers={["Khách", "Telegram ID", "Group", "Lý do", "Đơn gần nhất", "Hạn", "Live", "Cập nhật"]}
                rows={vipMemberAuditFiltered.map((item) => [
                  <><strong>{item.customer_name || "-"}</strong><div className="muted">{item.latest_event_type || "-"}</div></>,
                  item.telegram_user_id,
                  <><strong>{item.group_name || "-"}</strong><div className="muted">{item.group_id}</div></>,
                  <><strong>{item.risk_label}</strong><div className="muted">{item.risk_type}</div></>,
                  <><strong>{item.order_id || "-"}</strong><div className="muted">{item.latest_order_status || "-"}</div></>,
                  dateText(item.expire_at || ""),
                  item.live_checked ? (item.live_present ? "Có mặt" : "Không còn") : "Chưa live",
                  <><div>{dateText(item.latest_event_at) || "-"}</div><div className="muted">{item.live_status || ""}</div></>,
                ])}
              />
            </section>
            <section className="panel">
              <PanelHead
                title="Đơn lệch tên group"
                subtitle="Các đơn đang báo lỗi map group hoặc không còn khớp BTN_G/ID_G. Bảng này hiển thị luôn alias gợi ý để sửa nhanh trong CP."
                action={<Button variant="outlined" size="small" onClick={() => refreshVipGroupAudit(true)} startIcon={<RefreshCw size={16} />}>Quét lại</Button>}
              />
              <SimpleTable
                headers={["Khách", "Đơn", "Gói", "Group hiện tại", "Alias / gợi ý", "Lỗi"]}
                rows={vipGroupAuditMismatchRows.map((item) => item.row)}
                actions={(idx) => {
                  const item = vipGroupAuditMismatchRows[idx];
                  if (!item?.targetGroupNo) return null;
                  return (
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={(event) => { event.stopPropagation(); openGroupAliasEditor(item.targetGroupNo); }}
                      startIcon={<Settings size={14} />}
                    >
                      Sửa alias
                    </Button>
                  );
                }}
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
                    <Button variant="outlined" size="small" onClick={handleWebhookClearMaintenance} disabled={webhookCooldownSeconds > 0} startIcon={<ShieldCheck size={16} />}>Clear maintenance</Button>
                    <Button variant="contained" size="small" onClick={handleWebhookReset} disabled={webhookCooldownSeconds > 0} startIcon={<RefreshCw size={16} />}>Reset webhook</Button>
                  </div>
                }
              />
              <div className="system-list">
                <Info label="Webhook URL" value={webhook?.url || "Chưa cấu hình"} icon={<Activity size={16} />} />
                <Info label="Update đang chờ" value={String(webhook?.pending_update_count ?? 0)} icon={<BadgePercent size={16} />} />
                <Info label="Lỗi gần nhất" value={webhook?.last_error_message || "Không có"} icon={<XCircle size={16} />} />
                <Info label="Webhook health" value={webhookMeta?.maintenance_override?.active ? `Bảo trì do webhook: ${webhookMeta.maintenance_override.reason || "Không rõ nguyên nhân"}` : webhookMeta?.problem_reason ? `Có lỗi: ${webhookMeta.problem_reason}` : "Healthy"} icon={<ShieldCheck size={16} />} />
                <Info label="Failure streak" value={String(webhookMeta?.failure_streak ?? 0)} icon={<RefreshCw size={16} />} />
                <Info label="Webhook cooldown" value={webhookCooldownLabel} icon={<Clock3 size={16} />} />
              </div>
              {webhookCooldownSeconds > 0 ? (
                <div className="overview-health-card warning" style={{ marginTop: 12 }}>
                  <strong>Webhook đang cooldown</strong>
                  <span>Backend đang chặn reset webhook thêm để tránh spam `SetWebhook`. Còn lại khoảng {webhookCooldownSeconds} giây trước khi có thể reset hoặc clear maintenance an toàn.</span>
                </div>
              ) : null}
            </section>
            <section className="panel">
              <PanelHead title="Raw config" subtitle="Chỉ dùng khi cần kiểm tra sâu. Các form phía trên đã che key kỹ thuật." />
              <SimpleTable headers={["Tên kỹ thuật", "Giá trị"]} rows={config.map((item) => [item.key, item.value])} />
            </section>
          </div>
        ) : null}

        {tab === "license" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead
                title="License control center"
                subtitle="Quản lý flow license, map plan -> group, template deep link và message mặc định."
              />
              <div className="grid" style={{ padding: "0 16px 16px" }}>
                <Metric label="Licenses" value={String(licenses.length)} accent="blue" icon={<ShieldCheck size={16} />} />
                <Metric label="Sessions" value={String(licenseSessions.length)} accent="cyan" icon={<Clock3 size={16} />} />
                <Metric label="Audit logs" value={String(licenseAudits.length)} accent="emerald" icon={<ClipboardList size={16} />} />
                <Metric label="Config keys" value={String(LICENSE_FIELDS.length)} accent="amber" icon={<Settings size={16} />} />
              </div>
              <Tabs value="config" textColor="inherit" indicatorColor="primary" sx={{ px: 2, py: 1.5 }}>
                <Tab value="config" label="Templates & mapping" />
                <Tab value="records" label={`Records (${licenses.length})`} />
                <Tab value="sessions" label={`Sessions (${licenseSessions.length})`} />
                <Tab value="audits" label={`Audit (${licenseAudits.length})`} />
              </Tabs>
            </section>
            <section className="panel">
              <ConfigEditor
                title="License templates & mapping"
                subtitle="Chỉnh trực tiếp flow license: bật/tắt, deep link, JSON map plan -> groups và các message mặc định."
                fields={LICENSE_FIELDS}
                values={fieldValues}
                setValues={setFieldValues}
                onSave={saveFields}
              />
            </section>
            <section className="panel">
              <PanelHead title="License records" subtitle="Record chính từ bảng licenses." />
              <SimpleTable
                headers={["License", "Plan", "User", "Status", "Expire", "Source"]}
                rows={licenses.map((item) => [
                  item.license_key,
                  item.plan_code,
                  item.telegram_user_id,
                  item.status,
                  item.expires_at || "-",
                  item.source,
                ])}
              />
            </section>
            <section className="panel">
              <PanelHead title="License sessions" subtitle="Lượt verify / activate được bot ghi vào runtime." />
              <SimpleTable
                headers={["License", "User", "Plan", "Status", "Action", "Verified"]}
                rows={licenseSessions.map((item) => [
                  item.license_key,
                  item.telegram_user_id,
                  item.plan_code || "-",
                  item.status,
                  item.action,
                  item.verified_at || item.created_at,
                ])}
              />
            </section>
            <section className="panel">
              <PanelHead title="License audit" subtitle="Nhật ký license: verify, activate, expired, revoked, reminder." />
              <SimpleTable
                headers={["License", "User", "Event", "Plan", "Result", "Time"]}
                rows={licenseAudits.map((item) => [
                  item.license_key,
                  item.telegram_user_id,
                  item.event_type,
                  item.plan_code || "-",
                  item.result || "-",
                  item.created_at,
                ])}
              />
            </section>
          </div>
        ) : null}

        {comboSettingsOpen ? (
          <MuiDialogShell
            open
            title={comboSettingsVariant === "30d" ? "Combo 30 Ngày" : "Combo Trọn Đời"}
            subtitle="Bấm đổi tên hoặc đổi giá đúng card này. Dữ liệu legacy vẫn tương thích qua alias."
            onClose={() => setComboSettingsOpen(false)}
            maxWidth="lg"
          >
            <Box sx={{ borderBottom: 1, borderColor: "divider", px: 0.5, mb: 2 }}>
              <Tabs
                value={comboSettingsTab}
                onChange={(_, next) => setComboSettingsTab(next)}
                textColor="inherit"
                indicatorColor="primary"
                variant="fullWidth"
                sx={{ minHeight: 42, "& .MuiTab-root": { minHeight: 42, fontWeight: 800 } }}
              >
                <Tab value="price" label="Giá" />
                <Tab value="name" label="Tên & alias" />
              </Tabs>
            </Box>
            {comboSettingsTab === "price" ? (
              <ConfigEditor
                title={comboSettingsVariant === "30d" ? "Cài đặt giá Combo 30 ngày" : "Cài đặt giá Combo trọn đời"}
                subtitle="Giá VNĐ dùng PayOS/VietQR, giá USD dùng PayPal."
                fields={comboSettingsVariant === "30d" ? COMBO_PRICE_FIELDS.filter((field) => ["PRICE_COMBO_30D", "PRICE_COMBO_30D_USD"].includes(field.key)) : COMBO_PRICE_FIELDS.filter((field) => ["PRICE_COMBO_LIFE", "PRICE_COMBO_LIFE_USD"].includes(field.key))}
                values={fieldValues}
                setValues={setFieldValues}
                onSave={saveFields}
              />
            ) : (
              <ConfigEditor
                title={comboSettingsVariant === "30d" ? "Đổi tên Combo 30 ngày" : "Đổi tên Combo trọn đời"}
                subtitle="Sửa tên hiển thị và alias tương thích. Dữ liệu cũ vẫn chạy bằng alias legacy."
                fields={PLAN_VI_FIELDS.filter((field) => comboSettingsVariant === "30d" ? ["PLAN_COMBO_30D", "PLAN_COMBO_30D_ALIASES"].includes(field.key) : ["PLAN_COMBO_LIFE", "PLAN_COMBO_LIFE_ALIASES"].includes(field.key))}
                values={fieldValues}
                setValues={setFieldValues}
                onSave={saveFields}
              />
            )}
            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", pt: 1 }}>
              <Button variant="outlined" onClick={() => setComboSettingsOpen(false)}>Đóng</Button>
            </Stack>
          </MuiDialogShell>
        ) : null}

        {specialGroupSettingsOpen ? (
          <SettingsConfigModal
            title="Cài đặt tin nhắn Special Group"
            subtitle="Toàn bộ text VI/EN hiển thị khi khách nhập mã special, gặp lỗi, hoặc không đủ điều kiện mở khóa."
            fields={[...HIDDEN_MESSAGE_FIELDS, ...HIDDEN_MESSAGE_EN_FIELDS]}
            values={fieldValues}
            setValues={setFieldValues}
            onSave={saveFields}
            onClose={() => setSpecialGroupSettingsOpen(false)}
          />
        ) : null}

        {groupModalOpen ? (
          <MuiDialogShell
            open
            title={`Cấu hình nhóm G${groupNo}`}
            subtitle="Tên nhóm, group ID và giá bán được lưu tập trung tại đây."
            onClose={() => setGroupModalOpen(false)}
            maxWidth="md"
            actions={
              <>
                <Button variant="outlined" onClick={() => setGroupModalOpen(false)}>Đóng</Button>
                <Button variant="outlined" color="error" onClick={removeGroupConfig} disabled={saving === "group-delete"} startIcon={<Trash2 size={16} />}>Xoá nhóm</Button>
                <Button variant="contained" onClick={saveGroupConfig} disabled={saving === "group"} startIcon={saving === "group" ? <Loader2 size={16} className="spin" /> : <Save size={16} />}>Lưu nhóm</Button>
              </>
            }
          >
            <Box sx={{ p: 2 }}>
              <div className="form-grid">
                <TextField
                  className="field"
                  label="Nhóm cần cấu hình"
                  value={groupNo}
                  onChange={(event) => loadGroupForm(event.target.value)}
                  placeholder="Nhập số nhóm, ví dụ 5 hoặc 12"
                  helperText="Nhập số nhóm để sửa hoặc tạo mới. Bấm chip bên dưới để chọn nhanh nhóm đã có."
                  fullWidth
                  size="small"
                  sx={popupFieldSx}
                  slotProps={{ htmlInput: { inputMode: "numeric", pattern: "[0-9]*" } }}
                />
                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75, gridColumn: "1 / -1", mt: -0.5, mb: 1.5 }}>
                  {groupQuickOptions.map((item) => (
                    <Chip key={item} label={`G${item}${visibleGroups.map(String).includes(item) ? "" : " mới"}`} clickable variant={String(groupNo) === String(item) ? "filled" : "outlined"} color={String(groupNo) === String(item) ? "primary" : "default"} onClick={() => fillGroupForm(item)} />
                  ))}
                </Box>
                <TextField className="field" label="Tên nhóm tiếng Việt" value={groupName} onChange={(event) => setGroupName(event.target.value)} placeholder={getConfigValue(config, `BTN_G${groupNo}`) || "VD: Hang Cú Prime"} fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Tên nhóm tiếng Anh" value={groupNameEn} onChange={(event) => setGroupNameEn(event.target.value)} placeholder={getConfigValue(config, `BTN_G${groupNo}_EN`) || "VD: Prime Group"} fullWidth size="small" sx={popupFieldSx} />
                <TextField
                  className="field wide"
                  label="Alias cũ / thủ công"
                  value={groupAliases}
                  onChange={(event) => setGroupAliases(event.target.value)}
                  placeholder="Mỗi alias một dòng hoặc ngăn bằng dấu phẩy"
                  fullWidth
                  multiline
                  minRows={3}
                  size="small"
                  sx={popupFieldSx}
                  inputRef={groupAliasRef}
                  helperText="Dùng để giữ đơn cũ không vỡ khi đổi tên group, và cho phép map lại đơn báo lỗi."
                />
                <TextField className="field" label="Telegram group ID" value={groupId} onChange={(event) => setGroupId(event.target.value)} placeholder={getConfigValue(config, `ID_G${groupNo}`) || "VD: -1001234567890"} fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Giá VNĐ 30 ngày" value={groupPrice1m} onChange={(event) => setGroupPrice1m(normalizeMoneyInput(event.target.value, "VND"))} onBlur={() => setGroupPrice1m(roundMoneyInput(groupPrice1m, "VND"))} placeholder={getConfigValue(config, `PRICE_G${groupNo}_1M`) || "VD: 99000"} fullWidth size="small" sx={popupFieldSx} inputMode="numeric" />
                <TextField className="field" label="Giá VNĐ trọn đời" value={groupPriceLife} onChange={(event) => setGroupPriceLife(normalizeMoneyInput(event.target.value, "VND"))} onBlur={() => setGroupPriceLife(roundMoneyInput(groupPriceLife, "VND"))} placeholder={getConfigValue(config, `PRICE_G${groupNo}_LIFE`) || "VD: 299000"} fullWidth size="small" sx={popupFieldSx} inputMode="numeric" />
                <TextField className="field" label="Giá USD 30 ngày" value={groupPrice1mUsd} onChange={(event) => setGroupPrice1mUsd(normalizeMoneyInput(event.target.value, "USD"))} onBlur={() => setGroupPrice1mUsd(roundMoneyInput(groupPrice1mUsd, "USD"))} placeholder="VD: 4.99" fullWidth size="small" sx={popupFieldSx} inputMode="decimal" />
                <TextField className="field" label="Giá USD trọn đời" value={groupPriceLifeUsd} onChange={(event) => setGroupPriceLifeUsd(normalizeMoneyInput(event.target.value, "USD"))} onBlur={() => setGroupPriceLifeUsd(roundMoneyInput(groupPriceLifeUsd, "USD"))} placeholder="VD: 14.99" fullWidth size="small" sx={popupFieldSx} inputMode="decimal" />
              </div>
            </Box>
          </MuiDialogShell>
        ) : null}

        {hiddenGroupModalOpen ? (
          <MuiDialogShell
            open
            title={hiddenGroupForm.id ? `Special Group: ${hiddenGroupForm.id}` : "Tạo Special Group"}
            subtitle="Thiết lập group đặc biệt ẩn, giá, hạn và điều kiện mua. Không còn phải nhập JSON thủ công."
            onClose={() => setHiddenGroupModalOpen(false)}
            maxWidth="md"
            actions={
              <>
                <Button variant="outlined" onClick={() => setHiddenGroupModalOpen(false)}>Đóng</Button>
                {hiddenGroupForm.id ? <Button variant="outlined" onClick={() => setHiddenGroupForm({ ...hiddenGroupForm, id: hiddenSlug(hiddenGroupForm.name) || hiddenGroupForm.id })} startIcon={<RefreshCw size={16} />}>Tạo lại ID từ tên</Button> : null}
                <Button variant="contained" onClick={saveHiddenGroup} disabled={saving === `hidden-group-${hiddenGroupForm.id || hiddenSlug(hiddenGroupForm.name) || "new"}`} startIcon={saving === `hidden-group-${hiddenGroupForm.id || hiddenSlug(hiddenGroupForm.name) || "new"}` ? <Loader2 size={16} className="spin" /> : <Save size={16} />}>Lưu Special Group</Button>
              </>
            }
          >
            <Box sx={{ p: 2 }}>
              <div className="form-grid">
                <TextField className="field" label="ID kỹ thuật" value={hiddenGroupForm.id} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, id: hiddenSlug(event.target.value) })} placeholder="VD: prime_alpha" fullWidth size="small" sx={popupFieldSx} helperText={<span>Dùng trong plan token dạng <code>HG:prime_alpha:1M</code>. Để trống thì hệ thống tự tạo từ tên.</span>} />
                <TextField className="field" label="Tên hiển thị" value={hiddenGroupForm.name} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, name: event.target.value })} placeholder="VD: Prime Alpha" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Telegram group ID" value={hiddenGroupForm.chat_id} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, chat_id: event.target.value })} placeholder="-1001234567890" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field wide" label="Mô tả ngắn" value={hiddenGroupForm.description} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, description: event.target.value })} placeholder="Mô tả nội bộ hoặc nội dung bot dùng để giới thiệu Special Group." fullWidth multiline minRows={4} sx={popupFieldSx} />
                <div className="hint compact wide">Giá duration nào để 0 thì bot sẽ không hiện nút mua duration đó. Nếu chỉ bán trọn đời, để giá 30 ngày VND/USD = 0 và chỉ nhập giá trọn đời.</div>
                <TextField className="field" label="Giá VNĐ 30 ngày" value={hiddenGroupForm.price_1m_vnd} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, price_1m_vnd: normalizeMoneyInput(event.target.value, "VND") })} onBlur={() => setHiddenGroupForm((current) => ({ ...current, price_1m_vnd: roundMoneyInput(current.price_1m_vnd, "VND") }))} inputMode="numeric" placeholder="99000" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Giá VNĐ trọn đời" value={hiddenGroupForm.price_life_vnd} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, price_life_vnd: normalizeMoneyInput(event.target.value, "VND") })} onBlur={() => setHiddenGroupForm((current) => ({ ...current, price_life_vnd: roundMoneyInput(current.price_life_vnd, "VND") }))} inputMode="numeric" placeholder="299000" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Giá USD 30 ngày" value={hiddenGroupForm.price_1m_usd} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, price_1m_usd: normalizeMoneyInput(event.target.value, "USD") })} onBlur={() => setHiddenGroupForm((current) => ({ ...current, price_1m_usd: roundMoneyInput(current.price_1m_usd, "USD") }))} inputMode="decimal" placeholder="4.99" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Giá USD trọn đời" value={hiddenGroupForm.price_life_usd} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, price_life_usd: normalizeMoneyInput(event.target.value, "USD") })} onBlur={() => setHiddenGroupForm((current) => ({ ...current, price_life_usd: roundMoneyInput(current.price_life_usd, "USD") }))} inputMode="decimal" placeholder="14.99" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Hạn 30 ngày (days)" value={hiddenGroupForm.duration_1m_days} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, duration_1m_days: event.target.value })} inputMode="numeric" placeholder="30" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field" label="Hạn trọn đời (days)" value={hiddenGroupForm.lifetime_days} onChange={(event) => setHiddenGroupForm({ ...hiddenGroupForm, lifetime_days: event.target.value })} inputMode="numeric" placeholder="3650" fullWidth size="small" sx={popupFieldSx} helperText="Mặc định đồng bộ 10 năm = 3650 ngày." />
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
            </Box>
          </MuiDialogShell>
        ) : null}

        {hiddenCodeModalOpen ? (
          <MuiDialogShell
            open
            title={hiddenCodeForm.code ? `Special Code: ${hiddenCodeForm.code}` : "Tạo Special Code"}
            subtitle="Mã reveal catalog Special Group. Có thể giới hạn group, điều kiện và khoảng thời gian sử dụng."
            onClose={() => setHiddenCodeModalOpen(false)}
            maxWidth="md"
            actions={
              <>
                <Button variant="outlined" onClick={() => setHiddenCodeModalOpen(false)}>Đóng</Button>
                <Button variant="outlined" onClick={() => setHiddenCodeForm({ ...hiddenCodeForm, code: hiddenCodeSeed(hiddenCodeForm.name || hiddenCodeForm.description || "hidden-code") })} startIcon={<RefreshCw size={16} />}>Gợi ý mã từ tên</Button>
                <Button variant="contained" onClick={saveHiddenCode} disabled={saving === `hidden-code-${(hiddenCodeForm.code.trim() || hiddenCodeSeed(hiddenCodeForm.name)).toUpperCase()}`} startIcon={saving === `hidden-code-${(hiddenCodeForm.code.trim() || hiddenCodeSeed(hiddenCodeForm.name)).toUpperCase()}` ? <Loader2 size={16} className="spin" /> : <Save size={16} />}>Lưu Special Code</Button>
              </>
            }
          >
            <Box sx={{ p: 2 }}>
              <Box sx={{ display: "grid", gap: 1.5 }}>
                <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" } }}>
                  <TextField className="field" label="Mã special" value={hiddenCodeForm.code} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, code: event.target.value.toUpperCase().replace(/\s+/g, "-") })} placeholder="VD: PRIME-ALPHA" fullWidth size="small" sx={popupFieldSx} helperText="Bot chỉ hiện Special catalog cho người nhập đúng mã này." />
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
                      {HIDDEN_SCOPE_OPTIONS.map((item) => <MenuItem key={item.value} value={item.value}>{item.label.replace(/hidden/gi, "Special")}</MenuItem>)}
                    </Select>
                  </FormControl>
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="hidden-code-requirement-label">Điều kiện override</InputLabel>
                    <Select labelId="hidden-code-requirement-label" label="Điều kiện override" value={hiddenCodeForm.requirement_type} onChange={(event) => setHiddenCodeForm({ ...hiddenCodeForm, requirement_type: event.target.value, requirement_value: hiddenRequirementNeedsValue(event.target.value) ? hiddenCodeForm.requirement_value : "" })} sx={popupSelectSx}>
                      <MenuItem value="">Dùng rule của Special Group</MenuItem>
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
                    <strong>Special Groups được reveal</strong>
                    <span className="muted">{hiddenCodeForm.scope_type === "ALL_ACTIVE_HIDDEN_GROUPS" ? "Đang áp dụng cho mọi Special Group active." : `${hiddenCodeForm.group_ids.length} group đã chọn`}</span>
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
                    ) : <div className="empty-card">Cần tạo Special Group trước khi gán cho Special Code.</div>
                  ) : (
                    <div className="hint compact">Code này sẽ tự reveal toàn bộ Special Group đang bật, nên không cần chọn group thủ công.</div>
                  )}
                </div>
              </Box>
            </Box>
          </MuiDialogShell>
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
          <MuiDialogShell
            open
            title={menuForm.page_id ? `Menu: ${menuForm.page_id}` : "Thêm trang menu"}
            subtitle={menuLanguage === "en" ? "Trang tiếng Anh bắt buộc kết thúc bằng _en." : "Trang tiếng Việt không dùng hậu tố _en."}
            onClose={() => setMenuModalOpen(false)}
            maxWidth="md"
            actions={
              <>
                <Button variant="outlined" onClick={() => setMenuModalOpen(false)}>Đóng</Button>
                <Button variant="outlined" color="error" onClick={() => removeMenuPage()} disabled={!menuForm.page_id} startIcon={<Trash2 size={16} />}>Xoá trang</Button>
                <Button variant="contained" onClick={saveMenuPage} startIcon={<Save size={16} />}>Lưu menu</Button>
              </>
            }
          >
            <Box sx={{ p: 2 }}>
              <div className="form-grid two">
                <TextField className="field" label="Tên trang" value={menuForm.page_id} onChange={(event) => setMenuForm({ ...menuForm, page_id: event.target.value })} placeholder={menuLanguage === "en" ? "VD: main_menu_en, support_page_en" : "VD: main_menu, support_page"} fullWidth size="small" sx={popupFieldSx} helperText={menuLanguage === "en" ? "Trang tiếng Anh bắt buộc có hậu tố _en." : "Trang tiếng Việt không được dùng hậu tố _en."} />
                <TextField className="field" label="Ảnh cover" value={menuForm.image_url} onChange={(event) => setMenuForm({ ...menuForm, image_url: event.target.value })} placeholder="File ID Telegram hoặc URL ảnh" fullWidth size="small" sx={popupFieldSx} />
                <TextField className="field wide" label="Nội dung trang" value={menuForm.body} onChange={(event) => setMenuForm({ ...menuForm, body: event.target.value })} placeholder="Nhập nội dung HTML. Có thể dùng {PRICE_COMBO_30D}, {SALE_LABEL_PRICE_COMBO_30D}..." fullWidth multiline minRows={8} sx={popupFieldSx} />
                <TextField className="field wide" label="Nút bấm" value={menuForm.layout} onChange={(event) => setMenuForm({ ...menuForm, layout: event.target.value })} placeholder={"Mỗi dòng là một hàng nút. Ví dụ:\\nMua Combo => buy_full_1m | Hỗ trợ => nav:support_page"} fullWidth multiline minRows={5} sx={popupFieldSx} helperText={<span>Có thể dùng biến như {"{BTN_BUY_COMBO_30D}"}</span>} />
              </div>
            </Box>
          </MuiDialogShell>
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
                  <Typography variant="caption" color="text.secondary">Chỉ hiện collection đã setup, cộng với Combo.</Typography>
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
          <MuiDialogShell open title={couponForm.Code ? `Mã ${couponForm.Code}` : "Thêm mã"} subtitle="Tạo mã giảm giá, mã kích hoạt hoặc gen nhiều mã cùng điều kiện trong popup này." onClose={() => setCouponModalOpen(false)} maxWidth="lg">
              <Box sx={{ display: "grid", gap: 1.5 }}>
                <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap", alignItems: "center", px: 2, pt: 1.5 }}>
                  <Button variant="outlined" onClick={generateCouponCode} startIcon={<RefreshCw size={16} />}>Gen mã HANGCU_</Button>
                  <TextField value={couponBatchCount} onChange={(event) => setCouponBatchCount(event.target.value)} inputMode="numeric" size="small" title="Số lượng mã cần gen cùng điều kiện" sx={{ width: 140 }} />
                  <Button variant="outlined" onClick={generateManyCoupons} startIcon={<RefreshCw size={16} />}>Gen nhiều cùng điều kiện</Button>
                </Stack>
                <Box sx={{ display: "grid", gap: 1.5 }}>
                  <TextField className="field" label="Mã kích hoạt" value={couponForm.Code} onChange={(event) => setCouponForm({ ...couponForm, Code: event.target.value.toUpperCase() })} placeholder="VD: VIP2026" fullWidth size="small" sx={popupFieldSx} />
                  <FormControl className="field" fullWidth size="small">
                    <InputLabel id="coupon-type-label">Loại mã</InputLabel>
                    <Select labelId="coupon-type-label" label="Loại mã" value={couponForm.Coupon_Type} onChange={(event) => setCouponForm({ ...couponForm, Coupon_Type: event.target.value })} sx={popupSelectSx}>
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
                        <Typography variant="caption" color="text.secondary">Chọn một gói cố định, hoặc để khách tự chọn collection lẻ sau khi nhập mã.</Typography>
                      </FormControl>
                      <TextField className="field" label="Số ngày sử dụng" value={lifetimeCouponSelected ? lifetimeCouponDays : couponForm.Duration_Days} onChange={(event) => setCouponForm({ ...couponForm, Duration_Days: event.target.value })} placeholder="VD: 30" disabled={lifetimeCouponSelected} fullWidth size="small" sx={popupFieldSx} helperText={lifetimeCouponSelected ? "Gói trọn đời luôn dùng 10 năm = 3650 ngày." : "Dùng cho mã kích hoạt theo ngày."} />
                      <TextField className="field" label="Nhãn thời hạn" value={couponForm.Duration_Label} onChange={(event) => setCouponForm({ ...couponForm, Duration_Label: event.target.value })} placeholder="VD: 30 ngày, dùng thử, trọn đời" fullWidth size="small" sx={popupFieldSx} helperText={lifetimeCouponSelected ? "Để trống thì bot tự hiện “trọn đời”." : "Để trống thì bot tự dùng “N ngày”."} />
                      <TextField className="field" label="Mẫu tên gói" value={couponForm.Plan_Name_Template} onChange={(event) => setCouponForm({ ...couponForm, Plan_Name_Template: event.target.value })} placeholder="Collection {duration_label} - {group}" fullWidth size="small" sx={popupFieldSx} helperText={<span>Lưu vào đơn và hiện trong tin thành công. Dùng {"{duration_label}"}, {"{days}"}, {"{group}"}.</span>} />
                      <TextField className="field" label="Mẫu nút chọn collection" value={couponForm.Button_Template} onChange={(event) => setCouponForm({ ...couponForm, Button_Template: event.target.value })} placeholder="{plan_name}" fullWidth size="small" sx={popupFieldSx} helperText={<span>Dùng khi khách tự chọn collection. Dùng {"{plan_name}"}, {"{duration_label}"}, {"{group}"}.</span>} />
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
                <Button variant="outlined" color="error" onClick={() => removeCoupon()} disabled={!couponForm.Code} startIcon={<Trash2 size={16} />}>Xoá mã</Button>
                <Button variant="contained" onClick={saveCoupon} startIcon={<Gift size={16} />}>Lưu mã</Button>
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

        <Drawer anchor="right" open={orderEditorOpen} onClose={() => setOrderEditorOpen(false)}>
          <Box sx={{ width: { xs: "100vw", sm: 560 }, maxWidth: "100vw", height: "100%", display: "flex", flexDirection: "column" }}>
            <Box sx={{ p: 2, borderBottom: 1, borderColor: "divider", display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 2 }}>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 800, lineHeight: 1.15 }}>Sửa đơn {orderEditorOrderId}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>Chỉnh nhanh từ bảng đơn, không cần mở modal khách.</Typography>
              </Box>
              <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
                <IconButton onClick={() => copyOrderId(orderEditorOrderId)} title="Copy order ID">
                  <Copy size={18} />
                </IconButton>
                <IconButton onClick={() => setOrderEditorOpen(false)}><XCircle size={20} /></IconButton>
              </Stack>
            </Box>
            <Box sx={{ flex: 1, overflowY: "auto", p: 2, display: "grid", gap: 2 }}>
              <Alert severity={String(orderEditorForm.status || "").toUpperCase() === "PAID" ? "success" : "warning"} variant="outlined">
                {String(orderEditorForm.status || "").toUpperCase() === "PAID"
                  ? "Đơn PAID: có thể chỉnh đầy đủ các trường quan trọng."
                  : "Đơn chưa PAID: ưu tiên sửa trạng thái, tên gói, mã và ghi chú; hạn/paid_at đang khóa để tránh lệch luồng."}
              </Alert>
              <Box sx={{ display: "grid", gap: 1.5, gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" } }}>
                <TextField select label="Trạng thái" value={orderEditorForm.status} onChange={(event) => setOrderEditorForm({ ...orderEditorForm, status: event.target.value })} size="small" fullWidth>
                  <MenuItem value="PENDING">PENDING</MenuItem>
                  <MenuItem value="PAID">PAID</MenuItem>
                  <MenuItem value="CANCELLED">CANCELLED</MenuItem>
                  <MenuItem value="EXPIRED">EXPIRED</MenuItem>
                </TextField>
                <TextField select label="Tiền tệ" value={orderEditorForm.payment_currency} onChange={(event) => setOrderEditorForm({ ...orderEditorForm, payment_currency: event.target.value })} size="small" fullWidth helperText="Chọn tiền tệ để hiển thị và lưu đúng định dạng." >
                  <MenuItem value="VND">VNĐ</MenuItem>
                  <MenuItem value="USD">USD</MenuItem>
                </TextField>
                <TextField
                  label="Tên gói"
                  value={orderEditorForm.plan_name}
                  onChange={(event) => setOrderEditorForm({ ...orderEditorForm, plan_name: event.target.value })}
                  size="small"
                  fullWidth
                  helperText="Tên gói hiển thị trong báo cáo và lịch sử."
                  slotProps={{ input: { ref: orderEditorPlanInputRef } }}
                />
                <TextField
                  label="Số tiền"
                  value={orderEditorForm.amount}
                  onChange={(event) => setOrderEditorForm((current) => ({
                    ...current,
                    amount: normalizeMoneyInput(event.target.value, current.payment_currency || orderEditorForm.payment_currency),
                  }))}
                  onBlur={() => setOrderEditorForm((current) => ({ ...current, amount: roundMoneyInput(current.amount, current.payment_currency) }))}
                  size="small"
                  fullWidth
                  inputMode={normalizeRevenueCurrency(orderEditorForm.payment_currency) === "VND" ? "numeric" : "decimal"}
                  helperText={
                    normalizeRevenueCurrency(orderEditorForm.payment_currency) === "VND"
                      ? `VNĐ tự làm tròn số nguyên. Hiển thị: ${orderEditorAmountPreview()}`
                      : `USD giữ tối đa 2 số lẻ. Hiển thị: ${orderEditorAmountPreview()}`
                  }
                />
                <TextField
                  label="Ngày paid"
                  type="datetime-local"
                  value={orderEditorForm.paid_at}
                  onChange={(event) => setOrderEditorForm({ ...orderEditorForm, paid_at: event.target.value })}
                  size="small"
                  fullWidth
                  slotProps={{ inputLabel: { shrink: true } }}
                  disabled={String(orderEditorForm.status || "").toUpperCase() !== "PAID"}
                  helperText={String(orderEditorForm.status || "").toUpperCase() === "PAID" ? "Dùng khi cần sửa thời điểm ghi nhận đã trả tiền." : "Chỉ mở khi đổi trạng thái sang PAID."}
                />
                <TextField
                  label="Ngày hết hạn"
                  type="datetime-local"
                  value={orderEditorForm.expire_at}
                  onChange={(event) => setOrderEditorForm({ ...orderEditorForm, expire_at: event.target.value })}
                  size="small"
                  fullWidth
                  slotProps={{ inputLabel: { shrink: true } }}
                  disabled={String(orderEditorForm.status || "").toUpperCase() !== "PAID"}
                  helperText={String(orderEditorForm.status || "").toUpperCase() === "PAID" ? "Giữ đồng bộ với thời hạn cấp quyền." : "Chỉ mở khi đơn đã PAID."}
                />
                <TextField label="Mã kích hoạt" value={orderEditorForm.coupon_code} onChange={(event) => setOrderEditorForm({ ...orderEditorForm, coupon_code: event.target.value.toUpperCase() })} size="small" fullWidth helperText="Mã gắn với đơn nếu có." />
                <TextField label="Ghi chú nội bộ" value={orderEditorForm.note} onChange={(event) => setOrderEditorForm({ ...orderEditorForm, note: event.target.value })} size="small" fullWidth multiline minRows={3} helperText="Thông tin riêng cho admin / đối soát." />
              </Box>
              <Box sx={{ p: 1.5, borderRadius: 3, bgcolor: "background.paper", border: 1, borderColor: "divider" }}>
                <Typography sx={{ fontWeight: 800, mb: 1 }}>Lịch sử thay đổi</Typography>
                {orderEditorHistoryRows.length ? (
                  <Stack spacing={1.1} sx={{ position: "relative", pl: 0.5 }}>
                    <Box sx={{ position: "absolute", left: 13, top: 6, bottom: 6, width: 2, borderRadius: 999, bgcolor: "rgba(59,130,246,0.16)" }} />
                    {orderEditorHistoryRows.map((row, idx) => (
                      <Box key={`${row.at}-${idx}`} sx={{ display: "grid", gridTemplateColumns: "18px 1fr", gap: 1, alignItems: "flex-start" }}>
                        <Box sx={{ width: 18, height: 18, mt: 0.35, borderRadius: 999, bgcolor: idx === 0 ? "primary.main" : idx % 2 ? "warning.main" : "success.main", boxShadow: `0 0 0 4px ${idx === 0 ? "rgba(59,130,246,0.10)" : idx % 2 ? "rgba(245,158,11,0.10)" : "rgba(16,185,129,0.10)"}` }} />
                        <Box sx={{ p: 1.25, borderRadius: 2.5, border: 1, borderColor: idx === 0 ? "primary.light" : "divider", bgcolor: idx === 0 ? "rgba(59,130,246,0.04)" : "background.default" }}>
                          <Typography sx={{ fontWeight: 800, lineHeight: 1.2 }}>{row.title}</Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>{row.detail}</Typography>
                          <Typography variant="caption" color="text.secondary">{dateText(row.at)}</Typography>
                        </Box>
                      </Box>
                    ))}
                  </Stack>
                ) : (
                  <Alert severity="info" variant="outlined">Chưa thấy event lịch sử nào khớp order này trong support_events.</Alert>
                )}
              </Box>
            </Box>
            <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end", p: 2, borderTop: 1, borderColor: "divider", bgcolor: "background.paper" }}>
              <Button variant="outlined" onClick={() => setOrderEditorOpen(false)}>Đóng</Button>
              <Button
                variant="contained"
                onClick={saveOrderEditor}
                disabled={saving === `order-edit-${orderEditorOrderId}`}
                startIcon={saving === `order-edit-${orderEditorOrderId}` ? <Loader2 size={16} className="spin" /> : <Save size={16} />}
              >
                Lưu thay đổi
              </Button>
            </Stack>
          </Box>
        </Drawer>

        {renewalSettingsOpen ? (
          <SettingsConfigModal title="Cài đặt gia hạn" subtitle="Bật/tắt nhắc gia hạn, báo hết hạn và nội dung tin nhắn liên quan đến hạn thành viên." fields={RENEWAL_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} onClose={() => setRenewalSettingsOpen(false)} />
        ) : null}

        {securitySettingsOpen ? (
          <SettingsConfigModal title="Bảo mật bot và mã kích hoạt" subtitle="Chặn seller, ẩn menu nhập mã và chống dò mã. Mặc định khách chỉ cần nhắn mã bắt đầu bằng HANGCU_." fields={SECURITY_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={saveFields} onClose={() => setSecuritySettingsOpen(false)} />
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

        {adminReplyOpen && adminReplyTarget ? (
          <MuiDialogShell open title="Trả lời khách từ Nhật ký" subtitle={`${adminReplyTarget.fullName || adminReplyTarget.username || "Khách"} · ${adminReplyTarget.userId}`} onClose={() => setAdminReplyOpen(false)} maxWidth="md">
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
              <SupportThreadPanel
                title="Chat thread"
                threadLabel={`${adminReplyTarget.fullName || adminReplyTarget.username || "Khách"} · ${adminReplyTarget.userId}`}
                messages={adminReplyThreadMessages}
                loading={adminReplyThreadLoading}
                onLoadMore={loadAdminReplyThreadMore}
                loadMoreLabel="Tải thêm tin cũ"
                emptyText={`Tin gần nhất: ${adminReplyTarget.sourceText || "Không có nội dung tin gốc."}`}
                bottomRef={adminReplyThreadBottomRef}
              />
              <TextField
                autoFocus
                label="Nội dung trả lời"
                value={adminReplyText}
                onChange={(event) => setAdminReplyText(event.target.value)}
                placeholder="Nhập tin nhắn sẽ gửi trực tiếp cho khách..."
                fullWidth
                multiline
                minRows={5}
                helperText={`${adminReplyText.trim().length}/3500 ký tự. Tin sẽ gửi bằng bot qua Telegram.`}
                sx={popupFieldSx}
              />
              <Stack direction="row" spacing={1} sx={{ justifyContent: "flex-end" }}>
                <Button variant="outlined" onClick={() => setAdminReplyOpen(false)}>Đóng</Button>
                <Button variant="contained" onClick={submitAdminReply} disabled={saving === "admin-reply" || !adminReplyText.trim()} startIcon={saving === "admin-reply" ? <Loader2 size={16} className="spin" /> : <Send size={16} />}>
                  Gửi trả lời
                </Button>
              </Stack>
            </Box>
          </MuiDialogShell>
        ) : null}

        {customerQuickLookupOpen ? (
          <MuiDialogShell open title="Tra cứu nhanh khách hàng" subtitle="Search lazy theo Telegram ID hoặc tên, không tải toàn bộ đơn hàng khi mở popup." onClose={() => setCustomerQuickLookupOpen(false)} maxWidth="md">
            <Box sx={{ display: "grid", gap: 1.25 }}>
              <TextField
                autoFocus
                label="Telegram ID hoặc tên khách"
                value={customerQuickLookupQuery}
                onChange={(event) => setCustomerQuickLookupQuery(event.target.value)}
                placeholder="VD: 7344961485 hoặc Minh"
                size="small"
                helperText="Nhập tối thiểu 2 ký tự. Nếu nhập số, backend ưu tiên tìm chính xác Telegram ID để nhanh nhất."
                fullWidth
                onKeyDown={(event) => {
                  if (event.key !== "Enter") return;
                  const lookupId = customerQuickLookupQuery.trim();
                  if (!lookupId) return;
                  event.preventDefault();
                  if (customerQuickLookupResult) {
                    void openQuickLookupPrimaryAction(customerQuickLookupResult.id);
                    return;
                  }
                  if (/^\d+$/.test(lookupId)) openManualOrderFromLookup(lookupId);
                }}
              />
              {customerQuickLookupLoading ? (
                <Alert severity="info" variant="outlined" icon={<Loader2 size={16} className="spin" />}>Đang tra cứu dữ liệu nhỏ từ backend...</Alert>
              ) : null}
              {customerQuickLookupResults.length > 1 ? (
                <Box sx={{ display: "grid", gap: 0.75 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 800 }}>Tìm thấy {customerQuickLookupResults.length} khách, chọn một khách để xem nhanh:</Typography>
                  <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75 }}>
                    {customerQuickLookupResults.slice(0, 8).map((item) => (
                      <Button
                        key={item.id}
                        size="small"
                        variant={customerQuickLookupResult?.id === item.id ? "contained" : "outlined"}
                        onClick={() => setCustomerQuickLookupResults([item, ...customerQuickLookupResults.filter((candidate) => candidate.id !== item.id)])}
                        sx={{ borderRadius: 999, textTransform: "none" }}
                      >
                        {item.name || item.id} · {item.id}
                      </Button>
                    ))}
                  </Box>
                </Box>
              ) : null}
              {customerQuickLookupResult ? (
                <>
                  {customerQuickLookupResult.isBlacklisted ? (
                    <Alert severity="error" variant="outlined" icon={<ShieldCheck size={16} />}>
                      <strong>Khách này đang bị blacklist.</strong> Hệ thống sẽ từ chối phục vụ bot và admin nên cẩn thận trước khi tạo đơn/gia hạn. Lý do: {customerQuickLookupResult.blacklistEntry?.reason || "chưa ghi lý do"}.
                    </Alert>
                  ) : null}
                  <Box
                    sx={{
                      display: "grid",
                      gap: 1,
                      gridTemplateColumns: {
                        xs: "1fr",
                        sm: "repeat(2, minmax(0, 1fr))",
                      },
                    }}
                  >
                    {[
                      {
                        label: "Tên khách",
                        value: customerQuickLookupResult.name || "-",
                        icon: <Users size={15} />,
                        badge: customerQuickLookupResult.isBlacklisted ? "Blacklist" : "",
                        badgeTone: "error" as const,
                      },
                      { label: "Trạng thái", value: customerQuickLookupResult.statusText, icon: <ShieldCheck size={15} /> },
                      { label: "Đã có đơn", value: customerQuickLookupResult.hasPaidOrder ? "Có" : "Chưa", icon: <ClipboardList size={15} /> },
                      { label: "Đang còn hạn", value: customerQuickLookupResult.hasActiveOrder ? "Có" : "Không", icon: <CheckCircle2 size={15} /> },
                    ].map((item) => (
                      <Box
                        key={item.label}
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 1,
                          px: 1.5,
                          py: 1,
                          borderRadius: 2,
                          bgcolor: "rgba(15, 23, 42, 0.03)",
                          border: "1px solid rgba(148, 163, 184, 0.14)",
                        }}
                      >
                        <Box sx={{ width: 28, height: 28, borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: "rgba(37, 99, 235, 0.08)", color: "primary.main", flex: "0 0 auto" }}>
                          {item.icon}
                        </Box>
                        <Box sx={{ minWidth: 0 }}>
                          <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, flexWrap: "wrap" }}>
                            <Typography variant="caption" color="text.secondary" sx={{ display: "block", lineHeight: 1.2 }}>
                              {item.label}
                            </Typography>
                            {item.badge ? <Chip size="small" color={item.badgeTone} variant="outlined" label={item.badge} sx={{ height: 18, fontSize: 10.5, fontWeight: 800 }} /> : null}
                          </Box>
                          <Typography variant="body1" sx={{ fontWeight: 700, lineHeight: 1.2, wordBreak: "break-word" }}>
                            {item.value}
                          </Typography>
                        </Box>
                      </Box>
                    ))}
                  </Box>
                  <SimpleTable
                    headers={["Mục", "Giá trị"]}
                    rows={[
                      ["Telegram ID", customerQuickLookupResult.id],
                      ["Số đơn PAID", String(customerQuickLookupResult.paidOrderCount)],
                      ["Số đơn active", String(customerQuickLookupResult.activeOrderCount)],
                      ["Hạn gần nhất", customerQuickLookupResult.latestExpireText],
                      ["Gói gần nhất", customerQuickLookupResult.latestExpireOrder ? (
                        <Box sx={{ minWidth: 0 }}>
                          <Typography sx={{ fontWeight: 700, lineHeight: 1.2 }}>
                            {String(customerQuickLookupResult.latestExpireOrder.plan_name || "-").trim() || "-"}
                          </Typography>
                        </Box>
                      ) : "-"],
                      ["Group gần nhất", customerQuickLookupResult.latestExpireOrder ? groupNamesForOrder(customerQuickLookupResult.latestExpireOrder).join(", ") || "-" : "-"],
                    ]}
                  />
                  <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75, pt: 0.25 }}>
                    <Button
                      variant="contained"
                      onClick={() => void openQuickLookupPrimaryAction(customerQuickLookupResult.id)}
                      startIcon={customerQuickLookupResult.hasActiveOrder ? <RefreshCw size={16} /> : <Plus size={16} />}
                      disabled={customerQuickLookupResult.isBlacklisted}
                      sx={{ borderRadius: 999, px: 2.25, py: 0.9, boxShadow: "none" }}
                    >
                      {customerQuickLookupResult.hasActiveOrder ? "Gia hạn nhanh" : "Tạo đơn mới"}
                    </Button>
                    <Button variant="text" onClick={() => void openCustomerFromLookup(customerQuickLookupResult.id)} startIcon={<Search size={16} />} sx={{ borderRadius: 999, px: 1.75 }}>
                      Mở khách gần nhất
                    </Button>
                    <Button variant="text" onClick={() => void openCustomerRenewFromLookup(customerQuickLookupResult.id)} startIcon={<RefreshCw size={16} />} sx={{ borderRadius: 999, px: 1.75 }} disabled={customerQuickLookupResult.isBlacklisted}>
                      Gia hạn nhanh
                    </Button>
                    <Button variant="text" onClick={() => openManualOrderFromLookup(customerQuickLookupResult.id)} startIcon={<Plus size={16} />} sx={{ borderRadius: 999, px: 1.75 }} disabled={customerQuickLookupResult.isBlacklisted}>
                      Tạo đơn mới
                    </Button>
                    {customerQuickLookupResult.isBlacklisted ? (
                      <Button variant="outlined" color="error" onClick={() => openSecurityTabForCustomer(customerQuickLookupResult.id)} sx={{ borderRadius: 999, px: 1.75 }}>
                        Mở tab blacklist
                      </Button>
                    ) : null}
                  </Box>
                </>
              ) : customerQuickLookupSearched && customerQuickLookupQuery.trim().length >= 2 && !customerQuickLookupLoading ? (
                <>
                  <Alert severity="warning" variant="outlined">Không tìm thấy khách khớp Telegram ID/tên này.</Alert>
                  <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75, pt: 0.25 }}>
                    {/^\d+$/.test(customerQuickLookupQuery.trim()) ? <Button
                      variant="contained"
                      onClick={() => openManualOrderFromLookup(customerQuickLookupQuery.trim())}
                      startIcon={<Plus size={16} />}
                      sx={{ borderRadius: 999, px: 2.25, py: 0.9, boxShadow: "none" }}
                    >
                      Tạo đơn mới
                    </Button> : null}
                  </Box>
                </>
              ) : (
                <Alert severity="info" variant="outlined">Nhập Telegram ID hoặc tên, hệ thống chỉ search phần cần thiết thay vì load toàn bộ đơn hàng.</Alert>
              )}
            </Box>
          </MuiDialogShell>
        ) : null}

        <ManualOrderDialog
          open={manualOrderModalOpen}
          onClose={() => setManualOrderModalOpen(false)}
          saving={saving === "manual-order" || saving === "generate-active-code" || saving === "generate-join-link"}
          onSave={saveManualOrder}
          form={manualOrderForm}
          setForm={setManualOrderForm}
          result={manualOrderResult}
          onGenerateActiveCode={generateManualActiveCodeHandler}
          onGenerateJoinLink={generateManualJoinLinkHandler}
          activeSpecialGroups={activeSpecialGroups}
          configuredGroups={configuredGroups}
          customDurationEnabled={customDurationEnabled}
          manualPlanKeyOptions={manualPlanKeyOptions}
          manualPlanNameFromKey={manualPlanNameFromKey}
          hiddenGroupManualPrice={hiddenGroupManualPrice}
          hiddenGroupManualPlanName={hiddenGroupManualPlanName}
          onChangePlanKey={changeManualPlanKey}
          onChangeSpecialGroup={changeManualSpecialGroup}
          onCopy={(value) => navigator.clipboard.writeText(stripHtml(value || ""))}
        />

        {customerModalOpen && selectedCustomer ? (
          <MuiDialogShell open title={selectedCustomer.name} subtitle={`Telegram ID: ${selectedCustomer.id}`} onClose={() => setCustomerModalOpen(false)} maxWidth="xl">
              <Box sx={{ display: "flex", gap: 2, alignItems: "stretch", minHeight: "72vh", flexDirection: { xs: "column", md: "row" } }}>
	                <Box
	                  component="aside"
	                  sx={{
                    width: { xs: "100%", md: 320 },
                    flexShrink: 0,
                    display: "flex",
                    flexDirection: "column",
                    gap: 2,
                    p: 2,
                    border: 1,
                    borderColor: "rgba(148, 163, 184, 0.15)",
                    bgcolor: "rgba(255, 255, 255, 0.6)",
                    backdropFilter: "blur(12px)",
                    borderRadius: 3,
                    boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05), inset 0 1px 0 rgba(255, 255, 255, 0.6)",
	                  }}
	                >
	                  <Tabs
	                    orientation="vertical"
	                    value={customerDetailTab}
	                    onChange={(_, next) => setCustomerDetailTab(next)}
	                    textColor="inherit"
	                    indicatorColor="primary"
	                    sx={{
	                      ...customerPopupTabSx,
	                      "& .MuiTab-root": {
	                        borderRadius: 2,
	                        mb: 0.5,
	                        justifyContent: "flex-start",
	                        textAlign: "left",
	                        padding: "10px 16px",
	                      },
	                      "& .Mui-selected": {
	                        bgcolor: "var(--primary)",
	                        color: "white !important",
	                        boxShadow: "0 4px 10px rgba(59,130,246,0.3)",
	                      }
	                    }}
	                  >
	                    <Tab value="orders" label="Đơn hàng" iconPosition="start" icon={<CreditCard size={16} />} sx={{ minHeight: 44 }} />
	                    <Tab value="groups" label="Nhóm active" iconPosition="start" icon={<Users size={16} />} sx={{ minHeight: 44 }} />
	                    <Tab value="timeline" label="Dấu vết" iconPosition="start" icon={<Activity size={16} />} sx={{ minHeight: 44 }} />
	                  </Tabs>

	                  <Box sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
	                    {selectedCustomerIsBlacklisted ? (
	                      <Box sx={{ p: 1.5, borderRadius: 2.5, bgcolor: "error.lighter", border: 1, borderColor: "error.light" }}>
                        <Typography variant="subtitle2" color="error.main" sx={{ fontWeight: 800, display: "flex", alignItems: "center", gap: 0.5 }}>
                          <XCircle size={16} /> Khách bị Blacklist
                        </Typography>
                        <Typography variant="caption" color="error.main" sx={{ display: "block", mt: 0.5 }}>Lý do: {selectedCustomerBlacklistEntry?.reason || "chưa ghi rõ"}</Typography>
                      </Box>
                    ) : null}

                    {/* Compact Metrics Grid */}
                    <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
                      <Box sx={{ p: 1.5, borderRadius: 2.5, bgcolor: "background.paper", border: 1, borderColor: "divider", boxShadow: "0 2px 4px rgba(0,0,0,0.02)" }}>
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Đơn PAID</Typography>
                        <Typography sx={{ fontWeight: 800, fontSize: 20, color: "var(--ink)", lineHeight: 1 }}>{selectedCustomer.paidOrders.length}</Typography>
                      </Box>
                      <Box sx={{ p: 1.5, borderRadius: 2.5, bgcolor: "background.paper", border: 1, borderColor: "divider", boxShadow: "0 2px 4px rgba(0,0,0,0.02)" }}>
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Đang active</Typography>
                        <Typography sx={{ fontWeight: 800, fontSize: 20, color: "var(--ink)", lineHeight: 1 }}>{selectedCustomer.activeOrders.length}</Typography>
                      </Box>
                      <Box sx={{ p: 1.5, borderRadius: 2.5, bgcolor: "background.paper", border: 1, borderColor: "divider", boxShadow: "0 2px 4px rgba(0,0,0,0.02)" }}>
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Hạn gần nhất</Typography>
                        <Typography sx={{ fontWeight: 800, fontSize: 16, color: "var(--ink)", mt: 0.5 }}>{dateTextShort(selectedCustomer.latestExpire)}</Typography>
                      </Box>
                      <Box sx={{ p: 1.5, borderRadius: 2.5, bgcolor: "background.paper", border: 1, borderColor: "divider", boxShadow: "0 2px 4px rgba(0,0,0,0.02)" }}>
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Doanh thu</Typography>
                        <Typography sx={{ fontWeight: 800, fontSize: 16, color: "var(--primary)", mt: 0.5 }}>{formatDisplayCurrency(Number(selectedCustomer.revenue || 0), "VND")}</Typography>
                      </Box>
                    </Box>

                    {/* Attention Point */}
                    <Box sx={{ p: 1.5, borderRadius: 2.5, background: "linear-gradient(135deg, #eff6ff 0%, #e0e7ff 100%)", border: 1, borderColor: "rgba(59,130,246,0.2)" }}>
                      <Typography variant="caption" color="primary.main" sx={{ fontWeight: 800, textTransform: "uppercase", letterSpacing: 0.5 }}>Gợi ý Gia Hạn</Typography>
                      <Typography sx={{ fontWeight: 700, fontSize: 14, color: "var(--ink)", mt: 0.5 }}>
                        {selectedCustomerRenewTargetOrder ? selectedCustomerRenewTargetOrder.plan_name : "Khách chưa có đơn gợi ý"}
                      </Typography>
                      {selectedCustomerRenewTargetOrder ? (
                        <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.25 }}>
                          Đơn gốc: {selectedCustomerRenewTargetOrder.order_id}
                        </Typography>
                      ) : null}
                    </Box>

                    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.75, mt: 0.5 }}>
                      {selectedCustomer.groups.length ? renderLimitedTags(selectedCustomer.groups, "g") : null}
                      {selectedCustomer.coupons.length ? renderLimitedTags(selectedCustomer.coupons.map((item) => `Mã: ${item}`), "c") : null}
                    </Box>
                  </Box>

	                  <Box sx={{ flexGrow: 1 }} />
	                </Box>

	              <Box component="section" sx={{ flex: 1, minWidth: 0, p: 0, display: "flex", flexDirection: "column" }}>
	                {/* Sleek Header Bar */}
	                <Box sx={{ display: "flex", flexWrap: "wrap", gap: 2, alignItems: "center", justifyContent: "space-between", mb: 2.5, p: 2, borderRadius: 3, background: "rgba(255,255,255,0.5)", border: 1, borderColor: "divider", backdropFilter: "blur(10px)" }}>
                  <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                    <Chip
                      label={selectedCustomer.statusLabel}
                      size="small"
                      sx={{ ...statusChipSx(selectedCustomer.statusColor === "default" ? "muted" : (selectedCustomer.statusColor as "success" | "warning" | "error" | "muted" | "purple")), fontWeight: 800, height: 28, px: 1 }}
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500, display: { xs: "none", sm: "block" } }}>
                      {selectedCustomerIsBlacklisted ? "Khách đang bị Blacklist." : selectedCustomer.activeOrders.length ? "Khách đang Active." : "Khách chưa có quyền Active."}
                    </Typography>
                  </Box>
                  <Stack direction="row" spacing={1.5}>
                    <Button variant="outlined" onClick={openCustomerRenewModal} sx={{ borderRadius: 999, px: 2, bgcolor: "background.paper" }}>
                      Gia hạn
                    </Button>
                    <Button variant="contained" startIcon={<Plus size={16} />} onClick={openCustomerCreateOrderModal} sx={{ borderRadius: 999, px: 2, boxShadow: "0 4px 12px rgba(59,130,246,0.3)" }}>
                      Tạo đơn mới
                    </Button>
                  </Stack>
                </Box>
                {customerDetailTab === "orders" ? (
                  <>
                    <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: { xs: "1fr 1fr", lg: "repeat(4, minmax(0, 1fr))" }, mb: 1.5 }}>
                      <Metric label="Đơn hôm nay" value={String(selectedCustomerOrders.filter((item) => isWithinPeriod(item.created_at, "today")).length)} accent="blue" icon={<CalendarClock size={16} />} />
                      <Metric label="Đơn tháng này" value={String(selectedCustomerOrders.filter((item) => isWithinPeriod(item.created_at, "month")).length)} accent="cyan" icon={<BarChart3 size={16} />} />
                      <Metric label="Đã thanh toán" value={String(selectedCustomerOrders.filter((item) => item.status === "PAID").length)} accent="emerald" icon={<CheckCircle2 size={16} />} />
                      <Metric label="Trạng thái còn lại" value={String(selectedCustomerOrders.filter((item) => item.status !== "PAID").length)} accent="amber" icon={<Activity size={16} />} />
                    </Box>
                    <Tabs
                      value={customerOrderTab}
                      onChange={(_, next) => setCustomerOrderTab(next)}
                      variant="scrollable"
                      scrollButtons="auto"
                      textColor="inherit"
                      indicatorColor="primary"
                      sx={{ ...customerPopupTabSx, mb: 2 }}
                    >
                      <Tab value="paid" label={`Đã thanh toán (${selectedCustomerOrders.filter((item) => item.status === "PAID").length})`} />
                      <Tab value="other" label={`Trạng thái còn lại (${selectedCustomerOrders.filter((item) => item.status !== "PAID").length})`} />
                    </Tabs>
                    <CustomerOrdersTable
                      orders={selectedCustomerOrders.filter((item) => {
                        if (customerOrderTab === "paid") return item.status === "PAID";
                        if (customerOrderTab === "other") return item.status !== "PAID";
                        return item.status === "PAID";
                      })}
                      saving={saving}
                      onExpireChange={changeOrderExpire}
                      onPlanChange={changeOrderPlan}
                      onNoteChange={changeOrderNote}
                      onStatusChange={changeOrderStatus}
                    />
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
                      <Tab value="role" label="Quyền" />
                      <Tab value="restricted" label="Hạn chế" />
                      <Tab value="kickMute" label="Kick/Mute" />
                      <Tab value="orders" label="Order timeline" />
                    </Tabs>
                    <Box sx={{ display: "grid", gap: 1, gridTemplateColumns: { xs: "1fr 1fr", lg: "repeat(4, minmax(0, 1fr))" }, mb: 1.5 }}>
                      <Metric label="Tổng sự kiện" value={String(selectedCustomerTimelineCounts.total)} accent="blue" icon={<Activity size={16} />} />
                      <Metric label="Join" value={String(selectedCustomerTimelineCounts.joined)} accent="emerald" icon={<Plus size={16} />} />
                      <Metric label="Left" value={String(selectedCustomerTimelineCounts.left)} accent="amber" icon={<TrendingUp size={16} />} />
                      <Metric label="Kick / mute" value={`${selectedCustomerTimelineCounts.kicked} / ${selectedCustomerTimelineCounts.muted}`} accent="rose" icon={<XCircle size={16} />} />
                    </Box>
                    <section className="panel nested-panel" style={{ borderRadius: "20px" }}>
                      <PanelHead title="Timeline group" subtitle="Lịch sử join / out / mute / kick / nhắc gia hạn của khách theo dữ liệu bot theo dõi được." />
                      <SimpleTable
                        headers={["Sự kiện", "Group", "Đơn", "Giờ", "Chi tiết"]}
                        rows={selectedCustomerTimelineRows.slice(0, 12)}
                      />
                    </section>
                  </>
	                ) : null}
	                {customerDetailTab === "groups" ? (
	                  <>
	                    <section className="panel nested-panel" style={{ marginBottom: 16, borderRadius: "20px" }}>
	                      <PanelHead title="Nhóm còn active" subtitle="Danh sách group user vẫn còn quyền, ưu tiên nhìn nhanh khi rà soát." />
	                      {selectedCustomerActiveGroups.length ? (
	                        <div
	                          className="tag-list"
	                          style={{
	                            display: "flex",
	                            flexWrap: "wrap",
	                            gap: "10px",
	                            padding: "6px 0 2px",
	                          }}
	                        >
	                          {selectedCustomerActiveGroups.map((group) => (
	                            <span
	                              key={group}
	                              style={{
	                                fontSize: "14px",
	                                fontWeight: 800,
	                                padding: "10px 14px",
	                                borderRadius: "999px",
	                                background: "linear-gradient(135deg, rgba(37,99,235,0.12), rgba(14,165,233,0.08))",
	                                border: "1px solid rgba(37,99,235,0.18)",
	                                color: "#1e3a8a",
	                                boxShadow: "0 8px 18px rgba(37,99,235,0.08)",
	                              }}
	                            >
	                              {group}
	                            </span>
	                          ))}
	                        </div>
	                      ) : <div className="empty-card">Chưa có nhóm active nào.</div>}
	                    </section>
	                  </>
	                ) : null}
	                {customerDetailTab === "timeline" ? (
	                  <>
	                    <section className="panel nested-panel" style={{ borderRadius: "20px" }}>
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
              {selectedCustomerIsBlacklisted ? <Alert severity="error" variant="outlined">Khách này đang blacklist. Lý do: {selectedCustomerBlacklistEntry?.reason || "chưa ghi lý do"}.</Alert> : null}
              <TextField
                select
                label="Đơn / Gói cần gia hạn"
                value={customerRenewForm.plan_name}
                onChange={(event) => {
                  syncCustomerRenewPlan(event.target.value);
                }}
                fullWidth
                size="small"
              >
                {selectedCustomerRenewPlanOptions.map((plan) => <MenuItem key={plan} value={plan}>{plan}</MenuItem>)}
              </TextField>
              <Alert severity={isLifetimeText(customerRenewForm.plan_name) ? "warning" : "info"} variant="outlined">
                {isLifetimeText(customerRenewForm.plan_name)
                  ? "Đây là gói trọn đời nên số ngày sẽ luôn = 0. Nếu đang muốn gia hạn 30 ngày, hãy chọn lại gói 30 ngày."
                  : "Đây là gói theo ngày. Hệ thống sẽ tự set số ngày gia hạn mặc định theo gói đang chọn."}
              </Alert>
              <TextField
                label="Số tiền thanh toán"
                value={customerRenewForm.amount}
                onChange={(event) => setCustomerRenewForm((current) => ({ ...current, amount: normalizeMoneyInput(event.target.value, current.payment_currency) }))}
                onBlur={() => setCustomerRenewForm((current) => ({ ...current, amount: roundMoneyInput(current.amount, current.payment_currency) }))}
                placeholder="99000"
                fullWidth
                size="small"
                inputMode={normalizeRevenueCurrency(customerRenewForm.payment_currency) === "VND" ? "numeric" : "decimal"}
                helperText={normalizeRevenueCurrency(customerRenewForm.payment_currency) === "VND" ? "VNĐ tự làm tròn số nguyên." : "USD giữ tối đa 2 số lẻ."}
              />
              <TextField
                label="Số ngày gia hạn"
                type="number"
                value={customerRenewForm.duration_days}
                onChange={(event) => setCustomerRenewForm((current) => ({ ...current, duration_days: event.target.value }))}
                slotProps={{ htmlInput: { min: 1, step: 1 } }}
                disabled={isLifetimeText(customerRenewForm.plan_name)}
                helperText={isLifetimeText(customerRenewForm.plan_name) ? "Gói trọn đời không cần nhập số ngày." : "Nhập số ngày cộng thêm cho đơn gia hạn."}
                fullWidth
                size="small"
              />
              <TextField
                label="Ghi chú nội bộ"
                value={customerRenewForm.note}
                onChange={(event) => setCustomerRenewForm((current) => ({ ...current, note: event.target.value }))}
                placeholder="Ví dụ: gia hạn theo yêu cầu khách, đã chốt ngoài bot, cần follow sau..."
                fullWidth
                size="small"
                multiline
                minRows={3}
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
                  <MenuItem value="TRON_USDT">TRON_USDT</MenuItem>
                </TextField>
              </Stack>
              <div className="modal-actions">
                <Button variant="outlined" onClick={() => setCustomerRenewModalOpen(false)}>Huỷ</Button>
                <Button
                  variant="contained"
                  onClick={saveCustomerRenewal}
                  disabled={saving === `customer-renew-${selectedCustomer?.id}`}
                >
                  {saving === `customer-renew-${selectedCustomer?.id}` ? "Đang tạo..." : "Tạo đơn gia hạn"}
                </Button>
              </div>
            </Box>
          </MuiDialogShell>
        ) : null}
        {false ? (
          <>
            <Drawer
              anchor="right"
              open={false}
              onClose={() => undefined}
              slotProps={{
                paper: {
                  sx: {
                    width: { xs: "100vw", sm: 440 },
                    maxWidth: "100vw",
                    borderTopLeftRadius: 24,
                    borderBottomLeftRadius: 24,
                    boxShadow: "0 24px 80px rgba(15, 23, 42, 0.24)",
                    overflow: "hidden",
                  },
                },
              }}
            >
              <Box sx={{ display: "flex", flexDirection: "column", height: "100%", bgcolor: "background.default" }}>
                <Box sx={{ p: 2.25, borderBottom: 1, borderColor: "divider", background: "linear-gradient(135deg, rgba(37,99,235,0.12), rgba(99,102,241,0.12))" }}>
                  <Stack direction="row" spacing={1.25} sx={{ alignItems: "center", justifyContent: "space-between" }}>
                    <Box>
                      <Typography variant="h6" sx={{ fontWeight: 900, lineHeight: 1.1 }}>Thông báo</Typography>
                      <Typography variant="body2" color="text.secondary">
                        {unreadAdminNotificationCount} mục mới · đơn auto-paid và tin nhắn private
                      </Typography>
                    </Box>
                    <Badge badgeContent={unreadAdminNotificationCount} color="primary" overlap="circular">
                      <Box sx={{ width: 44, height: 44, borderRadius: "50%", display: "grid", placeItems: "center", bgcolor: "rgba(37,99,235,0.14)", color: "primary.main" }}>
                        <BellRing size={20} />
                      </Box>
                    </Badge>
                  </Stack>
                  <Stack direction="row" spacing={1} sx={{ mt: 1.5, flexWrap: "wrap" }}>
                    <Chip size="small" label={`Đơn mới: ${visibleAdminNotifications.filter((item) => item.kind === "order").length}`} variant="outlined" />
                    <Chip size="small" label={`Tin nhắn: ${visibleAdminNotifications.filter((item) => item.kind === "message").length}`} variant="outlined" />
                    <Chip size="small" label={`Quét mỗi ${notificationPollSeconds}s`} variant="outlined" />
                  </Stack>
                </Box>
                <Box sx={{ p: 1.5, display: "grid", gap: 1, overflowY: "auto", flex: 1 }}>
                  <Button
                    variant="contained"
                    onClick={markAllNotificationsRead}
                    sx={{ borderRadius: 999, alignSelf: "flex-start", textTransform: "none", fontWeight: 800 }}
                  >
                    Đánh dấu tất cả đã đọc
                  </Button>
                  {visibleAdminNotifications.map((item) => (
                    <Card
                      key={item.id}
                      variant="outlined"
                      sx={{
                        borderRadius: 4,
                        boxShadow: "0 10px 24px rgba(15, 23, 42, 0.05)",
                        borderColor: item.kind === "order" ? "rgba(59,130,246,0.22)" : "rgba(16,185,129,0.22)",
                        background: item.kind === "order" ? "linear-gradient(180deg, rgba(239,246,255,0.9), rgba(255,255,255,0.98))" : "linear-gradient(180deg, rgba(236,253,245,0.9), rgba(255,255,255,0.98))",
                      }}
                    >
                      <CardContent sx={{ display: "flex", gap: 1.25, py: 1.5, "&:last-child": { pb: 1.5 } }}>
                        <Box
                          sx={{
                            width: 36,
                            height: 36,
                            borderRadius: "50%",
                            display: "grid",
                            placeItems: "center",
                            flexShrink: 0,
                            bgcolor: item.kind === "order" ? "rgba(59,130,246,0.14)" : "rgba(16,185,129,0.14)",
                            color: item.kind === "order" ? "primary.main" : "success.main",
                          }}
                        >
                          {item.kind === "order" ? <ClipboardList size={18} /> : <MessageSquare size={18} />}
                        </Box>
                        <Box sx={{ minWidth: 0, flex: 1 }}>
                          <Typography sx={{ fontWeight: 900, lineHeight: 1.2 }}>{item.title}</Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.4, lineHeight: 1.45 }}>
                            {item.detail || "-"}
                          </Typography>
                          <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.5 }}>
                            {dateText(item.created_at)}
                            {item.plan_name ? ` · ${resolveOrderLabel({ plan_name: item.plan_name }).displayLabel}` : ""}
                          </Typography>
                        </Box>
                      </CardContent>
                    </Card>
                  ))}
                  {!visibleAdminNotifications.length ? (
                    <Alert severity="info" variant="outlined">Chưa có thông báo phù hợp với bộ lọc hiện tại.</Alert>
                  ) : null}
                </Box>
              </Box>
            </Drawer>
          </>
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
        borderRadius: "16px",
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

  function displayFieldValue(field: ConfigField) {
    const currentValue = String(values[field.key] || "").trim();
    if (!currentValue) return "Chưa thiết lập";
    if (field.kind === "multiselect") {
      const selected = new Set(currentValue.split(",").map((item) => item.trim()).filter(Boolean));
      return (field.options || []).filter((item) => selected.has(item.value)).map((item) => item.label).join(", ") || currentValue;
    }
    if (field.kind === "select") {
      return field.options?.find((item) => item.value === currentValue)?.label || currentValue;
    }
    return currentValue;
  }

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
              {displayFieldValue(field)}
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
              ) : editingField.kind === "multiselect" ? (
                <Stack spacing={1}>
                  {(editingField.options || []).map((item) => {
                    const selected = new Set(draftValue.split(",").map((part) => part.trim()).filter(Boolean));
                    const checked = selected.has(item.value);
                    return (
                      <FormControlLabel
                        key={item.value}
                        control={
                          <Checkbox
                            checked={checked}
                            onChange={(event) => {
                              const next = new Set(draftValue.split(",").map((part) => part.trim()).filter(Boolean));
                              if (event.target.checked) {
                                next.add(item.value);
                              } else {
                                next.delete(item.value);
                              }
                              setDraftValue(Array.from(next).join(","));
                            }}
                          />
                        }
                        label={item.label}
                      />
                    );
                  })}
                  <Typography variant="caption" color="text.secondary">
                    Các giá trị được lưu dưới dạng CSV: {editingField.options?.map((item) => item.value).join(", ")}
                  </Typography>
                </Stack>
              ) : editingField.kind === "select" ? (
                <TextField
                  select
                  autoFocus
                  value={draftValue}
                  onChange={(event) => setDraftValue(event.target.value)}
                  fullWidth
                  sx={popupFieldSx}
                >
                  <MenuItem value="" disabled>
                    Chưa thiết lập
                  </MenuItem>
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

function CustomerOrdersTable({ orders, saving, onExpireChange, onPlanChange, onNoteChange, onStatusChange }: { orders: Order[]; saving: string; onExpireChange: (orderId: string, expireAt: string) => void; onPlanChange: (orderId: string, planName: string) => void; onNoteChange: (orderId: string, note: string) => void; onStatusChange: (orderId: string, status: string) => void }) {
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
    return (safeDateMillis(b.created_at) ?? 0) - (safeDateMillis(a.created_at) ?? 0);
  });
  const [expandedOrders, setExpandedOrders] = useState<Record<string, boolean>>({});
  const statusChip = (order: Order) => {
    const normalized = String(order.status || "").toUpperCase();
    const active = isOrderActive(order);
    const expiringSoon = daysUntil(order.expire_at) >= 0 && daysUntil(order.expire_at) <= 3;
    return <Chip size="small" label={orderLifecycleLabel(order)} variant="outlined" sx={customerOrderStateChipSx(normalized, active, expiringSoon)} />;
  };
  return (
    <Stack spacing={1}>
      {sorted.map((order) => (
        (() => {
          const canEdit = String(order.status || "").toUpperCase() === "PAID";
          const orderLabel = resolveOrderLabel(order);
          const cardSx = canEdit
            ? undefined
            : {
                opacity: 0.72,
                filter: "grayscale(0.95)",
                bgcolor: "#f8fafc",
                borderColor: "divider",
                "&:hover": {
                  transform: "none",
                  boxShadow: "0 14px 30px rgba(15, 23, 42, 0.04)",
                  borderColor: "divider",
                },
              };
          return (
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
            ...cardSx,
          }}
        >
          <CardContent sx={{ p: 1.5, "&:last-child": { pb: 1.5 } }}>
            <Box sx={{ display: "flex", flexDirection: { xs: "column", sm: "row" }, gap: 2, alignItems: { sm: "center" } }}>
              {/* Cột 1: ID & Status */}
              <Box sx={{ flexShrink: 0, width: { sm: 160 }, display: "flex", flexDirection: "column", gap: 0.5 }}>
                <Typography sx={{ fontWeight: 900, lineHeight: 1.2, color: "var(--ink)", display: "flex", alignItems: "center", gap: 0.5 }}>
                  <ClipboardList size={14} color="var(--primary)" /> {order.order_id}
                </Typography>
                <Typography variant="body2" color="text.secondary">{dateText(order.created_at)}</Typography>
                <Box>{statusChip(order)}</Box>
              </Box>

              {/* Cột 2: Gói & Nhóm */}
              <Box sx={{ flexGrow: 1, minWidth: 0, pl: { sm: 2 }, borderLeft: { sm: "1px dashed rgba(148, 163, 184, 0.3)" }, display: "flex", flexDirection: "column", gap: 0.5 }}>
                <Tooltip title={orderLabel.showTechLabel ? `Kỹ thuật: ${orderLabel.techLabel}` : orderLabel.displayLabel} arrow>
                  <Box sx={{ minWidth: 0 }}>
                    <Typography sx={{ fontWeight: 800, lineHeight: 1.2, color: "var(--ink)", display: "block", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                      {orderLabel.displayLabel}
                    </Typography>
                  </Box>
                </Tooltip>
                <Typography variant="body2" color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: 0.75, flexWrap: "wrap" }}>
                  <Users size={14} /> {groupNamesForOrder(order).join(", ") || orderPlanKind(order)}
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ display: "flex", alignItems: "center", gap: 0.75, flexWrap: "wrap", mt: 0.25 }}>
                  <Ticket size={14} /> {orderCouponCode(order) ? <span style={{ color: "var(--amber)", fontWeight: 700 }}>{orderCouponCode(order)} (-{orderAmountValue(order) === 0 ? "Free" : orderMoney(order, order.coupon_discount_amount)})</span> : "Không mã"}
                </Typography>
              </Box>

              {/* Cột 3: Hạn & Action */}
              <Box sx={{ flexShrink: 0, display: "flex", flexDirection: "column", gap: 1, alignItems: { xs: "flex-start", sm: "flex-end" }, pl: { sm: 2 }, borderLeft: { sm: "1px dashed rgba(148, 163, 184, 0.3)" } }}>
                <Box sx={{ display: "flex", gap: 0.5 }}>
                  <Chip size="small" label={currencyLabel(inferOrderCurrency(order))} variant="outlined" sx={{ ...statusChipSx("purple"), height: 22, fontSize: 11 }} />
                  <Chip size="small" label={providerLabel(inferOrderProvider(order))} variant="outlined" sx={{ ...statusChipSx("warning"), height: 22, fontSize: 11 }} />
                  {isLifetimeText(order.plan_name) ? <Chip size="small" label="Trọn đời" variant="outlined" sx={{ ...statusChipSx("purple"), height: 22, fontSize: 11 }} /> : null}
                </Box>
                <Typography sx={{ fontWeight: 700, fontSize: 13, color: "text.secondary", mt: -0.25 }}>Hạn: {dateText(order.expire_at)}</Typography>
                <Button variant={expandedOrders[order.order_id] ? "contained" : "outlined"} color="inherit" size="small" onClick={() => setExpandedOrders((current) => ({ ...current, [order.order_id]: !current[order.order_id] }))} sx={{ fontWeight: 700, textTransform: "none", borderRadius: 4, minWidth: 90, height: 26, py: 0 }}>
                  {expandedOrders[order.order_id] ? "Thu gọn" : "Chi tiết"}
                </Button>
              </Box>
            </Box>

            <Box sx={{ display: expandedOrders[order.order_id] ? "grid" : "none", gap: 1, gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" }, pt: 0.25 }}>
              <Box sx={customerInnerCardSx}>
                <Typography variant="body2" color="text.secondary">Sửa tên gói</Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: "center" }}>
                  <TextField defaultValue={order.plan_name} id={`plan-${order.order_id}`} size="small" fullWidth sx={customerPopupInputSx} disabled={!canEdit} helperText={!canEdit ? "Chỉ xem vì đơn chưa PAID." : ""} />
                  <Button variant="contained" size="small" disabled={!canEdit || saving === `order-plan-${order.order_id}`} onClick={() => {
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
                  <Typography variant="caption" color="text.secondary">{canEdit ? "Chỉ xem nhanh, không chỉnh ở đây." : "Đơn chưa PAID nên chỉ theo dõi, không chỉnh sửa."}</Typography>
                </Box>
              </Box>

              <Box sx={customerInnerCardSx}>
                <Typography variant="body2" color="text.secondary">Cập nhật hạn</Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: "center" }}>
                  <TextField type="datetime-local" defaultValue={orderExpireValue(order.expire_at)} id={`expire-${order.order_id}`} size="small" fullWidth sx={customerPopupInputSx} slotProps={{ inputLabel: { shrink: true } }} disabled={!canEdit} helperText={!canEdit ? "Chỉ xem vì đơn chưa PAID." : ""} />
                  <Button variant="contained" size="small" disabled={!canEdit || saving === `order-expire-${order.order_id}`} onClick={() => {
                    const input = document.getElementById(`expire-${order.order_id}`) as HTMLInputElement | null;
                    onExpireChange(order.order_id, input?.value || "");
                  }} sx={{ borderRadius: 4, minWidth: 84 }}>Lưu hạn</Button>
                </Stack>
              </Box>

              <Box sx={{ ...customerInnerCardSx, gridColumn: { xs: "1 / -1", md: "1 / -1" } }}>
                <Typography variant="body2" color="text.secondary">Ghi chú nội bộ</Typography>
                <Stack direction="row" spacing={1} sx={{ mt: 1, alignItems: "flex-start" }}>
                  <TextField defaultValue={orderNoteText(order)} id={`note-${order.order_id}`} size="small" fullWidth multiline minRows={2} sx={customerPopupInputSx} placeholder="Ví dụ: khách quen, cần follow riêng, đổi gói theo yêu cầu..." />
                  <Button variant="contained" size="small" disabled={saving === `order-note-${order.order_id}`} onClick={() => {
                    const input = document.getElementById(`note-${order.order_id}`) as HTMLInputElement | HTMLTextAreaElement | null;
                    onNoteChange(order.order_id, input?.value || "");
                  }} sx={{ borderRadius: 4, minWidth: 84 }}>Lưu note</Button>
                </Stack>
              </Box>
            </Box>
          </CardContent>
        </Card>
          );
        })()
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
              <td>{group.stats.revenueByCurrency ? Object.entries(group.stats.revenueByCurrency).map(([currency, value]) => formatDisplayCurrency(Number(value || 0), currency)).join(" + ") : formatDisplayCurrency(Number(group.stats.revenue || 0), "VND")}</td>
              <td>{group.stats.paid}</td>
              <td>{group.stats.pending}</td>
              <td>{group.stats.cancelled + group.stats.expired}</td>
              <td>{group.stats.customers}</td>
              <td>{group.stats.averageByCurrency ? Object.entries(group.stats.averageByCurrency).map(([currency, value]) => formatDisplayCurrency(Number(value || 0), currency)).join(" + ") : formatDisplayCurrency(Number(group.stats.averageOrder || 0), "VND")}</td>
              <td>{group.stats.discountByCurrency ? Object.entries(group.stats.discountByCurrency).map(([currency, value]) => formatDisplayCurrency(Number(value || 0), currency)).join(" + ") : formatDisplayCurrency(Number(group.stats.discount || 0), "VND")}</td>
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
