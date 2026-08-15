"use client";

import { MenuItem, Stack, TextField } from "@mui/material";
import type { RenewalTab } from "./renewal-contract";

type Props = { tab: RenewalTab; query: string; onQueryChange: (value: string) => void; window: "all" | "24h" | "3d" | "7d"; onWindowChange: (value: Props["window"]) => void; status: string; onStatusChange: (value: string) => void };

export function RenewalFilters({ tab, query, onQueryChange, window, onWindowChange, status, onStatusChange }: Props) {
  return <Stack direction={{ xs: "column", md: "row" }} spacing={1} sx={{ py: 1.5 }}>
    <TextField value={query} onChange={(event) => onQueryChange(event.target.value)} size="small" fullWidth placeholder="Tìm tên khách, Telegram ID, order..." />
    {tab === "expiring-soon" ? <TextField select size="small" value={window} onChange={(event) => onWindowChange(event.target.value as Props["window"])} sx={{ minWidth: 170 }}><MenuItem value="all">Tất cả thời hạn</MenuItem><MenuItem value="24h">Trong 24 giờ</MenuItem><MenuItem value="3d">Trong 3 ngày</MenuItem><MenuItem value="7d">Trong 7 ngày</MenuItem></TextField> : <TextField select size="small" value={status} onChange={(event) => onStatusChange(event.target.value)} sx={{ minWidth: 180 }}><MenuItem value="ALL">Tất cả trạng thái</MenuItem><MenuItem value="PENDING">Chờ xử lý</MenuItem><MenuItem value="DONE">Đã kick</MenuItem><MenuItem value="RETAINED">Đã gia hạn</MenuItem><MenuItem value="ALREADY_ABSENT">Đã rời group</MenuItem><MenuItem value="RETRY">Sẽ thử lại</MenuItem><MenuItem value="REVIEW">Cần kiểm tra</MenuItem></TextField>}
  </Stack>;
}
