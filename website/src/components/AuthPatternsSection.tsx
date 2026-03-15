import React from "react";

interface Pattern {
  number: string;
  icon: "key" | "cloud" | "enterprise";
  label: string;
  title: string;
  color: string;
  when: string;
  flow: string[];
  href: string;
}

function PatternIcon({ kind }: { kind: Pattern["icon"] }): React.ReactElement {
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
    case "enterprise":
      return (
        <svg viewBox="0 0 24 24" aria-hidden="true" className="hp-icon-svg">
          <path
            d="M4 20V4h7v16H4Zm2-2h1v-2H6v2Zm0-4h1v-2H6v2Zm0-4h1V8H6v2Zm3 8h1v-2H9v2Zm0-4h1v-2H9v2Zm0-4h1V8H9v2Zm4 10V9l7-2v13h-7Zm2-2h1v-2h-1v2Zm0-4h1v-2h-1v2Zm3 4h1v-2h-1v2Zm0-4h1v-2h-1v2Z"
            fill="currentColor"
          />
        </svg>
      );
  }
}

const PATTERNS: Pattern[] = [
  {
    number: "01",
    icon: "key",
    label: "User-facing Auth",
    title: "JWT Bearer",
    color: "#1565C0",
    when: "Generic internet users — mobile apps, SPAs, public APIs.",
    flow: [
      "User sends credentials",
      "Server issues signed JWT",
      "Client attaches Bearer token",
      "Server verifies cryptographically — no DB hit",
    ],
    href: "/python-demo/docs/auth/jwt-bearer",
  },
  {
    number: "02",
    icon: "cloud",
    label: "Outbound Service Auth",
    title: "Cloud IAM / Workload Identity",
    color: "#0097A7",
    when: "Your app talking to managed cloud services (databases, queues, secrets) — zero secrets in code on any cloud.",
    flow: [
      "App requests token from platform metadata service",
      "Cloud IAM issues short-lived credential",
      "App presents token to cloud service",
      "Service validates — no password ever stored",
    ],
    href: "/python-demo/docs/auth/managed-identity",
  },
  {
    number: "03",
    icon: "enterprise",
    label: "Enterprise SSO",
    title: "Enterprise IdP",
    color: "#68217A",
    when: "Corporate users who authenticate via Cognito (AWS), Google Identity (GCP), or Entra ID (Azure) — with MFA and role-based access.",
    flow: [
      "User logs in via enterprise IdP (MFA, conditional access)",
      "IdP issues RS256 JWT with app roles / groups",
      "FastAPI fetches JWKS, validates token",
      "Roles claim drives authorization",
    ],
    href: "/python-demo/docs/auth/entra-id",
  },
];

export default function AuthPatternsSection(): React.ReactElement {
  return (
    <section className="hp-section hp-surface hp-framed">
      <div className="container">
        <div className="hp-section-header">
          <p className="hp-overline">The Big Picture</p>
          <h2 className="hp-title">Three auth patterns, one decision</h2>
          <p className="hp-subtitle hp-subtitle--wide">
            These patterns are not mutually exclusive — a production app
            typically uses all three simultaneously. Choose based on{" "}
            <em>who or what</em> is being authenticated.
          </p>
        </div>

        <div className="hp-grid hp-grid--three">
          {PATTERNS.map((p) => (
            <a
              key={p.number}
              href={p.href}
              className="hp-card hp-card--link hp-auth-card"
              style={{
                borderTop: `3px solid ${p.color}`,
                ["--hp-accent" as string]: p.color,
              }}
            >
              <div className="hp-card-inner hp-auth-inner">
                <div className="hp-auth-header">
                  <span
                    className="hp-icon-badge"
                    style={{ backgroundColor: `${p.color}28`, color: p.color }}
                  >
                    <PatternIcon kind={p.icon} />
                  </span>
                  <span
                    className="hp-auth-num"
                    style={{ color: `${p.color}55` }}
                  >
                    {p.number}
                  </span>
                </div>

                <span
                  className="hp-chip"
                  style={{ backgroundColor: `${p.color}28`, color: p.color }}
                >
                  {p.label}
                </span>

                <h3 className="hp-auth-title" style={{ color: p.color }}>
                  {p.title}
                </h3>

                <p className="hp-auth-when">
                  <strong>Use when:</strong> {p.when}
                </p>

                <hr className="hp-divider" />

                <div className="hp-flow-list">
                  {p.flow.map((step) => (
                    <div key={step} className="hp-flow-item">
                      <span
                        className="hp-flow-arrow"
                        style={{ color: p.color }}
                      >
                        →
                      </span>
                      <span className="hp-flow-text">{step}</span>
                    </div>
                  ))}
                </div>

                <span className="hp-cta" style={{ color: p.color }}>
                  Read the guide →
                </span>
              </div>
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
