"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ClipboardList,
  Loader2,
  Phone,
  Plus,
  RefreshCw,
  Send,
  Ticket,
} from "lucide-react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  IconButton,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import type { ActivityLogEntry, CustomerSearchResult, ManualOrderResult, Order, OverviewDashboard } from "@/lib/api";
import { createManualOrder, generateManualActiveCode, generateManualJoinLink, getActivityLog, getDashboardOverview, getOrders, searchCustomers } from "@/lib/api";
import { AppSection, AppToolbar, statusChipSx } from "../dashboard-components";
import { dateTextShort, dateTimePreviewText, daysUntil, orderLifecycleLabel, resolveOrderLabel, orderNoteText, isOrderActive, displayText } from "../dashboard-helpers";

type MobileAction = "lookup" | "manual";

function getStoredSecret() {
  if (typeof window === "undefined") return "";
  return window.localStorage.getItem("prive_admin_secret") || "";
}

function formatActivityLabel(item: ActivityLogEntry) {
  const title = item.title || item.typeLabel || item.type || "log";
  const detail = item.detail || "-";
  return { title, detail };
}

function miniStatusChipLabel(order: Order) {
  const active = isOrderActive(order);
  if (order.status === "PAID" && active) return "Active";
  return String(order.status || "-");
}

export default function MobileAdminPage() {
  const router = useRouter();
  const [secret, setSecret] = useState("");
  const [savedSecret, setSavedSecret] = useState("");
  const [refreshing, setRefreshing] = useState(false);
  const [reloadTick, setReloadTick] = useState(0);
  const [orders, setOrders] = useState<Order[]>([]);
  const [overview, setOverview] = useState<OverviewDashboard | null>(null);
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([]);
  const [customerQuery, setCustomerQuery] = useState("");
  const [customerLoading, setCustomerLoading] = useState(false);
  const [customerResults, setCustomerResults] = useState<CustomerSearchResult[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerSearchResult | null>(null);
  const [manualTab, setManualTab] = useState<MobileAction>("manual");
  const [manualSubmitting, setManualSubmitting] = useState(false);
  const [manualResult, setManualResult] = useState<ManualOrderResult | null>(null);
  const [copyNote, setCopyNote] = useState("");
  const [manualForm, setManualForm] = useState({
    telegram_user_id: "",
    full_name: "",
    plan_name: "FULL_1M",
    admin_label: "Full 1 tháng",
    amount: "",
    duration_days: "30",
    expire_at: "",
    payment_currency: "VND",
    payment_provider: "PAYOS",
    note: "",
  });

  const lastOrders = useMemo(() => [...orders].slice().sort((a, b) => String(b.created_at).localeCompare(String(a.created_at))).slice(0, 12), [orders]);
  const topActivity = useMemo(() => activityLog.slice(0, 12), [activityLog]);

  useEffect(() => {
    const stored = getStoredSecret();
    if (stored) {
      setSecret(stored);
      setSavedSecret(stored);
    }
  }, []);

  useEffect(() => {
    if (!savedSecret) return;
    let active = true;
    const load = async () => {
      setRefreshing(true);
      try {
        const [ordersRes, overviewRes, activityRes] = await Promise.all([
          getOrders(savedSecret, 120),
          getDashboardOverview(savedSecret),
          getActivityLog(savedSecret, { page: 1, limit: 30, direction: "all", type: "ALL", date: "ALL" }),
        ]);
        if (!active) return;
        setOrders(ordersRes.data || []);
        setOverview(overviewRes.data || null);
        setActivityLog(activityRes.data || []);
      } catch (error) {
        console.error(error);
      } finally {
        if (active) setRefreshing(false);
      }
    };
    void load();
    return () => {
      active = false;
    };
  }, [savedSecret, reloadTick]);

  useEffect(() => {
    if (!savedSecret || customerQuery.trim().length < 2) {
      setCustomerResults([]);
      setSelectedCustomer(null);
      return;
    }
    const timer = window.setTimeout(() => {
      setCustomerLoading(true);
      searchCustomers(savedSecret, customerQuery.trim(), 6)
        .then((res) => {
          const rows = res.data || [];
          setCustomerResults(rows);
          setSelectedCustomer(rows[0] || null);
        })
        .catch((error) => console.error(error))
        .finally(() => setCustomerLoading(false));
    }, 350);
    return () => window.clearTimeout(timer);
  }, [savedSecret, customerQuery]);

  useEffect(() => {
    if (!savedSecret) return;
    setManualForm((current) => ({
      ...current,
      telegram_user_id: selectedCustomer?.id || current.telegram_user_id,
      full_name: selectedCustomer?.name && selectedCustomer.name !== "-" ? selectedCustomer.name : current.full_name,
    }));
  }, [savedSecret, selectedCustomer]);

  async function login() {
    const value = secret.trim();
    if (!value) return;
    window.localStorage.setItem("prive_admin_secret", value);
    setSavedSecret(value);
  }

  async function refreshAll() {
    if (!savedSecret) return;
    setReloadTick((value) => value + 1);
  }

  async function copyText(value: string, label: string) {
    if (!value) return;
    await navigator.clipboard.writeText(value);
    setCopyNote(`Đã copy ${label}.`);
    window.setTimeout(() => setCopyNote(""), 1800);
  }

  async function submitManualOrder() {
    if (!savedSecret) return;
    setManualSubmitting(true);
    setCopyNote("");
    try {
      const res = await createManualOrder(savedSecret, {
        telegram_user_id: manualForm.telegram_user_id.trim(),
        full_name: displayText(manualForm.full_name) || undefined,
        plan_name: manualForm.plan_name.trim(),
        admin_label: displayText(manualForm.admin_label) || undefined,
        amount: manualForm.amount.trim() || undefined,
        duration_days: manualForm.duration_days.trim() || undefined,
        expire_at: manualForm.expire_at.trim() || undefined,
        note: displayText(manualForm.note) || undefined,
        payment_currency: manualForm.payment_currency.trim() || undefined,
        payment_provider: manualForm.payment_provider.trim() || undefined,
      });
      setManualResult(res.data);
      setCopyNote("Đã tạo đơn thủ công.");
      await refreshAll();
    } catch (error) {
      console.error(error);
      setCopyNote("Tạo đơn thất bại.");
    } finally {
      setManualSubmitting(false);
    }
  }

  async function submitActiveCode() {
    if (!savedSecret || !manualResult) return;
    try {
      const res = await generateManualActiveCode(savedSecret, {
        order_id: manualResult.order_id,
        telegram_user_id: manualResult.telegram_user_id,
        full_name: manualResult.full_name,
        plan_name: manualResult.plan_name,
        expire_at: manualResult.expire_at,
        expire_at_iso: manualResult.expire_at_iso,
      });
      setManualResult((current) => current ? { ...current, activation_code: res.data.activation_code, activation_url: res.data.activation_url, manual_order_message_url: res.data.manual_order_message_url, manual_order_text: res.data.manual_order_text } : current);
      setCopyNote("Đã gen active code.");
    } catch (error) {
      console.error(error);
      setCopyNote("Gen active code thất bại.");
    }
  }

  async function submitJoinLink() {
    if (!savedSecret || !manualResult) return;
    try {
      const res = await generateManualJoinLink(savedSecret, {
        order_id: manualResult.order_id,
        telegram_user_id: manualResult.telegram_user_id,
        full_name: manualResult.full_name,
        plan_name: manualResult.plan_name,
        expire_at: manualResult.expire_at,
      });
      setManualResult((current) => current ? { ...current, links_text: res.data.links_text, support_text: res.data.support_text, support_link: res.data.support_link, support_error: res.data.support_error, manual_order_join_text: res.data.manual_order_join_text } : current);
      setCopyNote("Đã gen link join group.");
    } catch (error) {
      console.error(error);
      setCopyNote("Gen link join group thất bại.");
    }
  }

  if (!savedSecret) {
    return (
      <Box sx={{ minHeight: "100vh", bgcolor: "background.default", p: 2, display: "grid", placeItems: "center" }}>
        <Card sx={{ width: "100%", maxWidth: 420 }}>
          <CardContent sx={{ p: 2.5, display: "grid", gap: 2 }}>
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 900, letterSpacing: "-0.03em" }}>Hang Cú VIP Mobile</Typography>
              <Typography variant="body2" color="text.secondary">Đăng nhập để mở giao diện điều khiển đơn hàng tối ưu cho điện thoại.</Typography>
            </Box>
            <TextField type="password" label="Mật khẩu admin" value={secret} onChange={(event) => setSecret(event.target.value)} placeholder="Dán ADMIN_SECRET" fullWidth size="small" />
            <Button variant="contained" onClick={login} size="large" startIcon={<Phone size={18} />}>Vào bản mobile</Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "#f8fafc", pb: 10 }}>
      <Box sx={{ position: "sticky", top: 0, zIndex: 20, backdropFilter: "blur(16px)", bgcolor: "rgba(248,250,252,0.9)", borderBottom: "1px solid rgba(148,163,184,0.16)" }}>
        <Box sx={{ px: 2, py: 1.5, display: "flex", justifyContent: "space-between", gap: 1, alignItems: "center" }}>
          <Box sx={{ minWidth: 0 }}>
            <Typography sx={{ fontWeight: 900, letterSpacing: "-0.03em", lineHeight: 1.1 }}>Mobile Control</Typography>
            <Typography variant="caption" color="text.secondary">Đơn hàng, tra cứu khách, active code, join link.</Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <IconButton size="small" onClick={() => void refreshAll()} disabled={refreshing}>
              {refreshing ? <Loader2 size={18} className="spin" /> : <RefreshCw size={18} />}
            </IconButton>
            <IconButton size="small" onClick={() => router.push("/") }><ArrowLeft size={18} /></IconButton>
          </Stack>
        </Box>
        <Box sx={{ px: 1.5, pb: 1.25 }}>
          <Tabs value={manualTab} onChange={(_, value) => setManualTab(value)} variant="scrollable" scrollButtons="auto" sx={{ minHeight: 40, "& .MuiTab-root": { minHeight: 40, textTransform: "none", fontWeight: 800 } }}>
            <Tab value="manual" label="Tác vụ" />
            <Tab value="lookup" label="Tra cứu" />
          </Tabs>
        </Box>
      </Box>

        <Box sx={{ px: 1.5, pt: 1.5, display: "grid", gap: 1.5 }}>
        {refreshing ? <Chip label="Đang tải dữ liệu..." size="small" variant="outlined" /> : null}
        <Box sx={{ display: "grid", gap: 1.25, gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
          <Card><CardContent sx={{ p: 1.5 }}><Typography variant="caption" color="text.secondary">Đơn</Typography><Typography sx={{ fontWeight: 900, fontSize: 24 }}>{orders.length}</Typography></CardContent></Card>
          <Card><CardContent sx={{ p: 1.5 }}><Typography variant="caption" color="text.secondary">PAID</Typography><Typography sx={{ fontWeight: 900, fontSize: 24 }}>{orders.filter((item) => item.status === "PAID").length}</Typography></CardContent></Card>
          <Card><CardContent sx={{ p: 1.5 }}><Typography variant="caption" color="text.secondary">Khách</Typography><Typography sx={{ fontWeight: 900, fontSize: 24 }}>{overview?.counts?.orders ?? selectedCustomer?.paidOrderCount ?? 0}</Typography></CardContent></Card>
          <Card><CardContent sx={{ p: 1.5 }}><Typography variant="caption" color="text.secondary">Log</Typography><Typography sx={{ fontWeight: 900, fontSize: 24 }}>{activityLog.length}</Typography></CardContent></Card>
        </Box>

        {copyNote ? <Alert severity={copyNote.includes("thất bại") ? "error" : "success"} variant="outlined">{copyNote}</Alert> : null}

        {manualTab === "lookup" ? (
          <AppSection title="Tra cứu khách hàng" subtitle="Nhập Telegram ID, tên, hoặc từ khóa gói." accent="violet">
            <Stack spacing={1.25}>
              <TextField size="small" value={customerQuery} onChange={(event) => setCustomerQuery(event.target.value)} placeholder="Ví dụ: 7508222302, @username, tên khách" fullWidth />
              {customerLoading ? <Chip icon={<Loader2 size={14} className="spin" />} label="Đang tra cứu" /> : null}
              {customerResults.map((item) => (
                <Card key={item.id} variant="outlined" onClick={() => setSelectedCustomer(item)} sx={{ cursor: "pointer", borderColor: selectedCustomer?.id === item.id ? "primary.main" : "divider" }}>
                  <CardContent sx={{ p: 1.5, display: "grid", gap: 0.75 }}>
                    <Box sx={{ display: "flex", justifyContent: "space-between", gap: 1 }}>
                      <Box>
                        <Typography sx={{ fontWeight: 800 }}>{item.name || "-"}</Typography>
                        <Typography variant="caption" color="text.secondary">{item.id}</Typography>
                      </Box>
                      <Chip size="small" label={item.statusText} sx={statusChipSx(item.isBlacklisted ? "error" : item.hasActiveOrder ? "success" : item.hasPaidOrder ? "warning" : "muted")} />
                    </Box>
                    <Typography variant="body2" color="text.secondary">{item.latestExpireText}</Typography>
                    <Box sx={{ display: "flex", gap: 0.75, flexWrap: "wrap" }}>
                      <Chip size="small" label={`${item.paidOrderCount} paid`} variant="outlined" />
                      <Chip size="small" label={`${item.activeOrderCount} active`} variant="outlined" />
                      {item.isBlacklisted ? <Chip size="small" color="error" label="Blacklist" variant="outlined" /> : null}
                    </Box>
                  </CardContent>
                </Card>
              ))}
              {selectedCustomer ? (
                <Card variant="outlined">
                  <CardContent sx={{ p: 1.5, display: "grid", gap: 1 }}>
                    <Typography sx={{ fontWeight: 900 }}>{selectedCustomer.name || "-"}</Typography>
                    <Typography variant="body2" color="text.secondary">{selectedCustomer.id}</Typography>
                    <Divider />
                    <Typography variant="body2">Gói gần nhất: <strong>{selectedCustomer.latestExpireOrder ? resolveOrderLabel(selectedCustomer.latestExpireOrder).displayLabel : "-"}</strong></Typography>
                    <Typography variant="body2">Tên kỹ thuật: {selectedCustomer.latestExpireOrder ? resolveOrderLabel(selectedCustomer.latestExpireOrder).techLabel : "-"}</Typography>
                    <Typography variant="body2">Hạn gần nhất: {selectedCustomer.latestExpireText}</Typography>
                    <Button variant="outlined" onClick={() => setManualTab("manual")} startIcon={<Plus size={16} />}>Dùng thông tin này để tạo đơn</Button>
                  </CardContent>
                </Card>
              ) : null}
            </Stack>
          </AppSection>
        ) : null}

        {manualTab === "manual" ? (
          <AppSection title="Tạo đơn thủ công" subtitle="Màn hình ngắn gọn để tạo order và lấy active code/join link." accent="blue">
            <Stack spacing={1.25}>
              <TextField size="small" label="Telegram ID" value={manualForm.telegram_user_id} onChange={(event) => setManualForm((current) => ({ ...current, telegram_user_id: event.target.value }))} fullWidth />
              <TextField size="small" label="Tên khách" value={manualForm.full_name} onChange={(event) => setManualForm((current) => ({ ...current, full_name: event.target.value }))} fullWidth />
              <TextField size="small" label="Plan name" value={manualForm.plan_name} onChange={(event) => setManualForm((current) => ({ ...current, plan_name: event.target.value }))} fullWidth />
              <TextField size="small" label="Admin label" value={manualForm.admin_label} onChange={(event) => setManualForm((current) => ({ ...current, admin_label: event.target.value }))} fullWidth />
              <Box sx={{ display: "grid", gap: 1.25, gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
                <TextField size="small" label="Số tiền" value={manualForm.amount} onChange={(event) => setManualForm((current) => ({ ...current, amount: event.target.value }))} />
                <TextField size="small" label="Số ngày" value={manualForm.duration_days} onChange={(event) => setManualForm((current) => ({ ...current, duration_days: event.target.value }))} />
              </Box>
              <TextField size="small" label="Expire at" value={manualForm.expire_at} onChange={(event) => setManualForm((current) => ({ ...current, expire_at: event.target.value }))} placeholder="YYYY-MM-DD HH:mm" fullWidth />
              <Box sx={{ display: "grid", gap: 1.25, gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
                <TextField size="small" label="Currency" value={manualForm.payment_currency} onChange={(event) => setManualForm((current) => ({ ...current, payment_currency: event.target.value }))} />
                <TextField size="small" label="Provider" value={manualForm.payment_provider} onChange={(event) => setManualForm((current) => ({ ...current, payment_provider: event.target.value }))} />
              </Box>
              <TextField size="small" label="Note" value={manualForm.note} onChange={(event) => setManualForm((current) => ({ ...current, note: event.target.value }))} multiline minRows={2} fullWidth />
              <Button variant="contained" onClick={() => void submitManualOrder()} disabled={manualSubmitting} startIcon={manualSubmitting ? <Loader2 size={16} className="spin" /> : <ClipboardList size={16} />}>Tạo đơn</Button>
            </Stack>
          </AppSection>
        ) : null}

        <AppSection
          title="Danh sách đơn gần đây"
          subtitle="Card list gọn để thao tác nhanh trên màn nhỏ."
          action={<AppToolbar><Button size="small" variant="outlined" onClick={() => void refreshAll()} startIcon={<RefreshCw size={14} />}>Tải lại</Button></AppToolbar>}
          accent="blue"
        >
          <Stack spacing={1}>
            {lastOrders.map((order) => (
              <Card key={order.order_id} variant="outlined">
                <CardContent sx={{ p: 1.5, display: "grid", gap: 0.75 }}>
                  <Box sx={{ display: "flex", justifyContent: "space-between", gap: 1, alignItems: "start" }}>
                    <Box sx={{ minWidth: 0 }}>
                      <Typography sx={{ fontWeight: 900, lineHeight: 1.2 }}>{resolveOrderLabel(order).displayLabel}</Typography>
                      <Typography variant="caption" color="text.secondary">{order.telegram_user_id} · {order.order_id}</Typography>
                    </Box>
                    <Chip size="small" label={miniStatusChipLabel(order)} color={order.status === "PAID" ? "success" : "default"} variant="outlined" />
                  </Box>
                  <Typography variant="body2" color="text.secondary">{orderLifecycleLabel(order)} · {dateTextShort(order.created_at)}</Typography>
                  <Typography variant="body2">Hạn: <strong>{dateTimePreviewText(order.expire_at)}</strong> · còn {daysUntil(order.expire_at)} ngày</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ wordBreak: "break-word" }}>{orderNoteText(order) || "Không có note"}</Typography>
                </CardContent>
              </Card>
            ))}
          </Stack>
        </AppSection>

        <AppSection
          title="Nhật ký gần đây"
          subtitle="Dòng log ngắn, đủ để nắm thao tác mới nhất."
          accent="violet"
        >
          <Stack spacing={1}>
            {topActivity.map((item) => {
              const label = formatActivityLabel(item);
              return (
                <Card key={item.id} variant="outlined">
                  <CardContent sx={{ p: 1.5, display: "grid", gap: 0.5 }}>
                    <Box sx={{ display: "flex", justifyContent: "space-between", gap: 1 }}>
                      <Typography sx={{ fontWeight: 800 }}>{label.title}</Typography>
                      <Typography variant="caption" color="text.secondary">{dateTextShort(item.createdAt)}</Typography>
                    </Box>
                    <Typography variant="body2" color="text.secondary">{label.detail}</Typography>
                  </CardContent>
                </Card>
              );
            })}
          </Stack>
        </AppSection>

        {manualResult ? (
          <AppSection title="Kết quả gần nhất" subtitle="Nhanh tay copy ngay khi cần." accent="emerald">
            <Stack spacing={1}>
              <Card variant="outlined"><CardContent sx={{ p: 1.5, display: "grid", gap: 1 }}><Typography sx={{ fontWeight: 800 }}>{manualResult.manual_order_text}</Typography><Button variant="outlined" onClick={() => void copyText(manualResult.manual_order_text, "manual text")}>Copy text</Button></CardContent></Card>
              <Box sx={{ position: "sticky", bottom: 12, zIndex: 5, display: "grid", gap: 1, gridTemplateColumns: "repeat(2, minmax(0, 1fr))", p: 1, mt: 0.5, borderRadius: 3, bgcolor: "rgba(255,255,255,0.92)", backdropFilter: "blur(10px)", boxShadow: "0 12px 30px rgba(15,23,42,0.08)", border: "1px solid rgba(148,163,184,0.16)" }}>
                <Button variant="contained" onClick={() => void submitActiveCode()} startIcon={<Ticket size={16} />}>Gen active code</Button>
                <Button variant="outlined" onClick={() => void submitJoinLink()} startIcon={<Send size={16} />}>Gen join group</Button>
              </Box>
              {manualResult.activation_url ? <Card variant="outlined"><CardContent sx={{ p: 1.5, display: "grid", gap: 1 }}><Typography variant="body2" sx={{ wordBreak: "break-word" }}>{manualResult.activation_url}</Typography><Button size="small" variant="outlined" onClick={() => void copyText(manualResult.activation_url, "active link")}>Copy link</Button></CardContent></Card> : null}
              {manualResult.links_text ? <Card variant="outlined"><CardContent sx={{ p: 1.5, display: "grid", gap: 1 }}><Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{manualResult.links_text}</Typography><Button size="small" variant="outlined" onClick={() => void copyText(manualResult.links_text, "join text")}>Copy text</Button></CardContent></Card> : null}
              {manualResult.support_text ? <Card variant="outlined"><CardContent sx={{ p: 1.5, display: "grid", gap: 1 }}><Typography sx={{ fontWeight: 800 }}>Support</Typography><Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{manualResult.support_text}</Typography></CardContent></Card> : null}
            </Stack>
          </AppSection>
        ) : null}
      </Box>
    </Box>
  );
}
