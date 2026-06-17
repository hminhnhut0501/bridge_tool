"use client";

import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { BadgeDollarSign, CheckCircle2, Coins, CreditCard, Loader2, Save, ShieldCheck, Trash2, TrendingUp, XCircle } from "lucide-react";
import { type ReactNode, useState } from "react";
import type { ConfigField } from "./dashboard-types";
import type { Order } from "@/lib/api";
import { dateText } from "./dashboard-helpers";

export function Metric({ label, value, tone, note }: { label: string; value: string; tone?: "vnd" | "usd" | "crypto" | "payos" | "paypal" | "neutral"; note?: string }) {
  const accent = tone === "vnd" ? "#16a34a" : tone === "usd" ? "#2563eb" : tone === "crypto" ? "#7c3aed" : tone === "payos" ? "#0f766e" : tone === "paypal" ? "#475569" : "#0d6b5d";
  const bg = tone === "vnd" ? "#f0fdf4" : tone === "usd" ? "#eff6ff" : tone === "crypto" ? "#f5f3ff" : tone === "payos" ? "#ecfeff" : tone === "paypal" ? "#f8fafc" : "#f8fafc";
  const glow = tone === "vnd" ? "rgba(34, 197, 94, 0.22)" : tone === "usd" ? "rgba(59, 130, 246, 0.22)" : tone === "crypto" ? "rgba(168, 85, 247, 0.22)" : tone === "payos" ? "rgba(20, 184, 166, 0.22)" : tone === "paypal" ? "rgba(71, 85, 105, 0.18)" : "rgba(13, 107, 93, 0.22)";
  const Icon = tone === "vnd" ? TrendingUp : tone === "usd" ? CreditCard : tone === "crypto" ? Coins : tone === "payos" ? ShieldCheck : tone === "paypal" ? BadgeDollarSign : null;
  const compactValue = (() => {
    const cleaned = value
      .replace(/^PAYOS:\s*/i, "")
      .replace(/^PAYPAL:\s*/i, "")
      .replace(/^NOWPAYMENTS:\s*/i, "")
      .replace(/^NOWPAYMENTS\s*\/\s*USDT:\s*/i, "")
      .replace(/^CRYPTO:\s*/i, "")
      .replace(/\bCRYPTO\b$/i, "")
      .trim();
    return cleaned || value;
  })();
  return (
    <Card
      sx={{
        position: "relative",
        overflow: "hidden",
        minHeight: 132,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        bgcolor: bg,
        borderColor: `${accent}22`,
        backgroundImage: `linear-gradient(135deg, rgba(255,255,255,0.72) 0%, ${bg} 40%, rgba(255,255,255,0.18) 100%)`,
        boxShadow: `0 1px 0 rgba(16, 24, 40, 0.03), 0 12px 24px rgba(16, 24, 40, 0.05), inset 0 1px 0 rgba(255,255,255,0.62), 0 0 0 1px ${glow}`,
      }}
    >
      <Box sx={{ position: "absolute", inset: "0 auto auto 0", height: 4, width: "100%", bgcolor: accent }} />
      <Box sx={{ position: "absolute", top: -12, right: -12, width: 92, height: 92, borderRadius: "50%", bgcolor: glow, filter: "blur(18px)", opacity: 0.6 }} />
      <CardContent sx={{ display: "flex", flexDirection: "column", gap: 1, minHeight: 132, "&:last-child": { pb: 2 } }}>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.3, fontWeight: 700 }}>{label}</Typography>
          {Icon ? <Box sx={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: 32, height: 32, borderRadius: "999px", bgcolor: `${accent}14`, color: accent }}><Icon size={16} /></Box> : null}
        </Box>
        <Typography
          sx={{
            mt: "auto",
            fontWeight: 900,
            lineHeight: 0.95,
            letterSpacing: "-0.03em",
            fontSize: { xs: "1.65rem", sm: "1.9rem", md: "2.05rem" },
            wordBreak: "break-word",
            overflowWrap: "anywhere",
            maxWidth: "100%",
            color: "text.primary",
          }}
        >
          {compactValue}
        </Typography>
        {note ? <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.35 }}>{note}</Typography> : null}
      </CardContent>
    </Card>
  );
}

export function PanelHead({ title, subtitle, action }: { title: string; subtitle?: string; action?: ReactNode }) {
  return (
    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", px: 2, py: 1.5, borderBottom: 1, borderColor: "divider", bgcolor: "background.paper" }}>
      <Box>
        <Typography variant="h6" sx={{ fontWeight: 700 }}>{title}</Typography>
        {subtitle ? <Typography variant="body2" color="text.secondary">{subtitle}</Typography> : null}
      </Box>
      {action}
    </Box>
  );
}

export function HealthItem({ ok, title, detail }: { ok: boolean; title: string; detail: string }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Box sx={{ display: "flex", gap: 1.5, alignItems: "flex-start" }}>
          {ok ? <CheckCircle2 color="#067647" size={20} /> : <XCircle color="#b42318" size={20} />}
          <Box>
            <Typography sx={{ fontWeight: 700 }}>{title}</Typography>
            <Typography variant="body2" color="text.secondary">{detail}</Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export function Info({ label, value }: { label: string; value: string }) {
  return (
    <Card variant="outlined">
      <CardContent sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}>
        <Typography variant="body2" color="text.secondary">{label}</Typography>
        <Typography sx={{ fontWeight: 700 }}>{value}</Typography>
      </CardContent>
    </Card>
  );
}

export function ConfigEditor({ title, subtitle, fields, values, setValues, onSave }: { title: string; subtitle: string; fields: ConfigField[]; values: Record<string, string>; setValues: (values: Record<string, string>) => void; onSave: (fields: ConfigField[], values: Record<string, string>) => Promise<boolean> }) {
  const [editingField, setEditingField] = useState<ConfigField | null>(null);
  const [draftValue, setDraftValue] = useState("");
  const [savingField, setSavingField] = useState(false);

  async function saveField() {
    if (!editingField) return;
    setSavingField(true);
    const nextValues = { ...values, [editingField.key]: draftValue };
    setValues(nextValues);
    try {
      const saved = await onSave([editingField], nextValues);
      if (saved) setEditingField(null);
      else setValues(values);
    } finally {
      setSavingField(false);
    }
  }

  return (
    <Card variant="outlined">
      <PanelHead title={title} subtitle={`${subtitle} Bấm vào từng mục để chỉnh sửa và lưu riêng.`} />
      <Box sx={{ display: "grid", gap: 1.25, p: 2 }}>
        {fields.map((field) => (
          <Card
            key={field.key}
            variant="outlined"
            sx={{
              cursor: "pointer",
              transition: "border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease",
              "&:hover": { borderColor: "primary.main", boxShadow: (theme) => `0 10px 24px ${theme.palette.primary.main}14`, transform: "translateY(-1px)" },
            }}
            onClick={() => { setEditingField(field); setDraftValue(values[field.key] || ""); }}
          >
            <CardContent sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2, py: 2, "&:last-child": { pb: 2 } }}>
              <Box>
                <Typography sx={{ fontWeight: 700 }}>{field.label}</Typography>
                <Typography variant="body2" color="text.secondary">{field.help}</Typography>
              </Box>
              <Typography variant="body2" sx={{ fontWeight: 700, color: values[field.key] ? "text.primary" : "text.secondary" }}>
                {field.kind === "select" ? field.options?.find((item) => item.value === (values[field.key] || field.placeholder))?.label || values[field.key] || field.placeholder : values[field.key] || "Chưa thiết lập"}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Box>
      <Dialog open={Boolean(editingField)} onClose={() => setEditingField(null)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ pr: 6 }}>{editingField?.label}</DialogTitle>
        <IconButton onClick={() => setEditingField(null)} sx={{ position: "absolute", right: 8, top: 8 }}>
          <XCircle size={18} />
        </IconButton>
        <DialogContent sx={{ pt: 1 }}>
          <Box sx={{ display: "grid", gap: 2 }}>
            <Typography variant="body2" color="text.secondary">{editingField?.help}</Typography>
            {editingField?.kind === "textarea" ? (
              <TextField multiline minRows={5} autoFocus value={draftValue} onChange={(event) => setDraftValue(event.target.value)} placeholder={editingField.placeholder} fullWidth />
            ) : editingField?.kind === "select" ? (
              <FormControl fullWidth>
                <Select autoFocus value={draftValue || editingField.placeholder} onChange={(event) => setDraftValue(String(event.target.value))}>
                  {(editingField.options || []).map((item) => <MenuItem key={item.value} value={item.value}>{item.label}</MenuItem>)}
                </Select>
              </FormControl>
            ) : (
              <TextField autoFocus value={draftValue} onChange={(event) => setDraftValue(event.target.value)} placeholder={editingField?.placeholder} fullWidth />
            )}
            <Typography variant="caption" color="text.secondary">Key kỹ thuật: {editingField?.key}</Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditingField(null)}>Huỷ</Button>
          <Button variant="contained" onClick={saveField} disabled={savingField} startIcon={savingField ? <Loader2 size={16} /> : <Save size={16} />}>Lưu thay đổi</Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
}

export function SettingsConfigModal(props: { title: string; subtitle: string; fields: ConfigField[]; values: Record<string, string>; setValues: (values: Record<string, string>) => void; onSave: (fields: ConfigField[], values: Record<string, string>) => Promise<boolean>; onClose: () => void }) {
  return (
    <MuiDialogShell open title={props.title} subtitle={props.subtitle} onClose={props.onClose} maxWidth="md">
        <ConfigEditor title={props.title} subtitle={props.subtitle} fields={props.fields} values={props.values} setValues={props.setValues} onSave={props.onSave} />
    </MuiDialogShell>
  );
}

export function MuiDialogShell({ open, title, subtitle, onClose, children, maxWidth = "md" }: { open: boolean; title: string; subtitle?: string; onClose: () => void; children: ReactNode; maxWidth?: "sm" | "md" | "lg" | "xl" }) {
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth={maxWidth}>
      <DialogTitle sx={{ pb: 1 }}>
        <Typography variant="h6" sx={{ fontWeight: 800 }}>{title}</Typography>
        {subtitle ? <Typography variant="body2" color="text.secondary" sx={{ mt: 0.75 }}>{subtitle}</Typography> : null}
      </DialogTitle>
      <DialogContent dividers sx={{ py: 2.5 }}>
        <Stack spacing={2.25}>
          {children}
        </Stack>
      </DialogContent>
      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button onClick={onClose}>Đóng</Button>
      </DialogActions>
    </Dialog>
  );
}

export function SimpleTable({ headers, rows, onRow, actions }: { headers: string[]; rows: ReactNode[][]; onRow?: (index: number) => void; actions?: (index: number) => ReactNode }) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          {headers.map((item) => <TableCell key={item}>{item}</TableCell>)}
          {actions ? <TableCell>Thao tác</TableCell> : null}
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.length ? rows.map((row, idx) => (
          <TableRow key={idx} hover onClick={() => onRow?.(idx)} sx={{ cursor: onRow ? "pointer" : "default" }}>
            {row.map((cell, cellIdx) => <TableCell key={cellIdx}>{cell}</TableCell>)}
            {actions ? <TableCell>{actions(idx)}</TableCell> : null}
          </TableRow>
        )) : (
          <TableRow>
            <TableCell colSpan={headers.length + (actions ? 1 : 0)} align="center">Chưa có dữ liệu. Bấm nút thêm mới để tạo.</TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}

export function Pagination({ page, totalPages, totalItems, onPage, label = "đơn" }: { page: number; totalPages: number; totalItems: number; onPage: (page: number) => void; label?: string }) {
  const safePage = Math.min(page, totalPages);
  return (
    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2, py: 1 }}>
      <Typography variant="body2" color="text.secondary">{totalItems} {label} • Trang {safePage}/{totalPages}</Typography>
      <Box sx={{ display: "flex", gap: 1 }}>
        <Button variant="outlined" size="small" disabled={safePage <= 1} onClick={() => onPage(safePage - 1)}>Trước</Button>
        <Button variant="outlined" size="small" disabled={safePage >= totalPages} onClick={() => onPage(safePage + 1)}>Sau</Button>
      </Box>
    </Box>
  );
}

export function OrdersTable({ orders, onStatusChange, onDeleteOrder, saving }: { orders: Order[]; onStatusChange: (orderId: string, status: string) => void; onDeleteOrder: (orderId: string, label?: string) => Promise<void>; saving: string }) {
  const statusChip = (status: string) => {
    const normalized = String(status || "").toUpperCase();
    if (normalized === "PAID") return <Chip size="small" label={status} color="success" variant="filled" sx={{ fontWeight: 700 }} />;
    if (normalized === "PENDING") return <Chip size="small" label={status} color="warning" variant="filled" sx={{ fontWeight: 700 }} />;
    if (normalized === "EXPIRED") return <Chip size="small" label={status} color="default" variant="filled" sx={{ fontWeight: 700 }} />;
    if (normalized === "CANCELLED") return <Chip size="small" label={status} color="error" variant="filled" sx={{ fontWeight: 700 }} />;
    return <Chip size="small" label={status || "-"} variant="outlined" sx={{ fontWeight: 700 }} />;
  };
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Mã đơn</TableCell><TableCell>Khách</TableCell><TableCell>Gói</TableCell><TableCell>Tiền</TableCell><TableCell>Coupon</TableCell><TableCell>Trạng thái</TableCell><TableCell>Tạo lúc</TableCell><TableCell>Đổi trạng thái</TableCell><TableCell>Xóa</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {orders.map((order) => (
          <TableRow key={order.order_id}>
            <TableCell>{order.order_id}</TableCell>
            <TableCell><Typography sx={{ fontWeight: 700 }}>{order.full_name || "-"}</Typography><Typography variant="caption" color="text.secondary">{order.telegram_user_id}</Typography></TableCell>
            <TableCell>{order.plan_name}</TableCell>
            <TableCell>{order.amount}</TableCell>
            <TableCell>{order.coupon_code || "-"}</TableCell>
            <TableCell>{statusChip(order.status)}</TableCell>
            <TableCell>{dateText(order.created_at)}</TableCell>
            <TableCell>
              <Select size="small" value={order.status} onChange={(event) => onStatusChange(order.order_id, String(event.target.value))} fullWidth>
                <MenuItem value="PENDING">PENDING</MenuItem><MenuItem value="PAID">PAID</MenuItem><MenuItem value="CANCELLED">CANCELLED</MenuItem><MenuItem value="EXPIRED">EXPIRED</MenuItem>
              </Select>
            </TableCell>
            <TableCell>
              <Button color="error" variant="outlined" size="small" onClick={() => onDeleteOrder(order.order_id, order.full_name || order.telegram_user_id)} disabled={saving === `order-delete-${order.order_id}`}>
                <Trash2 size={16} />
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export function TrendTable({ rows, title, subtitle }: { rows: { label: string; revenue: string; paid: number; pending: number; customers: number; aov: string; coupon: string; conversion: string; conversionColor: "good" | "warn" | "bad"; barWidth: number; trend: number; sparkline: number[] }[]; title: string; subtitle?: string }) {
  return (
    <Card variant="outlined">
      <PanelHead title={title} subtitle={subtitle} />
      <Box sx={{ overflowX: "auto" }}>
        <Table size="small" sx={{ minWidth: 1120 }}>
          <TableHead>
            <TableRow>
              <TableCell>Kỳ</TableCell>
              <TableCell>Doanh thu</TableCell>
              <TableCell>Bar</TableCell>
              <TableCell>Sparkline</TableCell>
              <TableCell>PAID</TableCell>
              <TableCell>PENDING</TableCell>
              <TableCell>Khách trả tiền</TableCell>
              <TableCell>AOV</TableCell>
              <TableCell>Coupon giảm</TableCell>
              <TableCell>Tỉ lệ thanh toán</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.length ? rows.map((row) => (
              <TableRow key={row.label}>
                <TableCell sx={{ fontWeight: 700 }}>{row.label}</TableCell>
                <TableCell>{row.revenue}</TableCell>
                <TableCell>
                  <Box sx={{ width: 220, height: 12, bgcolor: "grey.200", borderRadius: 999, overflow: "hidden" }}>
                    <Box sx={{
                      width: `${Math.max(6, row.barWidth)}%`,
                      height: "100%",
                      bgcolor: row.trend > 0 ? "success.main" : row.trend < 0 ? "error.main" : "primary.main",
                    }} />
                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{ width: 120, height: 28, display: "flex", alignItems: "center" }}>
                    <svg width="120" height="28" viewBox="0 0 120 28" aria-hidden="true">
                      <defs>
                        <linearGradient id={`sparkline-gradient-${row.label.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}`} x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor={row.trend > 0 ? "#067647" : row.trend < 0 ? "#b42318" : "#0d6b5d"} stopOpacity="0.22" />
                          <stop offset="100%" stopColor={row.trend > 0 ? "#22c55e" : row.trend < 0 ? "#ef4444" : "#14b8a6"} stopOpacity="0.88" />
                        </linearGradient>
                      </defs>
                      {(() => {
                        const values = row.sparkline.length ? row.sparkline : [0];
                        const max = Math.max(1, ...values);
                        const step = values.length > 1 ? 110 / (values.length - 1) : 110;
                        const points = values.map((value, index) => `${5 + index * step},${24 - (value / max) * 18}`).join(" ");
                        return (
                          <>
                            <polyline fill={`url(#sparkline-gradient-${row.label.replace(/[^a-z0-9]+/gi, "-").toLowerCase()})`} stroke="none" points={`5,24 ${points} 115,24`} />
                            <polyline fill="none" stroke={`url(#sparkline-gradient-${row.label.replace(/[^a-z0-9]+/gi, "-").toLowerCase()})`} strokeWidth="2.2" points={points} strokeLinecap="round" strokeLinejoin="round" />
                            {values.map((value, index) => (
                              <circle key={index} cx={5 + index * step} cy={24 - (value / max) * 18} r="1.8" fill={`url(#sparkline-gradient-${row.label.replace(/[^a-z0-9]+/gi, "-").toLowerCase()})`} />
                            ))}
                          </>
                        );
                      })()}
                    </svg>
                  </Box>
                </TableCell>
                <TableCell>{row.paid}</TableCell>
                <TableCell>{row.pending}</TableCell>
                <TableCell>{row.customers}</TableCell>
                <TableCell>{row.aov}</TableCell>
                <TableCell>{row.coupon}</TableCell>
                <TableCell>
                  <Box
                      sx={{
                        display: "inline-flex",
                        minWidth: 72,
                        justifyContent: "center",
                        px: 1.25,
                        py: 0.5,
                        borderRadius: 999,
                        fontWeight: 700,
                        color: row.conversionColor === "good" ? "#067647" : row.conversionColor === "warn" ? "#b54708" : "#b42318",
                        bgcolor: row.conversionColor === "good" ? "#ecfdf3" : row.conversionColor === "warn" ? "#fffaeb" : "#fef3f2",
                        border: "1px solid",
                        borderColor: row.conversionColor === "good" ? "#abefc6" : row.conversionColor === "warn" ? "#fedf89" : "#fecdca",
                      }}
                    >
                    {row.conversion}
                  </Box>
                </TableCell>
              </TableRow>
            )) : (
              <TableRow>
                <TableCell colSpan={9} align="center">Chưa có dữ liệu trong kỳ này.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Box>
    </Card>
  );
}
