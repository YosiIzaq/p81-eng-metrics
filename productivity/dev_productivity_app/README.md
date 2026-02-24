# Developer Productivity Scorer

A Python CLI tool for measuring and visualizing team productivity based on:
- **Jira Items Completed** (50% weight) - Stories/tasks in Done or Ready for Release status
- **PRs Authored** (30% weight) - Merged PRs demonstrating code shipped
- **Code Reviews** (20% weight) - Reviews performed (knowledge sharing)

## Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

### 1. Set Up Team Configuration

Team members are loaded from `team_config.json` in the repository root (`Jira/statistics/`). Copy the example and fill in your team's info:

```bash
cd ../..  # Go to Jira/statistics/
cp team_config.example.json team_config.json
# Edit team_config.json with your team's info
```

### 2. Set Up API Credentials

Create/edit `.env.yaml` in the app root:

```yaml
jira:
  email: "your.email@company.com"
  api_token: "your-jira-api-token"  # Get from: https://id.atlassian.com/manage-profile/security/api-tokens
  expires_at: "2026-12-31"  # Token expiration date (YYYY-MM-DD)
  cloud_id: "yoursite.atlassian.net"

github:
  org: "your-github-org"
```

See `.env.yaml.example` for the expected format.

## Quick Start

### Hybrid MCP Approach (Recommended)

This tool uses a **hybrid approach** where Jira data is fetched via MCP (Model Context Protocol) 
and GitHub data is fetched directly via `gh` CLI.

**Step 1: Ask the agent to fetch Jira data**

Ask: "Fetch Jira productivity data for my team for the last year/sprint"

The agent will:
1. Call `searchJiraIssuesUsingJql` via Atlassian MCP
2. Paginate through results (100 items per page)
3. Save to `data/jira_year_page*.json` files
4. Merge into `data/jira_year_merged.json`

**Step 2: Run the processing script**

```bash
source .venv/bin/activate

# For sprint data:
python fetch_via_mcp.py --jira-data data/jira_raw.json --period sprint --output report.md

# For yearly data:
python fetch_via_mcp.py --jira-data data/jira_year_merged.json --period last_year --output yearly_report.md
```

### Alternative: Direct API (if MCP unavailable)

**Option 1: Use `.env.yaml` (recommended)**

The script will:
- Automatically load credentials from `.env.yaml`
- Warn you 7 days before token expiration
- Alert if token is already expired

**Option 2: Environment variables**

```bash
export JIRA_API_TOKEN="your-api-token"
export JIRA_EMAIL="your-email@company.com"
python productivity_scorer.py run --period sprint --output report.md
```

**Note:** `.env.yaml` takes precedence over environment variables.

### Test Mode (Mock Data)

```bash
python productivity_scorer.py run --period sprint --test --output report.md
```

## Configuration File

The `config/default_config.json` contains settings like weights and periods:

```json
{
  "version": "1.0",
  "team": {
    "name": "My Team",
    "members": []
  },
  "weights": {
    "items_completed": 0.50,
    "prs_authored": 0.30,
    "code_reviews": 0.20
  },
  "periods": {
    "sprint": {
      "type": "fixed",
      "start": "2026-01-18",
      "end": "2026-02-07",
      "label": "Sprint Name"
    },
    "last_year": {
      "type": "relative",
      "days_back": 365,
      "label": "Full Year"
    }
  }
}
```

**Note:** Team members are loaded from `team_config.json` in the repo root, not from `default_config.json`.

## Formula

```
Productivity Score = (Items Score × 0.50) + (PRs Score × 0.30) + (Reviews Score × 0.20)
```

Each component is normalized to 0-100 relative to the team maximum.

## Scripts

| Script | Purpose |
|--------|---------|
| `productivity_scorer.py` | Main CLI (fetch/score/display) |
| `fetch_via_mcp.py` | Process MCP-fetched Jira data |
| `merge_jira_pages.py` | Merge paginated Jira responses |

## Output Formats

### Terminal Table

```
Productivity Rankings - Sprint Name
==========================================
Rank Name                 Items    PRs      Reviews  Total   
-------------------------------------------------------------
1    Alice Smith          50.0     30.0     4.6      84.6    
2    Bob Jones            32.6     12.9     20.0     65.5    
```

### Markdown Report

Generated with `--output report.md`

### Charts

- **Bar Chart** - Stacked bars showing component contributions
- **Ranking Chart** - Horizontal bars with rank labels
- **Trend Chart** - Line chart comparing multiple periods

## Architecture

```
dev_productivity_app/
├── productivity_scorer.py       # Main CLI entry point
├── fetch_via_mcp.py             # MCP data processor
├── merge_jira_pages.py          # Merge paginated Jira data
├── .env.yaml                    # API credentials (gitignored)
├── .env.yaml.example            # Credential template
├── fetchers/
│   ├── base_fetcher.py          # Abstract base class + data models
│   ├── github_fetcher.py        # GitHub CLI integration
│   └── jira_fetcher.py          # Jira REST API integration
├── calculator/
│   └── score_calculator.py      # Weighted scoring logic
├── display/
│   ├── charts.py                # matplotlib visualizations
│   └── tables.py                # Terminal/markdown tables
├── config/
│   ├── default_config.json      # App config (no PII)
│   └── schema.json              # JSON schema validation
├── data/                        # Generated data (gitignored)
│   ├── jira_raw.json            # Current sprint data
│   └── jira_year_merged.json    # Full year data
└── tests/                       # Test suite (84% coverage)
```

## Data Sources

| Metric | Source | API/Command |
|--------|--------|-------------|
| Items Completed | Jira | `searchJiraIssuesUsingJql` via Atlassian MCP |
| PRs Authored | GitHub | `gh search prs --author=<user> --merged` |
| Code Reviews | GitHub | `gh search prs --reviewed-by=<user>` |

## Refreshing Jira Data via MCP

To refresh Jira data, ask the agent:

```
"Fetch Jira data for my team's productivity - last year, all Done/Ready for Release items"
```

The agent will:
1. Build JQL: `project = PROJ AND assignee IN (...) AND status IN ('Done', 'Ready for Release') AND updated >= '2025-01-31'`
2. Call Atlassian MCP with pagination
3. Save each page to `data/jira_year_page*.json`
4. Run `python merge_jira_pages.py` to combine

## Testing

```bash
# Run all tests with coverage
python -m pytest tests/ -v --cov=. --cov-report=term-missing

# Run specific test module
python -m pytest tests/test_score_calculator.py -v
```

**Coverage:** 84%+ across all modules

## License

Internal use only.
