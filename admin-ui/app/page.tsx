"use client";

import {
  Activity,
  BadgePercent,
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

type Tab = "overview" | "setup" | "orders" | "content" | "coupons" | "sales" | "system";
type ContentSubTab = "bot" | "plans" | "messages" | "menu";

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

const EMPTY_COUPON_FORM = {
  Code: "",
  Coupon_Type: "DISCOUNT",
  Plan_Name: "G1_1M",
  Duration_Days: "30",
  Discount_Percent: "10",
  Applies_To: "ALL",
  Max_Uses: "1",
  Enabled: "ON",
};

function money(value: number) {
  return new Intl.NumberFormat("vi-VN").format(value || 0) + "đ";
}

function dateText(value: string | null | undefined) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("vi-VN", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
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
    [...BOT_FIELDS, ...MESSAGE_FIELDS, ...PLAN_FIELDS].forEach((field) => {
      nextValues[field.key] = getConfigValue(config, field.key);
    });
    setFieldValues(nextValues);
  }, [config]);

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
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "Không tải được dữ liệu.");
    } finally {
      setLoading(false);
    }
  }

  function login() {
    window.localStorage.setItem("prive_admin_secret", secret);
    setSavedSecret(secret);
    loadAll(secret);
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

  async function removeCoupon(code = couponForm.Code) {
    if (!code || !window.confirm(`Xoá coupon "${code}"? Lịch sử đã dùng vẫn được giữ riêng trong hệ thống.`)) return;
    await runAction(`coupon-delete-${code}`, async () => {
      await deleteCoupon(savedSecret, code);
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
      return matchQuery && matchStatus;
    });
  }, [orders, query, orderStatus]);

  function planOptionLabel(value: string) {
    if (value === "FULL_1M") return "SVIP chung - 1 tháng";
    if (value === "FULL_LIFE") return "SVIP chung - trọn đời";
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
          <section className="panel">
            <PanelHead title="Đơn hàng" subtitle="Theo dõi QR, thanh toán, hủy và hết hạn." />
            <div className="toolbar">
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Tìm mã đơn, tên khách, Telegram ID, tên gói..." />
              <select value={orderStatus} onChange={(event) => setOrderStatus(event.target.value)}>
                <option value="ALL">Tất cả trạng thái</option>
                <option value="PENDING">Đang chờ</option>
                <option value="PAID">Đã thanh toán</option>
                <option value="CANCELLED">Đã hủy</option>
                <option value="EXPIRED">Hết hạn</option>
              </select>
            </div>
            <OrdersTable orders={filteredOrders} onStatusChange={changeOrderStatus} saving={saving} />
          </section>
        ) : null}

        {tab === "content" ? (
          <div className="stack">
            <section className="panel content-hub">
              <PanelHead title="Nội dung Bot" subtitle="Tách từng nhóm cấu hình để dễ sửa. Bấm từng tab con bên dưới." />
              <div className="subtabs">
                <button className={contentTab === "bot" ? "active" : ""} onClick={() => setContentTab("bot")}>Cài đặt bot</button>
                <button className={contentTab === "plans" ? "active" : ""} onClick={() => setContentTab("plans")}>Gói & giá</button>
                <button className={contentTab === "messages" ? "active" : ""} onClick={() => setContentTab("messages")}>Tin nhắn</button>
                <button className={contentTab === "menu" ? "active" : ""} onClick={() => setContentTab("menu")}>Menu Builder</button>
              </div>
            </section>
            {contentTab === "bot" ? <ConfigEditor title="Cài đặt bot" subtitle="Bảo trì, nhắc hạn, QR 5 phút và tần suất check thanh toán." fields={BOT_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(BOT_FIELDS)} /> : null}
            {contentTab === "plans" ? <ConfigEditor title="Tên gói và giá SVIP" subtitle="Các gói chung không thuộc nhóm riêng. Nhóm riêng nằm ở Setup nhóm." fields={PLAN_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(PLAN_FIELDS)} /> : null}
            {contentTab === "messages" ? <ConfigEditor title="Tin nhắn tự động" subtitle="Các mẫu tin bot gửi cho khách. Placeholder được ghi rõ dưới từng ô." fields={MESSAGE_FIELDS} values={fieldValues} setValues={setFieldValues} onSave={() => saveFields(MESSAGE_FIELDS)} /> : null}
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
                  <label className="field"><span>Gói cấp cho khách</span><select value={couponForm.Plan_Name} onChange={(event) => setCouponForm({ ...couponForm, Plan_Name: event.target.value })}>{planKeyOptions.map((item) => <option key={item} value={item}>{planOptionLabel(item)}</option>)}</select><small>Chỉ hiện nhóm đã setup, cộng với SVIP chung.</small></label>
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
                  {planKeyOptions.map((item) => {
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
              rows={coupons.map((item) => [
                item.code,
                item.raw_data?.Coupon_Type === "DISCOUNT" ? "Giảm giá" : "Kích hoạt",
                item.raw_data?.Coupon_Type === "DISCOUNT" ? appliesLabel(item.raw_data?.Applies_To) : item.plan_name || "-",
                item.raw_data?.Coupon_Type === "DISCOUNT" ? `${item.raw_data?.Discount_Percent || 0}%` : "-",
                item.status,
                String(item.used_count),
                String(item.max_uses || "-"),
              ])}
              onRow={(idx) => {
                const item = coupons[idx];
                setCouponForm({
                  ...EMPTY_COUPON_FORM,
                  Code: item.code,
                  Coupon_Type: item.raw_data?.Coupon_Type || "ACTIVATION",
                  Plan_Name: item.raw_data?.Plan_Name || item.plan_name || "G1_1M",
                  Duration_Days: item.raw_data?.Duration_Days || "30",
                  Discount_Percent: item.raw_data?.Discount_Percent || "10",
                  Applies_To: item.raw_data?.Applies_To || "ALL",
                  Max_Uses: String(item.max_uses || 1),
                  Enabled: item.status === "ACTIVE" ? "ON" : "OFF",
                });
              }}
              actions={(idx) => (
                <button className="icon-danger" onClick={(event) => { event.stopPropagation(); removeCoupon(coupons[idx].code); }} title="Xoá coupon">
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
