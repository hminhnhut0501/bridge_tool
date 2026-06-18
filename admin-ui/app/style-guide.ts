export const styleGuide = {
  name: "mui-homepage-dashboard",
  summary:
    "Visual language for the admin UI: bright MUI-style surfaces, blue primary, purple secondary, soft shadows, and rounded cards/dialogs.",
  palette: {
    primary: {
      main: "#2563eb",
      light: "#60a5fa",
      dark: "#1d4ed8",
      contrastText: "#ffffff",
    },
    secondary: {
      main: "#7c3aed",
      light: "#c084fc",
      dark: "#6d28d9",
      contrastText: "#ffffff",
    },
    accent: {
      cyan: "#06b6d4",
      emerald: "#10b981",
      amber: "#f59e0b",
      rose: "#f43f5e",
      indigo: "#4f46e5",
    },
    background: {
      default: "#f6f8fc",
      paper: "#ffffff",
    },
    text: {
      primary: "#1f2937",
      secondary: "#6b7280",
    },
    divider: "#e2e8f0",
  },
  shape: {
    cardRadius: 18,
    dialogRadius: 24,
    inputRadius: 14,
    buttonRadius: 999,
  },
  shadows: {
    card: "0 1px 0 rgba(16, 24, 40, 0.03), 0 10px 24px rgba(16, 24, 40, 0.05)",
    dialog: "0 20px 60px rgba(15, 23, 42, 0.14)",
    focus: "0 0 0 4px rgba(37, 99, 235, 0.12)",
  },
  typography: {
    fontFamily: [
      "Inter",
      "ui-sans-serif",
      "system-ui",
      "-apple-system",
      "BlinkMacSystemFont",
      "Segoe UI",
      "sans-serif",
    ].join(","),
    displayTracking: "-0.04em",
    headingTracking: "-0.02em",
    bodyTracking: "-0.01em",
  },
  rules: [
    "Use MUI components by default: Button, TextField, Select, Tabs, Card, Dialog, Chip, Table, IconButton, Box, Stack.",
    "Prefer theme overrides and sx over ad-hoc CSS. Add global CSS only for shell-level layout or true reset needs.",
    "Primary action uses contained Button, secondary action uses outlined Button, destructive action uses outlined color=error.",
    "Prefer colorful accents only where they help scanning: metrics, badges, status chips, progress, and card headers.",
    "Dialog titles should be bold, compact, and include a close IconButton on the top-right.",
    "Keep cards white, borders subtle, and shadows soft. Reserve saturated color for selected states and badges only.",
    "Use rounded pills for tabs and chips. Use one blue primary, one purple accent, and a small set of secondary accent colors.",
    "Prefer semantic status colors from the theme and shared helpers rather than inline custom hex values.",
    "All dates/times should pass through shared format helpers, never raw ISO strings.",
    "When a section needs identity, assign one accent tone to that section instead of repeating the same blue everywhere.",
  ],
} as const;

export type StyleGuide = typeof styleGuide;
