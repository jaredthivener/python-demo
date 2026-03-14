import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  docs: [
    {
      type: "doc",
      id: "intro",
      label: "Introduction",
    },
    {
      type: "doc",
      id: "getting-started",
      label: "Getting Started",
    },
    {
      type: "category",
      label: "Authentication & Authorization",
      collapsed: false,
      items: [
        "auth/overview",
        "auth/jwt-bearer",
        "auth/managed-identity",
        "auth/entra-id",
      ],
    },
    {
      type: "category",
      label: "API Reference",
      collapsed: false,
      items: ["api/books"],
    },
    {
      type: "category",
      label: "Deployment",
      collapsed: false,
      items: [
        "deployment/index",
        {
          type: "category",
          label: "Amazon Web Services",
          collapsed: false,
          items: [
            "deployment/aws-lambda",
            "deployment/aws-ecs-fargate",
            "deployment/aws-eks",
          ],
        },
        {
          type: "category",
          label: "Google Cloud",
          collapsed: false,
          items: [
            "deployment/gcp-cloud-run",
            "deployment/gcp-gke",
            "deployment/gcp-app-engine",
          ],
        },
        {
          type: "category",
          label: "Microsoft Azure",
          collapsed: false,
          items: [
            "deployment/azure-functions",
            "deployment/aks",
            "deployment/app-service",
          ],
        },
      ],
    },
  ],
};

export default sidebars;
