"use client";

import {
  Box,
  Button,
  Card,
  CardContent,
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
import { CheckCircle2, Loader2, Save, Trash2, XCircle } from "lucide-react";
import { type ReactNode, useState } from "react";
import type { ConfigField } from "./dashboard-types";
import type { Order } from "@/lib/api";

export function Metric({ label, value, tone, note }: { label: string; value: string; tone?: "vnd" | "usd" | "crypto" | "payos" | "paypal" | "neutral"; note?: string }) {
  return (
    <Card sx={{ position: "relative", overflow: "hidden" }}>
      <Box sx={{ position: "absolute", inset: "0 auto auto 0", height: 4, width: "100%", bgcolor: tone === "vnd" ? "success.main" : tone === "usd" ? "info.main" : tone === "crypto" ? "secondary.main" : tone === "payos" ? "success.dark" : tone === "paypal" ? "slategray" : "primary.main" }} />
      <CardContent>
        <Typography variant="body2" color="text.secondary">{label}</Typography>
        <Typography variant="h4" sx={{ mt: 1, fontWeight: 800 }}>{value}</Typography>
        {note ? <Typography variant="caption" color="text.secondary">{note}</Typography> : null}
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
            <TableCell>{order.status}</TableCell>
            <TableCell>{order.created_at}</TableCell>
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
