const steps = [
  {
    step: 1,
    label: "Configure",
    code: `cp team_config.example.json team_config.json
# Edit with your team's GitHub usernames`,
  },
  {
    step: 2,
    label: "Fetch",
    code: `bash fetch_code_reviews.sh          # real data
bash fetch_code_reviews.sh --test   # mock data`,
  },
  {
    step: 3,
    label: "Visualize",
    code: `python visualize_reviews.py --chart comparison --export png`,
  },
];

export default function QuickStart() {
  return (
    <section>
      <div className="container">
        <h2>Quick Start</h2>
        <p>Three commands, real charts in under a minute.</p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
            gap: 20,
          }}
        >
          {steps.map((s) => (
            <div key={s.step} className="card">
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  marginBottom: 16,
                }}
              >
                <span
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: "50%",
                    background: "var(--accent)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontWeight: 700,
                    fontSize: "0.85rem",
                    flexShrink: 0,
                  }}
                >
                  {s.step}
                </span>
                <span style={{ fontWeight: 600, fontSize: "1.05rem" }}>
                  {s.label}
                </span>
              </div>
              <pre
                style={{
                  background: "var(--bg-primary)",
                  padding: 16,
                  borderRadius: "var(--radius-sm)",
                  fontSize: "0.8rem",
                  lineHeight: 1.7,
                  overflowX: "auto",
                  color: "var(--text-secondary)",
                }}
              >
                {s.code}
              </pre>
            </div>
          ))}
        </div>

        <div
          style={{
            marginTop: 48,
            textAlign: "center",
            color: "var(--text-muted)",
            fontSize: "0.85rem",
          }}
        >
          Built with Bash + Python + React &middot; No SaaS required
        </div>
      </div>
    </section>
  );
}
