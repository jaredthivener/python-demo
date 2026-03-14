import { createTheme } from "@mui/material/styles";

declare module "@mui/material/styles" {
  interface Palette {
    cloud: {
      aws: string;
      gcp: string;
      azure: string;
    };
  }
  interface PaletteOptions {
    cloud?: {
      aws?: string;
      gcp?: string;
      azure?: string;
    };
  }
}

export function getMuiTheme(mode: "light" | "dark" = "light") {
  return createTheme({
  palette: {
    mode,
    primary: {
      main: mode === "dark" ? "#5E92F3" : "#1565C0",
      light: "#7EA9F5",
      dark: "#003C8F",
      contrastText: "#FFFFFF",
    },
    secondary: {
      main: "#0097A7",
      light: "#56C8D8",
      dark: "#006978",
      contrastText: "#FFFFFF",
    },
    cloud: {
      aws: "#FF9900",
      gcp: "#4285F4",
      azure: "#0078D4",
    },
    background: {
      default: mode === "dark" ? "#0d1117" : "#F8FAFF",
      paper: mode === "dark" ? "#161b22" : "#FFFFFF",
    },
    text: {
      primary: mode === "dark" ? "#f0f6fc" : "#0D1B2A",
      secondary: mode === "dark" ? "#8b949e" : "#546E7A",
    },
    divider: mode === "dark" ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)",
    success: { main: "#2E7D32" },
    warning: { main: "#E65100" },
    error: { main: "#C62828" },
  },

  typography: {
    fontFamily:
      '"Inter", "Roboto", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    h1: { fontWeight: 800, letterSpacing: "-0.03em", lineHeight: 1.1 },
    h2: { fontWeight: 700, letterSpacing: "-0.02em", lineHeight: 1.2 },
    h3: { fontWeight: 600, letterSpacing: "-0.01em", lineHeight: 1.3 },
    h4: { fontWeight: 600, letterSpacing: "-0.01em" },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
    body1: { lineHeight: 1.7 },
    body2: { lineHeight: 1.6 },
    button: { fontWeight: 600, letterSpacing: "0.01em" },
    overline: { fontWeight: 700, letterSpacing: "0.12em" },
  },

  shape: { borderRadius: 12 },

  shadows: [
    "none",
    "0px 1px 3px rgba(0,0,0,0.06), 0px 1px 2px rgba(0,0,0,0.04)",
    "0px 3px 6px rgba(0,0,0,0.06), 0px 2px 4px rgba(0,0,0,0.04)",
    "0px 6px 12px rgba(0,0,0,0.07), 0px 3px 6px rgba(0,0,0,0.05)",
    "0px 8px 24px rgba(0,0,0,0.08), 0px 4px 8px rgba(0,0,0,0.05)",
    "0px 12px 32px rgba(0,0,0,0.09), 0px 6px 12px rgba(0,0,0,0.06)",
    "0px 16px 40px rgba(0,0,0,0.10), 0px 8px 16px rgba(0,0,0,0.06)",
    "0px 20px 48px rgba(0,0,0,0.11), 0px 10px 20px rgba(0,0,0,0.07)",
    "0px 24px 56px rgba(0,0,0,0.12), 0px 12px 24px rgba(0,0,0,0.07)",
    ...Array(16).fill("0px 24px 56px rgba(0,0,0,0.12)"),
  ] as any,

  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 600,
          borderRadius: 8,
          padding: "10px 24px",
          fontSize: "0.9375rem",
        },
        sizeLarge: { padding: "14px 32px", fontSize: "1rem" },
        sizeSmall: { padding: "6px 16px", fontSize: "0.8125rem" },
        containedPrimary: {
          background: "linear-gradient(135deg, #1976D2 0%, #1565C0 100%)",
          boxShadow: "0 4px 14px rgba(21, 101, 192, 0.35)",
          "&:hover": {
            background: "linear-gradient(135deg, #1565C0 0%, #0D47A1 100%)",
            boxShadow: "0 6px 20px rgba(21, 101, 192, 0.45)",
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          border: "1px solid rgba(0,0,0,0.06)",
          boxShadow: "0px 4px 20px rgba(0,0,0,0.06)",
          transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
          "&:hover": {
            transform: "translateY(-4px)",
            boxShadow: "0px 12px 40px rgba(21, 101, 192, 0.12)",
            borderColor: "rgba(21, 101, 192, 0.2)",
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          fontWeight: 600,
          letterSpacing: "0.02em",
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: { borderRadius: 16 },
        elevation1: { boxShadow: "0px 4px 20px rgba(0,0,0,0.06)" },
        elevation2: { boxShadow: "0px 8px 32px rgba(0,0,0,0.08)" },
      },
    },
    MuiCssBaseline: {
      styleOverrides: `
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        * { box-sizing: border-box; }
      `,
    },
  },
  });
}
