# Manual Testing Guide

Two parts: **A** — CLI tool (code review stats), **B** — GitHub Pages showcase.

---

## Part A — CLI Tool

### Prerequisites

```bash
# 1. Check gh CLI is authenticated
gh auth status

# 2. Confirm team config exists (gitignored, local only)
ls team_config.json

# 3. Activate Python venv (or create one)
source .venv/bin/activate        # if already created
# OR
python3 -m venv .venv && source .venv/bin/activate && pip install matplotlib numpy
```

---

### Step 1 — Test Mode (no API calls)

Validates the script and mock data without hitting GitHub.

```bash
bash fetch_code_reviews.sh --test
```

**Expected:**
- Prints a table with 8 members, all periods showing identical mock counts (5, 10, 15…)
- Creates `data/code_reviews_test.json`
- Ends with `✅ JSON validated`

---

### Step 2 — Real Fetch

Pulls live review counts from GitHub (~3–5 min due to throttling).

```bash
bash fetch_code_reviews.sh
```

**Expected:**
- Progress line per member: `Last Month... N | Last 3 Mo... N | H2 2025... N | Full 2025... N`
- Creates `data/code_reviews_<timestamp>.json` and symlink `data/code_reviews_latest.json`
- Ends with a summary table and `✅ Done!`

**If it fails on a member** — usually a GitHub rate limit. Re-run; it picks up from the latest file.

---

### Step 3 — Verify Output

```bash
# Check file exists and is valid JSON
cat data/code_reviews_latest.json | python3 -m json.tool | head -30

# Quick count check — should show non-zero numbers for active members
python3 -c "
import json
with open('data/code_reviews_latest.json') as f:
    d = json.load(f)
for r in d['reviews']:
    print(f\"{r['display_name']:25} {r['last_month']:4} {r['last_3_months']:4} {r['h2_2025']:4} {r['full_2025']:4}\")
"
```

**Expected:** All active members have non-zero counts in at least `last_3_months`.

---

### Step 4 — Visualize

Run each chart type (use `--no-show` to skip the GUI popup if headless):

```bash
# Bar chart — last 3 months
python3 visualize_reviews.py --chart bar --period last_3_months

# Pie chart — share of reviews
python3 visualize_reviews.py --chart pie --period last_3_months

# Comparison — all periods side-by-side
python3 visualize_reviews.py --chart comparison

# All charts at once
python3 visualize_reviews.py --chart all
```

**Expected:** Charts open in a window (or render silently). No Python tracebacks.

---

### Step 5 — Export PNG

```bash
python3 visualize_reviews.py --chart comparison --no-show --export png
ls -lh data/charts/
```

**Expected:** `comparison.png` exists, ~50–100 KB.

---

### Part A Checklist

- [ ] Test mode ran cleanly
- [ ] Real fetch completed (all or most members)
- [ ] `data/code_reviews_latest.json` is valid JSON with non-zero counts
- [ ] All chart types rendered without errors
- [ ] PNG exported to `data/charts/`

---

## Part B — GitHub Pages Showcase

**URL:** https://yosiizaq.github.io/p81-eng-metrics/

### What to Check

#### 1. Page Load

- [ ] Page loads without errors (check browser console: F12 → Console)
- [ ] Dark theme renders correctly
- [ ] No broken images or missing fonts

#### 2. Hero Section

- [ ] Title and tagline visible
- [ ] "View on GitHub" button opens https://github.com/YosiIzaq/p81-eng-metrics in a new tab
- [ ] "See Demo ↓" scrolls to the Code Review section

#### 3. Features Section

- [ ] All 4 cards visible: Code Review Tracking, Productivity Scoring, Multi-period Trends, Export
- [ ] Cards highlight on hover (border turns purple)

#### 4. Code Review Demo

- [ ] Three tabs work: **Bar**, **Pie**, **Comparison**
- [ ] Period dropdown (Last Month / Last 3 Months / H2 2025 / Full 2025) changes the Bar and Pie charts
- [ ] Comparison tab shows all 4 periods side-by-side, dropdown hidden
- [ ] Hovering chart shows tooltip with correct member name and count
- [ ] All 6 Phoenix Squad members appear in charts

#### 5. Productivity Demo

- [ ] Three tabs work: **Breakdown**, **Ranking**, **Sprint Trend**
- [ ] Breakdown: stacked bars with 3 color segments (Items / PRs / Reviews)
- [ ] Ranking: horizontal bars sorted highest to lowest, score inside bar
- [ ] Sprint Trend: 6 lines across Q1-S1 → Q1-S4, all distinct colors

#### 6. Quick Start Section

- [ ] 3 numbered steps visible with code blocks
- [ ] Code is readable (JetBrains Mono font)

#### 7. Responsive (optional)

- [ ] Resize browser to mobile width (~375px) — layout should stack, no overflow

---

### If the Page Is Stale

The GH Actions workflow auto-deploys on push to `main`. To trigger manually:

```bash
gh workflow run deploy-pages.yml --repo YosiIzaq/p81-eng-metrics
```

Or push a trivial change:

```bash
cd docs-site && echo "" >> index.html && git add index.html && git commit -m "trigger deploy" && git push
```

Check deployment status:

```bash
gh run list --repo YosiIzaq/p81-eng-metrics --limit 5
```
