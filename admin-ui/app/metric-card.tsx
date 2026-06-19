"use client";

import { Box, Card, CardContent, Typography } from "@mui/material";
import { Activity, BadgeDollarSign as BadgeDollarSignIcon, Coins, CreditCard, ShieldCheck, TrendingUp } from "lucide-react";
import type { ReactNode } from "react";

export type MetricTone = "vnd" | "usd" | "crypto" | "payos" | "paypal" | "neutral";
export type MetricAccent = "blue" | "cyan" | "emerald" | "amber" | "rose" | "violet" | "indigo";

const toneStyles: Record<MetricTone, { tintA: string; tintB: string; icon: string; badgeBg: string; border: string }> = {
  vnd: { tintA: "rgba(59,130,246,0.18)", tintB: "rgba(16,185,129,0.14)", icon: "#2563eb", badgeBg: "rgba(255,255,255,0.86)", border: "rgba(125, 211, 252, 0.55)" },
  usd: { tintA: "rgba(34,211,238,0.18)", tintB: "rgba(59,130,246,0.14)", icon: "#0ea5e9", badgeBg: "rgba(255,255,255,0.86)", border: "rgba(125, 211, 252, 0.5)" },
  crypto: { tintA: "rgba(192,132,252,0.18)", tintB: "rgba(244,114,182,0.14)", icon: "#c026d3", badgeBg: "rgba(255,255,255,0.86)", border: "rgba(216, 180, 254, 0.6)" },
  payos: { tintA: "rgba(45,212,191,0.18)", tintB: "rgba(96,165,250,0.14)", icon: "#14b8a6", badgeBg: "rgba(255,255,255,0.86)", border: "rgba(94, 234, 212, 0.55)" },
  paypal: { tintA: "rgba(167,139,250,0.18)", tintB: "rgba(96,165,250,0.14)", icon: "#6366f1", badgeBg: "rgba(255,255,255,0.86)", border: "rgba(196, 181, 253, 0.58)" },
  neutral: { tintA: "rgba(148,163,184,0.14)", tintB: "rgba(226,232,240,0.2)", icon: "#475569", badgeBg: "rgba(255,255,255,0.86)", border: "rgba(203,213,225,0.72)" },
};

const accentStyles: Record<MetricAccent, { main: string; bg: string; glow: string }> = {
  blue: { main: "#2563eb", bg: "#eff6ff", glow: "rgba(37, 99, 235, 0.18)" },
  cyan: { main: "#06b6d4", bg: "#ecfeff", glow: "rgba(6, 182, 212, 0.18)" },
  emerald: { main: "#10b981", bg: "#ecfdf5", glow: "rgba(16, 185, 129, 0.18)" },
  amber: { main: "#f59e0b", bg: "#fffbeb", glow: "rgba(245, 158, 11, 0.18)" },
  rose: { main: "#f43f5e", bg: "#fff1f2", glow: "rgba(244, 63, 94, 0.18)" },
  violet: { main: "#8b5cf6", bg: "#f5f3ff", glow: "rgba(139, 92, 246, 0.18)" },
  indigo: { main: "#6366f1", bg: "#eef2ff", glow: "rgba(79, 70, 229, 0.18)" },
};

export function Metric({ label, value, tone, note, accent, icon }: { label: string; value: string; tone?: MetricTone; note?: string; accent?: MetricAccent; icon?: ReactNode }) {
  const toneStyle = tone ? toneStyles[tone] : toneStyles.neutral;
  const accentStyle = accent ? accentStyles[accent] : null;
  const accentColor = accentStyle?.main || toneStyle.icon;
  const glow = accentStyle?.glow || toneStyle.border;
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
  const IconNode = icon || (tone === "vnd" ? <TrendingUp size={16} /> : tone === "usd" ? <CreditCard size={16} /> : tone === "crypto" ? <Coins size={16} /> : tone === "payos" ? <ShieldCheck size={16} /> : tone === "paypal" ? <BadgeDollarSignIcon size={16} /> : <Activity size={16} />);
  return (
    <Card
      variant="outlined"
      sx={{
        position: "relative",
        overflow: "hidden",
        minHeight: 136,
        p: 2.2,
        borderRadius: "28px",
        borderColor: accentStyle ? `${accentStyle.main}18` : "rgba(125, 211, 252, 0.28)",
        boxShadow: "0 10px 26px rgba(15, 23, 42, 0.05), inset 0 1px 0 rgba(255,255,255,0.92)",
        background: `linear-gradient(135deg, rgba(255,255,255,0.90) 0%, ${toneStyle.tintA} 36%, ${toneStyle.tintB} 68%, rgba(255,255,255,0.96) 100%)`,
        backdropFilter: "blur(18px) saturate(1.08)",
        WebkitBackdropFilter: "blur(18px) saturate(1.08)",
      }}
    >
      <Box sx={{ position: "absolute", inset: 10, borderRadius: "22px", pointerEvents: "none", background: `radial-gradient(circle at 18% 18%, rgba(255,255,255,0.84) 0%, transparent 18%), radial-gradient(circle at 84% 18%, ${glow} 0%, transparent 34%), linear-gradient(135deg, rgba(255,255,255,0.10) 0%, transparent 54%)`, opacity: 0.9 }} />
      <CardContent sx={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", gap: 1.1, minHeight: 130, "&:last-child": { pb: 2 } }}>
        <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.25, minWidth: 0 }}>
            <Box sx={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: 34, height: 34, borderRadius: "999px", bgcolor: "#ffffff", color: accentColor, border: `1px solid ${accentColor}12`, boxShadow: `0 8px 18px ${accentColor}10` }}>{IconNode}</Box>
            <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.25, fontWeight: 800, letterSpacing: "-0.01em" }}>{label}</Typography>
          </Box>
          <Box sx={{ display: "inline-flex", alignItems: "center", justifyContent: "center", minWidth: 58, height: 30, px: 1.1, borderRadius: "999px", bgcolor: "rgba(255,255,255,0.88)", color: "#7c8798", border: "1px solid rgba(226,232,240,0.95)", fontSize: "0.78rem", fontWeight: 800, letterSpacing: "0.04em" }}>
            {tone === "vnd" ? "VND" : tone === "usd" ? "USD" : tone === "crypto" ? "CRYPTO" : tone === "payos" ? "PAYOS" : tone === "paypal" ? "PAYPAL" : ""}
          </Box>
        </Box>
        <Typography sx={{ mt: "auto", fontWeight: 900, lineHeight: 0.94, letterSpacing: "-0.04em", fontSize: { xs: "1.75rem", sm: "2rem", md: "2.2rem" }, wordBreak: "break-word", overflowWrap: "anywhere", maxWidth: "100%", color: "text.primary" }}>
          {compactValue}
        </Typography>
        {note ? <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.35, fontSize: "0.93rem" }}>{note}</Typography> : null}
      </CardContent>
    </Card>
  );
}

export const MetricCard = Metric;
