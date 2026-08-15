"use client";

import { Box, Card, CardContent, Stack, Typography } from "@mui/material";
import type { RenewalSummary } from "./renewal-contract";

type Props = { summary: RenewalSummary; tab: "expiring-soon" | "expired" };

const cards = [
  { key: "expiringSoon", label: "Sắp hết hạn", color: "#f59e0b" },
  { key: "expiring24h", label: "Trong 24 giờ", color: "#ef4444" },
  { key: "reminderNotSent", label: "Chưa nhắc", color: "#06b6d4" },
  { key: "expired", label: "Đã hết hạn", color: "#f43f5e" },
  { key: "pendingKick", label: "Chờ kick", color: "#8b5cf6" },
  { key: "review", label: "Cần kiểm tra", color: "#64748b" },
] as const;

export function RenewalsSummary({ summary, tab }: Props) {
  const visible = tab === "expiring-soon" ? cards.slice(0, 3) : cards.slice(3);
  return (
    <Box sx={{ display: "grid", gridTemplateColumns: { xs: "repeat(2, 1fr)", md: `repeat(${visible.length}, 1fr)` }, gap: 1.25 }}>
      {visible.map((card) => (
        <Card key={card.key} variant="outlined" sx={{ borderRadius: 3, borderTop: `3px solid ${card.color}` }}>
          <CardContent sx={{ p: "14px !important" }}>
            <Stack spacing={0.5}><Typography variant="h5" sx={{ fontWeight: 900 }}>{summary[card.key]}</Typography><Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700 }}>{card.label}</Typography></Stack>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
}
