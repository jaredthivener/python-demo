import React from "react";

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
    tagline: "Lambda · EKS · Elastic Beanstalk",
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
        label: "EKS",
        description: "Kubernetes with IRSA for per-pod IAM",
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
    tagline: "Cloud Run · App Engine · GKE",
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
        label: "App Engine",
        description: "Managed PaaS with automatic scaling",
      },
      {
        label: "GKE",
        description: "Autopilot or standard Kubernetes with Workload Identity",
      },
    ],
    bestFor:
      "Container-first teams — Cloud Run is the simplest serverless container on any cloud",
    href: "/python-demo/docs/deployment/gcp",
  },
  {
    name: "Azure",
    tagline: "Functions · App Service · AKS",
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
        label: "App Service",
        description: "PaaS with deployment slots and Key Vault refs",
      },
      {
        label: "AKS",
        description: "Kubernetes with Workload Identity Federation",
      },
    ],
    bestFor:
      "Teams using Microsoft 365, Entra ID, or Azure DevOps — native identity federation",
    href: "/python-demo/docs/deployment/azure-functions",
  },
];

export default function HostingSection(): React.ReactElement {
  return (
    <section className="hp-section hp-surface">
      <div className="container">
        <div className="hp-section-header">
          <p className="hp-overline">Deploy Anywhere</p>
          <h2 className="hp-title">Pick your cloud provider</h2>
          <p className="hp-subtitle">
            All targets support platform-native IAM — no long-lived credentials
            stored anywhere in your deployment pipeline.
          </p>
        </div>

        <div className="hp-grid hp-grid--three">
          {OPTIONS.map((opt) => (
            <a
              key={opt.name}
                href={opt.href}
                className="hp-card hp-card--link hp-hosting-card"
                style={{ ["--hp-accent" as string]: opt.color }}
            >
              <div className="hp-hosting-band" style={{ backgroundColor: opt.color }}>
                <div className="hp-hosting-top">
                  <div className="hp-hosting-brand">
                    <img
                      src={opt.logo}
                      alt={`${opt.name} logo`}
                      className="hp-hosting-logo"
                    />
                    <h3 className="hp-hosting-name">{opt.name}</h3>
                  </div>
                  <span
                    className="hp-chip hp-chip--solid"
                    style={{ backgroundColor: opt.badgeColor }}
                  >
                    {opt.badge}
                  </span>
                </div>
                <p className="hp-hosting-tagline">{opt.tagline}</p>
              </div>

              <div className="hp-card-inner hp-hosting-inner">
                <div className="hp-services">
                  {opt.services.map((svc) => (
                    <div key={svc.label} className="hp-service-item">
                      <span className="hp-service-check" style={{ color: opt.color }}>
                        ✓
                      </span>
                      <div>
                        <p className="hp-service-label">{svc.label}</p>
                        <p className="hp-service-copy">{svc.description}</p>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="hp-hosting-footer">
                  <p className="hp-hosting-bestfor-label">BEST FOR</p>
                  <p className="hp-hosting-bestfor-copy">{opt.bestFor}</p>
                  <span className="hp-cta" style={{ color: opt.color }}>
                    Deployment guide →
                  </span>
                </div>
              </div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
