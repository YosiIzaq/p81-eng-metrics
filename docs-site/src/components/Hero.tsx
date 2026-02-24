const repoUrl = "https://github.com/YosiIzaq/p81-eng-metrics";

export default function Hero() {
  return (
    <section
      style={{
        minHeight: "80vh",
        display: "flex",
        alignItems: "center",
        background:
          "radial-gradient(ellipse at 50% 0%, rgba(99,102,241,0.15) 0%, transparent 60%)",
      }}
    >
      <div className="container" style={{ textAlign: "center" }}>
        <div
          style={{
            display: "inline-block",
            padding: "6px 16px",
            borderRadius: 20,
            border: "1px solid var(--border)",
            fontSize: "0.8rem",
            color: "var(--text-secondary)",
            marginBottom: 24,
          }}
        >
          Open-source &middot; Zero vendor lock-in &middot; CLI-first
        </div>

        <h1
          style={{
            fontSize: "clamp(2.5rem, 5vw, 4rem)",
            fontWeight: 800,
            lineHeight: 1.1,
            marginBottom: 20,
          }}
        >
          Engineering metrics
          <br />
          <span style={{ color: "var(--accent-light)" }}>for your team</span>
        </h1>

        <p
          style={{
            fontSize: "1.2rem",
            color: "var(--text-secondary)",
            maxWidth: 540,
            margin: "0 auto 40px",
          }}
        >
          Track code reviews, measure productivity, and visualize trends —
          all from your terminal. No dashboards to maintain, no SaaS bills.
        </p>

        <div style={{ display: "flex", gap: 16, justifyContent: "center", flexWrap: "wrap" }}>
          <a
            href={repoUrl}
            target="_blank"
            rel="noreferrer"
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "12px 28px",
              borderRadius: 8,
              background: "var(--accent)",
              color: "white",
              fontWeight: 600,
              fontSize: "1rem",
              textDecoration: "none",
              transition: "opacity 0.15s",
            }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z" />
            </svg>
            View on GitHub
          </a>
          <a
            href="#demo"
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "12px 28px",
              borderRadius: 8,
              border: "1px solid var(--border)",
              color: "var(--text-primary)",
              fontWeight: 600,
              fontSize: "1rem",
              textDecoration: "none",
            }}
          >
            See Demo ↓
          </a>
        </div>
      </div>
    </section>
  );
}
