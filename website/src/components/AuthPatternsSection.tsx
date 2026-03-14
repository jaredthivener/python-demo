import React from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Container from "@mui/material/Container";
import Divider from "@mui/material/Divider";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import KeyIcon from "@mui/icons-material/Key";
import CloudQueueIcon from "@mui/icons-material/CloudQueue";
import CorporateFareIcon from "@mui/icons-material/CorporateFare";
import ArrowRightAltIcon from "@mui/icons-material/ArrowRightAlt";

interface Pattern {
  number: string;
  icon: React.ReactElement;
  label: string;
  title: string;
  color: string;
  when: string;
  flow: string[];
  href: string;
}

const PATTERNS: Pattern[] = [
  {
    number: "01",
    icon: <KeyIcon />,
    label: "User-facing Auth",
    title: "JWT Bearer",
    color: "#1565C0",
    when: "Generic internet users — mobile apps, SPAs, public APIs.",
    flow: ["User sends credentials", "Server issues signed JWT", "Client attaches Bearer token", "Server verifies cryptographically — no DB hit"],
    href: "/python-demo/docs/auth/jwt-bearer",
  },
  {
    number: "02",
    icon: <CloudQueueIcon />,
    label: "Outbound Service Auth",
    title: "Cloud IAM / Workload Identity",
    color: "#0097A7",
    when: "Your app talking to managed cloud services (databases, queues, secrets) — zero secrets in code on any cloud.",
    flow: ["App requests token from platform metadata service", "Cloud IAM issues short-lived credential", "App presents token to cloud service", "Service validates — no password ever stored"],
    href: "/python-demo/docs/auth/managed-identity",
  },
  {
    number: "03",
    icon: <CorporateFareIcon />,
    label: "Enterprise SSO",
    title: "Enterprise IdP",
    color: "#68217A",
    when: "Corporate users who authenticate via Cognito (AWS), Google Identity (GCP), or Entra ID (Azure) — with MFA and role-based access.",
    flow: ["User logs in via enterprise IdP (MFA, conditional access)", "IdP issues RS256 JWT with app roles / groups", "FastAPI fetches JWKS, validates token", "Roles claim drives authorization"],
    href: "/python-demo/docs/auth/entra-id",
  },
];

export default function AuthPatternsSection(): React.ReactElement {
  return (
    <Box
      component="section"
      sx={{
        py: { xs: 10, md: 14 },
        bgcolor: "background.default",
        borderTop: "1px solid",
        borderBottom: "1px solid",
        borderColor: "divider",
      }}
    >
      <Container maxWidth="lg">
        <Box sx={{ textAlign: "center", mb: 8 }}>
          <Typography
            variant="overline"
            sx={{
              color: "primary.main",
              fontWeight: 700,
              letterSpacing: "0.12em",
              fontSize: "0.75rem",
            }}
          >
            The Big Picture
          </Typography>
          <Typography
            variant="h2"
            sx={{
              fontWeight: 800,
              letterSpacing: "-0.03em",
              mt: 1,
              fontSize: { xs: "2rem", md: "2.75rem" },
            }}
          >
            Three auth patterns, one decision
          </Typography>
          <Typography
            variant="body1"
            sx={{
              mt: 2,
              color: "text.secondary",
              maxWidth: 600,
              mx: "auto",
              lineHeight: 1.7,
            }}
          >
            These patterns are not mutually exclusive — a production app typically
            uses all three simultaneously. Choose based on <em>who or what</em> is
            being authenticated.
          </Typography>
        </Box>

        <Grid container spacing={3}>
          {PATTERNS.map((p) => (
            <Grid key={p.number} size={{ xs: 12, md: 4 }}>
              <Card
                component="a"
                href={p.href}
                sx={{
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  textDecoration: "none",
                  bgcolor: "background.paper",
                  border: "1px solid",
                  borderColor: "divider",
                  borderTop: `3px solid ${p.color}`,
                  borderRadius: "16px",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.35)",
                  transition: "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",
                  "&:hover": {
                    transform: "translateY(-4px)",
                    boxShadow: `0 20px 56px ${p.color}33`,
                    borderColor: p.color,
                    textDecoration: "none",
                  },
                }}
                elevation={0}
              >
                <CardContent sx={{ p: 3.5, flex: 1, display: "flex", flexDirection: "column" }}>
                  {/* Header */}
                  <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", mb: 2.5 }}>
                    <Box
                      sx={{
                        display: "inline-flex",
                        p: 1.5,
                        borderRadius: "12px",
                        bgcolor: `${p.color}28`,
                        color: p.color,
                      }}
                    >
                      {p.icon}
                    </Box>
                    <Typography
                      sx={{
                        fontSize: "2rem",
                        fontWeight: 800,
                        color: `${p.color}55`,
                        lineHeight: 1,
                        fontVariantNumeric: "tabular-nums",
                      }}
                    >
                      {p.number}
                    </Typography>
                  </Box>

                  <Chip
                    label={p.label}
                    size="small"
                    sx={{
                      mb: 1.5,
                      alignSelf: "flex-start",
                      bgcolor: `${p.color}28`,
                      color: p.color,
                      fontWeight: 700,
                      fontSize: "0.7rem",
                      letterSpacing: "0.05em",
                    }}
                  />

                  <Typography variant="h5" sx={{ fontWeight: 800, mb: 1, color: p.color }}>
                    {p.title}
                  </Typography>

                  <Typography variant="body2" sx={{ lineHeight: 1.65, mb: 3, color: "text.primary", opacity: 0.85 }}>
                    <strong>Use when:</strong> {p.when}
                  </Typography>

                  <Divider sx={{ mb: 2.5 }} />

                  {/* Flow */}
                  <Box sx={{ display: "flex", flexDirection: "column", gap: 1, flex: 1 }}>
                    {p.flow.map((step, i) => (
                      <Box key={i} sx={{ display: "flex", alignItems: "flex-start", gap: 1 }}>
                        <ArrowRightAltIcon sx={{ fontSize: "1rem", color: p.color, mt: "2px", flexShrink: 0 }} />
                        <Typography variant="caption" sx={{ lineHeight: 1.5, color: "text.primary", opacity: 0.8 }}>
                          {step}
                        </Typography>
                      </Box>
                    ))}
                  </Box>

                  {/* CTA */}
                  <Typography
                    variant="caption"
                    sx={{
                      mt: 3,
                      display: "block",
                      color: p.color,
                      fontWeight: 600,
                      letterSpacing: "0.04em",
                    }}
                  >
                    Read the guide →
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}
