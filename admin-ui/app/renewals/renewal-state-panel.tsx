"use client";

import { Alert, Box, CircularProgress, Typography } from "@mui/material";

type Props = { loading: boolean; error: string | null; rows: number; onRetry: () => void };

export function RenewalStatePanel({ loading, error, rows, onRetry }: Props) {
  if (loading) return <Box sx={{ py: 8, display: "flex", flexDirection: "column", alignItems: "center", gap: 1 }}><CircularProgress size={26} /><Typography color="text.secondary">Đang tải dữ liệu gia hạn...</Typography></Box>;
  if (error) return <Alert severity="error" action={<button type="button" onClick={onRetry}>Thử lại</button>}>{error}</Alert>;
  if (!rows) return <Alert severity="info">Không có dữ liệu trong bộ lọc hiện tại.</Alert>;
  return null;
}
