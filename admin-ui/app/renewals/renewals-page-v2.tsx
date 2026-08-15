"use client";

import { Box, Button, Paper, Stack, Typography } from "@mui/material";
import { RefreshCw } from "lucide-react";
import { useState } from "react";
import type { RenewalRow, RenewalTab, RenewalViewModel } from "./renewal-contract";
import { RenewalFilters } from "./renewal-filters";
import { RenewalDetailDrawerV2 } from "./renewal-detail-drawer-v2";
import { RenewalStatePanel } from "./renewal-state-panel";
import { RenewalsSummary } from "./renewals-summary";
import { RenewalTabs } from "./renewal-tabs";
import { ExpiredTable, ExpiringSoonTable } from "./renewal-tables";
import { RenewalWorkerConfig } from "./renewal-worker-config";

type Props = { view: RenewalViewModel; onRefresh: () => void; onSendReminder?: (row: RenewalRow) => void; onRetryKick?: (row: RenewalRow) => void; onTabChange?: (tab: RenewalTab) => void; workerConfig?: Record<string, unknown>; onWorkerConfigSave?: (payload: Record<string, unknown>) => void };

export function RenewalsPageV2({ view, onRefresh, onSendReminder, onRetryKick, onTabChange, workerConfig, onWorkerConfigSave }: Props) {
  const [query, setQuery] = useState("");
  const [window, setWindow] = useState<"all" | "24h" | "3d" | "7d">("all");
  const [status, setStatus] = useState("ALL");
  const [selected, setSelected] = useState<RenewalRow | null>(null);
  const rows = view.rows.filter((row) => {
    const q = query.trim().toLowerCase();
    const matchesQuery = !q || [row.customer.name, row.customer.telegramUserId, row.entitlement.orderId, row.entitlement.planName, row.entitlement.groupCode].some((value) => String(value || "").toLowerCase().includes(q));
    const matchesStatus = view.tab === "expiring-soon" || status === "ALL" || row.kick.status === status;
    const expiry = row.entitlement.expiresAt ? new Date(row.entitlement.expiresAt).getTime() - Date.now() : Number.POSITIVE_INFINITY;
    const matchesWindow = view.tab !== "expiring-soon" || window === "all" || expiry <= ({ "24h": 86_400_000, "3d": 259_200_000, "7d": 604_800_000 } as const)[window];
    return matchesQuery && matchesStatus && matchesWindow;
  });
  return <Stack spacing={2}>{workerConfig && onWorkerConfigSave ? <RenewalWorkerConfig config={workerConfig} onSave={onWorkerConfigSave} /> : null}
    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 1 }}><Box><Typography variant="h5" sx={{ fontWeight: 900 }}>Gia hạn</Typography><Typography variant="body2" color="text.secondary">Theo dõi hạn quyền, nhắc gia hạn và trạng thái kick theo từng group.</Typography></Box><Button variant="outlined" size="small" onClick={onRefresh} startIcon={<RefreshCw size={15} />}>Làm mới</Button></Box>
    {view.error ? <Typography variant="body2" color="warning.main">{view.error}</Typography> : null}
    <RenewalsSummary summary={view.summary} tab={view.tab} />
    <Paper variant="outlined" sx={{ borderRadius: 3, overflow: "hidden" }}>
      <RenewalTabs value={view.tab} onChange={(tab) => onTabChange?.(tab)} expiringCount={view.summary.expiringSoon} expiredCount={view.summary.expired} />
      <Box sx={{ px: 2 }}><RenewalFilters tab={view.tab} query={query} onQueryChange={setQuery} window={window} onWindowChange={setWindow} status={status} onStatusChange={setStatus} /></Box>
      <RenewalStatePanel loading={view.loading} error={view.error} rows={rows.length} onRetry={onRefresh} />
      {!view.loading && !view.error && rows.length ? <Box sx={{ overflowX: "auto", px: 2, pb: 2 }}>{view.tab === "expiring-soon" ? <ExpiringSoonTable rows={rows} onOpen={setSelected} /> : <ExpiredTable rows={rows} onOpen={setSelected} />}</Box> : null}
    </Paper>
    <RenewalDetailDrawerV2 open={Boolean(selected)} row={selected} onClose={() => setSelected(null)} onSendReminder={onSendReminder} onRetryKick={onRetryKick} />
  </Stack>;
}
