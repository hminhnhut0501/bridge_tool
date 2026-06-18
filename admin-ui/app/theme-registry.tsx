"use client";

import { CssBaseline, ThemeProvider, createTheme, responsiveFontSizes } from "@mui/material";
import { deepPurple } from "@mui/material/colors";
import type { ReactNode } from "react";

const baseTheme = createTheme({
  palette: {
    mode: "light",
    primary: {
      main: "#0d6b5d",
      dark: "#084f45",
      light: "#14b8a6",
      contrastText: "#ffffff",
    },
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
    borderRadius: 16,
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
          backgroundColor: "#0d6b5d",
          color: "#ffffff",
          "&:hover": {
            backgroundColor: "#084f45",
            boxShadow: "none",
          },
        },
        outlined: {
          borderColor: "#0d6b5d",
          backgroundColor: "#ffffff",
          color: "#0d6b5d",
          "&:hover": {
            borderColor: "#084f45",
            backgroundColor: "rgba(13, 107, 93, 0.04)",
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          minHeight: 46,
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
          alignItems: "center",
          border: "1px solid #d9e0e8",
          borderRadius: 999,
          color: "#172033",
          minHeight: 42,
          padding: "10px 14px",
          fontWeight: 700,
          letterSpacing: "-0.01em",
          textTransform: "none",
          transition: "background-color 160ms ease, border-color 160ms ease, color 160ms ease, box-shadow 160ms ease",
          "&:hover": {
            backgroundColor: "rgba(13, 107, 93, 0.06)",
            borderColor: "#a9e4d8",
          },
          "&.Mui-selected": {
            backgroundColor: "#0d6b5d",
            borderColor: "#0d6b5d",
            color: "#ffffff",
            boxShadow: "0 8px 20px rgba(13, 107, 93, 0.16)",
          },
          "&.Mui-selected:hover": {
            backgroundColor: "#084f45",
            borderColor: "#084f45",
          },
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 14,
          backgroundColor: "#ffffff",
          transition: "box-shadow 160ms ease, border-color 160ms ease, background-color 160ms ease",
          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: "#d9e0e8",
          },
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: "#aac6c0",
          },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: "#0d6b5d",
            borderWidth: 1.5,
          },
          "&.Mui-focused": {
            boxShadow: "0 0 0 4px rgba(13, 107, 93, 0.12)",
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
        select: {
          borderRadius: 14,
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
          border: "1px solid #d9e0e8",
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
          letterSpacing: "-0.01em",
          "&.Mui-selected": {
            backgroundColor: "rgba(13, 107, 93, 0.12)",
          },
          "&.Mui-selected:hover": {
            backgroundColor: "rgba(13, 107, 93, 0.18)",
          },
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
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          borderColor: "#d9e0e8",
          boxShadow: "0 1px 0 rgba(16, 24, 40, 0.03), 0 8px 20px rgba(16, 24, 40, 0.04)",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderColor: "#d9e0e8",
        },
        rounded: {
          borderRadius: 16,
        },
        outlined: {
          boxShadow: "0 1px 0 rgba(16, 24, 40, 0.03), 0 8px 20px rgba(16, 24, 40, 0.04)",
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        root: {
          backdropFilter: "blur(6px)",
        },
        paper: {
          borderRadius: 24,
          border: "1px solid #d9e0e8",
          boxShadow: "0 20px 60px rgba(15, 23, 42, 0.16)",
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
