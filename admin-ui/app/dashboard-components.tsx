"use client";

import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  MenuItem,
  Select,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { BadgeDollarSign, CheckCircle2, Coins, CreditCard, Loader2, Save, ShieldCheck, Trash2, TrendingUp, XCircle } from "lucide-react";
import { type ReactNode, useId, useState } from "react";
import type { ConfigField } from "./dashboard-types";
import type { Order } from "@/lib/api";
import { dateText } from "./dashboard-helpers";
import { styleGuide } from "./style-guide";

const statusPalette = {
  success: { main: "#067647", bg: "#ecfdf3", border: "#abefc6" },
  warning: { main: "#b54708", bg: "#fffaeb", border: "#fedf89" },
  error: { main: "#b42318", bg: "#fef3f2", border: "#fecdca" },
  muted: { main: "#667085", bg: "#f2f4f7", border: "#d0d5dd" },
  purple: { main: "#6d28d9", bg: "#efe7ff", border: "#d9c7ff" },
} as const;

export const tonePalette = {
  vnd: { main: "#16a34a", bg: "#f0fdf4", glow: "rgba(34, 197, 94, 0.22)" },
  usd: { main: "#2563eb", bg: "#eff6ff", glow: "rgba(59, 130, 246, 0.22)" },
  crypto: { main: "#7c3aed", bg: "#f5f3ff", glow: "rgba(168, 85, 247, 0.22)" },
  payos: { main: "#0f766e", bg: "#ecfeff", glow: "rgba(20, 184, 166, 0.22)" },
  paypal: { main: "#475569", bg: "#f8fafc", glow: "rgba(71, 85, 105, 0.18)" },
  neutral: { main: "#0d6b5d", bg: "#f8fafc", glow: "rgba(13, 107, 93, 0.22)" },
} as const;

const screenAccentMap = {
  blue: { main: styleGuide.palette.accent.blue, bg: "#eff6ff", glow: "rgba(37, 99, 235, 0.18)" },
  cyan: { main: styleGuide.palette.accent.cyan, bg: "#ecfeff", glow: "rgba(6, 182, 212, 0.18)" },
  emerald: { main: styleGuide.palette.accent.emerald, bg: "#ecfdf5", glow: "rgba(16, 185, 129, 0.18)" },
  amber: { main: styleGuide.palette.accent.amber, bg: "#fffbeb", glow: "rgba(245, 158, 11, 0.18)" },
  rose: { main: styleGuide.palette.accent.rose, bg: "#fff1f2", glow: "rgba(244, 63, 94, 0.18)" },
  violet: { main: styleGuide.palette.accent.violet, bg: "#f5f3ff", glow: "rgba(139, 92, 246, 0.18)" },
  indigo: { main: styleGuide.palette.accent.indigo, bg: "#eef2ff", glow: "rgba(79, 70, 229, 0.18)" },
} as const;

export type SectionTone = keyof typeof screenAccentMap;

export function sectionAccentTone(tone: SectionTone = "blue") {
  return screenAccentMap[tone];
}

export function statusChipSx(kind: keyof typeof statusPalette) {
  const token = statusPalette[kind];
  return {
    fontWeight: 700,
    letterSpacing: "-0.01em",
    bgcolor: token.bg,
    color: token.main,
    borderColor: token.border,
    boxShadow: `0 8px 18px ${token.main}12`,
    "& .MuiChip-label": { px: 1 },
  };
}

export function statusButtonSx(kind: keyof typeof statusPalette) {
  const token = statusPalette[kind];
  return {
    fontWeight: 700,
    letterSpacing: "-0.01em",
    borderColor: token.border,
    color: token.main,
    bgcolor: token.bg,
    boxShadow: `0 8px 18px ${token.main}0d`,
    "&:hover": {
      bgcolor: token.bg,
      borderColor: token.main,
    },
  };
}

export function Metric({ label, value, tone, note, accent: sectionAccent, icon }: { label: string; value: string; tone?: "vnd" | "usd" | "crypto" | "payos" | "paypal" | "neutral"; note?: string; accent?: SectionTone; icon?: ReactNode }) {
  const toneToken = sectionAccent ? sectionAccentTone(sectionAccent) : tone ? tonePalette[tone] : tonePalette.neutral;
  const accent = toneToken.main;
  const bg = toneToken.bg;
  const glow = toneToken.glow;
  const IconNode = icon || (tone === "vnd" ? <TrendingUp size={16} /> : tone === "usd" ? <CreditCard size={16} /> : tone === "crypto" ? <Coins size={16} /> : tone === "payos" ? <ShieldCheck size={16} /> : tone === "paypal" ? <BadgeDollarSign size={16} /> : null);
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
  return (
      <Card
        sx={{
          position: "relative",
          overflow: "hidden",
          minHeight: 138,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        bgcolor: bg,
        borderColor: `${accent}28`,
        backgroundImage: `radial-gradient(circle at 18% 16%, rgba(255,255,255,0.92) 0%, transparent 34%), linear-gradient(135deg, rgba(255,255,255,0.76) 0%, ${bg} 36%, rgba(255,255,255,0.14) 100%)`,
        boxShadow: `0 1px 0 rgba(16, 24, 40, 0.03), 0 14px 28px rgba(16, 24, 40, 0.07), inset 0 1px 0 rgba(255,255,255,0.72), 0 0 0 1px ${glow}`,
        }}
      >
        <Box sx={{ position: "absolute", inset: "0 auto auto 0", height: 4, width: "100%", bgcolor: accent }} />
      <Box sx={{ position: "absolute", top: -10, right: -8, width: 92, height: 92, borderRadius: "50%", bgcolor: glow, filter: "blur(18px)", opacity: 0.58 }} />
        <Box sx={{ position: "absolute", inset: "auto 0 0 0", height: 38, opacity: 0.98, background: `linear-gradient(90deg, transparent, ${accent}18 14%, ${accent}30 46%, ${accent}12 72%, transparent)` }} />
      <Box sx={{ position: "absolute", right: 14, bottom: 14, width: 58, height: 58, borderRadius: "50%", border: `1px solid ${accent}22`, background: `radial-gradient(circle at 30% 30%, ${accent}26, transparent 72%)`, opacity: 0.92 }} />
      <Box sx={{ position: "absolute", left: 18, bottom: 14, width: 48, height: 48, borderRadius: "50%", border: `1px solid ${accent}18`, background: `linear-gradient(180deg, rgba(255,255,255,0.52), ${accent}0f)`, opacity: 0.85 }} />
      <CardContent sx={{ display: "flex", flexDirection: "column", gap: 1, minHeight: 132, "&:last-child": { pb: 2 } }}>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.3, fontWeight: 800, letterSpacing: "-0.01em" }}>{label}</Typography>
          {IconNode ? <Box sx={{ display: "inline-flex", alignItems: "center", justifyContent: "center", width: 34, height: 34, borderRadius: "999px", bgcolor: `${accent}16`, color: accent, border: `1px solid ${accent}14`, boxShadow: `0 8px 18px ${accent}12` }}>{IconNode}</Box> : null}
        </Box>
        <Typography
          sx={{
            mt: "auto",
            fontWeight: 900,
            lineHeight: 0.95,
            letterSpacing: "-0.03em",
            fontSize: { xs: "1.65rem", sm: "1.9rem", md: "2.05rem" },
            wordBreak: "break-word",
            overflowWrap: "anywhere",
            maxWidth: "100%",
            color: "text.primary",
          }}
        >
          {compactValue}
        </Typography>
        {note ? <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.35 }}>{note}</Typography> : null}
      </CardContent>
    </Card>
  );
}

export function PanelHead({ title, subtitle, action, accent = "blue" }: { title: string; subtitle?: string; action?: ReactNode; accent?: SectionTone }) {
  const tone = sectionAccentTone(accent);
  return (
    <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", px: 2, py: 1.5, borderBottom: 1, borderColor: "divider", bgcolor: "background.paper", backgroundImage: `linear-gradient(180deg, ${tone.bg} 0%, rgba(255,255,255,0.96) 32%, rgba(255,255,255,1) 100%)` }}>
      <Box sx={{ position: "relative", pl: 1.5 }}>
        <Box sx={{ position: "absolute", left: 0, top: 8, bottom: 8, width: 4, borderRadius: 999, bgcolor: tone.main }} />
        <Typography variant="h6" sx={{ fontWeight: 700 }}>{title}</Typography>
        {subtitle ? <Typography variant="body2" color="text.secondary">{subtitle}</Typography> : null}
      </Box>
      {action}
    </Box>
  );
}

export function AppToolbar({ children }: { children: ReactNode }) {
  return (
    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 1.5, px: 2, py: 1.5 }}>
      {children}
    </Box>
  );
}

export function AppSection({ title, subtitle, action, children, compact = false, accent = "blue" }: { title: string; subtitle?: string; action?: ReactNode; children: ReactNode; compact?: boolean; accent?: SectionTone }) {
  const tone = sectionAccentTone(accent);
  return (
    <Card
      variant="outlined"
      sx={{
        overflow: "hidden",
        position: "relative",
        boxShadow: `0 12px 30px ${tone.main}10`,
        "&::before": {
          content: '""',
          position: "absolute",
          inset: 0,
          height: 4,
          background: `linear-gradient(90deg, ${tone.main}, rgba(124,58,237,0.92), rgba(16,185,129,0.9))`,
        },
      }}
    >
      <PanelHead title={title} subtitle={subtitle} action={action} accent={accent} />
      <Box sx={{ p: compact ? 1.5 : 2 }}>{children}</Box>
    </Card>
  );
}

export function AppDialog(props: { open: boolean; title: string; subtitle?: string; onClose: () => void; children: ReactNode; maxWidth?: "sm" | "md" | "lg" | "xl" }) {
  return <MuiDialogShell {...props} />;
}

export function TrendChart({
  title,
  subtitle,
  rangeLabel,
  points,
  accent = "blue",
  valueLabel,
  secondaryLabel,
}: {
  title: string;
  subtitle?: string;
  rangeLabel?: string;
  points: { label: string; value: number }[];
  accent?: SectionTone;
  valueLabel: string;
  secondaryLabel: string;
}) {
  const tone = sectionAccentTone(accent);
  const chartId = useId().replace(/:/g, "");
  const width = 720;
  const height = 220;
  const paddingX = 18;
  const paddingY = 20;
  const values = points.map((item) => item.value);
  const maxValue = Math.max(1, ...values);
  const minValue = Math.min(0, ...values);
  const span = Math.max(1, maxValue - minValue);
  const step = points.length > 1 ? (width - paddingX * 2) / (points.length - 1) : 0;
  const linePoints = points
    .map((item, index) => {
      const x = paddingX + step * index;
      const y = height - paddingY - ((item.value - minValue) / span) * (height - paddingY * 2);
      return `${x},${y}`;
    })
    .join(" ");
  const areaPoints = `${paddingX},${height - paddingY} ${linePoints} ${width - paddingX},${height - paddingY}`;
  return (
    <Card variant="outlined" sx={{ overflow: "hidden", bgcolor: "background.paper", backgroundImage: `linear-gradient(180deg, ${tone.bg} 0%, rgba(255,255,255,0.98) 26%, rgba(255,255,255,1) 100%)` }}>
      <PanelHead
        title={title}
        subtitle={subtitle}
        accent={accent}
        action={rangeLabel ? <Chip size="small" label={rangeLabel} variant="outlined" sx={statusChipSx("muted")} /> : null}
      />
      <Box sx={{ px: 2, pt: 1.5, pb: 2 }}>
        <Box sx={{ display: "flex", gap: 1, mb: 1.5, flexWrap: "wrap" }}>
          <Chip size="small" label={valueLabel} variant="outlined" sx={statusChipSx("success")} />
          <Chip size="small" label={secondaryLabel} variant="outlined" sx={statusChipSx("warning")} />
        </Box>
        <Box sx={{ width: "100%", overflowX: "auto" }}>
          <Box component="svg" viewBox={`0 0 ${width} ${height}`} sx={{ width: "100%", minWidth: 640, height: 260, display: "block" }}>
            <defs>
              <linearGradient id={`${chartId}-chart-area`} x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor={tone.main} stopOpacity="0.28" />
                <stop offset="100%" stopColor={tone.main} stopOpacity="0.03" />
              </linearGradient>
              <linearGradient id={`${chartId}-chart-line`} x1="0" x2="1" y1="0" y2="0">
                <stop offset="0%" stopColor={tone.main} />
                <stop offset="50%" stopColor={styleGuide.palette.secondary.main} />
                <stop offset="100%" stopColor={styleGuide.palette.accent.emerald} />
              </linearGradient>
            </defs>
            {[0, 1, 2, 3].map((line) => {
              const y = paddingY + ((height - paddingY * 2) / 3) * line;
              return <line key={line} x1={paddingX} x2={width - paddingX} y1={y} y2={y} stroke="rgba(148,163,184,0.18)" strokeDasharray="4 6" />;
            })}
            {points.length ? <polygon points={areaPoints} fill={`url(#${chartId}-chart-area)`} /> : null}
            {points.length ? <polyline points={linePoints} fill="none" stroke={`url(#${chartId}-chart-line)`} strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round" /> : null}
            {points.map((item, index) => {
              const x = paddingX + step * index;
              const y = height - paddingY - ((item.value - minValue) / span) * (height - paddingY * 2);
              return (
                <g key={`${item.label}-${index}`}>
                  <circle cx={x} cy={y} r="5.5" fill="#ffffff" stroke={tone.main} strokeWidth="3" />
                  <text x={x} y={height - 4} textAnchor="middle" fontSize="10" fill="#64748b">{item.label}</text>
                </g>
              );
            })}
          </Box>
        </Box>
        <Box sx={{ display: "flex", justifyContent: "space-between", gap: 2, mt: 1 }}>
          <Typography variant="caption" color="text.secondary">Kéo ngang để xem thêm mốc nếu cần.</Typography>
          <Typography variant="caption" color="text.secondary">Dữ liệu hiển thị theo {rangeLabel?.toLowerCase() || "kỳ đã chọn"}.</Typography>
        </Box>
      </Box>
    </Card>
  );
}

export function BreakdownChart({
  title,
  subtitle,
  accent = "blue",
  items,
}: {
  title: string;
  subtitle?: string;
  accent?: SectionTone;
  items: { label: string; value: number; note?: string }[];
}) {
  const tone = sectionAccentTone(accent);
  const maxValue = Math.max(1, ...items.map((item) => item.value));
  return (
    <Card variant="outlined" sx={{ overflow: "hidden", backgroundImage: `linear-gradient(180deg, ${tone.bg} 0%, rgba(255,255,255,0.98) 28%, rgba(255,255,255,1) 100%)` }}>
      <PanelHead title={title} subtitle={subtitle} accent={accent} />
      <Box sx={{ p: 2, display: "grid", gap: 1.25 }}>
        {items.map((item, index) => {
          const percent = Math.max(4, Math.round((item.value / maxValue) * 100));
          const palettes = [tone.main, styleGuide.palette.secondary.main, styleGuide.palette.accent.emerald, styleGuide.palette.accent.amber];
          const barColor = palettes[index % palettes.length];
          return (
            <Box key={item.label} sx={{ display: "grid", gap: 0.75 }}>
              <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 1 }}>
                <Typography sx={{ fontWeight: 700, lineHeight: 1.2 }}>{item.label}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 700 }}>{item.value}</Typography>
              </Box>
              <Box sx={{ height: 12, borderRadius: 999, bgcolor: "rgba(148,163,184,0.16)", overflow: "hidden" }}>
                <Box sx={{ width: `${percent}%`, height: "100%", borderRadius: 999, bgcolor: barColor, backgroundImage: `linear-gradient(90deg, ${barColor}, rgba(255,255,255,0.22))`, boxShadow: `0 8px 20px ${barColor}28` }} />
              </Box>
              {item.note ? <Typography variant="caption" color="text.secondary">{item.note}</Typography> : null}
            </Box>
          );
        })}
      </Box>
    </Card>
  );
}

export function DonutChart({
  title,
  subtitle,
  accent = "blue",
  segments,
  centerLabel,
}: {
  title: string;
  subtitle?: string;
  accent?: SectionTone;
  segments: { label: string; value: number; color?: string }[];
  centerLabel: string;
}) {
  const tone = sectionAccentTone(accent);
  const chartId = useId().replace(/:/g, "");
  const colors = [tone.main, styleGuide.palette.secondary.main, styleGuide.palette.accent.emerald, styleGuide.palette.accent.amber, styleGuide.palette.accent.rose, styleGuide.palette.accent.cyan];
  const total = Math.max(1, segments.reduce((sum, item) => sum + item.value, 0));
  const radius = 42;
  const circumference = 2 * Math.PI * radius;
  let offset = 0;
  return (
    <Card variant="outlined" sx={{ overflow: "hidden", backgroundImage: `linear-gradient(180deg, ${tone.bg} 0%, rgba(255,255,255,0.98) 28%, rgba(255,255,255,1) 100%)` }}>
      <PanelHead title={title} subtitle={subtitle} accent={accent} />
      <Box sx={{ p: 2, display: "grid", gap: 2 }}>
        <Box sx={{ display: "grid", gridTemplateColumns: "180px minmax(0, 1fr)", gap: 2, alignItems: "center" }}>
          <Box sx={{ position: "relative", width: 180, height: 180, display: "grid", placeItems: "center" }}>
            <Box component="svg" viewBox="0 0 120 120" sx={{ width: 180, height: 180, transform: "rotate(-90deg)" }}>
              <circle cx="60" cy="60" r={radius} fill="none" stroke="rgba(148,163,184,0.15)" strokeWidth="16" />
              {segments.map((segment, index) => {
                const fraction = segment.value / total;
                const dash = fraction * circumference;
                const stroke = segment.color || colors[index % colors.length];
                const circle = (
                  <circle
                    key={`${chartId}-${segment.label}`}
                    cx="60"
                    cy="60"
                    r={radius}
                    fill="none"
                    stroke={stroke}
                    strokeWidth="16"
                    strokeDasharray={`${dash} ${circumference - dash}`}
                    strokeDashoffset={-offset}
                    strokeLinecap="round"
                  />
                );
                offset += dash;
                return circle;
              })}
            </Box>
            <Box sx={{ position: "absolute", inset: 0, display: "grid", placeItems: "center", textAlign: "center", px: 2 }}>
              <Typography sx={{ fontWeight: 900, lineHeight: 1.05, letterSpacing: "-0.03em" }}>{centerLabel}</Typography>
            </Box>
          </Box>
          <Stack spacing={1}>
            {segments.map((segment, index) => (
              <Box key={segment.label} sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 1.5 }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                  <Box sx={{ width: 10, height: 10, borderRadius: 999, bgcolor: segment.color || colors[index % colors.length] }} />
                  <Typography sx={{ fontWeight: 700 }}>{segment.label}</Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 700 }}>{segment.value}</Typography>
              </Box>
            ))}
          </Stack>
        </Box>
      </Box>
    </Card>
  );
}

export function HealthItem({ ok, title, detail }: { ok: boolean; title: string; detail: string }) {
  return (
    <Card variant="outlined">
      <CardContent>
        <Box sx={{ display: "flex", gap: 1.5, alignItems: "flex-start" }}>
          {ok ? <CheckCircle2 color={statusPalette.success.main} size={20} /> : <XCircle color={statusPalette.error.main} size={20} />}
          <Box>
            <Typography sx={{ fontWeight: 700 }}>{title}</Typography>
            <Typography variant="body2" color="text.secondary">{detail}</Typography>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}

export function Info({ label, value }: { label: string; value: string }) {
  return (
    <Card variant="outlined">
      <CardContent sx={{ display: "flex", justifyContent: "space-between", gap: 2 }}>
        <Typography variant="body2" color="text.secondary">{label}</Typography>
        <Typography sx={{ fontWeight: 700 }}>{value}</Typography>
      </CardContent>
    </Card>
  );
}

export function ConfigEditor({ title, subtitle, fields, values, setValues, onSave }: { title: string; subtitle: string; fields: ConfigField[]; values: Record<string, string>; setValues: (values: Record<string, string>) => void; onSave: (fields: ConfigField[], values: Record<string, string>) => Promise<boolean> }) {
  const [editingField, setEditingField] = useState<ConfigField | null>(null);
  const [draftValue, setDraftValue] = useState("");
  const [savingField, setSavingField] = useState(false);

  async function saveField() {
    if (!editingField) return;
    setSavingField(true);
    const nextValues = { ...values, [editingField.key]: draftValue };
    setValues(nextValues);
    try {
      const saved = await onSave([editingField], nextValues);
      if (saved) setEditingField(null);
      else setValues(values);
    } finally {
      setSavingField(false);
    }
  }

  return (
    <Card variant="outlined">
      <PanelHead title={title} subtitle={`${subtitle} Bấm vào từng mục để chỉnh sửa và lưu riêng.`} />
      <Box sx={{ display: "grid", gap: 1.25, p: 2 }}>
        {fields.map((field) => (
          <Card
            key={field.key}
            variant="outlined"
            sx={{
              cursor: "pointer",
              transition: "border-color 120ms ease, box-shadow 120ms ease, transform 120ms ease",
              "&:hover": { borderColor: "primary.main", boxShadow: (theme) => `0 10px 24px ${theme.palette.primary.main}14`, transform: "translateY(-1px)" },
            }}
            onClick={() => { setEditingField(field); setDraftValue(values[field.key] || ""); }}
          >
            <CardContent sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2, py: 2, "&:last-child": { pb: 2 } }}>
              <Box>
                <Typography sx={{ fontWeight: 700 }}>{field.label}</Typography>
                <Typography variant="body2" color="text.secondary">{field.help}</Typography>
              </Box>
              <Typography variant="body2" sx={{ fontWeight: 700, color: values[field.key] ? "text.primary" : "text.secondary" }}>
                {field.kind === "select" ? field.options?.find((item) => item.value === (values[field.key] || field.placeholder))?.label || values[field.key] || field.placeholder : values[field.key] || "Chưa thiết lập"}
              </Typography>
            </CardContent>
          </Card>
        ))}
      </Box>
      <Dialog open={Boolean(editingField)} onClose={() => setEditingField(null)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ position: "relative", pr: 6, pb: 1.25 }}>
          <Typography variant="h6" sx={{ fontWeight: 800, letterSpacing: "-0.02em" }}>{editingField?.label}</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.75 }}>{editingField?.help}</Typography>
          <IconButton onClick={() => setEditingField(null)} size="small" sx={{ position: "absolute", right: 12, top: 12, border: 1, borderColor: "divider", bgcolor: "background.paper", "&:hover": { bgcolor: "action.hover" } }}>
            <XCircle size={18} />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers sx={{ py: 2.5, bgcolor: "background.default" }}>
          <Box sx={{ display: "grid", gap: 2 }}>
            <Typography variant="body2" color="text.secondary">{editingField?.help}</Typography>
            {editingField?.kind === "textarea" ? (
              <TextField multiline minRows={5} autoFocus value={draftValue} onChange={(event) => setDraftValue(event.target.value)} placeholder={editingField.placeholder} fullWidth />
            ) : editingField?.kind === "select" ? (
              <FormControl fullWidth>
                <Select autoFocus value={draftValue || editingField.placeholder} onChange={(event) => setDraftValue(String(event.target.value))}>
                  {(editingField.options || []).map((item) => <MenuItem key={item.value} value={item.value}>{item.label}</MenuItem>)}
                </Select>
              </FormControl>
            ) : (
              <TextField autoFocus value={draftValue} onChange={(event) => setDraftValue(event.target.value)} placeholder={editingField?.placeholder} fullWidth />
            )}
            <Typography variant="caption" color="text.secondary">Key kỹ thuật: {editingField?.key}</Typography>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button variant="outlined" onClick={() => setEditingField(null)} sx={statusButtonSx("muted")}>Huỷ</Button>
          <Button variant="contained" onClick={saveField} disabled={savingField} startIcon={savingField ? <Loader2 size={16} /> : <Save size={16} />}>Lưu thay đổi</Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
}

export function SettingsConfigModal(props: { title: string; subtitle: string; fields: ConfigField[]; values: Record<string, string>; setValues: (values: Record<string, string>) => void; onSave: (fields: ConfigField[], values: Record<string, string>) => Promise<boolean>; onClose: () => void }) {
  return (
    <AppDialog open title={props.title} subtitle={props.subtitle} onClose={props.onClose} maxWidth="md">
        <ConfigEditor title={props.title} subtitle={props.subtitle} fields={props.fields} values={props.values} setValues={props.setValues} onSave={props.onSave} />
    </AppDialog>
  );
}

export function MuiDialogShell({ open, title, subtitle, onClose, children, maxWidth = "md" }: { open: boolean; title: string; subtitle?: string; onClose: () => void; children: ReactNode; maxWidth?: "sm" | "md" | "lg" | "xl" }) {
  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth={maxWidth} scroll="paper">
      <DialogTitle sx={{ position: "relative", pr: 6 }}>
        <Typography variant="h6" sx={{ fontWeight: 800, letterSpacing: "-0.03em", lineHeight: 1.15 }}>{title}</Typography>
        {subtitle ? <Typography variant="body2" color="text.secondary" sx={{ mt: 0.9, maxWidth: 760, lineHeight: 1.5 }}>{subtitle}</Typography> : null}
        <IconButton
          aria-label="Đóng"
          onClick={onClose}
          size="small"
          sx={{
            position: "absolute",
            right: 16,
            top: 16,
            width: 36,
            height: 36,
            border: 1,
            borderColor: "divider",
            bgcolor: "background.paper",
            color: "text.secondary",
            boxShadow: "0 1px 0 rgba(16, 24, 40, 0.03)",
            "&:hover": { bgcolor: "action.hover", color: "text.primary" },
          }}
        >
          <XCircle size={18} />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers sx={{ py: 3, bgcolor: "background.default" }}>
        <Stack spacing={2.5}>
          {children}
        </Stack>
      </DialogContent>
    </Dialog>
  );
}

export function SimpleTable({ headers, rows, onRow, actions }: { headers: string[]; rows: ReactNode[][]; onRow?: (index: number) => void; actions?: (index: number) => ReactNode }) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          {headers.map((item) => <TableCell key={item}>{item}</TableCell>)}
          {actions ? <TableCell>Thao tác</TableCell> : null}
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.length ? rows.map((row, idx) => (
          <TableRow key={idx} hover onClick={() => onRow?.(idx)} sx={{ cursor: onRow ? "pointer" : "default" }}>
            {row.map((cell, cellIdx) => <TableCell key={cellIdx}>{cell}</TableCell>)}
            {actions ? <TableCell>{actions(idx)}</TableCell> : null}
          </TableRow>
        )) : (
          <TableRow>
            <TableCell colSpan={headers.length + (actions ? 1 : 0)} align="center">Chưa có dữ liệu. Bấm nút thêm mới để tạo.</TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}

export function Pagination({ page, totalPages, totalItems, onPage, label = "đơn" }: { page: number; totalPages: number; totalItems: number; onPage: (page: number) => void; label?: string }) {
  const safePage = Math.min(page, totalPages);
  return (
    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2, py: 1 }}>
      <Typography variant="body2" color="text.secondary">{totalItems} {label} • Trang {safePage}/{totalPages}</Typography>
      <Box sx={{ display: "flex", gap: 1 }}>
        <Button variant="outlined" size="small" disabled={safePage <= 1} onClick={() => onPage(safePage - 1)}>Trước</Button>
        <Button variant="outlined" size="small" disabled={safePage >= totalPages} onClick={() => onPage(safePage + 1)}>Sau</Button>
      </Box>
    </Box>
  );
}

export function OrdersTable({ orders, onStatusChange, onDeleteOrder, saving }: { orders: Order[]; onStatusChange: (orderId: string, status: string) => void; onDeleteOrder: (orderId: string, label?: string) => Promise<void>; saving: string }) {
  const statusChip = (status: string) => {
    const normalized = String(status || "").toUpperCase();
    if (normalized === "PAID") return <Chip size="small" label={status} variant="outlined" sx={statusChipSx("success")} />;
    if (normalized === "PENDING") return <Chip size="small" label={status} variant="outlined" sx={statusChipSx("warning")} />;
    if (normalized === "EXPIRED") return <Chip size="small" label={status} variant="outlined" sx={statusChipSx("muted")} />;
    if (normalized === "CANCELLED") return <Chip size="small" label={status} variant="outlined" sx={statusChipSx("error")} />;
    return <Chip size="small" label={status || "-"} variant="outlined" sx={statusChipSx("muted")} />;
  };
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>Mã đơn</TableCell><TableCell>Khách</TableCell><TableCell>Gói</TableCell><TableCell>Tiền</TableCell><TableCell>Coupon</TableCell><TableCell>Trạng thái</TableCell><TableCell>Tạo lúc</TableCell><TableCell>Đổi trạng thái</TableCell><TableCell>Xóa</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {orders.map((order) => (
          <TableRow key={order.order_id}>
            <TableCell>{order.order_id}</TableCell>
            <TableCell><Typography sx={{ fontWeight: 700 }}>{order.full_name || "-"}</Typography><Typography variant="caption" color="text.secondary">{order.telegram_user_id}</Typography></TableCell>
            <TableCell>{order.plan_name}</TableCell>
            <TableCell>{order.amount}</TableCell>
            <TableCell>{order.coupon_code || "-"}</TableCell>
            <TableCell>{statusChip(order.status)}</TableCell>
            <TableCell>{dateText(order.created_at)}</TableCell>
            <TableCell>
              <Select size="small" value={order.status} onChange={(event) => onStatusChange(order.order_id, String(event.target.value))} fullWidth>
                <MenuItem value="PENDING">PENDING</MenuItem><MenuItem value="PAID">PAID</MenuItem><MenuItem value="CANCELLED">CANCELLED</MenuItem><MenuItem value="EXPIRED">EXPIRED</MenuItem>
              </Select>
            </TableCell>
            <TableCell>
              <Button variant="outlined" size="small" sx={statusButtonSx("error")} onClick={() => onDeleteOrder(order.order_id, order.full_name || order.telegram_user_id)} disabled={saving === `order-delete-${order.order_id}`}>
                <Trash2 size={16} />
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

export function TrendTable({ rows, title, subtitle }: { rows: { label: string; revenue: string; paid: number; pending: number; customers: number; aov: string; coupon: string; conversion: string; conversionColor: "good" | "warn" | "bad"; barWidth: number; trend: number; sparkline: number[] }[]; title: string; subtitle?: string }) {
  return (
    <Card variant="outlined">
      <PanelHead title={title} subtitle={subtitle} />
      <Box sx={{ overflowX: "auto" }}>
        <Table size="small" sx={{ minWidth: 1120 }}>
          <TableHead>
            <TableRow>
              <TableCell>Kỳ</TableCell>
              <TableCell>Doanh thu</TableCell>
              <TableCell>Bar</TableCell>
              <TableCell>Sparkline</TableCell>
              <TableCell>PAID</TableCell>
              <TableCell>PENDING</TableCell>
              <TableCell>Khách trả tiền</TableCell>
              <TableCell>AOV</TableCell>
              <TableCell>Coupon giảm</TableCell>
              <TableCell>Tỉ lệ thanh toán</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.length ? rows.map((row) => (
              <TableRow key={row.label}>
                <TableCell sx={{ fontWeight: 700 }}>{row.label}</TableCell>
                <TableCell>{row.revenue}</TableCell>
                <TableCell>
                  <Box sx={{ width: 220, height: 12, bgcolor: "grey.200", borderRadius: 999, overflow: "hidden" }}>
                    <Box sx={{
                      width: `${Math.max(6, row.barWidth)}%`,
                      height: "100%",
                      bgcolor: row.trend > 0 ? "success.main" : row.trend < 0 ? "error.main" : "primary.main",
                    }} />
                  </Box>
                </TableCell>
                <TableCell>
                  <Box sx={{ width: 120, height: 28, display: "flex", alignItems: "center" }}>
                    <svg width="120" height="28" viewBox="0 0 120 28" aria-hidden="true">
                      <defs>
                        <linearGradient id={`sparkline-gradient-${row.label.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}`} x1="0%" y1="0%" x2="100%" y2="0%">
                          <stop offset="0%" stopColor={row.trend > 0 ? "#067647" : row.trend < 0 ? "#b42318" : "#0d6b5d"} stopOpacity="0.22" />
                          <stop offset="100%" stopColor={row.trend > 0 ? "#22c55e" : row.trend < 0 ? "#ef4444" : "#14b8a6"} stopOpacity="0.88" />
                        </linearGradient>
                      </defs>
                      {(() => {
                        const values = row.sparkline.length ? row.sparkline : [0];
                        const max = Math.max(1, ...values);
                        const step = values.length > 1 ? 110 / (values.length - 1) : 110;
                        const points = values.map((value, index) => `${5 + index * step},${24 - (value / max) * 18}`).join(" ");
                        return (
                          <>
                            <polyline fill={`url(#sparkline-gradient-${row.label.replace(/[^a-z0-9]+/gi, "-").toLowerCase()})`} stroke="none" points={`5,24 ${points} 115,24`} />
                            <polyline fill="none" stroke={`url(#sparkline-gradient-${row.label.replace(/[^a-z0-9]+/gi, "-").toLowerCase()})`} strokeWidth="2.2" points={points} strokeLinecap="round" strokeLinejoin="round" />
                            {values.map((value, index) => (
                              <circle key={index} cx={5 + index * step} cy={24 - (value / max) * 18} r="1.8" fill={`url(#sparkline-gradient-${row.label.replace(/[^a-z0-9]+/gi, "-").toLowerCase()})`} />
                            ))}
                          </>
                        );
                      })()}
                    </svg>
                  </Box>
                </TableCell>
                <TableCell>{row.paid}</TableCell>
                <TableCell>{row.pending}</TableCell>
                <TableCell>{row.customers}</TableCell>
                <TableCell>{row.aov}</TableCell>
                <TableCell>{row.coupon}</TableCell>
                <TableCell>
                  <Box
                      sx={{
                        display: "inline-flex",
                        minWidth: 72,
                        justifyContent: "center",
                        px: 1.25,
                        py: 0.5,
                        borderRadius: 999,
                        fontWeight: 700,
                        color: row.conversionColor === "good" ? "#067647" : row.conversionColor === "warn" ? "#b54708" : "#b42318",
                        bgcolor: row.conversionColor === "good" ? "#ecfdf3" : row.conversionColor === "warn" ? "#fffaeb" : "#fef3f2",
                        border: "1px solid",
                        borderColor: row.conversionColor === "good" ? "#abefc6" : row.conversionColor === "warn" ? "#fedf89" : "#fecdca",
                      }}
                    >
                    {row.conversion}
                  </Box>
                </TableCell>
              </TableRow>
            )) : (
              <TableRow>
                <TableCell colSpan={9} align="center">Chưa có dữ liệu trong kỳ này.</TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </Box>
    </Card>
  );
}
