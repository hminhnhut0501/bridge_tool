"use client";

import { Box, Card, CardContent, Typography } from "@mui/material";
import { Activity, BadgeDollarSign as BadgeDollarSignIcon, Coins, CreditCard, ShieldCheck, TrendingUp } from "lucide-react";
import type { ReactNode } from "react";

export type MetricTone = "vnd" | "usd" | "crypto" | "payos" | "paypal" | "neutral";
export type MetricAccent = "blue" | "cyan" | "emerald" | "amber" | "rose" | "violet" | "indigo";

const toneStyles: Record<MetricTone, { tintA: string; tintB: string; icon: string; badgeBg: string; border: string }> = {
  vnd: { tintA: "rgba(59,130,246,0.18)", tintB: "rgba(16,185,129,0.14)", icon: "#0066ff", badgeBg: "rgba(255,255,255,0.86)", border: "rgba(125, 211, 252, 0.55)" },
  usd: { tintA: "rgba(34,211,238,0.18)", tintB: "rgba(59,130,246,0.14)", icon: "#0ea5e9", badgeBg: "rgba(255,255,255,0.86)", border: "rgba(125, 211, 252, 0.5)" },
  crypto: { tintA: "rgba(192,132,252,0.18)", tintB: "rgba(244,114,182,0.14)", icon: "#c026d3", badgeBg: "rgba(255,255,255,0.86)", border: "rgba(216, 180, 254, 0.6)" },
  payos: { tintA: "rgba(45,212,191,0.18)", tintB: "rgba(96,165,250,0.14)", icon: "#14b8a6", badgeBg: "rgba(255,255,255,0.86)", border: "rgba(94, 234, 212, 0.55)" },
  paypal: { tintA: "rgba(167,139,250,0.18)", tintB: "rgba(96,165,250,0.14)", icon: "#6366f1", badgeBg: "rgba(255,255,255,0.86)", border: "rgba(196, 181, 253, 0.58)" },
  neutral: { tintA: "rgba(148,163,184,0.14)", tintB: "rgba(226,232,240,0.2)", icon: "#475569", badgeBg: "rgba(255,255,255,0.86)", border: "rgba(203,213,225,0.72)" },
};

const accentStyles: Record<MetricAccent, { main: string; bg: string; glow: string }> = {
  blue: { main: "#0066ff", bg: "#eff6ff", glow: "rgba(0, 102, 255, 0.18)" },
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
  const compactValue = (() => {
    const cleaned = value
      .replace(/^PAYOS:\s*/i, "")
      .replace(/^PAYPAL:\s*/i, "")
      .replace(/^CRYPTO:\s*/i, "")
      .replace(/\bCRYPTO\b$/i, "")
      .trim();
    return cleaned || value;
  })();
  const IconNode = icon || (tone === "vnd" ? <TrendingUp size={16} /> : tone === "usd" ? <CreditCard size={16} /> : tone === "crypto" ? <Coins size={16} /> : tone === "payos" ? <ShieldCheck size={16} /> : tone === "paypal" ? <BadgeDollarSignIcon size={16} /> : <Activity size={16} />);
  return (
    <Card
      sx={{
        position: "relative",
        overflow: "hidden",
        minHeight: 104,
        height: "100%",
        borderRadius: "10px",
        border: "1px solid",
        borderColor: accentStyle ? `${accentStyle.main}2a` : "rgba(125, 211, 252, 0.20)",
        background: `rgba(255, 255, 255, 0.7)`,
        backdropFilter: "blur(20px)",
        boxShadow: "0 4px 24px -4px rgba(15, 23, 42, 0.04), inset 0 1px 1px rgba(255, 255, 255, 0.4)",
        transition: "all 300ms cubic-bezier(0.4, 0, 0.2, 1)",
        "&:hover": {
          transform: "translateY(-4px)",
          boxShadow: `0 16px 40px -8px ${accentStyle?.glow || toneStyle.tintA}, inset 0 1px 1px rgba(255, 255, 255, 0.6)`,
          borderColor: accentStyle ? `${accentStyle.main}40` : "rgba(125, 211, 252, 0.40)",
          "& .glow-bg": {
            opacity: 0.8,
            transform: "scale(1.2)",
          }
        },
      }}
    >
      {/* Subtle background glow blob */}
      <Box 
        className="glow-bg"
        sx={{ 
          position: "absolute", 
          top: -30, 
          right: -30, 
          width: 120, 
          height: 120, 
          borderRadius: "50%", 
          background: `radial-gradient(circle, ${accentStyle?.glow || toneStyle.tintA} 0%, rgba(255,255,255,0) 70%)`,
          opacity: 0.4,
          transition: "all 400ms ease",
          zIndex: 0,
          pointerEvents: "none"
        }} 
      />
      <CardContent sx={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", gap: 1, p: 2.25, "&:last-child": { pb: 2.25 }, height: "100%" }}>
        <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, minWidth: 0 }}>
            <Box sx={{ 
              display: "inline-flex", 
              alignItems: "center", 
              justifyContent: "center", 
              width: 40, 
              height: 40, 
              borderRadius: "8px", 
              background: `linear-gradient(135deg, ${accentColor} 0%, ${accentColor}dd 100%)`, 
              color: "#ffffff", 
              boxShadow: `0 8px 16px -4px ${accentStyle?.glow || toneStyle.tintA}, inset 0 1px 1px rgba(255,255,255,0.4)`,
              position: "relative",
            }}>
              {IconNode}
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 700, letterSpacing: "0.02em", lineHeight: 1.2 }}>
              {label}
            </Typography>
          </Box>
        </Box>
        <Box sx={{ mt: "auto", pt: 1 }}>
          <Typography sx={{ fontWeight: 800, lineHeight: 1.1, fontSize: { xs: "1.45rem", sm: "1.65rem", md: "1.85rem" }, letterSpacing: "-0.02em", wordBreak: "break-word", overflowWrap: "anywhere", color: "text.primary" }}>
            {compactValue}
          </Typography>
          {note ? <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: "block", fontWeight: 600 }}>{note}</Typography> : null}
        </Box>
      </CardContent>
    </Card>
  );
}

export const MetricCard = Metric;
