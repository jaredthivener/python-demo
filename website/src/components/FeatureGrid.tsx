import React from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Container from "@mui/material/Container";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import KeyIcon from "@mui/icons-material/Key";
import CloudIcon from "@mui/icons-material/Cloud";
import BusinessIcon from "@mui/icons-material/Business";
import SecurityIcon from "@mui/icons-material/Security";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ApiIcon from "@mui/icons-material/Api";

interface Feature {
  icon: React.ReactElement;
  title: string;
  description: string;
  color: string;
}

const FEATURES: Feature[] = [
  {
    icon: <KeyIcon fontSize="medium" />,
    title: "JWT Bearer Auth",
    description:
      "Stateless, self-contained tokens with short expiry. Verify cryptographically — no DB round-trip per request. Powered by HS256 or RS256.",
    color: "#1565C0",
  },
  {
    icon: <CloudIcon fontSize="medium" />,
    title: "Cloud IAM / Workload Identity",
    description:
      "Zero secrets in code. IRSA on AWS, Workload Identity on GCP, Managed Identity on Azure. Your app gets short-lived tokens automatically from the platform.",
    color: "#0097A7",
  },
  {
    icon: <BusinessIcon fontSize="medium" />,
    title: "Enterprise SSO",
    description:
      "Cognito (AWS), Google Identity (GCP), or Microsoft Entra ID — enterprise login with MFA, conditional access, and app roles. JWKS-validated RS256 tokens.",
    color: "#68217A",
  },
  {
    icon: <SecurityIcon fontSize="medium" />,
    title: "RBAC Scopes",
    description:
      "Fine-grained authorization with OAuth2 scopes. Use Security() — not just Depends() — to cleanly enforce access per endpoint.",
    color: "#E65100",
  },
  {
    icon: <CheckCircleIcon fontSize="medium" />,
    title: "Pydantic v2 Models",
    description:
      "Separate request/response models so internal fields never leak. model_dump(exclude_unset=True) for clean partial updates.",
    color: "#2E7D32",
  },
  {
    icon: <ApiIcon fontSize="medium" />,
    title: "Auto OpenAPI 3.1",
    description:
      "Interactive Swagger UI and ReDoc generated from your type annotations — no YAML to maintain. Security schemes auto-wired.",
    color: "#6A1B9A",
  },
];

export default function FeatureGrid(): React.ReactElement {
  return (
    <Box
      component="section"
      sx={{
        py: { xs: 10, md: 14 },
        bgcolor: "background.default",
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
            What's Inside
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
            Everything you need for production
          </Typography>
          <Typography
            variant="body1"
            sx={{
              mt: 2,
              color: "text.secondary",
              maxWidth: 560,
              mx: "auto",
              lineHeight: 1.7,
            }}
          >
            Six pillars of a secure, maintainable FastAPI service — each
            demonstrated with working, copy-paste-ready code.
          </Typography>
        </Box>

        <Grid container spacing={3}>
          {FEATURES.map((feature) => (
            <Grid key={feature.title} size={{ xs: 12, sm: 6, md: 4 }}>
              <Card
                sx={{
                  height: "100%",
                  border: "1px solid",
                  borderColor: "divider",
                  borderRadius: "16px",
                  transition: "transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease",
                  "&:hover": {
                    transform: "translateY(-4px)",
                    boxShadow: `0 12px 40px rgba(0,0,0,0.1)`,
                    borderColor: feature.color,
                  },
                }}
                elevation={0}
              >
                <CardContent sx={{ p: 3.5 }}>
                  <Box
                    sx={{
                      display: "inline-flex",
                      p: 1.5,
                      borderRadius: "12px",
                      bgcolor: `${feature.color}14`,
                      color: feature.color,
                      mb: 2.5,
                    }}
                  >
                    {feature.icon}
                  </Box>
                  <Typography
                    variant="h6"
                    sx={{ fontWeight: 700, mb: 1.25, fontSize: "1.05rem" }}
                  >
                    {feature.title}
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{ lineHeight: 1.65 }}
                  >
                    {feature.description}
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
