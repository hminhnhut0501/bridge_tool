"use client";

import { Chip, Table, TableBody, TableCell, TableHead, TableRow, Typography } from "@mui/material";
import type { RenewalRow } from "./renewal-contract";
import { membershipStatusLabel, reminderStatusLabel, RENEWAL_STATUS_LABELS } from "./renewal-contract";

function formatDate(value: string | null): string {
  if (!value) return "Chưa có ngày";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Ngày không hợp lệ";
  return new Intl.DateTimeFormat("vi-VN", { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function daysLabel(value: string | null): string {
  if (!value) return "";
  const ms = new Date(value).getTime() - Date.now();
  const days = Math.ceil(ms / 86_400_000);
  if (days < 1) return "Trong hôm nay";
  return `Còn ${days} ngày`;
}

function tone(status: string): "success" | "warning" | "error" | "default" {
  if (["SENT", "DONE", "ALREADY_ABSENT", "RETAINED"].includes(status)) return "success";
  if (["NOT_SENT", "PENDING", "PROCESSING", "RETRY"].includes(status)) return "warning";
  if (["FAILED", "REVIEW", "UNKNOWN"].includes(status)) return "error";
  return "default";
}

function CustomerCell({ row }: { row: RenewalRow }) {
  return <TableCell><Typography sx={{ fontWeight: 800 }}>{row.customer.name || "Khách chưa có tên"}</Typography><Typography variant="caption" color="text.secondary">{row.customer.telegramUserId}</Typography></TableCell>;
}

export function ExpiringSoonTable({ rows, onOpen }: { rows: RenewalRow[]; onOpen: (row: RenewalRow) => void }) {
  return <Table size="small"><TableHead><TableRow><TableCell>Khách</TableCell><TableCell>Gói / group</TableCell><TableCell>Hết hạn</TableCell><TableCell>Nhắc gia hạn</TableCell><TableCell>Thao tác</TableCell></TableRow></TableHead><TableBody>
    {rows.map((row) => <TableRow hover key={`${row.entitlement.orderId}-${row.entitlement.groupCode}`}><CustomerCell row={row} /><TableCell><Typography sx={{ fontWeight: 700 }}>{row.entitlement.planName}</Typography><Typography variant="caption" color="text.secondary">{row.entitlement.groupCode}</Typography></TableCell><TableCell><Typography sx={{ fontWeight: 800 }}>{formatDate(row.entitlement.expiresAt)}</Typography><Typography variant="caption" color="warning.main">{daysLabel(row.entitlement.expiresAt)}</Typography></TableCell><TableCell><Chip size="small" label={reminderStatusLabel(row.reminder.status)} color={tone(row.reminder.status)} variant="outlined" />{row.reminder.sentAt ? <Typography variant="caption" sx={{ display: "block" }} color="text.secondary">{formatDate(row.reminder.sentAt)}</Typography> : null}</TableCell><TableCell><button type="button" onClick={() => onOpen(row)}>Mở chi tiết</button></TableCell></TableRow>)}
    {!rows.length ? <TableRow><TableCell colSpan={5}>Không có khách sắp hết hạn trong bộ lọc hiện tại.</TableCell></TableRow> : null}
  </TableBody></Table>;
}

export function ExpiredTable({ rows, onOpen }: { rows: RenewalRow[]; onOpen: (row: RenewalRow) => void }) {
  return <Table size="small"><TableHead><TableRow><TableCell>Khách</TableCell><TableCell>Gói / group</TableCell><TableCell>Hết hạn</TableCell><TableCell>Membership</TableCell><TableCell>Trạng thái kick</TableCell><TableCell>Lỗi gần nhất</TableCell><TableCell>Thao tác</TableCell></TableRow></TableHead><TableBody>
    {rows.map((row) => <TableRow hover key={`${row.entitlement.orderId}-${row.entitlement.groupCode}`}><CustomerCell row={row} /><TableCell><Typography sx={{ fontWeight: 700 }}>{row.entitlement.planName}</Typography><Typography variant="caption" color="text.secondary">{row.entitlement.groupCode}</Typography></TableCell><TableCell>{formatDate(row.entitlement.expiresAt)}</TableCell><TableCell><Chip size="small" label={membershipStatusLabel(row.membership)} color={tone(row.membership)} variant="outlined" /></TableCell><TableCell><Chip size="small" label={RENEWAL_STATUS_LABELS[row.kick.status]} color={tone(row.kick.status)} variant="outlined" /><Typography variant="caption" sx={{ display: "block" }} color="text.secondary">{row.kick.attempts} lần thử</Typography></TableCell><TableCell>{row.kick.lastError || "-"}</TableCell><TableCell><button type="button" onClick={() => onOpen(row)}>Mở chi tiết</button></TableCell></TableRow>)}
    {!rows.length ? <TableRow><TableCell colSpan={7}>Không có khách đã hết hạn trong bộ lọc hiện tại.</TableCell></TableRow> : null}
  </TableBody></Table>;
}
