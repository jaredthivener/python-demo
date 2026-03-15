import React from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Container from "@mui/material/Container";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";

const STEPS = [
  {
    cmd: "git clone https://github.com/jaredthivener/python-demo",
    comment: "# clone the repo",
  },
  { cmd: "cd python-demo", comment: "" },
  { cmd: "uv sync --group dev", comment: "# install dependencies" },
  {
    cmd: "uvicorn main:app --reload --no-access-log",
    comment: "# start the server",
  },
];

export default function QuickStartSection(): React.ReactElement {
  return (
    <Box
      component="section"
      sx={{
        py: { xs: 10, md: 14 },
        background: "linear-gradient(135deg, #0A0E1A 0%, #0D2B5E 100%)",
        color: "white",
      }}
    >
      <Container maxWidth="lg">
        <Grid container spacing={6} alignItems="center">
          {/* Left: copy */}
          <Grid size={{ xs: 12, md: 5 }}>
            <Typography
              variant="overline"
              sx={{
                color: "#4DD0E1",
                fontWeight: 700,
                letterSpacing: "0.12em",
                fontSize: "0.75rem",
              }}
            >
              Quick Start
            </Typography>
            <Typography
              variant="h2"
              sx={{
                fontWeight: 800,
                letterSpacing: "-0.03em",
                mt: 1,
                mb: 2.5,
                fontSize: { xs: "2rem", md: "2.5rem" },
              }}
            >
              Up and running in 60 seconds
            </Typography>
            <Typography
              variant="body1"
              sx={{ color: "rgba(255,255,255,0.7)", lineHeight: 1.7, mb: 4 }}
            >
              The live demo focuses on the Books API and observability basics.
              Hit{" "}
              <Box
                component="code"
                sx={{
                  bgcolor: "rgba(255,255,255,0.1)",
                  px: 0.75,
                  py: 0.25,
                  borderRadius: "4px",
                  fontFamily: "monospace",
                  fontSize: "0.875em",
                  color: "#4DD0E1",
                }}
              >
                /docs
              </Box>{" "}
              for the interactive Swagger UI. Auth and deployment patterns are
              explained in the docs alongside the running demo.
            </Typography>
            <Button
              variant="contained"
              size="large"
              href="/python-demo/docs/getting-started"
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
              Full Setup Guide
            </Button>
          </Grid>

          {/* Right: terminal */}
          <Grid size={{ xs: 12, md: 7 }}>
            <Box
              sx={{
                background: "rgba(13,17,23,0.9)",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "16px",
                overflow: "hidden",
                boxShadow: "0 24px 56px rgba(0,0,0,0.5)",
              }}
            >
              {/* Terminal chrome */}
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
                  {["#FF5F57", "#FFBD2E", "#28CA41"].map((c) => (
                    <Box
                      key={c}
                      sx={{
                        width: 12,
                        height: 12,
                        borderRadius: "50%",
                        bgcolor: c,
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
                  zsh
                </Typography>
              </Box>

              {/* Commands */}
              <Box sx={{ p: 3 }}>
                {STEPS.map(({ cmd, comment }, i) => (
                  <Box key={i} sx={{ mb: i < STEPS.length - 1 ? 1.5 : 0 }}>
                    <Box
                      sx={{ display: "flex", alignItems: "flex-start", gap: 1 }}
                    >
                      <Typography
                        sx={{
                          color: "#28CA41",
                          fontFamily: "monospace",
                          fontSize: "0.875rem",
                          flexShrink: 0,
                          lineHeight: 1.65,
                        }}
                      >
                        $
                      </Typography>
                      <Box sx={{ flex: 1 }}>
                        <Typography
                          component="span"
                          sx={{
                            fontFamily:
                              '"JetBrains Mono", "Fira Code", monospace',
                            fontSize: "0.875rem",
                            color: "#C9D1D9",
                            lineHeight: 1.65,
                          }}
                        >
                          {cmd}
                        </Typography>
                        {comment && (
                          <Typography
                            component="span"
                            sx={{
                              fontFamily: "monospace",
                              fontSize: "0.875rem",
                              color: "#6E7681",
                              ml: 1.5,
                              lineHeight: 1.65,
                            }}
                          >
                            {comment}
                          </Typography>
                        )}
                      </Box>
                    </Box>
                  </Box>
                ))}

                {/* Output */}
                <Box
                  sx={{
                    mt: 2.5,
                    pt: 2,
                    borderTop: "1px solid rgba(255,255,255,0.07)",
                  }}
                >
                  <Typography
                    sx={{
                      fontFamily: "monospace",
                      fontSize: "0.8rem",
                      color: "#6E7681",
                      lineHeight: 1.65,
                    }}
                  >
                    INFO: &nbsp;&nbsp; Started server process
                    <br />
                    INFO: &nbsp;&nbsp; Waiting for application startup.
                    <br />
                    INFO: &nbsp;&nbsp;{" "}
                    <Box component="span" sx={{ color: "#28CA41" }}>
                      Application startup complete.
                    </Box>
                    <br />
                    INFO: &nbsp;&nbsp; Uvicorn running on{" "}
                    <Box component="span" sx={{ color: "#4DD0E1" }}>
                      http://127.0.0.1:8000
                    </Box>
                  </Typography>
                </Box>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}
