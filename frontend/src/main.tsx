import React, { useCallback, useEffect, useState, useRef } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpRight,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  CircleX,
  Film,
  Image as ImageIcon,
  FileText,
  Copy,
  SlidersHorizontal,
  Clock,
  Database,
  Folder,
  HardDrive,
  Hash,
  LayoutDashboard,
  ListVideo,
  LoaderCircle,
  LockKeyhole,
  LogOut,
  Menu,
  Moon,
  MoreHorizontal,
  Pause,
  Play,
  Plus,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Sun,
  Terminal,
  Trash2,
  TriangleAlert,
  X,
  Zap,
  CloudDownload,
  Activity,
  Grid,
  List,
} from "lucide-react";
import "./style.css";
import "./luminous.css";

type Row = Record<string, any>;
type Page =
  | "dashboard"
  | "sources"
  | "topics"
  | "transfers"
  | "videos"
  | "failed"
  | "storage"
  | "settings"
  | "telegram";
let csrf = "";
let onUnauthorized = () => {};
async function api<T = Row>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method,
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(method !== "GET" ? { "X-CSRF-Token": csrf } : {}),
    },
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });
  const result = await response.json();
  if (!response.ok) {
    if (response.status === 401 && path !== "/auth/login") onUnauthorized();
    const detail =
      typeof result.detail === "string"
        ? result.detail
        : "Thông tin chưa hợp lệ. Kiểm tra lại các trường.";
    throw new Error(detail);
  }
  return result;
}
function useData<T = Row>(url: string | null, refresh = 0, interval = 4000) {
  const [data, setData] = useState<T | null>(null);
  const [dataUrl, setDataUrl] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    let alive = true;
    let request = 0;
    setLoading(true);
    setError("");
    async function load() {
      const current = ++request;
      if (!url) {
        setLoading(false);
        return;
      }
      try {
        const result = await api<T>(url);
        if (alive && current === request) {
          setData(result);
          setDataUrl(url);
          setError("");
        }
      } catch (e) {
        if (alive && current === request) setError((e as Error).message);
      } finally {
        if (alive && current === request) setLoading(false);
      }
    }
    void load();
    const timer = interval ? setInterval(load, interval) : undefined;
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [url, refresh, interval]);
  return { data: dataUrl === url ? data : null, error, loading };
}
function backupFilename(job: Row) {
  return (
    job.remote_path?.split("/").pop() ||
    job.original_filename ||
    `File #${job.message_id || job.id}`
  );
}

function bytes(value = 0) {
  if (!value) return "0 B";
  const units = ["B", "KiB", "MiB", "GiB", "TiB"];
  const i = Math.min(4, Math.floor(Math.log(value) / Math.log(1024)));
  return `${(value / 1024 ** i).toFixed(i > 1 ? 1 : 0)} ${units[i]}`;
}
function relative(stamp?: number) {
  if (!stamp) return "Chưa quét";
  const seconds = Math.max(0, Date.now() / 1000 - stamp);
  return seconds < 60
    ? "Vừa xong"
    : seconds < 3600
      ? `${Math.floor(seconds / 60)} phút trước`
      : `${Math.floor(seconds / 3600)} giờ trước`;
}
const statusNames: Row = {
  QUEUED: "Đang chờ",
  TRANSFERRING: "Đang truyền",
  VERIFYING: "Kiểm tra",
  COMPLETED: "Hoàn tất",
  RETRY_WAIT: "Chờ thử lại",
  FAILED: "Thất bại",
  SKIPPED: "Bỏ qua",
  CANCELLED: "Đã hủy",
};
function Badge({ status }: { status: string }) {
  return (
    <span
      className={`badge ${status.toLowerCase()} ${/hoàn tất|kết nối|connected/i.test(status) ? "success" : /tạm dừng|chờ|nghỉ|sẵn sàng/i.test(status) ? "warning" : /lỗi|failed/i.test(status) ? "error" : /quét|truyền|theo dõi/i.test(status) ? "info" : ""}`}
    >
      <span className="dot" />
      {statusNames[status] || status}
    </span>
  );
}
function Empty({
  icon: Icon = Folder,
  title,
  children,
}: {
  icon?: typeof Folder;
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Icon size={26} />
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
function ErrorBox({ text }: { text: string }) {
  return text ? (
    <div className="error-box" role="alert">
      <TriangleAlert size={16} />
      {text}
    </div>
  ) : null;
}
function Modal({
  title,
  close,
  children,
}: {
  title: string;
  close: () => void;
  children: React.ReactNode;
}) {
  const dialogRef = useRef<HTMLElement>(null);
  const closeRef = useRef(close);
  closeRef.current = close;
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const dialog = dialogRef.current;
    const focusable = () =>
      Array.from(
        dialog?.querySelectorAll<HTMLElement>(
          'button:not(:disabled), input:not(:disabled), select:not(:disabled), a[href], summary, [tabindex="0"]',
        ) || [],
      ).filter((el) => el.getClientRects().length > 0);
    (focusable()[0] || dialog)?.focus();
    const listener = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        closeRef.current();
      }
      if (e.key === "Tab") {
        const items = focusable();
        if (!items.length) {
          e.preventDefault();
          dialog?.focus();
          return;
        }
        if (e.shiftKey && document.activeElement === items[0]) {
          e.preventDefault();
          items.at(-1)?.focus();
        } else if (!e.shiftKey && document.activeElement === items.at(-1)) {
          e.preventDefault();
          items[0].focus();
        }
      }
    };
    window.addEventListener("keydown", listener);
    return () => {
      window.removeEventListener("keydown", listener);
      previous?.focus();
    };
  }, []);
  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <section
        className="modal"
        ref={dialogRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="modal-head">
          <h2>{title}</h2>
          <button className="icon-button" aria-label="Đóng" onClick={close}>
            <X size={20} />
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}
function Pager({
  next,
  history,
  setHistory,
}: {
  next?: number | null;
  history: number[];
  setHistory: (v: number[]) => void;
}) {
  if (history.length === 1 && next == null) return null;
  return (
    <div className="pager">
      <span>Trang {history.length}</span>
      <div>
        <button
          disabled={history.length === 1}
          onClick={() => setHistory(history.slice(0, -1))}
        >
          <ChevronLeft size={15} />
          Trước
        </button>
        <button
          disabled={next == null}
          onClick={() => setHistory([...history, next!])}
        >
          Tiếp
          <ChevronRight size={15} />
        </button>
      </div>
    </div>
  );
}

const navigation: {
  id: Page;
  label: string;
  icon: typeof Folder;
  section?: string;
}[] = [
  {
    id: "dashboard",
    label: "Tổng quan",
    icon: LayoutDashboard,
    section: "BACKUP",
  },
  { id: "sources", label: "Nguồn Telegram", icon: Folder },
  { id: "transfers", label: "Truyền & hàng đợi", icon: ArrowUpRight },
  { id: "videos", label: "Thư viện backup", icon: ListVideo },
  { id: "failed", label: "Cần xử lý", icon: TriangleAlert },
  { id: "storage", label: "Lưu trữ", icon: HardDrive, section: "HỆ THỐNG" },
  { id: "telegram", label: "Kết nối Telegram", icon: Zap },
  { id: "settings", label: "Cài đặt", icon: Settings },
];

function LoginScreen({ login }: { login: (user: string) => void }) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await api("/auth/login", "POST", { username, password });
      csrf = result.csrf;
      setPassword("");
      login(result.username);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login-screen">
      <div className="login-art">
        <div className="brand">
          <div className="brand-mark">
            <LockKeyhole size={24} />
          </div>
          <span>
            vault<span className="brand-light">bridge</span>
          </span>
        </div>
      </div>
      <div className="login-panel">
        <div className="login-form">
          <h2>Chào mừng trở lại</h2>
          <p>Đăng nhập để quản lý Vault Bridge.</p>
          <p className="muted">
            Ứng dụng độc lập sử dụng Telegram API; không phải sản phẩm chính
            thức của Telegram.
          </p>
          <form onSubmit={submit}>
            <label>
              Tài khoản
              <input
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </label>
            <label>
              Mật khẩu
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                maxLength={256}
              />
            </label>
            <ErrorBox text={error} />
            <button className="primary wide" disabled={busy}>
              {busy ? (
                <LoaderCircle className="spin" size={17} />
              ) : (
                <LockKeyhole size={17} />
              )}
              Đăng nhập
            </button>
          </form>
          <div className="setup-note">
            <Terminal size={18} />
            <div>
              Thiết lập lần đầu?<code>telegram-vault init-admin</code>
              <span>Chạy trong terminal local để tạo mật khẩu.</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

function App() {
  const [user, setUser] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);
  const initial = location.hash.slice(1) as Page;
  const [page, setPage] = useState<Page>(
    navigation.some((n) => n.id === initial) || initial === "topics"
      ? initial
      : "dashboard",
  );
  const [refresh, setRefresh] = useState(0);
  const [toast, setToast] = useState("");
  const [mobile, setMobile] = useState(false);
  const [theme, setTheme] = useState(
    localStorage.getItem("vault-theme") || "dark",
  );
  const [selectedSource, setSelectedSource] = useState<number | null>(null);
  const { data: overview, error: overviewError } = useData<Row>(
    user ? "/status" : null,
    refresh,
  );
  useEffect(() => {
    onUnauthorized = () => setUser(null);
    api("/auth/me")
      .then((r) => {
        csrf = r.csrf;
        setUser(r.username);
      })
      .catch(() => {})
      .finally(() => setChecking(false));
  }, []);
  useEffect(() => {
    const changed = () => {
      const next = location.hash.slice(1) as Page;
      if (navigation.some((n) => n.id === next) || next === "topics") {
        setPage(next);
        setMobile(false);
      }
    };
    window.addEventListener("hashchange", changed);
    return () => window.removeEventListener("hashchange", changed);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("vault-theme", theme);
  }, [theme]);
  useEffect(() => {
    if (toast) {
      const id = setTimeout(() => setToast(""), 6000);
      return () => clearTimeout(id);
    }
  }, [toast]);
  const navigate = (id: Page) => {
    setPage(id);
    location.hash = id;
    setMobile(false);
  };
  const action = useCallback(
    async (
      path: string,
      method = "POST",
      body?: unknown,
      message = "Đã cập nhật",
    ) => {
      try {
        await api(path, method, body);
        setRefresh((r) => r + 1);
        setToast(message);
        return true;
      } catch (e) {
        setToast(`Lỗi: ${(e as Error).message}`);
        return false;
      }
    },
    [],
  );
  if (checking)
    return (
      <div className="boot">
        <LockKeyhole />
        <span>Đang mở Vault…</span>
      </div>
    );
  if (!user) return <LoginScreen login={setUser} />;
  const failedCount = overview?.counts?.FAILED?.count || 0;
  const activeCount = overview?.active || 0;
  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobile ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">
            <LockKeyhole size={22} />
          </div>
          <span>
            vault<span className="brand-light">bridge</span>
          </span>
          <button
            className="mobile-only icon-button"
            onClick={() => setMobile(false)}
            aria-label="Đóng menu"
          >
            <X />
          </button>
        </div>
        <nav>
          {navigation.map((item) => (
            <React.Fragment key={item.id}>
              {item.section && <p className="nav-section">{item.section}</p>}
              <button
                className={
                  page === item.id ||
                  (page === "topics" && item.id === "sources")
                    ? "active"
                    : ""
                }
                aria-label={item.label}
                onClick={() => navigate(item.id)}
              >
                <item.icon size={18} />
                <span>{item.label}</span>
                {item.id === "failed" && failedCount > 0 && (
                  <b className="nav-count warning">{failedCount}</b>
                )}
                {item.id === "transfers" && activeCount > 0 && (
                  <b className="nav-count">{activeCount}</b>
                )}
              </button>
            </React.Fragment>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="encryption-note">
            <ShieldCheck size={20} />
            <div>
              Mã hóa luôn bật<small>Nội dung · Tên · Thư mục</small>
            </div>
          </div>
          <div className="user-row">
            <span className="user-avatar">{user[0].toUpperCase()}</span>
            <div>
              {user}
              <small>Quản trị viên</small>
            </div>
            <button
              className="icon-button"
              aria-label="Đăng xuất"
              onClick={async () => {
                if (await action("/auth/logout")) setUser(null);
              }}
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>
      {mobile && (
        <div className="sidebar-scrim" onClick={() => setMobile(false)} />
      )}
      <div className="main-area">
        <header className="topbar">
          <div>
            <button
              className="mobile-only icon-button"
              aria-label="Mở menu"
              onClick={() => setMobile(true)}
            >
              <Menu size={20} />
            </button>
            <span>Vault Bridge</span>
            <ChevronRight size={14} />
            <strong>
              {page === "topics"
                ? "Nguồn / Topics"
                : navigation.find((n) => n.id === page)?.label}
            </strong>
          </div>
          <div className="topbar-right">
            <span
              className={`connection ${overview?.telegram === "connected" ? "good" : ""}`}
            >
              <span className="dot" />
              {overview?.telegram === "connected"
                ? "Telegram đã kết nối"
                : "Telegram chưa kết nối"}
            </span>
            <button
              className="icon-button"
              title="Đổi giao diện sáng/tối"
              aria-label="Đổi giao diện sáng tối"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </header>
        <main className="content">
          {overview?.telegram_mode === "mock" && (
            <div className="demo-banner">
              <Terminal size={16} />
              <span>
                <b>Local test mode.</b> Telegram được mô phỏng; file thực sự đi
                qua rclone crypt trên máy local.
              </span>
              <span className="demo-tag">TEST ROOT</span>
            </div>
          )}
          {overview?.telegram_mode === "real" &&
            overview?.telegram !== "connected" &&
            page !== "telegram" &&
            page !== "dashboard" && (
              <div className="demo-banner">
                <Zap size={16} />
                <span>
                  Telegram chưa kết nối. Đăng nhập tài khoản để bắt đầu backup.
                </span>
                <button onClick={() => navigate("telegram")}>
                  Kết nối ngay
                </button>
              </div>
            )}
          <ErrorBox text={overviewError} />
          {page !== "dashboard" &&
            overview?.transfer_pause_until > Date.now() / 1000 && (
              <div className="demo-banner">
                <Clock size={16} />
                <span>
                  Đang nghỉ giữa các file — còn khoảng{" "}
                  {Math.ceil(
                    overview!.transfer_pause_until - Date.now() / 1000,
                  )}{" "}
                  giây.
                </span>
              </div>
            )}
          {page !== "dashboard" &&
            overview?.telegram_pause_until > Date.now() / 1000 && (
              <div className="error-box">
                <Clock size={16} />
                Telegram FloodWait: chờ đến{" "}
                {new Date(
                  overview!.telegram_pause_until * 1000,
                ).toLocaleTimeString("vi-VN")}
                . Queue được giữ lại.
              </div>
            )}
          {page === "dashboard" && (
            <Dashboard
              overview={overview}
              refresh={refresh}
              navigate={navigate}
            />
          )}
          {page === "sources" && (
            <Sources
              refresh={refresh}
              action={action}
              navigate={navigate}
              openTopics={(id) => {
                setSelectedSource(id);
                navigate("topics");
              }}
              mock={overview?.telegram_mode === "mock"}
            />
          )}
          {page === "topics" && (
            <Topics
              selected={selectedSource}
              select={setSelectedSource}
              refresh={refresh}
              action={action}
            />
          )}
          {(page === "transfers" || page === "failed" || page === "videos") && (
            <Jobs page={page} refresh={refresh} action={action} />
          )}
          {page === "storage" && <Storage refresh={refresh} action={action} />}
          {page === "telegram" && <TelegramConnection navigate={navigate} />}
          {page === "settings" && (
            <SettingsPage refresh={refresh} action={action} />
          )}
        </main>
      </div>
      {toast && (
        <div
          className={`toast ${toast.startsWith("Lỗi:") ? "bad" : ""}`}
          role="status"
        >
          {toast.startsWith("Lỗi:") ? (
            <TriangleAlert size={17} />
          ) : (
            <Check size={17} />
          )}
          {toast}
          <button
            className="icon-button"
            aria-label="Đóng thông báo"
            onClick={() => setToast("")}
          >
            <X size={15} />
          </button>
        </div>
      )}
    </div>
  );
}

type Action = (
  path: string,
  method?: string,
  body?: unknown,
  message?: string,
) => Promise<boolean>;
function Heading({
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="page-heading">
      <div>
        <h1>{title}</h1>
        {description && <p className="heading-description">{description}</p>}
      </div>
      <div className="heading-actions">{children}</div>
    </div>
  );
}
function CooldownWidget({
  now,
  overview,
  telegramWait,
  driveWait,
  rest,
}: {
  now: number;
  overview: Row | null;
  telegramWait: boolean;
  driveWait: boolean;
  rest: boolean;
}) {
  const deadline = telegramWait
    ? overview?.telegram_pause_until || 0
    : driveWait
      ? overview?.storage_pause_until || 0
      : overview?.transfer_pause_until || 0;
  const remainingSec = Math.max(0, Math.ceil(deadline - now));
  const totalSeconds = telegramWait ? 20 : driveWait ? 60 : 70;
  const progressRatio = Math.min(1, Math.max(0, remainingSec / totalSeconds));
  const circumference = 2 * Math.PI * 26;
  const strokeDashoffset = circumference * (1 - progressRatio);

  const title = telegramWait
    ? "Telegram Cooldown"
    : driveWait
      ? "Lưu trữ tạm nghỉ"
      : "Nghỉ an toàn bảo vệ tài khoản";

  const desc = telegramWait
    ? "Telegram DC yêu cầu giảm tần suất truy xuất (rate-limit). Hệ thống đang đếm ngược để tự động tiếp tục an toàn."
    : driveWait
      ? "Google Drive đang áp dụng hạn mức API tạm thời. Hệ thống tự động tiếp tục sau đếm ngược."
      : "Tự động giãn cách thời gian giữa các file đã tải để bảo vệ tài khoản Telegram khỏi thuật toán kiểm duyệt.";

  const toneClass = telegramWait ? "tone-amber" : driveWait ? "tone-amber" : "tone-purple";

  return (
    <div className={`cooldown-card ${toneClass}`}>
      <div className="cooldown-ring-wrapper">
        <svg className="cooldown-svg" width="66" height="66" viewBox="0 0 66 66">
          <circle className="cooldown-bg-circle" cx="33" cy="33" r="26" />
          <circle
            className="cooldown-fg-circle"
            cx="33"
            cy="33"
            r="26"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
          />
        </svg>
        <div className="cooldown-number">
          <strong>{remainingSec}</strong>
          <small>giây</small>
        </div>
      </div>
      <div className="cooldown-text">
        <div className="cooldown-badge">
          <span className="pulse-beacon" />
          {title}
        </div>
        <p>{desc}</p>
      </div>
    </div>
  );
}

function VideoCard({
  job,
  onDetail,
  onCopyPath,
}: {
  job: Row;
  onDetail: () => void;
  onCopyPath: () => void;
}) {
  return (
    <article className="video-card">
      <div className="video-card-top">
        <div className="video-glyph-box">
          <Film size={20} />
        </div>
        <div className="video-card-badges">
          <span className="size-badge">{bytes(job.size)}</span>
          <span className="verified-badge" title="Đã đối chiếu SHA-256 toàn vẹn">
            <Check size={11} /> Đã kiểm tra
          </span>
        </div>
      </div>
      <div className="video-card-content">
        <h4 title={backupFilename(job)} onClick={onDetail}>
          {backupFilename(job)}
        </h4>
        <div className="video-card-tags">
          <span className="source-tag" title={job.source_name}>
            {job.source_name}
          </span>
          {job.topic_name && (
            <span className="topic-tag" title={job.topic_name}>
              {job.topic_name}
            </span>
          )}
        </div>
      </div>
      <div className="video-card-footer">
        <time>{relative(job.completed_at || job.created_at)}</time>
        <div className="video-card-actions">
          <button
            className="icon-button"
            title="Sao chép đường dẫn Google Drive"
            onClick={onCopyPath}
          >
            <Copy size={14} />
          </button>
          <button
            className="icon-button"
            title="Xem chi tiết kỹ thuật"
            onClick={onDetail}
          >
            <CircleHelp size={14} />
          </button>
        </div>
      </div>
    </article>
  );
}

function Dashboard({
  overview,
  refresh,
  navigate,
}: {
  overview: Row | null;
  refresh: number;
  navigate: (p: Page) => void;
}) {
  const { data: jobs } = useData("/transfers", refresh);
  const { data: events } = useData("/events?limit=40", refresh);
  const { data: sources } = useData("/sources", refresh);
  const { data: storage } = useData("/storage/status", refresh);
  const { data: settings } = useData("/settings", refresh);
  const [now, setNow] = useState(Date.now() / 1000);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now() / 1000), 1000);
    return () => clearInterval(timer);
  }, []);
  const counts = overview?.counts || {};
  const active: Row[] = jobs?.items || [];
  const downloading = active.filter((j) => j.status === "TRANSFERRING").length;
  const verifying = active.filter((j) => j.status === "VERIFYING").length;
  const queued = (counts.QUEUED?.count || 0) + (counts.RETRY_WAIT?.count || 0);
  const failed = counts.FAILED?.count || 0;
  const remaining = (deadline: number) => {
    const seconds = Math.max(0, Math.ceil((deadline || 0) - now));
    return `${Math.floor(seconds / 60)
      .toString()
      .padStart(2, "0")}:${(seconds % 60).toString().padStart(2, "0")}`;
  };
  const rest = (overview?.transfer_pause_until || 0) > now;
  const driveWait = (overview?.storage_pause_until || 0) > now;
  const telegramWait = (overview?.telegram_pause_until || 0) > now;
  let status = downloading
    ? `Đang tải ${downloading} file`
    : verifying
      ? `Đang xác minh ${verifying} file`
      : queued
        ? "Đang chờ lượt tải tiếp theo"
        : "Sẵn sàng backup";
  if (downloading && verifying) status += ` · Xác minh ${verifying} file`;
  if (rest && !active.length) status = "Đang nghỉ giữa các file";
  if (rest)
    status += ` · File tiếp theo sau ${remaining(overview!.transfer_pause_until)}`;
  if (driveWait)
    status = `Lưu trữ đang tạm nghỉ · Thử lại sau ${remaining(overview!.storage_pause_until)}`;
  if (telegramWait)
    status = `Telegram đang tạm nghỉ · Thử lại sau ${remaining(overview!.telegram_pause_until)}`;
  if (overview?.telegram_mode === "real" && overview?.telegram !== "connected")
    status = "Cần kết nối Telegram để tiếp tục";
  if (overview?.scheduler_paused) status = "Hàng đợi đã tạm dừng";
  const metrics = [
    {
      label: "Đã backup",
      value: (counts.COMPLETED?.count || 0).toLocaleString(),
      sub: bytes(counts.COMPLETED?.bytes),
      icon: ShieldCheck,
      target: "videos",
      tone: "success",
    },
    {
      label: "Đang chờ",
      value: queued.toLocaleString(),
      sub: "file trong hàng đợi",
      icon: Clock,
      target: "transfers",
      tone: "",
    },
    {
      label: "Cần xử lý",
      value: failed.toLocaleString(),
      sub: failed ? "file cần kiểm tra" : "không có lỗi",
      icon: TriangleAlert,
      target: "failed",
      tone: failed ? "danger" : "",
    },
  ];
  const labels: Row = {
    service_started: "Hệ thống đã khởi động",
    source_added: "Đã thêm nguồn",
    scan_completed: "Quét nguồn hoàn tất",
    transfer_completed: "Backup hoàn tất",
    transfer_failed: "Backup gặp lỗi",
    transfer_waiting_telegram: "Job đang đợi Telegram",
    transfer_chunk_waiting: "Chờ Telegram, giữ tiến độ tải",
    transfer_chunk_resumed: "Tiếp tục chunk đang dở",
    transfer_no_progress_deferred: "File chưa nhận được dữ liệu, nhường hàng đợi",
    telegram_speed_recovery: "Tự phục hồi tốc độ tải",
    flood_wait: "Telegram yêu cầu chờ",
    telegram_repeated_flood_cooldown: "App nghỉ bảo vệ tài khoản",
    transfer_cancelled: "Đã hủy truyền",
    transfer_rest_started: "Nghỉ trước file tiếp theo",
    storage_remote_migrated: "Đã chuyển nơi lưu trữ",
    maintenance_failed: "Lưu trữ cần kiểm tra",
  };
  const seen = new Set<string>();
  const recent: Row[] = (events?.items || [])
    .filter((event: Row) => {
      if (!labels[event.kind]) return false;
      const key =
        event.kind === "scan_completed" ||
        event.kind === "transfer_rest_started"
          ? `${event.kind}:${event.source_id || ""}`
          : String(event.id);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    })
    .slice(0, 5);
  return (
    <div className="dashboard-simple">
      <Heading eyebrow="" title="Tổng quan Vault" description="">
        <button className="primary" onClick={() => navigate("sources")}>
          <Plus size={16} />
          Thêm nguồn
        </button>
      </Heading>
      <div
        className={`dashboard-status ${driveWait || telegramWait ? "waiting" : ""}`}
        role="status"
      >
        {downloading && !driveWait && !telegramWait ? (
          <ArrowDown size={18} />
        ) : verifying && !driveWait && !telegramWait ? (
          <ShieldCheck size={18} />
        ) : (
          <Clock size={18} />
        )}
        <span>{overview ? status : "Đang cập nhật trạng thái…"}</span>
      </div>
      {(driveWait || telegramWait || rest) && (
        <CooldownWidget
          now={now}
          overview={overview}
          telegramWait={telegramWait}
          driveWait={driveWait}
          rest={rest}
        />
      )}
      <div className="dashboard-metrics">
        {metrics.map((m) => (
          <button
            className={`dashboard-metric ${m.tone}`}
            key={m.label}
            onClick={() => navigate(m.target as Page)}
          >
            <span className="metric-label">
              <m.icon size={17} />
              {m.label}
            </span>
            <strong>{m.value}</strong>
            <small>{m.sub}</small>
          </button>
        ))}
      </div>
      <section className="dashboard-section">
        <div className="dashboard-section-head">
          <h2>Tiến trình hiện tại</h2>
          <button className="text-button" onClick={() => navigate("transfers")}>
            Xem tất cả <ArrowUpRight size={15} />
          </button>
        </div>
        {active.length ? (
          <div className="dashboard-jobs">
            {active.slice(0, 2).map((job) => {
              const checking = job.status === "VERIFYING";
              const percent =
                job.size > 0
                  ? Math.max(
                      0,
                      Math.min(
                        100,
                        Math.round(((job.downloaded || 0) / job.size) * 100),
                      ),
                    )
                  : 0;
              return (
                <article
                  className="dashboard-job"
                  key={job.id}
                  aria-label={`File ${backupFilename(job)}`}
                >
                  <FileGlyph job={job} small />
                  <div className="dashboard-job-body">
                    <strong title={backupFilename(job)}>
                      {backupFilename(job)}
                    </strong>
                    <small>
                      {job.source_name}
                      {job.topic_id ? ` / ${job.topic_name}` : ""}
                    </small>
                    {checking ? (
                      <div
                        className="verify-track"
                        aria-label="Đang đối chiếu dữ liệu đã truyền"
                      >
                        <i />
                      </div>
                    ) : (
                      <div
                        className="progress"
                        role="progressbar"
                        aria-label="Tiến độ truyền"
                        aria-valuemin={0}
                        aria-valuemax={100}
                        aria-valuenow={percent}
                      >
                        <i style={{ width: `${percent}%` }} />
                      </div>
                    )}
                  </div>
                  <div className="dashboard-job-state">
                    <span>
                      {checking ? (
                        <ShieldCheck size={14} />
                      ) : (
                        <ArrowDown size={14} />
                      )}
                      {checking ? "Đang xác minh" : `Đang tải · ${percent}%`}
                    </span>
                    <small>
                      {checking
                        ? bytes(job.size)
                        : `${bytes(job.download_speed)}/s`}
                    </small>
                  </div>
                </article>
              );
            })}
          </div>
        ) : (
          <div className="dashboard-idle">
            <Clock size={20} />
            <span>
              {rest || driveWait || telegramWait
                ? "File tiếp theo sẽ chạy sau thời gian nghỉ"
                : queued
                  ? "Hàng đợi được xử lý tự động theo cấu hình nguồn"
                  : "Thêm nguồn Telegram để bắt đầu backup"}
            </span>
          </div>
        )}
      </section>
      <section className="dashboard-section dashboard-recent">
        <div className="dashboard-section-head">
          <h2>Hoạt động gần đây</h2>
        </div>
        {recent.length ? (
          <div className="dashboard-events">
            {recent.map((event) => {
              const name = sources?.items?.find(
                (source: Row) => source.id === event.source_id,
              )?.name;
              return (
                <div
                  className={`dashboard-event ${event.kind.includes("failed") ? "danger" : ""}`}
                  key={event.id}
                >
                  {event.kind.includes("failed") ? (
                    <TriangleAlert size={16} />
                  ) : event.kind === "transfer_rest_started" ? (
                    <Clock size={16} />
                  ) : (
                    <Check size={16} />
                  )}
                  <span>
                    {labels[event.kind]}
                    {name && <small>{name}</small>}
                  </span>
                  <time>{relative(event.created_at)}</time>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="muted">Chưa có hoạt động</p>
        )}
      </section>
      <div className="dashboard-connections" aria-label="Kết nối hệ thống">
        <button onClick={() => navigate("telegram")}>
          <Zap size={15} />
          <span
            className={
              overview?.telegram === "connected" ? "connection-ok" : ""
            }
          >
            Telegram ·{" "}
            {overview?.telegram === "connected" ? "Đã kết nối" : "Chưa kết nối"}
          </span>
          <ArrowUpRight size={13} />
        </button>
        <button onClick={() => navigate("storage")}>
          <HardDrive size={15} />
          <span
            className={
              overview?.storage?.state === "connected" ? "connection-ok" : ""
            }
          >
            Drive ·{" "}
            {storage?.remote ||
              (overview?.storage?.state === "connected"
                ? "Đã kết nối"
                : "Chưa kết nối")}
          </span>
          <ArrowUpRight size={13} />
        </button>
        <button onClick={() => navigate("settings")}>
          <Settings size={15} />
          {settings?.concurrency || "—"} file song song
          <ArrowUpRight size={13} />
        </button>
      </div>
    </div>
  );
}

function FileGlyph({ job, small = false }: { job: Row; small?: boolean }) {
  const ext = (backupFilename(job).split(".").pop() || "FILE")
    .toUpperCase()
    .slice(0, 5);
  const image = /^(JPG|JPEG|PNG|WEBP|GIF|HEIC)$/.test(ext);
  const video = /^(MP4|MKV|MOV|WEBM|AVI|M4V|TS)$/.test(ext);
  const Icon = image ? ImageIcon : video ? Film : FileText;
  return (
    <span
      className={`file-glyph ${small ? "small" : ""} ${image ? "image" : video ? "video" : "document"}`}
      aria-hidden="true"
    >
      <span className="file-sheet">
        <Icon size={small ? 17 : 26} />
      </span>
      <span className="file-extension">{ext}</span>
    </span>
  );
}

function TransferCard({ job, cancel }: { job: Row; cancel?: () => void }) {
  const verifying = job.status === "VERIFYING";
  const percent =
    job.size > 0
      ? Math.max(
          0,
          Math.min(100, Math.round((job.downloaded / job.size) * 100)),
        )
      : 0;
  const [menu, setMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!menu) return;
    const outside = (event: PointerEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) setMenu(false);
    };
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMenu(false);
        menuRef.current?.querySelector("button")?.focus();
      }
    };
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", outside);
      document.removeEventListener("keydown", escape);
    };
  }, [menu]);
  return (
    <article
      className={`transfer-card luminous-card compact-transfer ${verifying ? "is-verifying" : "is-transferring"}`}
      aria-label={`File ${backupFilename(job)}`}
    >
      <div className="transfer-title">
        <FileGlyph job={job} small />
        <div className="transfer-file-info">
          <strong title={backupFilename(job)}>{backupFilename(job)}</strong>
          <small>
            {job.source_name}
            {job.topic_id ? ` / ${job.topic_name}` : ""}
          </small>
        </div>
        {cancel && (
          <div className="file-menu" ref={menuRef}>
            <button
              className="icon-button orbital-button"
              aria-label={`Thao tác file ${job.id}`}
              aria-expanded={menu}
              title="Thao tác file"
              onClick={() => setMenu(!menu)}
            >
              <MoreHorizontal size={19} />
            </button>
            {menu && (
              <div className="file-action-menu">
                <button
                  onClick={() => {
                    setMenu(false);
                    menuRef.current?.querySelector("button")?.focus();
                    cancel();
                  }}
                  aria-label="Hủy transfer"
                >
                  <CircleX size={16} /> Hủy công việc
                </button>
              </div>
            )}
          </div>
        )}
      </div>
      <div
        className={`transfer-capsule ${verifying ? "verification-capsule" : ""}`}
      >
        <div className="progress-label">
          <span>
            {verifying ? (
              <ShieldCheck size={18} />
            ) : (
              <LoaderCircle className="spin" size={18} />
            )}
            {verifying ? "Đang xác minh" : "Đang tải"}
          </span>
          <strong>
            {verifying ? (
              <span className="verify-indicator">
                <span /> Đối chiếu
              </span>
            ) : (
              `${percent}%`
            )}
          </strong>
        </div>
        {verifying ? (
          <div
            className="verify-track"
            aria-label="Đang đối chiếu dữ liệu đã truyền"
          >
            <i />
          </div>
        ) : (
          <div
            className="progress"
            role="progressbar"
            aria-label="Tiến độ truyền"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={percent}
          >
            <i style={{ width: `${percent}%` }} />
          </div>
        )}
      </div>
      <div className="transfer-detail">
        <span>
          {verifying ? (
            <>
              <Check size={14} /> Đã truyền xong · {bytes(job.size)}
            </>
          ) : (
            `${bytes(job.downloaded)} / ${bytes(job.size)}`
          )}
        </span>
        <span>
          {verifying ? (
            <>
              <ShieldCheck size={14} /> Xác minh dữ liệu
            </>
          ) : (
            <>
              <ArrowDown size={15} />
              {bytes(job.download_speed)}/s
            </>
          )}
        </span>
      </div>
    </article>
  );
}

function Sources({
  refresh,
  action,
  openTopics,
  navigate,
  mock,
}: {
  refresh: number;
  action: Action;
  navigate: (page: Page) => void;
  openTopics: (id: number) => void;
  mock: boolean;
}) {
  const [focusedSource, setFocusedSource] = useState<number | null>(null);
  const [localRefresh, setLocalRefresh] = useState(0);
  const [added, setAdded] = useState<Row | null>(null);
  const [addError, setAddError] = useState("");
  const { data: system } = useData("/status", refresh + localRefresh);
  const [history, setHistory] = useState([0]);
  const [add, setAdd] = useState(false);
  const [search, setSearch] = useState("");
  const [rights, setRights] = useState(false);
  const [browse, setBrowse] = useState(false);
  const [reference, setReference] = useState("");
  const [edit, setEdit] = useState<Row | null>(null);
  const [remove, setRemove] = useState<Row | null>(null);
  const { data, error, loading } = useData(
    `/sources?cursor=${history.at(-1)}&limit=12`,
    refresh + localRefresh,
  );
  const {
    data: discovery,
    error: discoveryError,
    loading: discoveryLoading,
  } = useData(add && browse ? "/discovery" : null, refresh, 0);
  const [busy, setBusy] = useState<number | null>(null);
  useEffect(() => {
    if (
      added &&
      focusedSource !== added.id &&
      data?.items?.some((s: Row) => s.id === added.id)
    ) {
      requestAnimationFrame(() =>
        document
          .getElementById(`source-${added.id}`)
          ?.scrollIntoView({ behavior: "smooth", block: "start" }),
      );
      setFocusedSource(added.id);
    }
  }, [added, data, focusedSource]);
  async function addSource(chatId: number | string, start = false) {
    setBusy(typeof chatId === "number" ? chatId : 0);
    setAddError("");
    try {
      const result = await api("/sources", "POST", {
        ...(typeof chatId === "number"
          ? { chat_id: chatId }
          : { reference: chatId }),
        rights_confirmed: rights,
        start,
      });
      setFocusedSource(null);
      setAdded({ ...result, started: start });
      setAdd(false);
      setHistory(result.id > 1 ? [0, result.id - 1] : [0]);
      setLocalRefresh((r) => r + 1);
    } catch (error) {
      setAddError((error as Error).message);
    } finally {
      setBusy(null);
    }
  }
  return (
    <>
      <Heading
        eyebrow="CONNECTED SOURCES"
        title="Nguồn Telegram"
        description="Thêm group/channel → bắt đầu quét → file tự vào hàng đợi và backup lên Drive."
      >
        <button
          className="primary"
          onClick={() => {
            setRights(false);
            setBrowse(false);
            setReference("");
            setAdd(true);
          }}
        >
          <Plus size={17} />
          Thêm nguồn
        </button>
      </Heading>
      <ErrorBox text={error} />
      {system?.scheduler_paused && (
        <section className="panel source-guide">
          <strong>Lịch toàn hệ thống đang tạm dừng</strong>
          <p>
            Nguồn sẽ không quét hoặc truyền cho đến khi mở lại lịch toàn hệ
            thống. Nguồn tạm dừng riêng vẫn giữ nguyên.
          </p>
          <button
            className="primary"
            onClick={() =>
              action(
                "/queue/control",
                "POST",
                { operation: "resume" },
                "Đã tiếp tục toàn hệ thống",
              )
            }
          >
            Tiếp tục toàn hệ thống
          </button>
        </section>
      )}
      {added && (
        <section className="source-added" role="status">
          <strong>Đã thêm: {added.name}</strong>
          <p>
            {added.started
              ? "Đã lên lịch quét. File phù hợp sẽ tự vào hàng đợi."
              : "Chọn Bắt đầu backup hoặc cấu hình trước."}
          </p>
        </section>
      )}
      {data?.items?.length ? (
        <div className="source-grid">
          {data.items.map((source: Row) => {
            const complete = source.counts.COMPLETED || 0;
            const total = Object.values(source.counts).reduce(
              (a: number, b: any) => a + b,
              0,
            );
            return (
              <section
                id={`source-${source.id}`}
                className={`panel source-card source-row ${added?.id === source.id ? "new-source-focus" : ""}`}
                key={source.id}
              >
                <div className="source-row-identity">
                  <span className="source-icon">
                    <Folder size={22} />
                  </span>
                  <div>
                    <h2>{source.name}</h2>
                    <p>
                      {source.kind === "channel"
                        ? "Channel"
                        : source.forum
                          ? "Group · Forum"
                          : "Group"}
                      {source.forum ? ` · ${source.topic_count} topics` : ""}
                    </p>
                  </div>
                </div>
                <div className="source-row-stats">
                  <span>
                    <strong>{complete}</strong> Đã lưu
                  </span>
                  <span>
                    <strong>
                      {(source.counts.QUEUED || 0) +
                        (source.counts.RETRY_WAIT || 0)}
                    </strong>{" "}
                    Chờ tải
                  </span>
                  {!!source.counts.FAILED && (
                    <span className="error-stat">
                      <strong>{source.counts.FAILED}</strong> Lỗi
                    </span>
                  )}
                </div>
                <div className="source-row-state">
                  <Badge
                    status={
                      source.flow?.label ||
                      (source.paused ? "Đã tạm dừng" : "Đang chạy")
                    }
                  />
                  {source.flow?.rest_until > Date.now() / 1000 && (
                    <small>
                      <Clock size={12} /> Chờ{" "}
                      {Math.ceil(source.flow.rest_until - Date.now() / 1000)}s
                    </small>
                  )}
                </div>
                <div className="source-actions">
                  <button
                    className={source.paused ? "primary" : "icon-button"}
                    disabled={!!system?.scheduler_paused}
                    title={
                      source.paused
                        ? "Bắt đầu hoặc tiếp tục backup"
                        : "Tạm dừng nguồn"
                    }
                    aria-label={
                      source.paused
                        ? source.flow?.stage === "ready"
                          ? "Bắt đầu backup"
                          : "Tiếp tục"
                        : `Tạm dừng ${source.name}`
                    }
                    onClick={async () => {
                      if (
                        await action(
                          `/sources/${source.id}/${source.paused ? "resume" : "pause"}`,
                          "POST",
                          undefined,
                          source.paused
                            ? "Backup đã bắt đầu: quét và truyền chạy tự động"
                            : "Đã tạm dừng nguồn",
                        )
                      )
                        setAdded(null);
                    }}
                  >
                    {source.paused ? <Play size={16} /> : <Pause size={16} />}
                    {!!source.paused &&
                      (source.flow?.stage === "ready"
                        ? "Bắt đầu backup"
                        : "Tiếp tục")}
                  </button>
                  {!!source.forum && (
                    <button
                      className="icon-button"
                      title="Chọn Topics"
                      aria-label="Topics"
                      onClick={() => openTopics(source.id)}
                    >
                      <Hash size={18} />
                    </button>
                  )}
                  <button
                    className="icon-button"
                    title="Bộ lọc nguồn"
                    aria-label={`Cài đặt ${source.name}`}
                    onClick={() => setEdit(source)}
                  >
                    <SlidersHorizontal size={18} />
                  </button>
                </div>
                {source.scan_target != null && (
                  <div className="source-scan">
                    <LoaderCircle size={13} className="spin" /> Đang quét ·{" "}
                    {source.scanned.toLocaleString()} tin nhắn đã kiểm tra
                  </div>
                )}
                {source.active_files?.map((job: Row) => (
                  <div className="source-live" key={job.id}>
                    <ArrowUpRight size={14} />
                    <strong>{backupFilename(job)}</strong>
                    <small>
                      {job.status === "VERIFYING"
                        ? "Đang kiểm tra"
                        : `${bytes(job.speed)}/s`}
                    </small>
                  </div>
                ))}
                {source.scan_error && <ErrorBox text={source.scan_error} />}
                <details className="source-details">
                  <summary>
                    <MoreHorizontal size={18} />
                    <span className="sr-only">Chi tiết {source.name}</span>
                  </summary>
                  <div className="source-details-body">
                    <p>{source.flow?.detail}</p>
                    <small>
                      {total} file phát hiện · {source.extensions} ·{" "}
                      {source.scanned.toLocaleString()} tin nhắn đã kiểm tra
                    </small>
                    <div className="source-track">
                      <button
                        className="text-button"
                        onClick={() => navigate("transfers")}
                      >
                        <ArrowUpRight size={14} /> Truyền & hàng đợi
                      </button>
                      <button
                        className="text-button"
                        onClick={() => navigate("videos")}
                      >
                        <ListVideo size={14} /> Thư viện
                      </button>
                      <button
                        className="text-button"
                        disabled={
                          !!source.paused ||
                          !!system?.scheduler_paused ||
                          !!source.scan_requested
                        }
                        onClick={() =>
                          action(
                            `/sources/${source.id}/scan`,
                            "POST",
                            undefined,
                            "Đã yêu cầu quét incremental",
                          )
                        }
                      >
                        <RefreshCw size={14} /> Quét lại
                      </button>
                      {source.flow?.stage === "telegram" && (
                        <button
                          className="text-button"
                          onClick={() => navigate("telegram")}
                        >
                          Kết nối Telegram
                        </button>
                      )}
                      <button
                        className="text-button danger"
                        onClick={() => setRemove(source)}
                      >
                        <Trash2 size={14} /> Gỡ nguồn
                      </button>
                      {mock && (
                        <button
                          className="text-button demo-emit"
                          onClick={() =>
                            action(
                              `/demo/emit/${source.id}`,
                              "POST",
                              undefined,
                              "Đã phát event video mới qua listener",
                            )
                          }
                        >
                          <Zap size={14} /> Test video mới
                        </button>
                      )}
                    </div>
                  </div>
                </details>
              </section>
            );
          })}
        </div>
      ) : loading ? (
        <div className="loading">
          <LoaderCircle className="spin" />
          Đang tải nguồn…
        </div>
      ) : (
        <section className="panel">
          <Empty icon={Folder} title="Bắt đầu với nguồn đầu tiên">
            Kết nối một group mà tài khoản Telegram của bạn có quyền truy cập.
            <br />
            <button
              className="primary"
              onClick={() => {
                setRights(false);
                setBrowse(false);
                setReference("");
                setAddError("");
                setAdd(true);
              }}
            >
              <Plus size={16} />
              Thêm nguồn Telegram
            </button>
          </Empty>
        </section>
      )}
      <Pager
        history={history}
        setHistory={setHistory}
        next={data?.next_cursor}
      />
      <details className="help-disclosure">
        <summary>
          <CircleHelp size={16} /> Thông tin thêm
        </summary>
        <div className="info-callout">
          <CircleHelp size={18} />
          <p>
            Tạm dừng dừng cả scanner và file đang truyền; tiếp tục tải lại file
            chưa xong từ đầu. Gỡ nguồn giữ nguyên tất cả backup.
          </p>
        </div>
      </details>
      {add && (
        <Modal title="Thêm nguồn Telegram" close={() => setAdd(false)}>
          <ErrorBox text={addError} />
          <p className="modal-description">
            Dán link group/channel hoặc link tin nhắn để thêm trực tiếp. Tài
            khoản Telegram cần đã tham gia group/channel.
          </p>
          <input
            aria-label="Link nguồn Telegram"
            placeholder="https://t.me/group_or_channel hoặc https://t.me/c/…"
            value={reference}
            onChange={(e) => setReference(e.target.value)}
          />
          <label className="rights-confirmation">
            <input
              type="checkbox"
              checked={rights}
              onChange={(e) => setRights(e.target.checked)}
            />
            Tôi sở hữu nội dung hoặc có quyền sao chép nội dung của nguồn này.
          </label>
          <button
            className="primary"
            disabled={
              !rights ||
              !reference.trim() ||
              busy !== null ||
              !!system?.scheduler_paused
            }
            onClick={() => addSource(reference.trim(), true)}
          >
            {busy === 0 ? "Đang thêm…" : "Thêm và bắt đầu backup"}
          </button>
          <button
            className="secondary"
            disabled={!rights || !reference.trim() || busy !== null}
            onClick={() => addSource(reference.trim(), false)}
          >
            Thêm để cấu hình
          </button>
          <p className="modal-description">
            Bắt đầu ngay sẽ quét tất cả topics theo bộ lọc mặc định của nguồn
            (video). Chọn Thêm để cấu hình nếu cần giới hạn topic, ngày, kích
            thước hoặc loại file trước.
          </p>
          <button className="secondary" onClick={() => setBrowse(true)}>
            Xem danh sách group/channel
          </button>
          {browse && (
            <div className="search-field">
              <Search size={17} />
              <input
                autoFocus
                placeholder="Tìm group/channel…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          )}

          {browse && <ErrorBox text={discoveryError} />}
          {browse &&
            (discoveryLoading ? (
              <div className="loading">
                <LoaderCircle className="spin" />
                Đang khám phá Telegram…
              </div>
            ) : (
              <div className="discovery-list">
                {discovery?.items
                  ?.filter((s: Row) =>
                    s.name.toLowerCase().includes(search.toLowerCase()),
                  )
                  .map((s: Row) => (
                    <button
                      key={s.chat_id}
                      onClick={() => addSource(s.chat_id)}
                      disabled={busy !== null || !rights}
                    >
                      <span className="source-icon">
                        <Folder size={20} />
                      </span>
                      <div>
                        <strong>{s.name}</strong>
                        <small>
                          {s.kind} ·{" "}
                          {s.forum ? "Forum topics" : "Toàn bộ nội dung"}
                        </small>
                      </div>
                      {busy === s.chat_id ? (
                        <LoaderCircle className="spin" size={18} />
                      ) : (
                        <Plus size={18} />
                      )}
                    </button>
                  ))}
                {discovery?.items?.length === 0 && (
                  <Empty title="Không tìm thấy group/channel">
                    Mở Kết nối Telegram trong menu để đăng nhập tài khoản và
                    kiểm tra quyền truy cập.
                  </Empty>
                )}
              </div>
            ))}
        </Modal>
      )}
      {edit && (
        <SourceSettings
          source={edit}
          close={() => setEdit(null)}
          action={action}
        />
      )}{" "}
      {remove && (
        <Modal title="Gỡ nguồn khỏi cấu hình?" close={() => setRemove(null)}>
          <p className="modal-description">
            Nguồn <b>{remove.name}</b> sẽ ngừng backup. Các file đã backup và
            job chưa hoàn thành sẽ được xóa khỏi lịch. File đã backup và bản ghi
            hoàn thành vẫn được giữ lại.
          </p>
          <div className="modal-actions">
            <button onClick={() => setRemove(null)}>Đóng</button>
            <button
              className="danger"
              onClick={async () => {
                if (
                  await action(
                    `/sources/${remove.id}`,
                    "DELETE",
                    undefined,
                    "Đã gỡ nguồn; backup được giữ lại",
                  )
                )
                  setRemove(null);
              }}
            >
              <Trash2 size={15} />
              Gỡ nguồn
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
function SourceSettings({
  source,
  close,
  action,
}: {
  source: Row;
  close: () => void;
  action: Action;
}) {
  const [min, setMin] = useState(String(source.min_size / 1048576));
  const [max, setMax] = useState(String(source.max_size / 1048576));
  const [extensions, setExtensions] = useState(source.extensions);
  const [enabled, setEnabled] = useState(!!source.enabled);
  const dateInput = (value: number | null) =>
    value ? new Date(value * 1000).toISOString().slice(0, 10) : "";
  const [after, setAfter] = useState(dateInput(source.date_after));
  const [before, setBefore] = useState(dateInput(source.date_before));
  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (
      await action(`/sources/${source.id}`, "PATCH", {
        min_size: Math.round(Number(min) * 1048576),
        max_size: Math.round(Number(max) * 1048576),
        extensions,
        enabled,
        date_after: after ? Date.parse(after) / 1000 : null,
        date_before: before ? Date.parse(before) / 1000 + 86399 : null,
      })
    )
      close();
  }
  return (
    <Modal title={`Cài đặt · ${source.name}`} close={close}>
      <form onSubmit={save} className="settings-form">
        <label className="check-row">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
          />
          Enable backup
        </label>
        <div className="form-grid">
          <label>
            Kích thước tối thiểu (MiB)
            <input
              type="number"
              min="0"
              step="any"
              value={min}
              onChange={(e) => setMin(e.target.value)}
            />
          </label>
          <label>
            Tối đa (MiB, 0 = không giới hạn)
            <input
              type="number"
              min="0"
              step="any"
              value={max}
              onChange={(e) => setMax(e.target.value)}
            />
          </label>
          <label>
            Từ ngày (UTC)
            <input
              type="date"
              value={after}
              onChange={(e) => setAfter(e.target.value)}
            />
          </label>
          <label>
            Đến ngày (UTC)
            <input
              type="date"
              value={before}
              onChange={(e) => setBefore(e.target.value)}
            />
          </label>
        </div>
        <label>
          Video extensions
          <input
            value={extensions}
            onChange={(e) => setExtensions(e.target.value)}
            pattern="[a-z0-9]+(,[a-z0-9]+)*"
            required
          />
        </label>
        <p className="muted">
          Native video và MIME video/* luôn được nhận diện. Bộ lọc áp dụng cho
          lần quét tiếp theo; backup cũ được giữ.
        </p>
        <div className="modal-actions">
          <button
            type="button"
            onClick={() =>
              action(
                `/sources/${source.id}/scan?full=true`,
                "POST",
                undefined,
                "Đã yêu cầu rescan toàn bộ, dedupe được giữ",
              )
            }
          >
            Rescan toàn bộ
          </button>
          <button className="primary" type="submit">
            <Check size={15} />
            Lưu cài đặt
          </button>
        </div>
      </form>
    </Modal>
  );
}

function Topics({
  selected,
  select,
  refresh,
  action,
}: {
  selected: number | null;
  select: (id: number | null) => void;
  refresh: number;
  action: Action;
}) {
  const { data: sources, error: sourceError } = useData(
    "/sources?limit=100",
    refresh,
  );
  const [topics, setTopics] = useState<Row[]>([]);
  const [all, setAll] = useState(true);
  const [chosen, setChosen] = useState<number[]>([]);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const current = sources?.items?.find((s: Row) => s.id === selected);
  const [baseline, setBaseline] = useState("");
  const selectionKey = JSON.stringify([all, [...chosen].sort((a, b) => a - b)]);
  const dirty = selectionKey !== baseline;
  useEffect(() => {
    if (!selected && sources?.items?.some((s: Row) => s.forum))
      select(sources.items.find((s: Row) => s.forum).id);
  }, [sources, selected, select]);
  useEffect(() => {
    let alive = true;
    if (!selected) return;
    setLoading(true);
    (async () => {
      try {
        const source = await api(`/sources/${selected}`);
        let cursor = -1;
        const items: Row[] = [];
        do {
          const result = await api(
            `/sources/${selected}/topics?cursor=${cursor}`,
          );
          items.push(...result.items);
          cursor = result.next_cursor ?? -1;
        } while (cursor !== -1 && items.length < 5000);
        if (alive) {
          setTopics(items);
          setAll(!!source.all_topics);
          const chosenIds = items
            .filter((t) => t.selected)
            .map((t) => t.topic_id);
          setChosen(chosenIds);
          setBaseline(
            JSON.stringify([
              !!source.all_topics,
              [...chosenIds].sort((a, b) => a - b),
            ]),
          );
          setError("");
        }
      } catch (e) {
        if (alive) setError((e as Error).message);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [selected, refresh]);
  return (
    <>
      <Heading
        eyebrow="CHOOSE WHAT MATTERS"
        title="Telegram Topics"
        description="Backup tất cả hoặc chọn riêng các topic bạn muốn giữ."
      >
        <button
          className="secondary"
          disabled={!selected}
          onClick={() => action(`/sources/${selected}/topics/refresh`)}
        >
          <RefreshCw size={16} />
          Làm mới topics
        </button>
      </Heading>
      <ErrorBox text={sourceError || error} />
      {!sources?.items?.some((s: Row) => s.forum) ||
      (current && !current.forum) ? (
        <section className="panel">
          <Empty icon={Hash} title="Nguồn này không có Topics">
            Nội dung được quản lý trực tiếp trong Nguồn Telegram.
          </Empty>
        </section>
      ) : (
        <section className="panel topics-panel">
          <div className="topic-toolbar">
            <label>
              Nguồn Telegram
              <select
                value={selected || ""}
                onChange={(e) => {
                  if (!dirty || window.confirm("Bỏ thay đổi Topics chưa lưu?"))
                    select(Number(e.target.value));
                }}
              >
                {sources.items
                  .filter((s: Row) => s.forum)
                  .map((s: Row) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
              </select>
            </label>
            <div className="search-field">
              <Search size={16} />
              <input
                placeholder="Tìm topic…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>
          <div className="all-topics">
            <div>
              <Hash size={22} />
              <div>
                <strong>Backup tất cả topics</strong>
                <small>Tự bao gồm các topic mới trong tương lai</small>
              </div>
            </div>
            <label className="switch">
              <input
                aria-label="Backup tất cả topics"
                type="checkbox"
                checked={all}
                onChange={(e) => setAll(e.target.checked)}
              />
              <span />
            </label>
          </div>
          {loading ? (
            <div className="loading">
              <LoaderCircle className="spin" />
              Đang tải topics…
            </div>
          ) : all ? (
            <div className="topic-summary">
              <Hash size={20} /> Tự backup mọi topic, kể cả topic mới.
            </div>
          ) : (
            topics
              .filter((t) =>
                t.name.toLowerCase().includes(search.toLowerCase()),
              )
              .map((topic) => (
                <label
                  className={`topic-row ${all || chosen.includes(topic.topic_id) ? "selected" : ""}`}
                  key={topic.topic_id}
                >
                  <input
                    type="checkbox"
                    disabled={all}
                    checked={all || chosen.includes(topic.topic_id)}
                    onChange={(e) =>
                      setChosen(
                        e.target.checked
                          ? [...chosen, topic.topic_id]
                          : chosen.filter((id) => id !== topic.topic_id),
                      )
                    }
                  />
                  <span className="hash-icon">
                    <Hash size={18} />
                  </span>
                  <div>
                    <strong>{topic.name}</strong>
                    <small>Topic ID: {topic.topic_id}</small>
                  </div>
                  <span>{topic.videos} file</span>
                </label>
              ))
          )}
          <div className="topic-save">
            <p>
              <ShieldCheck size={15} />
              Thay đổi lựa chọn giữ nguyên backup đã có.
            </p>
            <button
              className="primary"
              disabled={!selected || loading || !dirty}
              onClick={async () => {
                if (
                  await action(
                    `/sources/${selected}/topics`,
                    "PUT",
                    { all_topics: all, selected: chosen },
                    "Đã lưu topics và yêu cầu quét lại",
                  )
                )
                  setBaseline(selectionKey);
              }}
            >
              <Check size={16} />
              Lưu lựa chọn
            </button>
          </div>
          {current && !current.forum && (
            <details className="help-disclosure">
              <summary>
                <CircleHelp size={16} /> Thông tin thêm
              </summary>
              <div className="info-callout">
                <CircleHelp size={17} />
                Group này không có forum topics. Media nằm trong thư mục group.
              </div>
            </details>
          )}
        </section>
      )}
    </>
  );
}

function QueueControls({
  action,
  refresh,
}: {
  action: Action;
  refresh: number;
}) {
  const [opened, setOpened] = useState(false);
  const [source, setSource] = useState("");
  const [topic, setTopic] = useState("");
  const [confirm, setConfirm] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const { data: sources } = useData("/sources?limit=100", refresh);
  const { data: topics } = useData(
    source ? `/sources/${source}/topics?limit=100` : null,
    refresh,
  );
  const { data: status } = useData("/status", refresh);
  const selectedSource = sources?.items?.find(
    (s: Row) => String(s.id) === source,
  );
  const scope = source
    ? `${selectedSource?.name || source}${topic ? ` / ${topics?.items?.find((t: Row) => String(t.topic_id) === topic)?.name || topic}` : ""}`
    : "Tất cả nguồn";
  const labels: Row = {
    pause: "Tạm dừng",
    resume: "Tiếp tục",
    cancel: "Hủy",
    delete: "Xóa lịch",
  };
  async function execute(operation: string) {
    setBusy(true);
    const ok = await action(
      "/queue/control",
      "POST",
      {
        operation,
        source_id: source ? Number(source) : null,
        topic_id: topic ? Number(topic) : null,
      },
      `${labels[operation]}: ${scope}. Backup đã lưu được giữ lại.`,
    );
    if (ok) setConfirm(null);
    setBusy(false);
    if (ok && operation === "delete" && source && !topic) setSource("");
  }
  return (
    <div className="queue-controls">
      <button
        className="icon-button scope-trigger"
        title={`Quản lý phạm vi · ${scope}`}
        aria-label="Quản lý phạm vi"
        onClick={() => setOpened(true)}
      >
        <SlidersHorizontal size={18} />
      </button>
      {opened && !confirm && (
        <Modal title="Quản lý phạm vi" close={() => !busy && setOpened(false)}>
          <div className="scope-body">
            {status?.scheduler_paused && (
              <p className="inline-error">
                Toàn bộ lịch đang tạm dừng. Chọn Tất cả nguồn → Tiếp tục để mở
                lại lịch.
              </p>
            )}
            <div className="queue-scope">
              <label>
                Phạm vi group
                <select
                  aria-label="Phạm vi group"
                  value={source}
                  onChange={(e) => {
                    setSource(e.target.value);
                    setTopic("");
                  }}
                >
                  <option value="">Tất cả nguồn</option>
                  {sources?.items?.map((s: Row) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Phạm vi topic
                <select
                  aria-label="Phạm vi topic"
                  value={topic}
                  disabled={!source}
                  onChange={(e) => setTopic(e.target.value)}
                >
                  <option value="">Tất cả topics</option>
                  {topics?.items?.map((t: Row) => (
                    <option key={t.topic_id} value={t.topic_id}>
                      {t.name}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <div className="queue-buttons">
              {Object.entries(labels)
                .filter(([op]) => {
                  if (op !== "pause" && op !== "resume") return true;
                  if (topic) {
                    const enabled =
                      !!selectedSource?.all_topics ||
                      !!topics?.items?.find(
                        (t: Row) => String(t.topic_id) === topic,
                      )?.selected;
                    return op === (enabled ? "pause" : "resume");
                  }
                  const paused = source
                    ? !!selectedSource?.paused
                    : !!status?.scheduler_paused;
                  return op === (paused ? "resume" : "pause");
                })
                .map(([op, label]) => (
                  <button
                    key={op}
                    className={op === "delete" ? "danger" : "secondary"}
                    disabled={busy}
                    onClick={() =>
                      op === "resume" ? void execute(op) : setConfirm(op)
                    }
                  >
                    {op === "pause" ? (
                      <Pause size={16} />
                    ) : op === "resume" ? (
                      <Play size={16} />
                    ) : op === "delete" ? (
                      <Trash2 size={16} />
                    ) : (
                      <CircleX size={16} />
                    )}
                    {String(label)}
                    {!source ? " tất cả" : topic ? " topic" : " group"}
                  </button>
                ))}
            </div>
            <p className="muted scope-help">
              Áp dụng cho mọi job trong phạm vi đã chọn, kể cả ngoài trang này.
            </p>
          </div>
        </Modal>
      )}
      {confirm && (
        <Modal
          title={`${labels[confirm]} ${scope}`}
          close={() => !busy && setConfirm(null)}
        >
          <p>
            {confirm === "pause"
              ? "Dừng scanner và transfer trong phạm vi này, giữ job để tiếp tục sau."
              : confirm === "cancel"
                ? "Dừng lập lịch và hủy các job chưa hoàn thành trong phạm vi này. Có thể retry từng job sau."
                : "Dừng lập lịch và xóa các job chưa hoàn thành trong phạm vi này. Group sẽ được gỡ khỏi nguồn nếu chọn cả group; topic sẽ được bỏ chọn. Backup đã lưu và file trên Drive được giữ lại."}
          </p>
          <div className="queue-buttons">
            <button
              className="secondary"
              disabled={busy}
              onClick={() => setConfirm(null)}
            >
              Quay lại
            </button>
            <button
              className={confirm === "pause" ? "primary" : "danger"}
              disabled={busy}
              onClick={() => void execute(confirm)}
            >
              {busy ? "Đang xử lý…" : "Xác nhận"}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}

function Jobs({
  page,
  refresh,
  action,
}: {
  page: "transfers" | "failed" | "videos";
  refresh: number;
  action: Action;
}) {
  const [history, setHistory] = useState([0]);
  const [tab, setTab] = useState("active");
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("");
  const [filter, setFilter] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "table">("grid");
  const [detail, setDetail] = useState<Row | null>(null);
  const [pending, setPending] = useState<{
    job: Row;
    operation: string;
  } | null>(null);
  const [busy, setBusy] = useState(false);
  const { data: sources } = useData("/sources?limit=100", refresh);
  const { data: system } = useData("/status", refresh);
  const status =
    page === "videos"
      ? "COMPLETED"
      : page === "failed"
        ? filter || "FAILED"
        : tab === "active"
          ? "TRANSFERRING,VERIFYING"
          : "QUEUED,RETRY_WAIT";
  const { data, error, loading } = useData(
    `/jobs?limit=25&cursor=${history.at(-1)}&status=${status}&q=${encodeURIComponent(query)}${source ? `&source_id=${source}` : ""}`,
    refresh,
  );
  useEffect(() => {
    setHistory([0]);
    setTab("active");
    setFilter("");
    setQuery("");
    setSearch("");
    setSource("");
    setDetail(null);
  }, [page]);
  const runPending = async () => {
    if (!pending) return;
    setBusy(true);
    const { job, operation } = pending;
    const ok = await action(
      operation === "delete"
        ? "/queue/control"
        : `/jobs/${job.id}/${operation}`,
      "POST",
      operation === "delete" ? { operation, job_id: job.id } : undefined,
      "Đã cập nhật công việc",
    );
    setBusy(false);
    if (ok) setPending(null);
  };
  const title =
    page === "transfers"
      ? "Truyền & hàng đợi"
      : page === "failed"
        ? "Cần xử lý"
        : "Thư viện backup";
  return (
    <>
      <Heading eyebrow="" title={title} description="">
        {page === "transfers" && (
          <>
            <span className="speed-pill">
              <span className="live-eq-wave" aria-hidden="true">
                <span />
                <span />
                <span />
              </span>
              <ArrowDown size={16} />
              <strong>{bytes(system?.download_speed)}/s</strong>
            </span>
            <button
              className={system?.scheduler_paused ? "primary" : "secondary"}
              title="Áp dụng cho toàn hệ thống. File bị dừng có thể tải lại từ đầu khi tiếp tục."
              onClick={() =>
                system?.scheduler_paused
                  ? action(
                      "/queue/control",
                      "POST",
                      { operation: "resume" },
                      "Đã tiếp tục toàn hệ thống",
                    )
                  : setPending({ job: { id: 0 }, operation: "pause-all" })
              }
            >
              {system?.scheduler_paused ? (
                <Play size={17} />
              ) : (
                <Pause size={17} />
              )}
              {system?.scheduler_paused ? "Tiếp tục tất cả" : "Tạm dừng tất cả"}
            </button>
          </>
        )}
      </Heading>
      {page === "transfers" && (
        <div
          className="view-tabs"
          role="tablist"
          aria-label="Truyền và hàng đợi"
        >
          <button
            role="tab"
            aria-selected={tab === "active"}
            onClick={() => {
              setTab("active");
              setHistory([0]);
            }}
          >
            <ArrowUpRight size={17} /> Đang xử lý{" "}
            <span>{system?.active || 0}</span>
          </button>
          <button
            role="tab"
            aria-selected={tab === "queue"}
            onClick={() => {
              setTab("queue");
              setHistory([0]);
            }}
          >
            <Clock size={17} /> Hàng đợi{" "}
            <span>
              {(system?.counts?.QUEUED?.count || 0) +
                (system?.counts?.RETRY_WAIT?.count || 0)}
            </span>
          </button>
        </div>
      )}
      <div className="jobs-toolbar">
        <form
          className="search-field"
          role="search"
          onSubmit={(e) => {
            e.preventDefault();
            setQuery(search.trim());
            setHistory([0]);
          }}
        >
          <Search size={17} />
          <input
            aria-label="Tìm file"
            placeholder="Tìm tên file…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button
            type="submit"
            className="icon-button"
            aria-label="Tìm kiếm"
            title="Tìm trên toàn bộ danh sách"
          >
            <ChevronRight size={17} />
          </button>
          {query && (
            <button
              type="button"
              className="icon-button"
              aria-label="Xóa tìm kiếm"
              onClick={() => {
                setQuery("");
                setSearch("");
                setHistory([0]);
              }}
            >
              <X size={16} />
            </button>
          )}
        </form>
        <select
          aria-label="Lọc nguồn"
          value={source}
          onChange={(e) => {
            setSource(e.target.value);
            setHistory([0]);
          }}
        >
          <option value="">Tất cả nguồn</option>
          {sources?.items?.map((s: Row) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
        {page === "failed" && (
          <select
            aria-label="Lọc trạng thái"
            value={filter}
            onChange={(e) => {
              setFilter(e.target.value);
              setHistory([0]);
            }}
          >
            <option value="">Thất bại</option>
            <option value="CANCELLED">Đã hủy</option>
            <option value="SKIPPED">Đã bỏ qua</option>
          </select>
        )}
        {page === "videos" && (
          <div className="view-switch-btn-group">
            <button
              type="button"
              className={`view-switch-btn ${viewMode === "grid" ? "active" : ""}`}
              onClick={() => setViewMode("grid")}
              title="Xem dạng thẻ gallery"
            >
              <Grid size={15} /> Thẻ
            </button>
            <button
              type="button"
              className={`view-switch-btn ${viewMode === "table" ? "active" : ""}`}
              onClick={() => setViewMode("table")}
              title="Xem dạng danh sách bảng"
            >
              <List size={15} /> Bảng
            </button>
          </div>
        )}
        {page === "transfers" && (
          <QueueControls action={action} refresh={refresh} />
        )}
      </div>
      <ErrorBox text={error} />
      {loading && !data ? (
        <div className="loading">
          <LoaderCircle className="spin" /> Đang tải…
        </div>
      ) : !data?.items?.length ? (
        <section className="panel">
          <Empty
            icon={page === "failed" ? ShieldCheck : ListVideo}
            title={
              query
                ? "Không tìm thấy file"
                : page === "videos"
                  ? "Chưa có backup hoàn tất"
                  : page === "failed"
                    ? "Không có mục cần xử lý"
                    : tab === "active"
                      ? "Không có file đang xử lý"
                      : "Hàng đợi trống"
            }
          >
            {query
              ? "Thử tên khác hoặc bỏ bộ lọc."
              : page === "videos"
                ? "File xuất hiện tại đây sau khi tải lên và kiểm tra xong."
                : "Trạng thái tự cập nhật."}
          </Empty>
        </section>
      ) : page === "transfers" && tab === "active" ? (
        <div className="transfers-grid">
          {data.items.map((job: Row) => (
            <div className="transfer-slot" key={job.id}>
              <TransferCard
                job={job}
                cancel={() => setPending({ job, operation: "cancel" })}
              />
            </div>
          ))}
        </div>
      ) : page === "videos" && viewMode === "grid" ? (
        <div className="video-gallery-grid">
          {data.items.map((job: Row) => (
            <VideoCard
              key={job.id}
              job={job}
              onDetail={() => setDetail(job)}
              onCopyPath={async () => {
                try {
                  await navigator.clipboard.writeText(job.remote_path);
                  setDetail({ ...job, copied: true });
                } catch {
                  setDetail({ ...job, copyError: true });
                }
              }}
            />
          ))}
        </div>
      ) : (
        <section className="panel table-panel">
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>File / Nguồn</th>
                  <th>Trạng thái</th>
                  <th>Dung lượng</th>
                  <th>{page === "videos" ? "Đã lưu" : "Cập nhật"}</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {data.items.map((job: Row) => (
                  <tr key={job.id}>
                    <td>
                      <div className="file-cell">
                        <FileGlyph job={job} small />
                        <button
                          className="file-name"
                          title={backupFilename(job)}
                          onClick={() => setDetail(job)}
                        >
                          <strong>{backupFilename(job)}</strong>
                          <small>
                            {job.source_name}
                            {job.topic_id ? ` / ${job.topic_name}` : ""}
                          </small>
                          <span className="mobile-file-meta">
                            <Badge status={job.status} /> {bytes(job.size)}
                          </span>
                          {job.last_error && page === "failed" && (
                            <span className="inline-error">
                              {job.last_error.length > 100
                                ? job.last_error.slice(0, 100) + "…"
                                : job.last_error}
                            </span>
                          )}
                        </button>
                      </div>
                    </td>
                    <td>
                      <Badge status={job.status} />
                    </td>
                    <td className="mono">{bytes(job.size)}</td>
                    <td className="muted">
                      {relative(
                        job.completed_at || job.started_at || job.created_at,
                      )}
                    </td>
                    <td>
                      <div className="row-actions">
                        {["FAILED", "CANCELLED", "SKIPPED"].includes(
                          job.status,
                        ) && (
                          <button
                            title="Thử lại"
                            aria-label={`Thử lại job ${job.id}`}
                            onClick={() => action(`/jobs/${job.id}/retry`)}
                          >
                            <RefreshCw size={17} />
                          </button>
                        )}
                        <button
                          title="Chi tiết"
                          aria-label={`Chi tiết job ${job.id}`}
                          onClick={() => setDetail(job)}
                        >
                          <MoreHorizontal size={18} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
      <Pager
        history={history}
        setHistory={setHistory}
        next={data?.next_cursor}
      />
      {pending && (
        <Modal
          title={
            pending.operation === "pause-all"
              ? "Tạm dừng toàn hệ thống?"
              : `${pending.operation === "cancel" ? "Hủy" : "Xóa lịch"} file?`
          }
          close={() => !busy && setPending(null)}
        >
          {pending.job.id > 0 && (
            <p className="confirm-filename">{backupFilename(pending.job)}</p>
          )}
          <p>
            {pending.operation === "pause-all"
              ? "Dừng quét và truyền, giữ hàng đợi. Khi tiếp tục, file chưa xong có thể tải lại từ đầu."
              : pending.operation === "cancel"
                ? "Dừng file này. Công việc không tự thử lại; backup đã lưu được giữ nguyên."
                : "Xóa công việc chưa hoàn tất. Backup trên Drive được giữ nguyên; công việc này không tự xuất hiện lại khi quét."}
          </p>
          <div className="dialog-actions">
            <button disabled={busy} onClick={() => setPending(null)}>
              Quay lại
            </button>
            <button
              className={
                pending.operation === "pause-all" ? "primary" : "danger"
              }
              disabled={busy}
              onClick={async () => {
                if (pending.operation === "pause-all") {
                  setBusy(true);
                  const ok = await action(
                    "/queue/control",
                    "POST",
                    { operation: "pause" },
                    "Đã tạm dừng toàn hệ thống",
                  );
                  setBusy(false);
                  if (ok) setPending(null);
                } else await runPending();
              }}
            >
              {busy ? "Đang xử lý…" : "Xác nhận"}
            </button>
          </div>
        </Modal>
      )}
      {detail && (
        <Modal title="Chi tiết file" close={() => setDetail(null)}>
          <div className="job-details">
            <Badge status={detail.status} />
            <h3>{backupFilename(detail)}</h3>
            <dl>
              <dt>Nguồn</dt>
              <dd>{detail.source_name}</dd>
              {!!detail.topic_id && (
                <>
                  <dt>Topic</dt>
                  <dd>{detail.topic_name}</dd>
                </>
              )}
              <dt>Dung lượng</dt>
              <dd>{bytes(detail.size)}</dd>
              <dt>Tên gốc</dt>
              <dd>{detail.original_filename || "Telegram không cung cấp"}</dd>
              <dt>Đường dẫn lưu</dt>
              <dd className="mono wrap">
                {detail.remote_path}
                <button
                  className="copy-path"
                  title="Sao chép đường dẫn"
                  onClick={async () => {
                    try {
                      await navigator.clipboard.writeText(detail.remote_path);
                      setDetail({ ...detail, copied: true });
                    } catch {
                      setDetail({ ...detail, copyError: true });
                    }
                  }}
                >
                  <Copy size={16} />
                  {detail.copied ? "Đã sao chép" : "Sao chép"}
                </button>
                {detail.copyError && (
                  <small className="inline-error">
                    Không thể sao chép; chọn đường dẫn để copy thủ công.
                  </small>
                )}
              </dd>
            </dl>
            <details className="technical-details">
              <summary>
                <CircleHelp size={16} /> Chi tiết kỹ thuật
              </summary>
              <dl>
                <dt>Message ID</dt>
                <dd>{detail.message_id}</dd>
                <dt>Lần thử</dt>
                <dd>{detail.attempts}</dd>
                <dt>SHA-256</dt>
                <dd className="mono wrap">
                  {detail.plaintext_sha256 || "Chưa có"}
                </dd>
                <dt>Lỗi gần nhất</dt>
                <dd className="wrap">{detail.last_error || "Không có"}</dd>
              </dl>
            </details>
            {detail.status !== "COMPLETED" && (
              <div className="dialog-actions">
                {["QUEUED", "TRANSFERRING", "VERIFYING", "RETRY_WAIT"].includes(
                  detail.status,
                ) && (
                  <button
                    onClick={() => {
                      setPending({ job: detail, operation: "cancel" });
                      setDetail(null);
                    }}
                  >
                    <CircleX size={16} /> Hủy công việc
                  </button>
                )}
                <button
                  className="danger"
                  onClick={() => {
                    setPending({ job: detail, operation: "delete" });
                    setDetail(null);
                  }}
                >
                  <Trash2 size={16} /> Xóa lịch
                </button>
              </div>
            )}
          </div>
        </Modal>
      )}
    </>
  );
}

function Storage({ refresh, action }: { refresh: number; action: Action }) {
  const { data, error } = useData("/storage/status", refresh);
  const { data: settings } = useData("/settings", refresh);
  return (
    <>
      <Heading
        eyebrow="ENCRYPTED DESTINATION"
        title="Lưu trữ"
        description="Một lớp mã hóa cho nội dung, tên file và toàn bộ cấu trúc thư mục."
      >
        <button
          className="secondary"
          onClick={() =>
            action(
              "/storage/check",
              "POST",
              undefined,
              "Đã kiểm tra kết nối remote",
            )
          }
        >
          <RefreshCw size={16} />
          Kiểm tra kết nối
        </button>
      </Heading>
      <ErrorBox text={error} />
      <div className="storage-grid">
        <section className="panel storage-main">
          <div className="storage-hero">
            <div className="storage-icon">
              <HardDrive size={35} />
            </div>
            <div>
              <span className="eyebrow">RCLONE CRYPT</span>
              <h2>{data?.remote || "crypt:"}</h2>
              <p>Thư mục gốc: {data?.root || "—"}</p>
            </div>
            <Badge status={data?.state || "Chưa cấu hình"} />
          </div>
          <div className="encryption-grid">
            {[
              ["Nội dung", "content_encrypted"],
              ["Tên file", "filenames_encrypted"],
              ["Thư mục", "directories_encrypted"],
            ].map(([label, key]) => (
              <div key={key}>
                <ShieldCheck size={21} />
                <strong>{label}</strong>
                <span>{data?.[key] ? "Mã hóa bật" : "Cần cấu hình"}</span>
              </div>
            ))}
          </div>
          <div className="storage-path-preview">
            <Folder size={18} />
            <code>{data?.root || "—"}/Telegram/Nguồn/[Topic]/File</code>
          </div>
          <details className="storage-technical">
            <summary>
              <LockKeyhole size={16} /> Mã hóa & đường dẫn
            </summary>
            <p>
              Đường dẫn trên app là tên đã giải mã. Drive lưu nội dung, tên file
              và thư mục được mã hóa.
            </p>
          </details>
          <div className="storage-info-row">
            <span>Kiểm tra dữ liệu</span>
            <strong>
              {data?.verification === "sha256"
                ? "Size + decrypted SHA-256"
                : "Kích thước file"}
            </strong>
          </div>
          <div className="storage-info-row">
            <span>Kiểm tra kết nối gần nhất</span>
            <strong>{relative(data?.checked_at)}</strong>
          </div>
          <div className="storage-info-row">
            <span>Dung lượng Drive</span>
            <strong>Chưa có dữ liệu quota</strong>
          </div>
        </section>
        <section className="panel reconciliation-panel">
          <span className="panel-icon">
            <RefreshCw size={21} />
          </span>
          <h2>Đối chiếu backup</h2>
          <p>Kiểm tra file đã lưu: phát hiện file mất hoặc sai kích thước.</p>
          <button
            className="primary wide"
            disabled={settings?.reconcile_running}
            onClick={() =>
              action(
                "/storage/reconcile",
                "POST",
                undefined,
                "Reconciliation đang chạy trên backend",
              )
            }
          >
            {settings?.reconcile_running ? (
              <LoaderCircle className="spin" size={16} />
            ) : (
              <RefreshCw size={16} />
            )}
            Đối chiếu backup
          </button>
          {settings?.last_reconcile_result && (
            <div className="reconcile-result">
              {Object.entries(settings.last_reconcile_result).map(
                ([key, value]) => (
                  <span key={key}>
                    {key}
                    <strong>{String(value)}</strong>
                  </span>
                ),
              )}
            </div>
          )}
        </section>
      </div>
      <details className="help-disclosure">
        <summary>
          <CircleHelp size={16} /> Thông tin thêm
        </summary>
        <div className="info-callout">
          <Terminal size={18} />
          <p>
            Thiết lập remote bằng <code>rclone config</code> trong terminal, rồi
            trỏ <code>RCLONE_CONFIG</code> tới file quyền 600. Đăng nhập tài
            khoản trong mục Kết nối Telegram.
          </p>
        </div>
      </details>
    </>
  );
}

function SettingsPage({
  refresh,
  action,
}: {
  refresh: number;
  action: Action;
}) {
  const { data, error } = useData("/settings", refresh, 0);
  const { data: rateStatus } = useData("/telegram/rate-status", refresh, 10000);
  const [form, setForm] = useState<Row | null>(null);
  useEffect(() => {
    if (data) setForm(data);
  }, [data]);
  const settingKeys = [
    "concurrency",
    "download_bandwidth",
    "upload_bandwidth",
    "reconciliation_interval",
    "max_retries",
    "verify_hash",
    "file_pause_enabled",
    "file_pause_min_seconds",
    "file_pause_max_seconds",
  ];
  const dirty =
    !!form &&
    !!data &&
    settingKeys.some((key) => String(form[key]) !== String(data[key]));
  const [saving, setSaving] = useState(false);
  function update(key: string, value: any) {
    setForm((old: Row | null) => ({ ...old, [key]: value }));
  }
  async function save(e: React.FormEvent) {
    e.preventDefault();
    if (!form) return;
    setSaving(true);
    await action(
      "/settings",
      "PATCH",
      {
        concurrency: Number(form.concurrency),
        download_bandwidth: Math.round(Number(form.download_bandwidth)),
        upload_bandwidth: Math.round(Number(form.upload_bandwidth)),
        reconciliation_interval: Number(form.reconciliation_interval),
        max_retries: Number(form.max_retries),
        verify_hash: form.verify_hash,
        file_pause_enabled: form.file_pause_enabled,
        file_pause_min_seconds: Number(form.file_pause_min_seconds),
        file_pause_max_seconds: Number(form.file_pause_max_seconds),
      },
      "Cài đặt đã lưu",
    );
    setSaving(false);
  }
  return (
    <>
      <Heading
        eyebrow="VAULT PREFERENCES"
        title="Cài đặt"
        description="Giới hạn tài nguyên, quản lý tính toàn vẹn và cấu hình kết nối."
      />
      <ErrorBox text={error} />
      <details className="help-disclosure">
        <summary>
          <CircleHelp size={16} /> Thông tin thêm
        </summary>
        <div className="info-callout">
          <ShieldCheck size={18} />
          <p>
            Khởi đầu với một nguồn nhỏ và một worker. Giới hạn tải là lựa chọn
            vận hành, không phải ngưỡng Telegram bảo đảm không khóa tài khoản.
            FloodWait được chờ đầy đủ; gặp 3 lần trong 1 giờ, app nghỉ ít nhất 1
            giờ.
          </p>
        </div>
      </details>
      {form && (
        <form className="preferences" onSubmit={save}>
          <section className="panel preference-panel">
            <div className="preference-head">
              <span className="panel-icon">
                <ArrowUpRight size={20} />
              </span>
              <div>
                <h2>Truyền tải & nghỉ</h2>
                <p>Điều chỉnh tốc độ và khoảng nghỉ.</p>
              </div>
            </div>
            <div className="setting-line">
              <div>
                <strong>File tải/upload song song</strong>
                {rateStatus && <p>Telegram Premium: {rateStatus.premium === true ? "Đã xác nhận" : rateStatus.premium === false ? "Chưa có trên tài khoản kết nối" : "Chưa kiểm tra"} · Nhịp chunk: {Number(rateStatus.media_interval_seconds).toFixed(2)} giây · {rateStatus.lanes_per_file} luồng/file</p>}
                <p>Min 1 · Max 4 · Khuyến nghị 1–2. Chọn 1 nếu thường gặp Flood Wait; 3–4 tăng tải VPS và có thể tăng thời gian chờ Telegram.</p>
                <p>Áp dụng ngay cho slot trống. Giảm số file không ngắt file đang chạy. Xác minh có 1 slot riêng.</p>
              </div>
              <input aria-label="File tải/upload song song" type="number" min="1" max="4" step="1" required
                value={form.concurrency} onChange={(e) => update("concurrency", e.target.value)} />
            </div>
            <div className="setting-line">
              <div>
                <strong>Nghỉ ngẫu nhiên giữa các file</strong>
                <p>Nghỉ sau mỗi file hoàn tất; file đang chạy vẫn tiếp tục.</p>
              </div>
              <label className="switch">
                <input
                  aria-label="Bật nghỉ giữa các file"
                  type="checkbox"
                  checked={form.file_pause_enabled}
                  onChange={(e) =>
                    update("file_pause_enabled", e.target.checked)
                  }
                />
                <span />
              </label>
            </div>
            <div className="setting-line">
              <div>
                <strong>Nghỉ tối thiểu</strong>
                <p>Đơn vị giây · 0–3600.</p>
              </div>
              <input
                aria-label="Nghỉ tối thiểu"
                type="number"
                min="0"
                max="3600"
                required
                disabled={!form.file_pause_enabled}
                value={form.file_pause_min_seconds}
                onChange={(e) =>
                  update("file_pause_min_seconds", e.target.value)
                }
              />
            </div>
            <div className="setting-line">
              <div>
                <strong>Nghỉ tối đa</strong>
                <p>Giây · phải lớn hơn hoặc bằng mức tối thiểu.</p>
              </div>
              <input
                aria-label="Nghỉ tối đa"
                type="number"
                min={form.file_pause_min_seconds || 0}
                max="3600"
                required
                disabled={!form.file_pause_enabled}
                value={form.file_pause_max_seconds}
                onChange={(e) =>
                  update("file_pause_max_seconds", e.target.value)
                }
              />
            </div>
            <div className="setting-line">
              <div>
                <strong>Giới hạn tải xuống</strong>
                <p>Bytes/giây. 0 = không giới hạn.</p>
              </div>
              <input
                aria-label="Giới hạn tải xuống"
                type="number"
                min="0"
                value={form.download_bandwidth}
                onChange={(e) => update("download_bandwidth", e.target.value)}
              />
            </div>
            <div className="setting-line">
              <div>
                <strong>Giới hạn tải lên</strong>
                <p>Bytes/giây · 0 = không giới hạn.</p>
              </div>
              <input
                aria-label="Giới hạn tải lên"
                type="number"
                min="0"
                value={form.upload_bandwidth}
                onChange={(e) => update("upload_bandwidth", e.target.value)}
              />
            </div>
            <div className="setting-line">
              <div>
                <strong>Số lần thử lại tối đa</strong>
                <p>Không tính thời gian chờ Telegram.</p>
              </div>
              <input
                aria-label="Số lần thử lại tối đa"
                type="number"
                min="1"
                max="20"
                value={form.max_retries}
                onChange={(e) => update("max_retries", e.target.value)}
              />
            </div>
            <div className="setting-line">
              <div>
                <strong>File song song</strong>
                <p>Cấu hình trên server.</p>
              </div>
              <span className="value-pill">{form.concurrency} file</span>
            </div>
          </section>
          <section className="panel preference-panel">
            <div className="preference-head">
              <span className="panel-icon">
                <ShieldCheck size={20} />
              </span>
              <div>
                <h2>Xác minh & quét</h2>
                <p>Kiểm tra dữ liệu trước khi đánh dấu hoàn tất.</p>
              </div>
            </div>
            <div className="setting-line">
              <div>
                <strong>Xác minh nội dung</strong>
                <p>
                  Kiểm tra checksum khi upload. Đọc lại SHA-256 khi phục hồi
                  hoặc không có bằng chứng kiểm tra.
                </p>
              </div>
              <label className="switch">
                <input
                  aria-label="Xác minh SHA-256"
                  type="checkbox"
                  checked={form.verify_hash}
                  onChange={(e) => update("verify_hash", e.target.checked)}
                />
                <span />
              </label>
            </div>
            <div className="setting-line">
              <div>
                <strong>Chu kỳ quét (giây)</strong>
                <p>Khoảng cách giữa các lượt kiểm tra tin mới.</p>
              </div>
              <input
                aria-label="Chu kỳ quét (giây)"
                type="number"
                min="30"
                max="86400"
                value={form.reconciliation_interval}
                onChange={(e) =>
                  update("reconciliation_interval", e.target.value)
                }
              />
            </div>
          </section>
          <details className="panel preference-panel security-details">
            <summary>
              <LockKeyhole size={18} /> Kết nối & bảo mật
            </summary>
            <div className="setting-line">
              <div>
                <strong>Kết nối Telegram</strong>
                <p>
                  {form.telegram_mode === "mock"
                    ? "Local test mode dùng metadata/stream mô phỏng."
                    : "Telethon account session trên server."}
                </p>
              </div>
              <code>{form.telegram_mode}</code>
            </div>
            <div className="setting-line">
              <div>
                <strong>Nhịp gọi Telegram</strong>
                <p>
                  Khoảng cách tối thiểu giữa các thao tác được điều tiết; tự
                  tăng khi gặp FloodWait.
                </p>
              </div>
              <code>
                {form.telegram_request_pace}s · {form.concurrency} worker
              </code>
            </div>
            <div className="setting-line">
              <div>
                <strong>Đăng nhập quản trị</strong>
                <p>{form.auth}</p>
              </div>
              <ShieldCheck className="green-text" size={20} />
            </div>
            <div className="setting-line">
              <div>
                <strong>Cookie bảo mật</strong>
                <p>Bật COOKIE_SECURE=true cùng APP_URL HTTPS khi lên VPS.</p>
              </div>
              <span className="value-pill">
                {form.secure_cookie ? "Yêu cầu HTTPS" : "Local HTTP"}
              </span>
            </div>
            <div className="setting-line">
              <div>
                <strong>Đổi mật khẩu</strong>
                <p>Chạy CLI để lưu hash mới và thu hồi các session hiện tại.</p>
              </div>
              <code>telegram-vault init-admin</code>
            </div>
          </details>
          {dirty && (
            <div className="save-bar">
              <span>Thay đổi chưa lưu</span>
              <button
                type="button"
                disabled={saving}
                onClick={() => setForm(data)}
              >
                Hủy thay đổi
              </button>
              <button className="primary" type="submit" disabled={saving}>
                {saving ? (
                  <LoaderCircle className="spin" size={16} />
                ) : (
                  <Check size={16} />
                )}
                Lưu cài đặt
              </button>
            </div>
          )}
        </form>
      )}
    </>
  );
}

createRoot(document.getElementById("root")!).render(<App />);

function TelegramConnection({ navigate }: { navigate: (page: Page) => void }) {
  const [refresh, setRefresh] = useState(0);
  const { data, error: loadError } = useData("/telegram/auth", refresh, 2000);
  const [result, setResult] = useState<Row | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [apiId, setApiId] = useState("");
  const [apiHash, setApiHash] = useState("");
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [editApi, setEditApi] = useState(false);
  const [confirmLogout, setConfirmLogout] = useState(false);
  useEffect(() => {
    if (data) setResult(data);
  }, [data]);
  const state = result || data;
  const step = editApi ? "credentials" : state?.step || "credentials";
  const blocked =
    busy ||
    state?.busy ||
    !state?.can_control ||
    state?.mode === "mock" ||
    state?.retry_after > 1;
  async function submit(path: string, body?: Row) {
    setBusy(true);
    setError("");
    try {
      const next = await api(`/telegram/${path}`, "POST", body);
      setResult(next);
      setRefresh((x) => x + 1);
      setEditApi(false);
      setConfirmLogout(false);
      setApiHash("");
      setCode("");
      setPassword("");
    } catch (e) {
      setError((e as Error).message);
      setCode("");
      setPassword("");
      setRefresh((x) => x + 1);
    } finally {
      setBusy(false);
    }
  }
  const number =
    step === "credentials"
      ? 1
      : step === "phone"
        ? 2
        : step === "connected"
          ? 4
          : 3;
  return (
    <>
      <Heading
        eyebrow="ACCOUNT CONNECTION"
        title="Kết nối Telegram"
        description="Đăng nhập tài khoản cá nhân để chọn group, topics và bắt đầu backup."
      />
      <ErrorBox text={error || loadError} />
      <section className="panel telegram-connect">
        {step !== "connected" && (
          <div className="telegram-steps" aria-label="Các bước đăng nhập">
            {["API Telegram", "Số điện thoại", "OTP / 2FA", "Kết nối"].map(
              (label, index) => (
                <span
                  className={number >= index + 1 ? "current" : ""}
                  key={label}
                >
                  <b>{index + 1}</b>
                  {label}
                </span>
              ),
            )}
          </div>
        )}
        {state?.mode === "mock" ? (
          <Empty icon={Zap} title="Local test mode">
            Instance này dùng Telegram giả lập. Đăng nhập tài khoản thật tại
            instance VPS.
          </Empty>
        ) : (
          state && (
            <>
              {state.state === "account_mismatch" && (
                <p className="telegram-notice">
                  Session thuộc tài khoản khác với nguồn đã lưu. Tạm dừng các
                  nguồn, sau đó{" "}
                  <button onClick={() => setConfirmLogout(true)}>
                    Ngắt kết nối
                  </button>{" "}
                  để đăng nhập lại.
                </p>
              )}
              {!state.can_control && (
                <p role="status" className="telegram-notice">
                  Một phiên quản trị khác đang đăng nhập. Chờ phiên đó hoàn tất
                  hoặc hết hạn.
                </p>
              )}
              {state.retry_after > 1 && (
                <p role="status" className="telegram-notice">
                  Telegram đang giới hạn yêu cầu. Thử lại sau khoảng{" "}
                  {state.retry_after} giây.
                </p>
              )}
              {step === "credentials" && (
                <form
                  className="telegram-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void submit("credentials", {
                      api_id: Number(apiId),
                      api_hash: apiHash.trim(),
                    });
                  }}
                >
                  <h2>1. Cấu hình API Telegram</h2>
                  <p>
                    Lấy thông tin tại{" "}
                    <a
                      href="https://my.telegram.org/apps"
                      target="_blank"
                      rel="noreferrer"
                    >
                      my.telegram.org → API development tools
                    </a>
                    . API ID và API hash thuộc ứng dụng Telegram của bạn.
                  </p>
                  <label>
                    API ID
                    <input
                      type="number"
                      min="1"
                      max="2147483647"
                      required
                      value={apiId}
                      onChange={(e) => setApiId(e.target.value)}
                      autoComplete="off"
                    />
                  </label>
                  <label>
                    API hash
                    <input
                      type="password"
                      required
                      minLength={32}
                      maxLength={32}
                      pattern="[a-fA-F0-9]{32}"
                      value={apiHash}
                      onChange={(e) => setApiHash(e.target.value)}
                      autoComplete="new-password"
                    />
                  </label>
                  <p className="muted">
                    Thông tin được lưu trong file private trên server; API hash
                    không hiển thị lại trên web.
                  </p>
                  <div className="telegram-actions">
                    <button className="primary" disabled={blocked}>
                      {busy && <LoaderCircle className="spin" size={16} />}Lưu
                      API và tiếp tục
                    </button>
                    {state.configured && (
                      <button type="button" onClick={() => setEditApi(false)}>
                        Quay lại
                      </button>
                    )}
                  </div>
                </form>
              )}
              {step === "phone" && (
                <form
                  className="telegram-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void submit("send-code", {
                      phone: phone.replace(/\s/g, ""),
                    });
                  }}
                >
                  <h2>2. Nhập số điện thoại</h2>
                  <p>
                    API đã cấu hình. Nhập số điện thoại kèm mã quốc gia, ví dụ
                    +84901234567.
                  </p>
                  <label>
                    Số điện thoại Telegram
                    <input
                      type="tel"
                      required
                      pattern="\+[1-9][0-9]{6,14}"
                      placeholder="+84…"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      autoComplete="tel"
                    />
                  </label>
                  <p className="muted">
                    Telegram có thể gửi mã vào ứng dụng Telegram hoặc SMS. Chỉ
                    gửi lại khi đã chờ đủ 60 giây.
                  </p>
                  <div className="telegram-actions">
                    <button
                      className="primary"
                      disabled={blocked || Date.now() / 1000 < state.send_after}
                    >
                      {busy && <LoaderCircle className="spin" size={16} />}Gửi
                      mã đăng nhập
                    </button>
                    <button
                      type="button"
                      disabled={blocked}
                      onClick={() => setEditApi(true)}
                    >
                      Đổi API
                    </button>
                  </div>
                </form>
              )}
              {step === "code" && (
                <form
                  className="telegram-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void submit("verify-code", { code });
                  }}
                >
                  <h2>3. Xác nhận mã OTP</h2>
                  <p>
                    Kiểm tra tin nhắn từ Telegram trên ứng dụng hoặc SMS của số{" "}
                    {state.phone}. Phiên xác nhận có hiệu lực tối đa 10 phút.
                  </p>
                  <label>
                    Mã OTP
                    <input
                      required
                      inputMode="numeric"
                      pattern="[0-9]{4,10}"
                      maxLength={10}
                      value={code}
                      onChange={(e) =>
                        setCode(e.target.value.replace(/\D/g, ""))
                      }
                      autoComplete="one-time-code"
                    />
                  </label>
                  <div className="telegram-actions">
                    <button className="primary" disabled={blocked}>
                      {busy && <LoaderCircle className="spin" size={16} />}Xác
                      nhận mã OTP
                    </button>
                    <button
                      type="button"
                      disabled={blocked}
                      onClick={() => void submit("cancel")}
                    >
                      Hủy / gửi mã mới
                    </button>
                  </div>
                </form>
              )}
              {step === "password" && (
                <form
                  className="telegram-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    void submit("verify-password", { password });
                  }}
                >
                  <h2>Xác minh hai bước</h2>
                  <p>
                    Tài khoản này bật 2FA. Nhập mật khẩu xác minh hai bước của
                    Telegram.
                  </p>
                  <label>
                    Mật khẩu 2FA
                    <input
                      type="password"
                      required
                      maxLength={512}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      autoComplete="off"
                    />
                  </label>
                  <p className="muted">
                    OTP và mật khẩu 2FA không được lưu trên server. Session đăng
                    nhập được giữ riêng để backup tiếp tục sau restart.
                  </p>
                  <div className="telegram-actions">
                    <button className="primary" disabled={blocked}>
                      {busy && <LoaderCircle className="spin" size={16} />}Kết
                      nối tài khoản
                    </button>
                    <button
                      type="button"
                      disabled={blocked}
                      onClick={() => void submit("cancel")}
                    >
                      Hủy đăng nhập
                    </button>
                  </div>
                </form>
              )}
              {step === "connected" && (
                <div className="telegram-form">
                  <ShieldCheck size={40} />
                  <h2>Telegram đã kết nối</h2>
                  <p>
                    Bạn có thể khám phá group, chọn topics và bắt đầu backup.
                    Session được lưu riêng trên server.
                  </p>
                  <div className="telegram-actions">
                    <button
                      className="primary"
                      onClick={() => navigate("sources")}
                    >
                      Đi tới nguồn
                    </button>
                    <button
                      disabled={blocked}
                      onClick={() => setConfirmLogout(true)}
                    >
                      Ngắt kết nối
                    </button>
                  </div>
                </div>
              )}
            </>
          )
        )}
      </section>
      <details className="panel telegram-help">
        <summary>
          <CircleHelp size={17} /> Hướng dẫn đăng nhập
        </summary>
        <ol>
          <li>
            Tạo API tại my.telegram.org, chọn API development tools và điền
            thông tin ứng dụng.
          </li>
          <li>
            Lưu API ID/API hash trên trang này, gửi mã đến số điện thoại của
            bạn.
          </li>
          <li>Nhập OTP, sau đó nhập mật khẩu 2FA nếu Telegram yêu cầu.</li>
          <li>Mở Nguồn Telegram, thêm group và chọn topics cần backup.</li>
        </ol>
        <p>
          Không gửi mã OTP hoặc mật khẩu 2FA vào chat. Nếu server restart giữa
          chừng, gửi mã mới để tiếp tục.
        </p>
      </details>
      {confirmLogout && (
        <Modal
          title="Ngắt kết nối Telegram?"
          close={() => setConfirmLogout(false)}
        >
          <p>
            Session trên server sẽ được đăng xuất. Tạm dừng các nguồn và chờ
            transfer hoàn tất trước khi tiếp tục. File backup được giữ lại.
          </p>
          <div className="telegram-actions">
            <button onClick={() => setConfirmLogout(false)}>Quay lại</button>
            <button
              className="primary"
              disabled={busy}
              onClick={() => void submit("logout")}
            >
              Xác nhận ngắt kết nối
            </button>
          </div>
        </Modal>
      )}
    </>
  );
}
