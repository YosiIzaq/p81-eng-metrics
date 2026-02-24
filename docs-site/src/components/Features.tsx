const features = [
  {
    icon: "🔍",
    title: "Code Review Tracking",
    desc: "Fetch review counts per team member across multiple time periods using the GitHub CLI.",
  },
  {
    icon: "📊",
    title: "Productivity Scoring",
    desc: "Weighted formula (Items 50% + PRs 30% + Reviews 20%) that normalizes raw counts into comparable scores.",
  },
  {
    icon: "📈",
    title: "Multi-period Trends",
    desc: "Compare performance across sprints and quarters — spot ramp-ups, drops, and steady performers.",
  },
  {
    icon: "📤",
    title: "Export (PNG / Markdown)",
    desc: "Generate charts for Slack updates or Markdown tables for Confluence — no copy-paste gymnastics.",
  },
];

export default function Features() {
  return (
    <section>
      <div className="container">
        <h2>What It Does</h2>
        <p>Four capabilities, zero dependencies on paid tools.</p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
            gap: 20,
          }}
        >
          {features.map((f) => (
            <div
              key={f.title}
              className="card"
              style={{
                transition: "border-color 0.15s",
              }}
              onMouseEnter={(e) =>
                (e.currentTarget.style.borderColor = "var(--accent)")
              }
              onMouseLeave={(e) =>
                (e.currentTarget.style.borderColor = "var(--border)")
              }
            >
              <div style={{ fontSize: "2rem", marginBottom: 12 }}>{f.icon}</div>
              <h3 style={{ fontSize: "1.1rem", marginBottom: 8 }}>{f.title}</h3>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
