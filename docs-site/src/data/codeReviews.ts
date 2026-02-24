export interface TeamMember {
  name: string;
  github: string;
  last_month: number;
  last_3_months: number;
  h2_2025: number;
  full_2025: number;
}

export const teamName = "Phoenix Squad";

export const members: TeamMember[] = [
  { name: "Alex Rivera", github: "alex-rivera-dev", last_month: 42, last_3_months: 118, h2_2025: 165, full_2025: 210 },
  { name: "Sam Chen", github: "samchen99", last_month: 31, last_3_months: 87, h2_2025: 142, full_2025: 195 },
  { name: "Jordan Lee", github: "jordanl-eng", last_month: 58, last_3_months: 162, h2_2025: 201, full_2025: 298 },
  { name: "Riley Patel", github: "riley-patel", last_month: 19, last_3_months: 53, h2_2025: 88, full_2025: 124 },
  { name: "Morgan Kim", github: "mkim-dev", last_month: 37, last_3_months: 95, h2_2025: 158, full_2025: 227 },
  { name: "Casey Brooks", github: "casey-brooks", last_month: 25, last_3_months: 71, h2_2025: 112, full_2025: 163 },
];

export const periods = ["last_month", "last_3_months", "h2_2025", "full_2025"] as const;

export const periodLabels: Record<string, string> = {
  last_month: "Last Month",
  last_3_months: "Last 3 Months",
  h2_2025: "H2 2025",
  full_2025: "Full 2025",
};

export const colors = ["#6366f1", "#22d3ee", "#f59e0b", "#ef4444", "#10b981", "#8b5cf6"];
