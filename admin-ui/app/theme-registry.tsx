"use client";

import { CssBaseline, ThemeProvider, createTheme, responsiveFontSizes } from "@mui/material";
import type { ReactNode } from "react";
import { styleGuide } from "./style-guide";

const baseTheme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: styleGuide.palette.primary.main,
      dark: styleGuide.palette.primary.dark,
      light: styleGuide.palette.primary.light,
      contrastText: "#ffffff",
    },
    secondary: {
      main: styleGuide.palette.secondary.main,
      light: styleGuide.palette.secondary.light,
      dark: styleGuide.palette.secondary.dark,
      contrastText: "#ffffff",
    },
    info: {
      main: styleGuide.palette.accent.cyan,
      light: "#67e8f9",
      dark: "#0891b2",
      contrastText: "#ffffff",
    },
    success: {
      main: styleGuide.palette.accent.emerald,
      light: "#34d399",
      dark: "#059669",
      contrastText: "#ffffff",
    },
    warning: {
      main: styleGuide.palette.accent.amber,
      light: "#fbbf24",
      dark: "#d97706",
      contrastText: "#ffffff",
    },
    error: {
      main: styleGuide.palette.accent.rose,
      light: "#fb7185",
      dark: "#e11d48",
      contrastText: "#ffffff",
    },
    background: {
      default: styleGuide.palette.background.default,
      paper: styleGuide.palette.background.paper,
    },
    text: {
      primary: styleGuide.palette.text.primary,
      secondary: styleGuide.palette.text.secondary,
    },
    divider: styleGuide.palette.divider,
  },
  shape: {
    borderRadius: styleGuide.shape.cardRadius,
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
    fontWeightLight: 400,
    fontWeightRegular: 500,
    fontWeightMedium: 600,
    fontWeightBold: 800,
    h1: { fontWeight: 800, lineHeight: 1.05, letterSpacing: "-0.04em" },
    h2: { fontWeight: 800, lineHeight: 1.08, letterSpacing: "-0.035em" },
    h3: { fontWeight: 800, lineHeight: 1.1, letterSpacing: "-0.03em" },
    h4: { fontWeight: 800, lineHeight: 1.15, letterSpacing: "-0.025em" },
    h5: { fontWeight: 700, lineHeight: 1.2, letterSpacing: "-0.02em" },
    h6: { fontWeight: 700, lineHeight: 1.25, letterSpacing: "-0.015em" },
    subtitle1: { fontWeight: 600, lineHeight: 1.35, letterSpacing: "-0.01em" },
    subtitle2: { fontWeight: 600, lineHeight: 1.35, letterSpacing: "-0.008em" },
    body1: { fontWeight: 500, lineHeight: 1.55, letterSpacing: "-0.004em" },
    body2: { fontWeight: 500, lineHeight: 1.45, letterSpacing: "-0.002em" },
    caption: { fontWeight: 500, lineHeight: 1.35, letterSpacing: "0" },
    button: { fontWeight: 700, textTransform: "none" },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        html: {
          backgroundColor: styleGuide.palette.background.default,
        },
        body: {
          backgroundColor: styleGuide.palette.background.default,
          color: styleGuide.palette.text.primary,
          fontFamily: styleGuide.typography.fontFamily,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: styleGuide.shape.buttonRadius,
          boxShadow: "none",
          letterSpacing: styleGuide.typography.bodyTracking,
        },
        contained: {
          boxShadow: "0 10px 22px rgba(37, 99, 235, 0.16)",
          backgroundImage: "linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%)",
          color: "#ffffff",
          "&:hover": {
            backgroundImage: "linear-gradient(135deg, #1d4ed8 0%, #0284c7 100%)",
            boxShadow: "0 12px 26px rgba(37, 99, 235, 0.22)",
          },
        },
        outlined: {
          borderColor: styleGuide.palette.primary.main,
          backgroundColor: "#ffffff",
          color: styleGuide.palette.primary.main,
          "&:hover": {
            borderColor: styleGuide.palette.primary.dark,
            backgroundColor: "rgba(25, 118, 210, 0.04)",
          },
        },
        text: {
          color: styleGuide.palette.primary.main,
          "&:hover": {
            backgroundColor: "rgba(37, 99, 235, 0.06)",
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          minHeight: 46,
          gap: 8,
        },
        indicator: {
          display: "none",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          fontWeight: 700,
          letterSpacing: styleGuide.typography.bodyTracking,
        },
        outlined: {
          borderColor: styleGuide.palette.divider,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          alignItems: "center",
          border: `1px solid ${styleGuide.palette.divider}`,
          borderRadius: 999,
          backgroundColor: "#ffffff",
          color: styleGuide.palette.text.primary,
          minHeight: 42,
          padding: "10px 14px",
          fontWeight: 700,
          letterSpacing: styleGuide.typography.bodyTracking,
          textTransform: "none",
          transition: "background-color 160ms ease, border-color 160ms ease, color 160ms ease, box-shadow 160ms ease",
          "&:hover": {
            backgroundColor: "rgba(25, 118, 210, 0.06)",
            borderColor: styleGuide.palette.primary.light,
          },
          "&.Mui-selected": {
            backgroundImage: "linear-gradient(135deg, #2563eb 0%, #0ea5e9 100%)",
            borderColor: styleGuide.palette.primary.main,
            color: "#ffffff",
            boxShadow: "0 8px 20px rgba(25, 118, 210, 0.16)",
          },
          "&.Mui-selected:hover": {
            backgroundImage: "linear-gradient(135deg, #1d4ed8 0%, #0284c7 100%)",
            borderColor: styleGuide.palette.primary.dark,
          },
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: styleGuide.shape.inputRadius,
          backgroundColor: "#ffffff",
          transition: "box-shadow 160ms ease, border-color 160ms ease, background-color 160ms ease",
          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: styleGuide.palette.divider,
          },
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: "#c5d9ef",
          },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: styleGuide.palette.primary.main,
            borderWidth: 1.5,
          },
          "&.Mui-focused": {
            boxShadow: styleGuide.shadows.focus,
          },
        },
        input: {
          paddingTop: 13,
          paddingBottom: 13,
          fontWeight: 500,
          letterSpacing: "-0.01em",
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          letterSpacing: "-0.01em",
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          backgroundColor: styleGuide.tokens.field.background,
        },
        select: {
          borderRadius: styleGuide.shape.inputRadius,
        },
        icon: {
          color: "#667085",
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          borderRadius: 16,
          border: `1px solid ${styleGuide.palette.divider}`,
          boxShadow: "0 18px 50px rgba(15, 23, 42, 0.14)",
          marginTop: 8,
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          minHeight: 42,
          borderRadius: 10,
          margin: "4px 8px",
          fontWeight: 600,
          letterSpacing: styleGuide.typography.bodyTracking,
          "&.Mui-selected": {
            backgroundColor: "rgba(25, 118, 210, 0.12)",
          },
          "&.Mui-selected:hover": {
            backgroundColor: "rgba(25, 118, 210, 0.18)",
          },
        },
      },
    },
    MuiFormControl: {
      styleOverrides: {
        root: {
          width: "100%",
        },
      },
    },
    MuiFormHelperText: {
      styleOverrides: {
        root: {
          marginLeft: 0,
          marginRight: 0,
          fontWeight: 500,
          letterSpacing: "-0.002em",
        },
      },
    },
    MuiCheckbox: {
      styleOverrides: {
        root: {
          padding: 8,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 700,
          letterSpacing: styleGuide.typography.bodyTracking,
        },
        body: {
          letterSpacing: "-0.005em",
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: styleGuide.shape.cardRadius,
          borderColor: styleGuide.palette.divider,
          boxShadow: styleGuide.shadows.card,
          backgroundImage: "linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,0.96) 100%)",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderColor: styleGuide.palette.divider,
        },
        rounded: {
          borderRadius: styleGuide.shape.cardRadius,
        },
        outlined: {
          boxShadow: styleGuide.shadows.card,
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        root: {
          backdropFilter: "blur(6px)",
        },
        paper: {
          borderRadius: styleGuide.shape.dialogRadius,
          border: `1px solid ${styleGuide.palette.divider}`,
          boxShadow: styleGuide.shadows.dialog,
          overflow: "hidden",
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          padding: "22px 24px 18px",
          background: "linear-gradient(180deg, rgba(248,250,252,0.96) 0%, rgba(255,255,255,0.9) 100%)",
          borderBottom: "1px solid #e6ebf0",
        },
      },
    },
    MuiDialogContent: {
      styleOverrides: {
        root: {
          padding: 24,
          backgroundColor: "#f4f6f8",
        },
      },
    },
    MuiDialogActions: {
      styleOverrides: {
        root: {
          padding: "16px 24px 22px",
          background: "#ffffff",
          borderTop: "1px solid #e6ebf0",
        },
      },
    },
    MuiTextField: {
      defaultProps: {
        variant: "outlined",
        size: "small",
      },
    },
  },
});

const theme = responsiveFontSizes(baseTheme);

export default function ThemeRegistry({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
}
