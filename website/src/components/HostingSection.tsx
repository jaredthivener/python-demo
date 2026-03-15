import React from "react";
import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Container from "@mui/material/Container";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import CheckIcon from "@mui/icons-material/Check";

interface HostingOption {
  name: string;
  tagline: string;
  color: string;
  logo: string;
  badge: string;
  badgeColor: string;
  services: { label: string; description: string }[];
  bestFor: string;
  href: string;
}

const OPTIONS: HostingOption[] = [
  {
    name: "AWS",
    tagline: "Lambda · ECS Fargate · Elastic Beanstalk",
    color: "#FF9900",
    logo: "/python-demo/img/aws-logo.svg",
    badge: "Most Adopted",
    badgeColor: "#E53935",
    services: [
      {
        label: "Lambda",
        description: "Serverless, pay-per-invocation with IRSA for secrets",
      },
      {
        label: "ECS Fargate",
        description: "Managed containers, no nodes to patch",
      },
      {
        label: "Elastic Beanstalk",
        description: "PaaS with one-command deploys",
      },
    ],
    bestFor:
      "Teams already on AWS — native IAM, ECR, RDS, and Secrets Manager integration",
    href: "/python-demo/docs/deployment/aws",
  },
  {
    name: "Google Cloud",
    tagline: "Cloud Run · GKE · App Engine",
    color: "#34A853",
    logo: "/python-demo/img/gcp-logo.svg",
    badge: "Best Serverless Containers",
    badgeColor: "#00ACC1",
    services: [
      {
        label: "Cloud Run",
        description: "Container-native serverless, scales to zero",
      },
      {
        label: "GKE",
        description: "Autopilot or standard Kubernetes with Workload Identity",
      },
      {
        label: "App Engine",
        description: "Managed PaaS with automatic scaling",
      },
    ],
    bestFor:
      "Container-first teams — Cloud Run is the simplest serverless container on any cloud",
    href: "/python-demo/docs/deployment/gcp",
  },
  {
    name: "Azure",
    tagline: "Functions · AKS · App Service",
    color: "#0078D4",
    logo: "/python-demo/img/azure-logo.svg",
    badge: "Deep Microsoft Integration",
    badgeColor: "#8B5CF6",
    services: [
      {
        label: "Azure Functions",
        description: "Serverless with Managed Identity built-in",
      },
      {
        label: "AKS",
        description: "Kubernetes with Workload Identity Federation",
      },
      {
        label: "App Service",
        description: "PaaS with deployment slots and Key Vault refs",
      },
    ],
    bestFor:
      "Teams using Microsoft 365, Entra ID, or Azure DevOps — native identity federation",
    href: "/python-demo/docs/deployment/azure-functions",
  },
];

export default function HostingSection(): React.ReactElement {
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
            Deploy Anywhere
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
            Pick your cloud provider
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
            All targets support platform-native IAM — no long-lived credentials
            stored anywhere in your deployment pipeline.
          </Typography>
        </Box>

        <Grid container spacing={3}>
          {OPTIONS.map((opt) => (
            <Grid key={opt.name} size={{ xs: 12, md: 4 }}>
              <Card
                component="a"
                href={opt.href}
                sx={{
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  textDecoration: "none",
                  border: "1px solid",
                  borderColor: "divider",
                  borderRadius: "16px",
                  overflow: "hidden",
                  transition: "transform 0.2s ease, box-shadow 0.2s ease",
                  "&:hover": {
                    transform: "translateY(-4px)",
                    boxShadow: `0 16px 48px ${opt.color}33`,
                    textDecoration: "none",
                  },
                }}
                elevation={0}
              >
                {/* Cloud-coloured header band */}
                <Box
                  sx={{
                    bgcolor: opt.color,
                    px: 3.5,
                    pt: 2.5,
                    pb: 2.5,
                    display: "flex",
                    flexDirection: "column",
                    gap: 1.5,
                  }}
                >
                  {/* Top row: logo + name on left, badge pinned to right */}
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "flex-start",
                      justifyContent: "space-between",
                      gap: 1,
                    }}
                  >
                    <Box
                      sx={{ display: "flex", alignItems: "center", gap: 1.5 }}
                    >
                      <Box
                        component="img"
                        src={opt.logo}
                        alt={`${opt.name} logo`}
                        sx={{
                          width: 36,
                          height: 36,
                          objectFit: "contain",
                          flexShrink: 0,
                        }}
                      />
                      <Typography
                        variant="h5"
                        sx={{
                          fontWeight: 800,
                          color: "white",
                          lineHeight: 1.1,
                          fontSize: "1.25rem",
                        }}
                      >
                        {opt.name}
                      </Typography>
                    </Box>
                    <Chip
                      label={opt.badge}
                      size="small"
                      sx={{
                        flexShrink: 0,
                        bgcolor: opt.badgeColor,
                        color: "white",
                        fontWeight: 700,
                        fontSize: "0.65rem",
                        letterSpacing: "0.02em",
                        border: "none",
                        boxShadow: `0 0 8px ${opt.badgeColor}cc, 0 0 18px ${opt.badgeColor}88, 0 0 32px ${opt.badgeColor}44`,
                        "& .MuiChip-label": { px: 1.25 },
                      }}
                    />
                  </Box>
                  {/* Tagline row */}
                  <Typography
                    variant="caption"
                    sx={{
                      color: "rgba(255,255,255,0.85)",
                      fontSize: "0.75rem",
                      lineHeight: 1.4,
                    }}
                  >
                    {opt.tagline}
                  </Typography>
                </Box>

                <CardContent
                  sx={{
                    p: 3.5,
                    flex: 1,
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 1.5,
                      flex: 1,
                    }}
                  >
                    {opt.services.map((svc) => (
                      <Box
                        key={svc.label}
                        sx={{
                          display: "flex",
                          alignItems: "flex-start",
                          gap: 1.25,
                        }}
                      >
                        <CheckIcon
                          sx={{
                            fontSize: "1rem",
                            color: opt.color,
                            mt: "3px",
                            flexShrink: 0,
                          }}
                        />
                        <Box>
                          <Typography
                            variant="body2"
                            sx={{ fontWeight: 600, lineHeight: 1.3 }}
                          >
                            {svc.label}
                          </Typography>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ lineHeight: 1.55, fontSize: "0.8rem" }}
                          >
                            {svc.description}
                          </Typography>
                        </Box>
                      </Box>
                    ))}
                  </Box>

                  <Box
                    sx={{
                      mt: 3,
                      pt: 2.5,
                      borderTop: "1px solid",
                      borderColor: "divider",
                    }}
                  >
                    <Typography
                      variant="caption"
                      sx={{
                        fontWeight: 600,
                        color: "text.secondary",
                        display: "block",
                        mb: 0.5,
                      }}
                    >
                      BEST FOR
                    </Typography>
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ lineHeight: 1.55 }}
                    >
                      {opt.bestFor}
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{
                        mt: 2,
                        display: "block",
                        color: opt.color,
                        fontWeight: 600,
                      }}
                    >
                      Deployment guide →
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>
    </Box>
  );
}
