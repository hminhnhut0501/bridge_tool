export const styleGuide = {
  name: "mui-homepage-dashboard",
  summary:
    "Visual language for the admin UI: bright MUI-style surfaces, gradient blue primary, vibrant secondary, soft shadows, and rounded cards/dialogs.",
  palette: {
    primary: {
      main: "#0066ff",
      light: "#66a3ff",
      dark: "#0052cc",
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
      sky: "#0ea5e9",
      violet: "#8b5cf6",
      blue: "#0066ff",
      green: "#10b981",
    },
    background: {
      default: "#f8fafc",
      paper: "#ffffff",
    },
    text: {
      primary: "#0f172a",
      secondary: "#64748b",
    },
    divider: "#f1f5f9",
  },
  shape: {
    cardRadius: 10,
    dialogRadius: 12,
    inputRadius: 8,
    buttonRadius: 8,
  },
  shadows: {
    card: "0 4px 20px rgba(15, 23, 42, 0.03), 0 1px 2px rgba(15, 23, 42, 0.02)",
    dialog: "0 24px 64px rgba(15, 23, 42, 0.08)",
    focus: "0 0 0 4px rgba(0, 102, 255, 0.15)",
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
    displayTracking: "-0.03em",
    headingTracking: "-0.015em",
    bodyTracking: "-0.005em",
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
  tokens: {
    field: {
      radius: 8,
      border: "#e2e8f0",
      hoverBorder: "#cbd5e1",
      focusBorder: "#0066ff",
      background: "#ffffff",
    },
    button: {
      radius: 8,
      containedShadow: "0 8px 20px rgba(0, 102, 255, 0.16)",
      outlinedShadow: "0 4px 10px rgba(15, 23, 42, 0.02)",
    },
    panel: {
      headerRadius: 10,
      border: "#f1f5f9",
      shadow: "0 10px 30px rgba(15, 23, 42, 0.04)",
    },
  },
  screenThemes: {
    overview: ["blue", "cyan", "emerald"],
    orders: ["blue", "amber", "rose"],
    customers: ["violet", "emerald", "blue"],
    campaigns: ["cyan", "violet", "amber"],
    channelPosts: ["cyan", "violet", "amber"],
  },
} as const;

export type StyleGuide = typeof styleGuide;
