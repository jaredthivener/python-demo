import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

const config: Config = {
  title: "FastAPI Docs",
  tagline:
    "Production-ready authentication, authorization, and deployment patterns for AWS, GCP, and Azure",
  favicon: "img/favicon.svg",

  // GitHub Pages
  url: "https://jaredthivener.github.io",
  baseUrl: "/python-demo/",
  organizationName: "jaredthivener",
  projectName: "python-demo",
  trailingSlash: false,
  onBrokenLinks: "throw",
  markdown: {
    hooks: { onBrokenMarkdownLinks: "warn" },
  },

  i18n: { defaultLocale: "en", locales: ["en"] },

  presets: [
    [
      "classic",
      {
        docs: {
          sidebarPath: "./sidebars.ts",
          editUrl:
            "https://github.com/jaredthivener/python-demo/edit/main/website/",
        },
        blog: false,
        theme: { customCss: "./src/css/custom.css" },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: "img/social-card.png",
    colorMode: {
      defaultMode: "dark",
      disableSwitch: true,
      respectPrefersColorScheme: false,
    },
    navbar: {
      title: "",
      logo: { alt: "FastAPI in the Cloud Logo", src: "img/logo.svg" },
      items: [
        {
          type: "docSidebar",
          sidebarId: "docs",
          position: "left",
          label: "Docs",
        },
        {
          to: "/docs/auth/overview",
          label: "Auth",
          position: "left",
        },
        {
          to: "/docs/api/books",
          label: "API Reference",
          position: "left",
        },
        {
          to: "/docs/deployment",
          label: "Deploy",
          position: "left",
        },
        {
          href: "https://github.com/jaredthivener/python-demo",
          label: "GitHub",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "Getting Started",
          items: [
            { label: "Introduction", to: "/docs/intro" },
            { label: "Quick Start", to: "/docs/getting-started" },
            { label: "Books API Demo", to: "/docs/api/books" },
          ],
        },
        {
          title: "Auth & Security",
          items: [
            { label: "The Big Picture", to: "/docs/auth/overview" },
            { label: "JWT Bearer", to: "/docs/auth/jwt-bearer" },
            {
              label: "Cloud IAM / Workload Identity",
              to: "/docs/auth/managed-identity",
            },
            { label: "Enterprise SSO", to: "/docs/auth/entra-id" },
          ],
        },
        {
          title: "Deployment",
          items: [
            { label: "Overview", to: "/docs/deployment" },
            { label: "AWS (Lambda / ECS)", to: "/docs/deployment/aws-lambda" },
            { label: "GCP (Cloud Run / GKE)", to: "/docs/deployment/gcp-cloud-run" },
            { label: "Azure (Functions / AKS)", to: "/docs/deployment/azure-functions" },
          ],
        },
        {
          title: "Resources",
          items: [
            {
              label: "FastAPI Docs",
              href: "https://fastapi.tiangolo.com",
            },
            {
              label: "AWS IAM Roles for Service Accounts",
              href: "https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html",
            },
            {
              label: "GCP Workload Identity",
              href: "https://cloud.google.com/kubernetes-engine/docs/concepts/workload-identity",
            },
            {
              label: "Azure Managed Identity",
              href: "https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview",
            },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} FastAPI in the Cloud. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ["python", "bash", "json", "yaml", "typescript"],
    },
    algolia: undefined,
  } satisfies Preset.ThemeConfig,
};

export default config;
