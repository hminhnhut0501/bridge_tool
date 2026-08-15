"use client";

import { Tab, Tabs } from "@mui/material";
import type { RenewalTab } from "./renewal-contract";

type Props = { value: RenewalTab; onChange: (value: RenewalTab) => void; expiringCount: number; expiredCount: number };

export function RenewalTabs({ value, onChange, expiringCount, expiredCount }: Props) {
  return <Tabs value={value} onChange={(_, next: RenewalTab) => onChange(next)} variant="scrollable" scrollButtons="auto" sx={{ minHeight: 48 }}><Tab value="expiring-soon" label={`Sắp hết hạn (${expiringCount})`} sx={{ fontWeight: 800 }} /><Tab value="expired" label={`Đã hết hạn (${expiredCount})`} sx={{ fontWeight: 800 }} /></Tabs>;
}
