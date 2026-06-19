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
        minHeight: 128,
        p: 2,
        borderRadius: "20px",
        borderColor: accentStyle ? `${accentStyle.main}1a` : "rgba(125, 211, 252, 0.20)",
        boxShadow: "0 10px 24px rgba(15, 23, 42, 0.04), inset 0 1px 0 rgba(255,255,255,0.9)",
        background: `linear-gradient(135deg, rgba(255,255,255,0.92) 0%, ${toneStyle.tintA} 34%, ${toneStyle.tintB} 72%, rgba(255,255,255,0.98) 100%)`,
        backdropFilter: "blur(16px) saturate(1.05)",
        WebkitBackdropFilter: "blur(16px) saturate(1.05)",
      }}
    >
      <Box sx={{ position: "absolute", inset: 6, borderRadius: "16px", pointerEvents: "none", background: `radial-gradient(circle at 18% 18%, rgba(255,255,255,0.88) 0%, transparent 16%), radial-gradient(circle at 84% 16%, ${glow} 0%, transparent 28%), linear-gradient(135deg, rgba(255,255,255,0.10) 0%, transparent 58%)`, opacity: 0.78 }} />
      <CardContent sx={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", gap: 1.1, minHeight: 120, "&:last-child": { pb: 1.9 } }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.25, minWidth: 0 }}>
          <Box sx={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: 36, height: 36, borderRadius: "999px", bgcolor: "rgba(255,255,255,0.9)", color: accentColor, boxShadow: `0 6px 14px ${accentColor}14` }}>{IconNode}</Box>
          <Typography variant="body1" color="text.primary" sx={{ lineHeight: 1.2, fontWeight: 700, letterSpacing: "-0.02em" }}>
            {label}
          </Typography>
        </Box>
        <Typography sx={{ mt: "auto", fontWeight: 900, lineHeight: 0.96, letterSpacing: "-0.05em", fontSize: { xs: "1.8rem", sm: "2.05rem", md: "2.2rem" }, wordBreak: "break-word", overflowWrap: "anywhere", maxWidth: "100%", color: "text.primary" }}>
          {compactValue}
        </Typography>
        {note ? <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.35, fontSize: "0.93rem" }}>{note}</Typography> : null}
      </CardContent>
    </Card>
  );
}

export const MetricCard = Metric;
