import React, { useMemo, useState, useEffect } from "react";
import { ThemeProvider } from "@mui/material/styles";
import { getMuiTheme } from "./muiTheme";

// Root wraps the entire app with MUI ThemeProvider.
// useColorMode() cannot be used here (Root sits outside ColorModeProvider),
// so we observe Docusaurus's data-theme attribute on <html> directly.
export default function Root({
  children,
}: {
  children: React.ReactNode;
}): React.ReactElement {
  const [colorMode, setColorMode] = useState<"light" | "dark">("light");

  useEffect(() => {
    const getMode = (): "light" | "dark" =>
      document.documentElement.getAttribute("data-theme") === "dark"
        ? "dark"
        : "light";

    setColorMode(getMode());

    const observer = new MutationObserver(() => setColorMode(getMode()));
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => observer.disconnect();
  }, []);

  const theme = useMemo(() => getMuiTheme(colorMode), [colorMode]);
  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}
