export const styleGuide = {
  name: "mui-homepage-dashboard",
  summary:
    "Visual language for the admin UI: bright MUI-style surfaces, blue primary, purple secondary, soft shadows, and rounded cards/dialogs.",
  palette: {
    primary: {
      main: "#1976d2",
      light: "#42a5f5",
      dark: "#1565c0",
      contrastText: "#ffffff",
    },
    secondary: {
      main: "#7c3aed",
      light: "#a855f7",
      dark: "#5b21b6",
      contrastText: "#ffffff",
    },
    background: {
      default: "#f7f9fc",
      paper: "#ffffff",
    },
    text: {
      primary: "#1f2937",
      secondary: "#6b7280",
    },
    divider: "#e5e7eb",
  },
  shape: {
    cardRadius: 18,
    dialogRadius: 24,
    inputRadius: 14,
    buttonRadius: 999,
  },
  shadows: {
    card: "0 1px 0 rgba(16, 24, 40, 0.03), 0 8px 20px rgba(16, 24, 40, 0.04)",
    dialog: "0 20px 60px rgba(15, 23, 42, 0.16)",
    focus: "0 0 0 4px rgba(25, 118, 210, 0.12)",
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
    "Dialog titles should be bold, compact, and include a close IconButton on the top-right.",
    "Keep cards white, borders subtle, and shadows soft. Reserve saturated color for selected states and badges only.",
    "Use rounded pills for tabs and chips. Use a single blue primary and one purple accent, not multiple greens/blues.",
    "Prefer semantic status colors from the theme and shared helpers rather than inline custom hex values.",
    "All dates/times should pass through shared format helpers, never raw ISO strings.",
  ],
} as const;

export type StyleGuide = typeof styleGuide;
