import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
} from "recharts";
import {
  scores,
  sprintTrends,
  memberColors,
  type ProductivityScore,
} from "../data/productivity";

type View = "stacked" | "ranking" | "trend";

const tooltipStyle = {
  contentStyle: {
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 8,
    fontSize: "0.8rem",
  },
  labelStyle: { color: "#f1f5f9" },
};

export default function ProductivityDemo() {
  const [view, setView] = useState<View>("stacked");

  return (
    <section>
      <div className="container">
        <h2>Productivity Scores</h2>
        <p>
          Weighted formula: Items&nbsp;50% + PRs&nbsp;30% + Reviews&nbsp;20%.
        </p>

        <div className="tabs">
          {(["stacked", "ranking", "trend"] as const).map((v) => (
            <button
              key={v}
              className={`tab ${view === v ? "active" : ""}`}
              onClick={() => setView(v)}
            >
              {v === "stacked"
                ? "Breakdown"
                : v === "ranking"
                  ? "Ranking"
                  : "Sprint Trend"}
            </button>
          ))}
        </div>

        <div className="card" style={{ padding: 32 }}>
          {view === "stacked" && <StackedView />}
          {view === "ranking" && <RankingView />}
          {view === "trend" && <TrendView />}
        </div>
      </div>
    </section>
  );
}

function StackedView() {
  const data = scores.map((s) => ({
    name: s.name.split(" ")[0],
    "Items (50%)": s.items_score * 0.5,
    "PRs (30%)": s.prs_score * 0.3,
    "Reviews (20%)": s.reviews_score * 0.2,
  }));

  return (
    <ResponsiveContainer width="100%" height={380}>
      <BarChart data={data} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
        <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 13 }} />
        <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} domain={[0, 100]} />
        <Tooltip {...tooltipStyle} formatter={(v: number) => v.toFixed(1)} />
        <Legend />
        <Bar dataKey="Items (50%)" stackId="a" fill="#6366f1" radius={[0, 0, 0, 0]} maxBarSize={56} />
        <Bar dataKey="PRs (30%)" stackId="a" fill="#22d3ee" />
        <Bar dataKey="Reviews (20%)" stackId="a" fill="#f59e0b" radius={[6, 6, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

function RankingView() {
  const sorted = [...scores].sort((a, b) => b.total - a.total);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      {sorted.map((s, i) => (
        <RankBar key={s.name} score={s} rank={i + 1} max={sorted[0].total} />
      ))}
    </div>
  );
}

function RankBar({
  score,
  rank,
  max,
}: {
  score: ProductivityScore;
  rank: number;
  max: number;
}) {
  const pct = (score.total / max) * 100;
  const color = memberColors[score.name] ?? "#6366f1";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
      <span
        style={{
          width: 28,
          textAlign: "right",
          fontWeight: 700,
          color: rank <= 3 ? "var(--accent-light)" : "var(--text-muted)",
          fontSize: "0.9rem",
        }}
      >
        #{rank}
      </span>
      <span
        style={{
          width: 110,
          fontSize: "0.9rem",
          color: "var(--text-secondary)",
          flexShrink: 0,
        }}
      >
        {score.name}
      </span>
      <div
        style={{
          flex: 1,
          background: "var(--bg-primary)",
          borderRadius: 6,
          height: 28,
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: `${pct}%`,
            height: "100%",
            background: `linear-gradient(90deg, ${color}, ${color}cc)`,
            borderRadius: 6,
            transition: "width 0.6s ease",
            display: "flex",
            alignItems: "center",
            paddingLeft: 12,
            fontSize: "0.75rem",
            fontWeight: 600,
            color: "white",
          }}
        >
          {score.total.toFixed(1)}
        </div>
      </div>
    </div>
  );
}

function TrendView() {
  const memberNames = Object.keys(memberColors);

  return (
    <ResponsiveContainer width="100%" height={380}>
      <LineChart
        data={sprintTrends}
        margin={{ top: 10, right: 20, bottom: 20, left: 0 }}
      >
        <XAxis dataKey="sprint" tick={{ fill: "#94a3b8", fontSize: 13 }} />
        <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} domain={[0, 110]} />
        <Tooltip {...tooltipStyle} />
        <Legend />
        {memberNames.map((name) => (
          <Line
            key={name}
            type="monotone"
            dataKey={name}
            stroke={memberColors[name]}
            strokeWidth={2.5}
            dot={{ r: 4, fill: memberColors[name] }}
            activeDot={{ r: 6 }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}
