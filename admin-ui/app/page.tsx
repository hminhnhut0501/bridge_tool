"use client";

import { BadgePercent, FileText, RefreshCw, Save, Settings, ShoppingCart, Ticket, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  ConfigRow,
  Coupon,
  MenuPage,
  Order,
  SaleRule,
  UserRow,
  createCoupon,
  getConfig,
  getCoupons,
  getMenuPages,
  getOrders,
  getSaleRules,
  getUsers,
  updateMenuPage,
  updateConfig,
  updateOrderStatus,
  upsertSaleRule,
} from "@/lib/api";

type Tab = "orders" | "users" | "config" | "menu" | "sales" | "coupons";

function money(value: number) {
  return new Intl.NumberFormat("vi-VN").format(value || 0) + "đ";
}

function dateText(value: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

function statusClass(status: string) {
  const normalized = status.toLowerCase();
  if (normalized === "paid") return "status paid";
  if (normalized === "expired") return "status expired";
  return "status pending";
}

export default function Home() {
  const [secret, setSecret] = useState("");
  const [savedSecret, setSavedSecret] = useState("");
  const [tab, setTab] = useState<Tab>("orders");
  const [orders, setOrders] = useState<Order[]>([]);
  const [users, setUsers] = useState<UserRow[]>([]);
  const [config, setConfig] = useState<ConfigRow[]>([]);
  const [menuPages, setMenuPages] = useState<MenuPage[]>([]);
  const [saleRules, setSaleRules] = useState<SaleRule[]>([]);
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [editingKey, setEditingKey] = useState("");
  const [editingValue, setEditingValue] = useState("");
  const [menuForm, setMenuForm] = useState({ page_id: "", image_url: "", body: "", layout: "" });
  const [saleForm, setSaleForm] = useState({ sale_id: "", price_key: "", discount_percent: "", sale_price: "", slot_limit: "", enabled: "ON", start_at: "", end_at: "" });
  const [couponForm, setCouponForm] = useState({ Code: "", Plan_Name: "", Duration_Days: "30", Max_Uses: "1", Enabled: "ON" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem("prive_admin_secret") || "";
    setSavedSecret(stored);
    setSecret(stored);
  }, []);

  async function loadAll(activeSecret = savedSecret) {
    if (!activeSecret) return;
    setLoading(true);
    setError("");
    try {
      const [ordersRes, usersRes, configRes, menuRes, salesRes, couponsRes] = await Promise.all([
        getOrders(activeSecret),
        getUsers(activeSecret),
        getConfig(activeSecret),
        getMenuPages(activeSecret),
        getSaleRules(activeSecret),
        getCoupons(activeSecret),
      ]);
      setOrders(ordersRes.data);
      setUsers(usersRes.data);
      setConfig(configRes.data);
      setMenuPages(menuRes.data);
      setSaleRules(salesRes.data);
      setCoupons(couponsRes.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không tải được dữ liệu");
    } finally {
      setLoading(false);
    }
  }

  function login() {
    window.localStorage.setItem("prive_admin_secret", secret);
    setSavedSecret(secret);
    loadAll(secret);
  }

  async function saveConfig() {
    if (!editingKey) return;
    await updateConfig(savedSecret, editingKey, editingValue);
    setEditingKey("");
    setEditingValue("");
    await loadAll();
  }

  async function saveMenuPage() {
    if (!menuForm.page_id) return;
    await updateMenuPage(savedSecret, menuForm.page_id, menuForm);
    setMenuForm({ page_id: "", image_url: "", body: "", layout: "" });
    await loadAll();
  }

  async function saveSaleRule() {
    if (!saleForm.sale_id || !saleForm.price_key) return;
    await upsertSaleRule(savedSecret, saleForm);
    setSaleForm({ sale_id: "", price_key: "", discount_percent: "", sale_price: "", slot_limit: "", enabled: "ON", start_at: "", end_at: "" });
    await loadAll();
  }

  async function saveCoupon() {
    if (!couponForm.Code || !couponForm.Plan_Name) return;
    await createCoupon(savedSecret, couponForm);
    setCouponForm({ Code: "", Plan_Name: "", Duration_Days: "30", Max_Uses: "1", Enabled: "ON" });
    await loadAll();
  }

  async function changeOrderStatus(orderId: string, status: string) {
    await updateOrderStatus(savedSecret, orderId, status);
    await loadAll();
  }

  const metrics = useMemo(() => {
    const paid = orders.filter((item) => item.status === "PAID").length;
    const pending = orders.filter((item) => item.status === "PENDING").length;
    const revenue = orders
      .filter((item) => item.status === "PAID")
      .reduce((sum, item) => sum + (item.amount || 0), 0);
    return { paid, pending, revenue, users: users.length };
  }, [orders, users]);

  if (!savedSecret) {
    return (
      <main className="login-page">
        <section className="login-panel stack">
          <div>
            <h1>Prive Admin</h1>
            <p className="muted">Nhập ADMIN_SECRET đã cấu hình trên Render.</p>
          </div>
          <label className="field">
            <span>Admin secret</span>
            <input
              type="password"
              value={secret}
              onChange={(event) => setSecret(event.target.value)}
              placeholder="ADMIN_SECRET"
            />
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
        <nav className="nav">
          <button className={tab === "orders" ? "active" : ""} onClick={() => setTab("orders")}>
            <ShoppingCart size={18} /> Đơn hàng
          </button>
          <button className={tab === "users" ? "active" : ""} onClick={() => setTab("users")}>
            <Users size={18} /> Users
          </button>
          <button className={tab === "config" ? "active" : ""} onClick={() => setTab("config")}>
            <Settings size={18} /> Config
          </button>
          <button className={tab === "menu" ? "active" : ""} onClick={() => setTab("menu")}>
            <FileText size={18} /> Menu
          </button>
          <button className={tab === "sales" ? "active" : ""} onClick={() => setTab("sales")}>
            <BadgePercent size={18} /> Sale
          </button>
          <button className={tab === "coupons" ? "active" : ""} onClick={() => setTab("coupons")}>
            <Ticket size={18} /> Coupon
          </button>
        </nav>
      </aside>

      <section className="main">
        <div className="topbar">
          <div>
            <h1 className="title">Dashboard</h1>
            <div className="muted">Quản lý dữ liệu bot từ Supabase qua Render backend.</div>
          </div>
          <button className="btn secondary" onClick={() => loadAll()} disabled={loading}>
            <RefreshCw size={17} /> {loading ? "Đang tải" : "Tải lại"}
          </button>
        </div>

        {error ? <div className="error">{error}</div> : null}

        <div className="grid">
          <div className="card">
            <div className="muted">Doanh thu PAID</div>
            <div className="metric">{money(metrics.revenue)}</div>
          </div>
          <div className="card">
            <div className="muted">Đơn PAID</div>
            <div className="metric">{metrics.paid}</div>
          </div>
          <div className="card">
            <div className="muted">Đơn PENDING</div>
            <div className="metric">{metrics.pending}</div>
          </div>
          <div className="card">
            <div className="muted">Users gần đây</div>
            <div className="metric">{metrics.users}</div>
          </div>
        </div>

        {tab === "orders" ? (
          <section className="panel">
            <div className="panel-head">
              <strong>Đơn hàng</strong>
              <span className="muted">{orders.length} dòng</span>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Mã đơn</th>
                    <th>User</th>
                    <th>Gói</th>
                    <th>Tiền</th>
                    <th>Trạng thái</th>
                    <th>Tạo lúc</th>
                    <th>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {orders.map((order) => (
                    <tr key={order.order_id}>
                      <td>{order.order_id}</td>
                      <td>{order.full_name || order.telegram_user_id}</td>
                      <td>{order.plan_name}</td>
                      <td>{money(order.amount)}</td>
                      <td><span className={statusClass(order.status)}>{order.status}</span></td>
                      <td>{dateText(order.created_at)}</td>
                      <td>
                        <select
                          value={order.status}
                          onChange={(event) => changeOrderStatus(order.order_id, event.target.value)}
                        >
                          <option value="PENDING">PENDING</option>
                          <option value="PAID">PAID</option>
                          <option value="CANCELLED">CANCELLED</option>
                          <option value="EXPIRED">EXPIRED</option>
                        </select>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        {tab === "users" ? (
          <section className="panel">
            <div className="panel-head">
              <strong>Users</strong>
              <span className="muted">{users.length} dòng</span>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Telegram ID</th>
                    <th>Tên</th>
                    <th>Gói gần nhất</th>
                    <th>Trạng thái</th>
                    <th>Hết hạn</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => (
                    <tr key={user.telegram_user_id}>
                      <td>{user.telegram_user_id}</td>
                      <td>{user.full_name || "-"}</td>
                      <td>{user.plan_name}</td>
                      <td><span className={statusClass(user.status)}>{user.status}</span></td>
                      <td>{dateText(user.expire_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        {tab === "config" ? (
          <section className="panel">
            <div className="panel-head">
              <strong>Config</strong>
              <button className="btn" onClick={saveConfig}>
                <Save size={16} /> Lưu config
              </button>
            </div>
            <div className="card stack">
              <label className="field">
                <span>Key</span>
                <input value={editingKey} onChange={(event) => setEditingKey(event.target.value)} placeholder="VD: MSG_DELIVERY" />
              </label>
              <label className="field">
                <span>Value</span>
                <input value={editingValue} onChange={(event) => setEditingValue(event.target.value)} placeholder="Giá trị mới" />
              </label>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Key</th>
                    <th>Value</th>
                    <th>Cập nhật</th>
                  </tr>
                </thead>
                <tbody>
                  {config.map((item) => (
                    <tr
                      key={item.key}
                      onClick={() => {
                        setEditingKey(item.key);
                        setEditingValue(item.value);
                      }}
                    >
                      <td>{item.key}</td>
                      <td>{item.value}</td>
                      <td>{dateText(item.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        {tab === "menu" ? (
          <section className="panel">
            <div className="panel-head">
              <strong>Menu pages</strong>
              <button className="btn" onClick={saveMenuPage}><Save size={16} /> Lưu page</button>
            </div>
            <div className="card stack">
              <label className="field"><span>Page ID</span><input value={menuForm.page_id} onChange={(event) => setMenuForm({ ...menuForm, page_id: event.target.value })} /></label>
              <label className="field"><span>Image URL</span><input value={menuForm.image_url} onChange={(event) => setMenuForm({ ...menuForm, image_url: event.target.value })} /></label>
              <label className="field"><span>Body</span><input value={menuForm.body} onChange={(event) => setMenuForm({ ...menuForm, body: event.target.value })} /></label>
              <label className="field"><span>Layout</span><input value={menuForm.layout} onChange={(event) => setMenuForm({ ...menuForm, layout: event.target.value })} /></label>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Page ID</th><th>Body</th><th>Layout</th><th>Cập nhật</th></tr></thead>
                <tbody>
                  {menuPages.map((item) => (
                    <tr key={item.page_id} onClick={() => setMenuForm({ page_id: item.page_id, image_url: item.image_url || "", body: item.body || "", layout: item.layout || "" })}>
                      <td>{item.page_id}</td><td>{item.body}</td><td>{item.layout}</td><td>{dateText(item.updated_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        {tab === "sales" ? (
          <section className="panel">
            <div className="panel-head">
              <strong>Sale rules</strong>
              <button className="btn" onClick={saveSaleRule}><Save size={16} /> Lưu sale</button>
            </div>
            <div className="card stack">
              <label className="field"><span>Sale ID</span><input value={saleForm.sale_id} onChange={(event) => setSaleForm({ ...saleForm, sale_id: event.target.value })} /></label>
              <label className="field"><span>Price key</span><input value={saleForm.price_key} onChange={(event) => setSaleForm({ ...saleForm, price_key: event.target.value })} /></label>
              <label className="field"><span>Discount %</span><input value={saleForm.discount_percent} onChange={(event) => setSaleForm({ ...saleForm, discount_percent: event.target.value })} /></label>
              <label className="field"><span>Sale price</span><input value={saleForm.sale_price} onChange={(event) => setSaleForm({ ...saleForm, sale_price: event.target.value })} /></label>
              <label className="field"><span>Slot limit</span><input value={saleForm.slot_limit} onChange={(event) => setSaleForm({ ...saleForm, slot_limit: event.target.value })} /></label>
              <label className="field"><span>Enabled</span><select value={saleForm.enabled} onChange={(event) => setSaleForm({ ...saleForm, enabled: event.target.value })}><option value="ON">ON</option><option value="OFF">OFF</option></select></label>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Sale ID</th><th>Price key</th><th>Giảm</th><th>Giá sale</th><th>Slot</th><th>Bật</th></tr></thead>
                <tbody>
                  {saleRules.map((item) => (
                    <tr key={item.sale_id} onClick={() => setSaleForm({ sale_id: item.sale_id, price_key: item.price_key, discount_percent: String(item.discount_percent || ""), sale_price: String(item.sale_price || ""), slot_limit: String(item.slot_limit || ""), enabled: item.enabled ? "ON" : "OFF", start_at: item.starts_at || "", end_at: item.ends_at || "" })}>
                      <td>{item.sale_id}</td><td>{item.price_key}</td><td>{item.discount_percent || "-"}</td><td>{item.sale_price || "-"}</td><td>{item.slot_limit || "-"}</td><td>{item.enabled ? "ON" : "OFF"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}

        {tab === "coupons" ? (
          <section className="panel">
            <div className="panel-head">
              <strong>Coupons</strong>
              <button className="btn" onClick={saveCoupon}><Save size={16} /> Tạo coupon</button>
            </div>
            <div className="card stack">
              <label className="field"><span>Code</span><input value={couponForm.Code} onChange={(event) => setCouponForm({ ...couponForm, Code: event.target.value })} /></label>
              <label className="field"><span>Plan name</span><input value={couponForm.Plan_Name} onChange={(event) => setCouponForm({ ...couponForm, Plan_Name: event.target.value })} /></label>
              <label className="field"><span>Duration days</span><input value={couponForm.Duration_Days} onChange={(event) => setCouponForm({ ...couponForm, Duration_Days: event.target.value })} /></label>
              <label className="field"><span>Max uses</span><input value={couponForm.Max_Uses} onChange={(event) => setCouponForm({ ...couponForm, Max_Uses: event.target.value })} /></label>
              <label className="field"><span>Enabled</span><select value={couponForm.Enabled} onChange={(event) => setCouponForm({ ...couponForm, Enabled: event.target.value })}><option value="ON">ON</option><option value="OFF">OFF</option></select></label>
            </div>
            <div className="table-wrap">
              <table>
                <thead><tr><th>Code</th><th>Plan</th><th>Status</th><th>Used</th><th>Max</th><th>Expire</th></tr></thead>
                <tbody>
                  {coupons.map((item) => (
                    <tr key={item.code} onClick={() => setCouponForm({ Code: item.code, Plan_Name: item.plan_name || "", Duration_Days: item.raw_data?.Duration_Days || "30", Max_Uses: String(item.max_uses || 1), Enabled: item.status === "ACTIVE" ? "ON" : "OFF" })}>
                      <td>{item.code}</td><td>{item.plan_name || "-"}</td><td>{item.status}</td><td>{item.used_count}</td><td>{item.max_uses || "-"}</td><td>{dateText(item.expires_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        ) : null}
      </section>
    </main>
  );
}
