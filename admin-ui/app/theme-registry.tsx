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
    h1: { fontWeight: 800 },
    h2: { fontWeight: 800 },
    h3: { fontWeight: 800 },
    h4: { fontWeight: 800 },
    h5: { fontWeight: 700 },
    h6: { fontWeight: 700 },
    body1: { fontWeight: 500, lineHeight: 1.55 },
    body2: { fontWeight: 500, lineHeight: 1.45 },
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
