"use client";

import { RefreshCw, Save, Settings, ShoppingCart, Users } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  ConfigRow,
  Order,
  UserRow,
  getConfig,
  getOrders,
  getUsers,
  updateConfig,
  updateOrderStatus,
} from "@/lib/api";

type Tab = "orders" | "users" | "config";

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
  const [editingKey, setEditingKey] = useState("");
  const [editingValue, setEditingValue] = useState("");
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
      const [ordersRes, usersRes, configRes] = await Promise.all([
        getOrders(activeSecret),
        getUsers(activeSecret),
        getConfig(activeSecret),
      ]);
      setOrders(ordersRes.data);
      setUsers(usersRes.data);
      setConfig(configRes.data);
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
      </section>
    </main>
  );
}
