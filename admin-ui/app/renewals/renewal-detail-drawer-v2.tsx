"use client";

import { Alert, Box, Chip, Divider, Drawer, IconButton, Stack, Typography } from "@mui/material";
import { X } from "lucide-react";
import type { RenewalRow } from "./renewal-contract";
import { membershipStatusLabel, reminderStatusLabel, RENEWAL_STATUS_LABELS } from "./renewal-contract";

function formatDate(value: string | null): string {
  if (!value) return "Chưa có";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Ngày không hợp lệ" : new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

type Props = {
  open: boolean;
  row: RenewalRow | null;
  onClose: () => void;
  onSendReminder?: (row: RenewalRow) => void;
  onRetryKick?: (row: RenewalRow) => void;
};

export function RenewalDetailDrawerV2({ open, row, onClose, onSendReminder, onRetryKick }: Props) {
  return <Drawer anchor="right" open={open} onClose={onClose} sx={{ "& .MuiDrawer-paper": { width: { xs: "100%", sm: 460 }, p: 2 } }}>
    {!row ? <Box /> : <Stack spacing={2}>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}><Box><Typography variant="h6" sx={{ fontWeight: 900 }}>{row.customer.name || "Khách chưa có tên"}</Typography><Typography variant="body2" color="text.secondary">Telegram ID: {row.customer.telegramUserId}</Typography></Box><IconButton onClick={onClose} aria-label="Đóng"><X size={18} /></IconButton></Box>
      <Divider />
      <Box><Typography variant="overline" color="text.secondary">Quyền truy cập</Typography><Typography sx={{ fontWeight: 800 }}>{row.entitlement.planName}</Typography><Typography variant="body2">{row.entitlement.planFamily} · {row.entitlement.groupCode}</Typography><Typography variant="body2" color="text.secondary">Hết hạn: {formatDate(row.entitlement.expiresAt)}</Typography></Box>
      <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}><Chip label={`Membership: ${membershipStatusLabel(row.membership)}`} size="small" variant="outlined" /><Chip label={`Kick: ${RENEWAL_STATUS_LABELS[row.kick.status]}`} size="small" color={row.kick.status === "REVIEW" ? "error" : "default"} variant="outlined" /></Box>
      <Box><Typography variant="overline" color="text.secondary">Nhắc gia hạn</Typography><Stack spacing={0.5}><Typography variant="body2">Trạng thái: {reminderStatusLabel(row.reminder.status)}</Typography><Typography variant="body2">Lần gửi gần nhất: {formatDate(row.reminder.sentAt)}</Typography><Typography variant="body2">Số lần gửi: {row.reminder.attempts}</Typography>{row.reminder.lastError ? <Alert severity="error" sx={{ mt: 1 }}>{row.reminder.lastError}</Alert> : null}</Stack></Box>
      <Box><Typography variant="overline" color="text.secondary">Kick</Typography><Stack spacing={0.5}><Typography variant="body2">Cập nhật: {formatDate(row.kick.updatedAt)}</Typography><Typography variant="body2">Số lần thử: {row.kick.attempts}</Typography>{row.kick.lastError ? <Alert severity="error" sx={{ mt: 1 }}>{row.kick.lastError}</Alert> : null}</Stack></Box>
      <Stack direction="row" spacing={1}>{onSendReminder && row.reminder.status !== "SENT" ? <button type="button" onClick={() => onSendReminder(row)}>Gửi nhắc gia hạn</button> : null}{onRetryKick && ["RETRY", "REVIEW"].includes(row.kick.status) ? <button type="button" onClick={() => onRetryKick(row)}>Thử lại kick</button> : null}</Stack>
    </Stack>}
  </Drawer>;
}
