"use client";

import { Box, Button, Chip, Stack, Typography } from "@mui/material";
import { RefreshCw, ShieldAlert, Zap } from "lucide-react";

export type RenewalCutoverRow = {
  order_id?: string;
  orderId?: string;
  telegram_user_id?: string;
  telegramId?: string;
  customer_name?: string;
  customerName?: string;
  plan_name?: string;
  planName?: string;
  task_state?: string;
  kick_state?: string;
  next_action?: string;
  blocked_reason?: string;
  latest_error?: string;
  order_state?: string;
  group_summary?: Record<string, number>;
  last_attempt?: { attempt_state?: string; error?: string; started_at?: string } | null;
};

type Props = {
  rows: RenewalCutoverRow[];
  summary: { total?: number; processing?: number; done?: number; blocked?: number; review_required?: number; review?: number };
  onRefresh: () => void;
  onKick: (row: RenewalCutoverRow) => void;
  onReview: (row: RenewalCutoverRow) => void;
  detail: React.ReactNode;
};

function rowId(row: RenewalCutoverRow) {
  return String(row.order_id || row.orderId || "");
}

function rowState(row: RenewalCutoverRow) {
  return String(row.task_state || row.kick_state || "none");
}

function action(row: RenewalCutoverRow) {
  return String(row.next_action || "none");
}

export function RenewalsSection({ rows, summary, onRefresh, onKick, onReview, detail }: Props) {
  return (
    <div className="stack">
      <div className="grid">
        <div className="metric"><strong>{summary.total || rows.length}</strong><span>Tổng renewal</span></div>
        <div className="metric"><strong>{summary.processing || 0}</strong><span>Đang xử lý</span></div>
        <div className="metric"><strong>{summary.done || 0}</strong><span>Đã xong</span></div>
        <div className="metric"><strong>{summary.review_required || summary.review || 0}</strong><span>Cần review</span></div>
      </div>
      <section className="panel">
        <Box sx={{ p: 2, display: "flex", justifyContent: "space-between", gap: 1, flexWrap: "wrap" }}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 900 }}>Gia hạn · Core mới</Typography>
            <Typography variant="body2" color="text.secondary">Hiển thị từ renewal view-model, không suy luận từ support_events.</Typography>
          </Box>
          <Button variant="outlined" size="small" onClick={onRefresh} startIcon={<RefreshCw size={15} />}>Làm mới</Button>
        </Box>
        <Box sx={{ px: 2, pb: 2, overflowX: "auto" }}>
          <table className="data-table">
            <thead><tr><th>Khách</th><th>Gói</th><th>Task</th><th>Hành động kế tiếp</th><th>Thao tác</th></tr></thead>
            <tbody>
              {rows.map((row) => {
                const next = action(row);
                const review = next === "review" || rowState(row) === "review_required";
                return (
                  <tr key={rowId(row)}>
                    <td><strong>{row.customer_name || row.customerName || row.telegram_user_id || row.telegramId || "-"}</strong><div className="muted">{rowId(row)}</div></td>
                    <td>{row.plan_name || row.planName || "-"}</td>
                    <td><Chip size="small" label={rowState(row)} color={review ? "error" : "default"} variant="outlined" /></td>
                    <td>{row.blocked_reason || row.latest_error || row.last_attempt?.error || next}</td>
                    <td><Stack direction="row" spacing={0.5}>
                      {next === "kick" ? <Button size="small" color="error" onClick={() => onKick(row)} startIcon={<Zap size={14} />}>Kick</Button> : null}
                      {review ? <Button size="small" onClick={() => onReview(row)} startIcon={<ShieldAlert size={14} />}>Review</Button> : null}
                    </Stack></td>
                  </tr>
                );
              })}
              {!rows.length ? <tr><td colSpan={5}>Không có dữ liệu renewal.</td></tr> : null}
            </tbody>
          </table>
        </Box>
      </section>
      {detail}
    </div>
  );
}
