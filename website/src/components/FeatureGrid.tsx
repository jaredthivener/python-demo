import React from "react";

interface Feature {
  icon: "key" | "cloud" | "building" | "shield" | "check" | "api";
  title: string;
  description: string;
  color: string;
}

function FeatureIcon({
  kind,
}: {
  kind: Feature["icon"];
}): React.ReactElement {
  switch (kind) {
    case "key":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" className="hp-icon-svg">
          <path
            d="M14.5 10a4.5 4.5 0 1 0-1.3 3.2L16 16h2v2h2v2h2v-2.7L17 12.4A4.48 4.48 0 0 0 14.5 10Z"
            fill="currentColor"
          />
        </svg>
      );
    case "cloud":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" className="hp-icon-svg">
          <path
            d="M7.5 19A4.5 4.5 0 0 1 7 10a6 6 0 0 1 11.5 1.6A3.8 3.8 0 1 1 18.8 19H7.5Z"
            fill="currentColor"
          />
        </svg>
      );
    case "building":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" className="hp-icon-svg">
          <path
            d="M4 20V4h7v16H4Zm2-2h1v-2H6v2Zm0-4h1v-2H6v2Zm0-4h1V8H6v2Zm3 8h1v-2H9v2Zm0-4h1v-2H9v2Zm0-4h1V8H9v2Zm4 10V9l7-2v13h-7Zm2-2h1v-2h-1v2Zm0-4h1v-2h-1v2Zm3 4h1v-2h-1v2Zm0-4h1v-2h-1v2Z"
            fill="currentColor"
          />
        </svg>
      );
    case "shield":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" className="hp-icon-svg">
          <path
            d="M12 3 5 6v6c0 4.9 2.9 7.9 7 9 4.1-1.1 7-4.1 7-9V6l-7-3Zm-1 12-3-3 1.4-1.4 1.6 1.6 3.6-3.6L16 10l-5 5Z"
            fill="currentColor"
          />
        </svg>
      );
    case "check":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" className="hp-icon-svg">
          <path
            d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2Zm-1.2 14.6L6.7 12.5l1.4-1.4 2.7 2.7 5-5 1.4 1.4-6.4 6.4Z"
            fill="currentColor"
          />
        </svg>
      );
    case "api":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" className="hp-icon-svg">
          <path
            d="M8.7 17.9 2.8 12l5.9-5.9L10.1 7.5 5.6 12l4.5 4.5-1.4 1.4Zm6.6 0-1.4-1.4 4.5-4.5-4.5-4.5 1.4-1.4 5.9 5.9-5.9 5.9ZM9.6 20l3.2-16h1.6l-3.2 16H9.6Z"
            fill="currentColor"
          />
        </svg>
      );
  }
}

const FEATURES: Feature[] = [
  {
    icon: "key",
    title: "JWT Bearer Auth",
    description:
      "Stateless, self-contained tokens with short expiry. Verify cryptographically — no DB round-trip per request. Powered by HS256 or RS256.",
    color: "#1565C0",
  },
  {
    icon: "cloud",
    title: "Cloud IAM / Workload Identity",
    description:
      "Zero secrets in code. IRSA on AWS, Workload Identity on GCP, Managed Identity on Azure. Your app gets short-lived tokens automatically from the platform.",
    color: "#0097A7",
  },
  {
    icon: "building",
    title: "Enterprise SSO",
    description:
      "Cognito (AWS), Google Identity (GCP), or Microsoft Entra ID — enterprise login with MFA, conditional access, and app roles. JWKS-validated RS256 tokens.",
    color: "#68217A",
  },
  {
    icon: "shield",
    title: "RBAC Scopes",
    description:
      "Fine-grained authorization with OAuth2 scopes. Use Security() — not just Depends() — to cleanly enforce access per endpoint.",
    color: "#E65100",
  },
  {
    icon: "check",
    title: "Pydantic v2 Models",
    description:
      "Separate request/response models so internal fields never leak. model_dump(exclude_unset=True) for clean partial updates.",
    color: "#2E7D32",
  },
  {
    icon: "api",
    title: "Auto OpenAPI 3.1",
    description:
      "Interactive Swagger UI and ReDoc generated from your type annotations — no YAML to maintain. Security schemes auto-wired.",
    color: "#C2185B",
  },
];

export default function FeatureGrid(): React.ReactElement {
  return (
    <section className="hp-section hp-surface">
      <div className="container">
        <div className="hp-section-header">
          <p className="hp-overline">What The Docs Cover</p>
          <h2 className="hp-title">Concepts first, implementation second</h2>
          <p className="hp-subtitle">
            Six core topics covered by the documentation. The live demo app
            implements the API-focused pieces and stays intentionally small.
          </p>
        </div>

        <div className="hp-grid hp-grid--three">
          {FEATURES.map((feature) => (
            <article
              key={feature.title}
              className="hp-card"
              style={{
                borderColor: "var(--ifm-color-emphasis-200)",
                ["--hp-accent" as string]: feature.color,
              }}
            >
              <div className="hp-card-inner"
              >
                <span
                  className="hp-icon-badge"
                  style={{
                    backgroundColor: `${feature.color}14`,
                    color: feature.color,
                  }}
                >
                  <FeatureIcon kind={feature.icon} />
                </span>
                <h3 className="hp-card-title">{feature.title}</h3>
                <p className="hp-card-copy">{feature.description}</p>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
