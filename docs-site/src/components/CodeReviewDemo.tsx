import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import {
  members,
  teamName,
  periods,
  periodLabels,
  colors,
  type TeamMember,
} from "../data/codeReviews";

type Period = (typeof periods)[number];
type ChartView = "bar" | "pie" | "comparison";

function barData(period: Period) {
  return members.map((m) => ({ name: m.name.split(" ")[0], reviews: m[period] }));
}

function pieData(period: Period) {
  return members.map((m, i) => ({
    name: m.name,
    value: m[period],
    color: colors[i],
  }));
}

function comparisonData() {
  return members.map((m) => ({
    name: m.name.split(" ")[0],
    ...Object.fromEntries(periods.map((p) => [periodLabels[p], m[p]])),
  }));
}

const compColors = ["#6366f1", "#22d3ee", "#f59e0b", "#10b981"];

const tooltipStyle = {
  contentStyle: {
    background: "#1e293b",
    border: "1px solid #334155",
    borderRadius: 8,
    fontSize: "0.8rem",
  },
  labelStyle: { color: "#f1f5f9" },
};

export default function CodeReviewDemo() {
  const [view, setView] = useState<ChartView>("bar");
  const [period, setPeriod] = useState<Period>("last_3_months");

  return (
    <section id="demo">
      <div className="container">
        <h2>Code Review Stats</h2>
        <p>
          Interactive demo with sample data from <strong>{teamName}</strong>.
        </p>

        <div className="tabs">
          {(["bar", "pie", "comparison"] as const).map((v) => (
            <button
              key={v}
              className={`tab ${view === v ? "active" : ""}`}
              onClick={() => setView(v)}
            >
              {v === "bar" ? "Bar" : v === "pie" ? "Pie" : "Comparison"}
            </button>
          ))}
        </div>

        {view !== "comparison" && (
          <div className="select-wrapper">
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value as Period)}
            >
              {periods.map((p) => (
                <option key={p} value={p}>
                  {periodLabels[p]}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="card" style={{ padding: 32 }}>
          {view === "bar" && <BarView period={period} />}
          {view === "pie" && <PieView period={period} />}
          {view === "comparison" && <ComparisonView />}
        </div>
      </div>
    </section>
  );
}

function BarView({ period }: { period: Period }) {
  const data = barData(period);
  return (
    <ResponsiveContainer width="100%" height={380}>
      <BarChart data={data} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
        <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 13 }} />
        <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
        <Tooltip {...tooltipStyle} />
        <Bar
          dataKey="reviews"
          radius={[6, 6, 0, 0]}
          maxBarSize={56}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={colors[i]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function PieView({ period }: { period: Period }) {
  const data = pieData(period);
  const total = data.reduce((s, d) => s + d.value, 0);

  return (
    <ResponsiveContainer width="100%" height={380}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={80}
          outerRadius={140}
          paddingAngle={3}
          dataKey="value"
          label={({ name, value }: { name: string; value: number }) =>
            `${name.split(" ")[0]} (${Math.round((value / total) * 100)}%)`
          }
        >
          {data.map((d, i) => (
            <Cell key={i} fill={d.color} />
          ))}
        </Pie>
        <Tooltip {...tooltipStyle} />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
}

function ComparisonView() {
  const data = comparisonData();
  return (
    <ResponsiveContainer width="100%" height={380}>
      <BarChart data={data} margin={{ top: 10, right: 20, bottom: 20, left: 0 }}>
        <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 13 }} />
        <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
        <Tooltip {...tooltipStyle} />
        <Legend />
        {Object.values(periodLabels).map((label, i) => (
          <Bar
            key={label}
            dataKey={label}
            fill={compColors[i]}
            radius={[4, 4, 0, 0]}
            maxBarSize={24}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
