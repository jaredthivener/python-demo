import React from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import Container from "@mui/material/Container";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import GitHubIcon from "@mui/icons-material/GitHub";
import LockIcon from "@mui/icons-material/Lock";

const CODE_SNIPPET = `from fastapi import FastAPI, Query
from pydantic import BaseModel

class BookListResponse(BaseModel):
  items: list[BookResponse]
  total: int
  skip: int
  limit: int

@app.get("/api/v1/books", response_model=BookListResponse)
async def list_books(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
  return paginate_books(list(store.values()), skip=skip, limit=limit)`;

/**
 * Tokenize a Python snippet into React nodes without regex chaining issues.
 * Each token type is detected once in priority order using a single combined regex.
 */
function highlightPython(code: string): React.ReactNode[] {
  const TOKEN_RE = new RegExp(
    [
      /(#[^\n]*)/.source, // comment
      /(@\w+)/.source, // decorator
      /"[^"]*"/.source, // string
      /\b(from|import|async|def|return|class|int|list)\b/.source, // keyword
      /\b(BaseModel|BookListResponse|BookResponse|Query|paginate_books|list_books)\b/
        .source, // function
    ].join("|"),
    "g",
  );

  const nodes: React.ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = TOKEN_RE.exec(code)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(code.slice(lastIndex, match.index));
    }
    const text = match[0];
    let cls: string;
    if (text.startsWith("#")) cls = "cm";
    else if (text.startsWith("@")) cls = "dec";
    else if (text.startsWith('"')) cls = "str";
    else if (/^(from|import|async|def|return|class|int|list)$/.test(text))
      cls = "kw";
    else cls = "fn";
    nodes.push(
      <span key={match.index} className={cls}>
        {text}
      </span>,
    );
    lastIndex = TOKEN_RE.lastIndex;
  }

  if (lastIndex < code.length) {
    nodes.push(code.slice(lastIndex));
  }
  return nodes;
}

export default function HomepageHero(): React.ReactElement {
  return (
    <Box
      component="section"
      sx={{
        background:
          "linear-gradient(135deg, #0A0E1A 0%, #0D2B5E 60%, #0D47A1 100%)",
        color: "white",
        pt: { xs: 10, md: 14 },
        pb: { xs: 10, md: 14 },
        position: "relative",
        overflow: "hidden",
        "&::before": {
          content: '""',
          position: "absolute",
          inset: 0,
          backgroundImage:
            "radial-gradient(ellipse 80% 60% at 50% -20%, rgba(21,101,192,0.35) 0%, transparent 70%)",
          pointerEvents: "none",
        },
      }}
    >
      {/* Subtle grid pattern overlay */}
      <Box
        sx={{
          position: "absolute",
          inset: 0,
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)",
          backgroundSize: "48px 48px",
          pointerEvents: "none",
        }}
      />

      <Container maxWidth="lg" sx={{ position: "relative", zIndex: 1 }}>
        <Grid container spacing={6} alignItems="center">
          {/* ── Left column ── */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: "2.5rem", sm: "3rem", md: "3.5rem" },
                fontWeight: 800,
                lineHeight: 1.1,
                letterSpacing: "-0.03em",
                mb: 2.5,
              }}
            >
              Secure{" "}
              <Box
                component="span"
                sx={{
                  display: "inline-flex",
                  verticalAlign: "middle",
                  mb: { xs: "6px", md: "10px" },
                  mr: 0.5,
                }}
              >
                <LockIcon
                  sx={{
                    fontSize: { xs: "2.2rem", md: "3rem" },
                    color: "#4DD0E1",
                    filter: "drop-shadow(0 0 8px #4DD0E188)",
                  }}
                />
              </Box>
              FastAPI in the{" "}
              <Box
                component="span"
                sx={{
                  background:
                    "linear-gradient(90deg, #FF9900 0%, #4DD0E1 50%, #5E92F3 100%)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                }}
              >
                Cloud
              </Box>
            </Typography>

            <Typography
              variant="h6"
              sx={{
                color: "rgba(255,255,255,0.72)",
                fontWeight: 400,
                lineHeight: 1.65,
                mb: 4,
                maxWidth: 480,
              }}
            >
              A compact FastAPI reference app with a working Books API, rich
              request logging, and balanced guidance for authentication and
              deployment on AWS, GCP, and Azure.
            </Typography>

            <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
              <Button
                variant="contained"
                size="large"
                href="/python-demo/docs/intro"
                endIcon={<ArrowForwardIcon />}
                sx={{
                  bgcolor: "#1976D2",
                  "&:hover": { bgcolor: "#1565C0" },
                  px: 3,
                  py: 1.5,
                  fontWeight: 700,
                  borderRadius: "10px",
                  boxShadow: "0 4px 20px rgba(21,101,192,0.5)",
                }}
              >
                Get Started
              </Button>
              <Button
                variant="outlined"
                size="large"
                href="https://github.com/jaredthivener/python-demo"
                target="_blank"
                rel="noopener noreferrer"
                startIcon={<GitHubIcon />}
                sx={{
                  color: "white",
                  borderColor: "rgba(255,255,255,0.3)",
                  "&:hover": {
                    borderColor: "white",
                    bgcolor: "rgba(255,255,255,0.06)",
                  },
                  px: 3,
                  py: 1.5,
                  fontWeight: 600,
                  borderRadius: "10px",
                }}
              >
                GitHub
              </Button>
            </Box>

            {/* Stats row */}
            <Box sx={{ display: "flex", gap: 4, mt: 5 }}>
              {[
                { value: "6", label: "Books Endpoints" },
                { value: "3", label: "Cloud Providers" },
                { value: "0", label: "Secrets in Code" },
              ].map(({ value, label }) => (
                <Box key={label}>
                  <Typography
                    sx={{
                      fontSize: "1.75rem",
                      fontWeight: 800,
                      color: "#4DD0E1",
                      lineHeight: 1,
                    }}
                  >
                    {value}
                  </Typography>
                  <Typography
                    sx={{
                      fontSize: "0.78rem",
                      color: "rgba(255,255,255,0.55)",
                      fontWeight: 500,
                      mt: 0.3,
                    }}
                  >
                    {label}
                  </Typography>
                </Box>
              ))}
            </Box>

            {/* Brand chips */}
            <Box sx={{ display: "flex", gap: 1.25, flexWrap: "wrap", mt: 3.5 }}>
              {[
                { label: "FastAPI", color: "#009688" },
                { label: "AWS", color: "#FF9900" },
                { label: "GCP", color: "#34A853" },
                { label: "Azure", color: "#0078D4" },
              ].map(({ label, color }) => (
                <Box
                  key={label}
                  sx={{
                    px: 1.75,
                    py: 0.6,
                    borderRadius: "999px",
                    bgcolor: `${color}22`,
                    border: `1px solid ${color}55`,
                    color: color,
                    fontWeight: 700,
                    fontSize: "0.75rem",
                    letterSpacing: "0.05em",
                    boxShadow: `0 0 8px ${color}99, 0 0 18px ${color}55`,
                    transition: "box-shadow 0.2s ease",
                    "&:hover": {
                      boxShadow: `0 0 12px ${color}cc, 0 0 28px ${color}88`,
                    },
                  }}
                >
                  {label}
                </Box>
              ))}
            </Box>
          </Grid>

          {/* ── Right column — Code card ── */}
          <Grid size={{ xs: 12, md: 6 }}>
            <Box
              sx={{
                background: "rgba(13,17,23,0.85)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "16px",
                overflow: "hidden",
                boxShadow:
                  "0 32px 64px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.05)",
                backdropFilter: "blur(12px)",
              }}
            >
              {/* Window chrome */}
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  px: 2.5,
                  py: 1.5,
                  borderBottom: "1px solid rgba(255,255,255,0.07)",
                  background: "rgba(255,255,255,0.03)",
                }}
              >
                <Box sx={{ display: "flex", gap: 0.75 }}>
                  {["#FF5F57", "#FFBD2E", "#28CA41"].map((color) => (
                    <Box
                      key={color}
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: "50%",
                        bgcolor: color,
                      }}
                    />
                  ))}
                </Box>
                <Typography
                  sx={{
                    ml: 2,
                    fontSize: "0.75rem",
                    color: "rgba(255,255,255,0.35)",
                    fontFamily: "monospace",
                  }}
                >
                  main.py
                </Typography>
              </Box>

              {/* Code */}
              <Box
                component="pre"
                sx={{
                  m: 0,
                  p: 3,
                  fontSize: "0.78rem",
                  lineHeight: 1.65,
                  fontFamily: '"JetBrains Mono", "Fira Code", monospace',
                  color: "#C9D1D9",
                  overflowX: "auto",
                  "& .kw": { color: "#FF7B72" },
                  "& .fn": { color: "#D2A8FF" },
                  "& .str": { color: "#A5D6FF" },
                  "& .cm": { color: "#8B949E", fontStyle: "italic" },
                  "& .dec": { color: "#79C0FF" },
                }}
              >
                <code>{highlightPython(CODE_SNIPPET)}</code>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}
