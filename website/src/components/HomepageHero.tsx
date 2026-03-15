import React from "react";

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
    <section className="hp-hero">
      <div className="hp-hero-grid-overlay" />
      <div className="container hp-hero-content">
        <div className="hp-grid hp-grid--hero">
          <div>
            <h1 className="hp-hero-title">
              Secure{" "}
              <span className="hp-lock-glyph" aria-hidden="true">
                🔒
              </span>
              FastAPI in the{" "}
              <span className="hp-hero-gradient-text">Cloud</span>
            </h1>

            <p className="hp-hero-subtitle">
              A compact FastAPI reference app with a working Books API, rich
              request logging, and balanced guidance for authentication and
              deployment on AWS, GCP, and Azure.
            </p>

            <div className="hp-hero-actions">
              <a
                className="button button--primary button--lg hp-btn-primary"
                href="/python-demo/docs/intro"
              >
                Get Started →
              </a>
              <a
                className="button button--outline button--lg hp-btn-outline"
                href="https://github.com/jaredthivener/python-demo"
                target="_blank"
                rel="noopener noreferrer"
              >
                GitHub
              </a>
            </div>

            <div className="hp-hero-stats">
              {[
                { value: "6", label: "Books Endpoints" },
                { value: "3", label: "Cloud Providers" },
                { value: "0", label: "Secrets in Code" },
              ].map(({ value, label }) => (
                <div key={label}>
                  <p className="hp-hero-stat-value">{value}</p>
                  <p className="hp-hero-stat-label">{label}</p>
                </div>
              ))}
            </div>

            <div className="hp-hero-chips">
              {[
                { label: "FastAPI", color: "#009688" },
                { label: "AWS", color: "#FF9900" },
                { label: "GCP", color: "#34A853" },
                { label: "Azure", color: "#0078D4" },
              ].map(({ label, color }) => (
                <span
                  key={label}
                  className="hp-chip"
                  style={{
                    backgroundColor: `${color}22`,
                    borderColor: `${color}55`,
                    color,
                    boxShadow: `0 0 8px ${color}99, 0 0 18px ${color}55`,
                  }}
                >
                  {label}
                </span>
              ))}
            </div>
          </div>

          <div>
            <div className="hp-terminal">
              <div className="hp-terminal-bar">
                <div className="hp-terminal-dots">
                  {["#FF5F57", "#FFBD2E", "#28CA41"].map((color) => (
                    <span
                      key={color}
                      className="hp-terminal-dot"
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
                <span className="hp-terminal-file">main.py</span>
              </div>

              <pre className="hp-code-pre">
                <code>{highlightPython(CODE_SNIPPET)}</code>
              </pre>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
