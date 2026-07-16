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
  MenuItem,
  Tooltip,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import type { ActivityLogEntry, CustomerSearchResult, ManualOrderResult, Order } from "@/lib/api";
import { createManualOrder, generateManualActiveCode, generateManualJoinLink, getActivityLog, getConfig, getDashboardOverview, getOrders, searchCustomers } from "@/lib/api";
import { AppSection, AppToolbar, MuiDialogShell, statusChipSx } from "../dashboard-components";
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
  const [activityLog, setActivityLog] = useState<ActivityLogEntry[]>([]);
  const [customerQuery, setCustomerQuery] = useState("");
  const [customerLoading, setCustomerLoading] = useState(false);
  const [customerResults, setCustomerResults] = useState<CustomerSearchResult[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<CustomerSearchResult | null>(null);
  const [manualTab, setManualTab] = useState<MobileAction>("manual");
  const [manualDrawerOpen, setManualDrawerOpen] = useState(false);
  const [manualSubmitting, setManualSubmitting] = useState(false);
  const [manualResult, setManualResult] = useState<ManualOrderResult | null>(null);
  const [customDurationEnabled, setCustomDurationEnabled] = useState(true);
  const [copyNote, setCopyNote] = useState("");
  const [manualForm, setManualForm] = useState({
    telegram_user_id: "",
    full_name: "",
    plan_name: "FULL_1M",
    plan_mode: "",
    entitlement_type: "ALL_ACCESS",
    entitlement_key: "",
    amount: "",
    duration_days: "30",
    expire_at: "",
    payment_currency: "VND",
    payment_provider: "PAYOS",
    note: "",
  });

  const lastOrders = useMemo(() => [...orders].slice().sort((a, b) => String(b.created_at).localeCompare(String(a.created_at))).slice(0, 12), [orders]);
  const topActivity = useMemo(() => activityLog.slice(0, 12), [activityLog]);
  const uniqueCustomerCount = useMemo(() => new Set(orders.map((item) => String(item.telegram_user_id || "").trim()).filter(Boolean)).size, [orders]);
  const selectedCustomerOrderLabel = useMemo(() => {
    const activeOrder = selectedCustomer?.activeOrders?.[0] || null;
    const latestPaidOrder = selectedCustomer?.paidOrders?.[0] || null;
    const targetOrder = activeOrder || latestPaidOrder || selectedCustomer?.latestExpireOrder || null;
    return targetOrder ? resolveOrderLabel(targetOrder) : null;
  }, [selectedCustomer]);

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
        const [ordersRes, , activityRes, configRes] = await Promise.all([
          getOrders(savedSecret, 120),
          getDashboardOverview(savedSecret),
          getActivityLog(savedSecret, { page: 1, limit: 30, direction: "all", type: "ALL", date: "ALL" }),
          getConfig(savedSecret),
        ]);
        if (!active) return;
        setOrders(ordersRes.data || []);
        setActivityLog(activityRes.data || []);
        const customFlag = (configRes.data || []).find((item) => item.key === "MANUAL_CUSTOM_DURATION_ENABLED")?.value;
        setCustomDurationEnabled(!customFlag || ["ON", "1", "TRUE", "YES"].includes(String(customFlag).toUpperCase()));
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
      plan_name: selectedCustomerOrderLabel?.techLabel || current.plan_name,
    }));
  }, [savedSecret, selectedCustomer, selectedCustomerOrderLabel]);

  function openManualDrawerFromCustomer(customer?: CustomerSearchResult | null) {
    setManualTab("manual");
    if (customer) {
      const activeOrder = customer.activeOrders?.[0] || null;
      const latestPaidOrder = customer.paidOrders?.[0] || null;
      const targetOrder = activeOrder || latestPaidOrder || customer.latestExpireOrder || null;
      const latestLabel = targetOrder ? resolveOrderLabel(targetOrder) : null;
      setManualForm((current) => ({
        ...current,
        telegram_user_id: customer.id || current.telegram_user_id,
        full_name: customer.name && customer.name !== "-" ? customer.name : current.full_name,
        plan_name: latestLabel?.techLabel || current.plan_name,
      }));
    }
    setManualDrawerOpen(true);
  }

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
        plan_mode: manualForm.plan_mode || undefined,
        entitlement_type: manualForm.plan_mode === "CUSTOM_DURATION" ? manualForm.entitlement_type : undefined,
        entitlement_key: manualForm.plan_mode === "CUSTOM_DURATION" ? manualForm.entitlement_key : undefined,
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
          <Card><CardContent sx={{ p: 1.5 }}><Typography variant="caption" color="text.secondary">Khách</Typography><Typography sx={{ fontWeight: 900, fontSize: 24 }}>{uniqueCustomerCount}</Typography></CardContent></Card>
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
                    {selectedCustomer.latestExpireOrder ? (
                      <Tooltip title={`Kỹ thuật: ${resolveOrderLabel(selectedCustomer.latestExpireOrder).techLabel}`} arrow>
                        <Chip size="small" label="Thông tin kỹ thuật" variant="outlined" sx={{ width: "fit-content", fontWeight: 700 }} />
                      </Tooltip>
                    ) : null}
                    <Typography variant="body2">Hạn gần nhất: {selectedCustomer.latestExpireText}</Typography>
                    <Stack direction="row" spacing={1}>
                      <Button variant="outlined" onClick={() => openManualDrawerFromCustomer(selectedCustomer)} startIcon={<Plus size={16} />}>Dùng thông tin này để tạo đơn</Button>
                      <Button variant="contained" onClick={() => openManualDrawerFromCustomer(selectedCustomer)} startIcon={<ClipboardList size={16} />}>Mở lại drawer</Button>
                    </Stack>
                  </CardContent>
                </Card>
              ) : null}
            </Stack>
          </AppSection>
        ) : null}

        {manualTab === "manual" ? (
          <AppSection
            title="Tạo đơn thủ công"
            subtitle="Mở drawer tạo đơn theo đúng luồng PC, rồi lấy active code/join link ngay trong kết quả."
            accent="blue"
            action={<Button variant="contained" onClick={() => openManualDrawerFromCustomer(selectedCustomer)} startIcon={<ClipboardList size={16} />}>Tạo đơn</Button>}
          >
            <Stack spacing={1.25}>
              <Alert severity="info" variant="outlined">Bấm nút Tạo đơn để mở drawer giống PC, form sẽ giữ cùng nhịp thao tác nhưng tối ưu cho màn nhỏ.</Alert>
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

      <MuiDialogShell
        open={manualDrawerOpen}
        title="Tạo đơn thủ công"
        subtitle="Nhập thông tin khách, tạo order PAID và gen link join group."
        onClose={() => setManualDrawerOpen(false)}
        maxWidth="md"
        fullScreenOnMobile
        actions={
          <>
            <Button variant="outlined" onClick={() => setManualDrawerOpen(false)}>Đóng</Button>
            <Button variant="contained" onClick={() => void submitManualOrder()} disabled={manualSubmitting} startIcon={manualSubmitting ? <Loader2 size={16} className="spin" /> : <ClipboardList size={16} />}>Tạo đơn</Button>
          </>
        }
      >
        <Box sx={{ maxHeight: { xs: "100dvh", md: "66vh" }, overflowY: "auto", pr: 0.5 }}>
          <Box sx={{ display: "grid", gap: 1.75, gridTemplateColumns: { xs: "1fr", md: "1fr 1fr" }, pb: 0.5 }}>
            <Stack spacing={1.5}>
              <TextField label="Telegram ID" value={manualForm.telegram_user_id} onChange={(event) => setManualForm((current) => ({ ...current, telegram_user_id: event.target.value }))} placeholder="VD: 7344961485" size="small" helperText="ID số của khách. Không dùng username @." />
              <TextField label="Tên khách" value={manualForm.full_name} onChange={(event) => setManualForm((current) => ({ ...current, full_name: event.target.value }))} placeholder="Tên hiển thị để dễ quản lý" size="small" />
              <TextField select label="Gói lưu vào đơn" value={manualForm.plan_mode === "CUSTOM_DURATION" ? "CUSTOM_DURATION" : manualForm.plan_name} onChange={(event) => setManualForm((current) => event.target.value === "CUSTOM_DURATION" ? ({ ...current, plan_name: "Tùy chỉnh", plan_mode: "CUSTOM_DURATION", entitlement_type: "ALL_ACCESS", entitlement_key: "", duration_days: "1", expire_at: "" }) : ({ ...current, plan_name: event.target.value, plan_mode: "", entitlement_key: "" }))} size="small" helperText="Chọn gói thường hoặc Tùy chỉnh thời hạn.">
                <MenuItem value="FULL_1M">All Access - 30 ngày</MenuItem>
                <MenuItem value="FULL_LIFE">All Access - Trọn đời</MenuItem>
                <MenuItem value="CUSTOM">Tự nhập tên gói</MenuItem>
                {customDurationEnabled ? <MenuItem value="CUSTOM_DURATION">Tùy chỉnh thời hạn</MenuItem> : null}
              </TextField>
              {manualForm.plan_mode === "CUSTOM_DURATION" ? (
                <>
                  <TextField select label="Phạm vi cấp quyền" value={manualForm.entitlement_type} onChange={(event) => setManualForm((current) => ({ ...current, entitlement_type: event.target.value, entitlement_key: "" }))} size="small">
                    <MenuItem value="ALL_ACCESS">All Access</MenuItem>
                    <MenuItem value="GROUP_COLLECTION">Group / Collection</MenuItem>
                  </TextField>
                  {manualForm.entitlement_type === "GROUP_COLLECTION" ? (
                    <TextField label="Group / Collection" value={manualForm.entitlement_key} onChange={(event) => setManualForm((current) => ({ ...current, entitlement_key: event.target.value }))} placeholder="VD: G4" size="small" required helperText="Nhập key group đã cấu hình, ví dụ G4." />
                  ) : null}
                </>
              ) : null}
              <TextField label="Mã / ghi chú" value={manualForm.note} onChange={(event) => setManualForm((current) => ({ ...current, note: event.target.value }))} placeholder="VD: MANUAL_ADMIN" size="small" />
            </Stack>
            <Stack spacing={1.5}>
              <Box sx={{ display: "grid", gridTemplateColumns: "1fr 100px", gap: 1 }}>
                <TextField label="Số tiền" value={manualForm.amount} onChange={(event) => setManualForm((current) => ({ ...current, amount: event.target.value }))} placeholder="0" inputMode="numeric" size="small" helperText="VNĐ tự làm tròn số nguyên." />
                <TextField select label="Tiền tệ" value={manualForm.payment_currency} onChange={(event) => setManualForm((current) => ({ ...current, payment_currency: event.target.value }))} size="small">
                  <MenuItem value="VND">VNĐ</MenuItem>
                  <MenuItem value="USD">USD</MenuItem>
                  <MenuItem value="USDT">USDT</MenuItem>
                </TextField>
              </Box>
              <TextField select label="Phương thức thanh toán" value={manualForm.payment_provider} onChange={(event) => setManualForm((current) => ({ ...current, payment_provider: event.target.value }))} size="small" helperText="Chỉ để ghi nhận báo cáo và đối soát, không đổi flow cấp quyền chính.">
                <MenuItem value="MANUAL">Thủ công</MenuItem>
                <MenuItem value="PAYOS">PayOS / VietQR</MenuItem>
                <MenuItem value="PAYPAL">PayPal</MenuItem>
                <MenuItem value="TRON_USDT">USDT TRC20</MenuItem>
              </TextField>
              <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1 }}>
                <TextField select label="Kiểu hết hạn" value={manualForm.expire_at ? "date" : "days"} onChange={(event) => setManualForm((current) => ({ ...current, duration_days: event.target.value === "days" ? current.duration_days || (current.plan_mode === "CUSTOM_DURATION" ? "1" : "30") : current.duration_days, expire_at: event.target.value === "days" ? "" : current.expire_at }))} size="small">
                  <MenuItem value="days">Theo số ngày</MenuItem>
                  <MenuItem value="date">Ngày cụ thể</MenuItem>
                </TextField>
                <TextField label="Số ngày sử dụng" value={manualForm.duration_days} onChange={(event) => setManualForm((current) => ({ ...current, duration_days: event.target.value }))} placeholder={manualForm.plan_mode === "CUSTOM_DURATION" ? "1" : "30"} inputMode="numeric" size="small" helperText={`Sẽ áp dụng: ${manualForm.duration_days || (manualForm.plan_mode === "CUSTOM_DURATION" ? "1" : "30")} ngày`} />
              </Box>
              <TextField label="Ngày hết hạn cụ thể" type="datetime-local" value={manualForm.expire_at} onChange={(event) => setManualForm((current) => ({ ...current, expire_at: event.target.value }))} size="small" slotProps={{ inputLabel: { shrink: true } }} helperText="Dùng khi muốn set giờ cụ thể thay vì số ngày." />
            </Stack>
          </Box>
        </Box>
      </MuiDialogShell>
    </Box>
  );
}
