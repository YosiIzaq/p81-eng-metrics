# Code Review Statistics

**Purpose:** Track and visualize code review contributions by team members.

---

## Quick Start

### 1. Set Up Configuration

```bash
# Copy the example config and fill in your team's info
cp team_config.example.json team_config.json
# Edit team_config.json with your team's GitHub usernames and display names
```

### 2. Fetch Data

```bash
./fetch_code_reviews.sh
```

### 3. Visualize

```bash
# Show all charts
python3 visualize_reviews.py

# Specific period
python3 visualize_reviews.py --period full_2025

# Export as PNG
python3 visualize_reviews.py --export png
```

---

## Configuration

Team configuration is stored in `team_config.json` (gitignored). This file contains:
- Team name
- Team member GitHub usernames
- Display names
- Optional custom colors for charts

See `team_config.example.json` for the expected format.

---

## Files

| File | Purpose |
|------|---------|
| `fetch_code_reviews.sh` | Fetches data from GitHub via `gh` CLI |
| `test_fetch_code_reviews.sh` | Test suite (43 tests, >85% coverage) |
| `visualize_reviews.py` | Creates charts and graphs |
| `test_visualize_reviews.py` | Python test suite (37 tests) |
| `team_config.json` | Team configuration (gitignored, local-only) |
| `team_config.example.json` | Example config template |
| `ARCHITECTURE.md` | Architecture documentation with code links |
| `coverage_report.txt` | Test coverage report |
| `data/` | Raw JSON data files (gitignored) |
| `data/code_reviews_latest.json` | Symlink to most recent data |
| `data/charts/` | Exported chart images |

---

## Dependencies

### Shell Script
- `gh` (GitHub CLI) - authenticated
- `jq` (JSON processor)

### Python Script
```bash
pip install matplotlib numpy
```

---

## Usage Examples

### Fetch Fresh Data
```bash
./fetch_code_reviews.sh
```

### Test Mode (no API calls)
```bash
./fetch_code_reviews.sh --test
```

### Dry Run
```bash
./fetch_code_reviews.sh --dry-run
```

### With PR Details (default)
```bash
./fetch_code_reviews.sh  # Stores PR numbers and URLs for verification
```

### Without PR Details (faster, smaller files)
```bash
./fetch_code_reviews.sh --no-details
```

### View Summary Table
```bash
python3 visualize_reviews.py
```

### Export Charts
```bash
python3 visualize_reviews.py --export png
```

### Specific Period
```bash
python3 visualize_reviews.py --period last_month
python3 visualize_reviews.py --period last_3_months
python3 visualize_reviews.py --period h2_2025
python3 visualize_reviews.py --period full_2025
```

### Chart Types
```bash
python3 visualize_reviews.py --chart bar
python3 visualize_reviews.py --chart pie
python3 visualize_reviews.py --chart comparison
python3 visualize_reviews.py --chart all
```

### Fetch and Visualize
```bash
python3 visualize_reviews.py --fetch
```

---

## Data Format

```json
{
  "generated_at": "2026-01-27T18:33:54+02:00",
  "team": "My Team",
  "include_pr_details": true,
  "periods": {
    "last_month": {"start": "2025-12-27", "end": "2026-01-27"},
    "last_3_months": {"start": "2025-10-27", "end": "2026-01-27"},
    "h2_2025": {"start": "2025-06-01", "end": "2025-12-31"},
    "full_2025": {"start": "2025-01-01", "end": "2025-12-31"}
  },
  "reviews": [
    {
      "github_username": "dev-alice",
      "display_name": "Alice Smith",
      "full_2025": {
        "count": 127,
        "prs": [
          {
            "pr": 2957,
            "repo": "org/repo",
            "url": "https://github.com/org/repo/pull/2957"
          }
        ]
      }
    }
  ]
}
```

**Note:** Each period now includes both the count AND a list of PR numbers/URLs for verification.

---

## Testing

### Run Test Suite
```bash
./test_fetch_code_reviews.sh
```

### Test Coverage
- **43 tests** covering positive, negative, and edge cases
- **~87% estimated line coverage**
- Coverage report: `coverage_report.txt`

### Test Categories
| Category | Tests | Description |
|----------|:-----:|-------------|
| Positive | 12 | Happy path scenarios |
| Negative | 11 | Error handling, invalid inputs |
| Edge Cases | 5 | Boundary conditions |
| Dependencies | 3 | Required tools availability |
| Output Format | 4 | Console output correctness |
| JSON Structure | 3 | Valid JSON output |
| Mock Data | 2 | Test mode consistency |
| Function Isolation | 3 | Unit-level function tests |

---

## Notes

- Data is fetched from GitHub using `gh search prs --reviewed-by=<username>`
- Maximum 500 results per query (GitHub limit)
- Zero reviews may indicate:
  - User reviews in a different org
  - User reviews under different username
  - User doesn't do formal PR reviews

---

**Created:** 2026-01-27
