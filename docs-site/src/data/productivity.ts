export interface ProductivityScore {
  name: string;
  items_completed: number;
  prs_authored: number;
  code_reviews: number;
  items_score: number;
  prs_score: number;
  reviews_score: number;
  total: number;
}

export interface SprintTrend {
  sprint: string;
  [member: string]: number | string;
}

export const scores: ProductivityScore[] = [
  { name: "Alex Rivera", items_completed: 18, prs_authored: 14, code_reviews: 42, items_score: 90, prs_score: 70, reviews_score: 84, total: 82.8 },
  { name: "Sam Chen", items_completed: 14, prs_authored: 11, code_reviews: 31, items_score: 70, prs_score: 55, reviews_score: 62, total: 63.9 },
  { name: "Jordan Lee", items_completed: 20, prs_authored: 20, code_reviews: 58, items_score: 100, prs_score: 100, reviews_score: 100, total: 100 },
  { name: "Riley Patel", items_completed: 10, prs_authored: 8, code_reviews: 19, items_score: 50, prs_score: 40, reviews_score: 38, total: 44.6 },
  { name: "Morgan Kim", items_completed: 16, prs_authored: 15, code_reviews: 37, items_score: 80, prs_score: 75, reviews_score: 74, total: 77.3 },
  { name: "Casey Brooks", items_completed: 12, prs_authored: 9, code_reviews: 25, items_score: 60, prs_score: 45, reviews_score: 50, total: 53.5 },
];

export const sprintTrends: SprintTrend[] = [
  { sprint: "Q1-S1", "Alex Rivera": 78, "Sam Chen": 59, "Jordan Lee": 92, "Riley Patel": 41, "Morgan Kim": 72, "Casey Brooks": 48 },
  { sprint: "Q1-S2", "Alex Rivera": 81, "Sam Chen": 62, "Jordan Lee": 95, "Riley Patel": 38, "Morgan Kim": 75, "Casey Brooks": 51 },
  { sprint: "Q1-S3", "Alex Rivera": 85, "Sam Chen": 65, "Jordan Lee": 98, "Riley Patel": 44, "Morgan Kim": 78, "Casey Brooks": 55 },
  { sprint: "Q1-S4", "Alex Rivera": 83, "Sam Chen": 64, "Jordan Lee": 100, "Riley Patel": 45, "Morgan Kim": 77, "Casey Brooks": 54 },
];

export const memberColors: Record<string, string> = {
  "Alex Rivera": "#6366f1",
  "Sam Chen": "#22d3ee",
  "Jordan Lee": "#f59e0b",
  "Riley Patel": "#ef4444",
  "Morgan Kim": "#10b981",
  "Casey Brooks": "#8b5cf6",
};
