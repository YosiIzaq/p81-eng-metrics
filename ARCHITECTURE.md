# Code Review Statistics - Architecture Documentation

## Overview

A two-component system for fetching and visualizing GitHub code review statistics for a development team.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Code Review Statistics System                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────┐     ┌─────────────┐     ┌────────────────────┐   │
│  │ fetch_code_reviews.sh│────▶│  data/*.json │────▶│visualize_reviews.py│   │
│  │      (Bash)          │     │   (JSON)     │     │     (Python)       │   │
│  └──────────────────────┘     └─────────────┘     └────────────────────┘   │
│           │                         │                      │                │
│           ▼                         ▼                      ▼                │
│    GitHub API (gh)           code_reviews_          matplotlib charts       │
│    Rate limiting             latest.json             (bar, pie, grouped)    │
│    Retry logic               (symlink)                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component 1: Data Fetcher (`fetch_code_reviews.sh`)

### Purpose
Fetches PR review counts from GitHub for each team member across multiple time periods.

### Architecture Pattern
- **Script Type:** Shell (Bash 4+)
- **Pattern:** Pipeline with validation gates
- **I/O:** External API → JSON file
- **Configuration:** Loaded from `team_config.json`

### Key Functions

#### 1. Configuration Loading

Team members are loaded from `team_config.json` at startup using `jq`:

```bash
load_team_config() {
    TEAM_NAME=$(jq -r '.team_name // "Team"' "$CONFIG_FILE")
    # Load members from config...
}
```

**Why:** Keeps PII (names, usernames) out of the codebase.

#### 2. Validation Layer

```bash
validate_arrays() {
    if [ ${#USERNAMES[@]} -ne ${#DISPLAY_NAMES[@]} ]; then
        echo "❌ Error: USERNAMES and DISPLAY_NAMES arrays have different lengths" >&2
        return 1
    fi
    return 0
}
```

**Why:** Parallel arrays pattern requires length validation to prevent index mismatches.

#### 3. Cross-Platform Date Handling

```bash
get_date_offset() {
    local offset="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        date -v"$offset" +%Y-%m-%d
    else
        date -d "$offset" +%Y-%m-%d
    fi
}
```

**Why:** macOS `date` uses `-v` for offsets, GNU `date` uses `-d`. This abstraction ensures cross-platform compatibility.

#### 4. Rate Limit Handling with Retry

```bash
for ((attempt=1; attempt<=retries; attempt++)); do
    sleep 1  # Avoid rate limiting
    raw_output=$(gh search prs --reviewed-by="$user" --created="$start_date..$end_date" --limit=500 --json number 2>/dev/null) || true
    
    if [[ -n "$raw_output" ]]; then
        count=$(echo "$raw_output" | jq 'length' 2>/dev/null) || count=""
        if [[ -n "$count" && "$count" =~ ^[0-9]+$ ]]; then
            echo "$count"
            return 0
        fi
    fi
    
    if [[ $attempt -lt $retries ]]; then
        sleep 2
    fi
done
```

**Design Decisions:**
- **1-second delay** before each request prevents hitting rate limits
- **3 retries** with exponential backoff (sleep 2 between retries)
- **Silent failure** returns 0 to prevent breaking the overall run

#### 5. Test Mode with Mock Data

```bash
if [ "$TEST_MODE" = true ]; then
    # Generate mock counts based on user index (for consistency in tests)
    case "$user_index" in
        0) mock_count=5 ;;
        1) mock_count=10 ;;
        # ...
    esac
    return 0
fi
```

**Why:** Test mode allows running the full script without API calls, enabling fast test iterations. Uses index-based mock data to avoid hardcoding usernames.

### Data Flow

```
1. Load team config from team_config.json
        ↓
2. Validate inputs (arrays, dependencies, auth)
        ↓
3. For each team member:
   a. Fetch count for each period (with retry)
   b. Append to JSON file
        ↓
4. Validate output JSON
        ↓
5. Update symlink (skip in test mode)
        ↓
6. Print summary table
```

---

## Component 2: Visualizer (`visualize_reviews.py`)

### Purpose
Loads JSON data and generates matplotlib charts (bar, pie, grouped comparison).

### Architecture Pattern
- **Script Type:** Python 3.x with argparse CLI
- **Pattern:** Load → Transform → Render
- **Dependencies:** matplotlib, numpy
- **Configuration:** Loaded from `team_config.json`

### Key Functions

#### 1. Configuration Loading

```python
def load_team_config() -> tuple[dict, dict, str]:
    """Load team configuration from team_config.json."""
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    
    team_name = config.get("team_name", "Team")
    # Build TEAM_MEMBERS and COLORS dicts...
    return team_members, colors, team_name
```

**Why:** Keeps PII (names, usernames) out of the codebase.

#### 2. Graceful Dependency Import

```python
try:
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("   pip install matplotlib numpy")
    sys.exit(1)
```

**Why:** Clear error message guides users to install dependencies rather than cryptic import errors.

#### 3. Null-Safe Data Loading

```python
def plot_bar_chart(data: dict, period: str = "full_2025", save_path: str = None):
    if data is None:
        print("⚠️ No data to display")
        return
    
    reviews = data.get("reviews", [])
    if not reviews:
        print("⚠️ No reviews data to display")
        return
```

**Why:** Defensive programming prevents crashes when data is missing or malformed.

#### 4. Dynamic Color Mapping

Colors are loaded from `team_config.json` with fallback to a default color cycle:

```python
DEFAULT_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]

for i, member in enumerate(members):
    color = member.get("color", DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
```

**Why:** Consistent colors across charts make team members visually identifiable.

---

## Data Model

### JSON Schema

```json
{
  "generated_at": "2026-01-27T19:07:01+02:00",
  "team": "My Team",
  "test_mode": false,
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
      "last_month": 32,
      "last_3_months": 74,
      "h2_2025": 60,
      "full_2025": 60
    }
  ]
}
```

### File Structure

```
statistics/
├── fetch_code_reviews.sh      # Data fetcher (Bash)
├── test_fetch_code_reviews.sh # Bash test suite (43 tests)
├── visualize_reviews.py       # Visualization (Python)
├── test_visualize_reviews.py  # Python test suite (37 tests)
├── team_config.json           # Team config (gitignored, local-only)
├── team_config.example.json   # Example config template
├── README.md                  # User documentation
├── ARCHITECTURE.md            # This file
├── coverage_report.txt        # Test coverage report
├── .venv/                     # Python virtual environment
└── data/                      # All data files (gitignored)
    ├── code_reviews_YYYYMMDD_HHMMSS.json  # Timestamped data
    ├── code_reviews_latest.json           # Symlink to latest
    └── charts/
        ├── bar_full_2025.png
        ├── pie_full_2025.png
        └── comparison.png
```

---

## Design Decisions

### 1. Bash + Python Hybrid

| Concern | Bash | Python |
|---------|------|--------|
| GitHub CLI integration | ✅ Native | ❌ Subprocess |
| JSON parsing | `jq` | ✅ Native |
| Visualization | ❌ None | ✅ matplotlib |
| Testing | BATS-like | ✅ unittest |

**Decision:** Use each language for its strengths.

### 2. External Configuration

Team member PII (names, usernames) is stored in `team_config.json` which is:
- **Gitignored:** Never committed to version control
- **Local-only:** Each user creates from template
- **Single source:** Used by both bash and Python components

### 3. Symlink for Latest Data

```bash
ln -sf "$OUTPUT_FILE" "$DATA_DIR/code_reviews_latest.json"
```

**Why:** 
- Timestamped files provide history
- Symlink provides stable path for consumers
- Test mode skips symlink to avoid corrupting production pointer

### 4. Test Mode Isolation

- `--test` flag enables mock data
- Test data goes to separate file (`code_reviews_test.json`)
- Production symlink not updated during tests

### 5. Graceful Degradation

All functions handle:
- `None` data
- Empty arrays
- Missing fields (via `.get()` with defaults)
- API failures (returns 0 instead of crashing)

---

## Testing Strategy

### Bash Tests (43 tests)

| Category | Count | Examples |
|----------|:-----:|----------|
| Positive | 12 | Script runs, JSON valid |
| Negative | 11 | Empty username, invalid dates |
| Edge Cases | 5 | Same date range, future dates |
| Dependencies | 3 | gh, jq availability |
| Output Format | 4 | Table formatting |

### Python Tests (37 tests)

| Category | Count | Examples |
|----------|:-----:|----------|
| Data Loading | 3 | Valid JSON, missing file |
| Validation | 4 | Empty reviews, missing fields |
| Config | 4 | Team members, colors |
| Charts | 10 | Bar, pie, comparison |
| Edge Cases | 8 | Unicode, large counts |

---

## Error Handling

### GitHub Rate Limiting

```
HTTP 403: You have exceeded a secondary rate limit.
```

**Mitigation:**
1. 1-second delay between requests
2. 3 retries with 2-second wait
3. Graceful fallback to 0

### Missing Dependencies

```bash
if ! command -v gh &> /dev/null; then
    missing+=("gh (GitHub CLI)")
fi
```

**Pattern:** Check before use, fail fast with helpful message.

### Missing Configuration

```bash
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ Error: Team configuration file not found: $CONFIG_FILE"
    echo "To set up:"
    echo "  1. Copy team_config.example.json to team_config.json"
    echo "  2. Fill in your team's GitHub usernames and display names"
    exit 1
fi
```

**Pattern:** Clear setup instructions when configuration is missing.

---

## Future Improvements

1. **Chunked Fetching:** Split large date ranges to avoid 500-result limit
2. **Caching:** Store raw PR data for detailed analysis
3. **Trend Charts:** Plot reviews over time
4. **Slack Integration:** Automatic weekly reports

---

**Last Updated:** 2026-01-27
