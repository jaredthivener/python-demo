import React from "react";

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
    <section className="hp-section hp-quickstart">
      <div className="container">
        <div className="hp-grid hp-grid--quickstart">
          <div>
            <p className="hp-overline hp-overline--cyan">Quick Start</p>
            <h2 className="hp-title hp-title--on-dark">
              Up and running in 60 seconds
            </h2>
            <p className="hp-quickstart-copy">
              The live demo focuses on the Books API and observability basics.
              Hit <code className="hp-inline-code">/docs</code> for the
              interactive Swagger UI. Auth and deployment patterns are explained
              in the docs alongside the running demo.
            </p>
            <a
              className="button button--primary button--lg hp-btn-primary"
              href="/python-demo/docs/getting-started"
            >
              Full Setup Guide →
            </a>
          </div>

          <div>
            <div className="hp-terminal">
              <div className="hp-terminal-bar">
                <div className="hp-terminal-dots">
                  {["#FF5F57", "#FFBD2E", "#28CA41"].map((c) => (
                    <span
                      key={c}
                      className="hp-terminal-dot"
                      style={{ backgroundColor: c }}
                    />
                  ))}
                </div>
                <span className="hp-terminal-file">zsh</span>
              </div>

              <div className="hp-terminal-body">
                {STEPS.map(({ cmd, comment }, i) => (
                  <div
                    key={cmd}
                    className={`hp-terminal-line ${i < STEPS.length - 1 ? "hp-terminal-line--spaced" : ""}`}
                  >
                    <span className="hp-terminal-prompt">$</span>
                    <div>
                      <span className="hp-terminal-cmd">{cmd}</span>
                      {comment && (
                        <span className="hp-terminal-comment">{comment}</span>
                      )}
                    </div>
                  </div>
                ))}

                <div className="hp-terminal-output">
                  <p className="hp-terminal-output-text">
                    INFO: &nbsp;&nbsp; Started server process
                    <br />
                    INFO: &nbsp;&nbsp; Waiting for application startup.
                    <br />
                    INFO: &nbsp;&nbsp;{" "}
                    <span className="hp-terminal-ok">
                      Application startup complete.
                    </span>
                    <br />
                    INFO: &nbsp;&nbsp; Uvicorn running on{" "}
                    <span className="hp-terminal-link">
                      http://127.0.0.1:8000
                    </span>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
