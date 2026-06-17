"use client";

import { CssBaseline, ThemeProvider, createTheme, responsiveFontSizes } from "@mui/material";
import { deepPurple, teal } from "@mui/material/colors";
import type { ReactNode } from "react";

const baseTheme = createTheme({
  palette: {
    mode: "light",
    primary: teal,
    secondary: deepPurple,
    background: {
      default: "#f4f6f8",
      paper: "#ffffff",
    },
    text: {
      primary: "#172033",
      secondary: "#667085",
    },
    divider: "#d9e0e8",
  },
  shape: {
    borderRadius: 14,
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
          backgroundColor: "#f4f6f8",
        },
        body: {
          backgroundColor: "#f4f6f8",
          color: "#172033",
          fontFamily: [
            "Inter",
            "ui-sans-serif",
            "system-ui",
            "-apple-system",
            "BlinkMacSystemFont",
            "Segoe UI",
            "sans-serif",
          ].join(","),
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          boxShadow: "none",
          letterSpacing: "-0.01em",
        },
        contained: {
          boxShadow: "none",
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 999,
          fontWeight: 700,
          letterSpacing: "-0.01em",
        },
        outlined: {
          borderColor: "#cfd8e3",
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          fontWeight: 700,
          letterSpacing: "-0.01em",
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          fontWeight: 700,
          letterSpacing: "-0.01em",
        },
        body: {
          letterSpacing: "-0.005em",
        },
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
