#!/usr/bin/env bash
# Fetch code review statistics for a team
# Usage: ./fetch_code_reviews.sh [--test] [--dry-run] [--details] [--throttle=N]
#
# Options:
#   --test        Run in test mode (uses mock data)
#   --dry-run     Show what would be done without fetching
#   --details     Store full PR details (numbers, URLs) for verification
#   --no-details  Don't store full PR details
#   --throttle=N  Wait N seconds between users (default: 20)
#   --no-throttle Disable throttling (use with caution - may hit rate limits)
#
# Configuration:
#   Requires team_config.json in the same directory. Copy team_config.example.json
#   and fill in your team's GitHub usernames and display names.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
DETAILS_DIR="$DATA_DIR/details"
CONFIG_FILE="$SCRIPT_DIR/team_config.json"
TEST_MODE=false
DRY_RUN=false
STORE_DETAILS=true  # Default to storing details for verification
THROTTLE_DELAY=20   # Default: 20 seconds between users
PERIOD_DELAY=3      # Delay between period fetches within a user

# Parse arguments
for arg in "$@"; do
    case $arg in
        --test)
            TEST_MODE=true
            THROTTLE_DELAY=0  # No throttle in test mode
            PERIOD_DELAY=0
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        --details)
            STORE_DETAILS=true
            ;;
        --no-details)
            STORE_DETAILS=false
            ;;
        --throttle=*)
            THROTTLE_DELAY="${arg#*=}"
            ;;
        --no-throttle)
            THROTTLE_DELAY=0
            PERIOD_DELAY=0
            ;;
    esac
done

# Load team configuration from JSON
load_team_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "❌ Error: Team configuration file not found: $CONFIG_FILE" >&2
        echo "" >&2
        echo "To set up:" >&2
        echo "  1. Copy team_config.example.json to team_config.json" >&2
        echo "  2. Fill in your team's GitHub usernames and display names" >&2
        echo "" >&2
        echo "Example:" >&2
        echo "  cp team_config.example.json team_config.json" >&2
        echo "  # Edit team_config.json with your team's info" >&2
        return 1
    fi
    
    if ! command -v jq &> /dev/null; then
        echo "❌ Error: jq is required to parse config file" >&2
        return 1
    fi
    
    # Load team name
    TEAM_NAME=$(jq -r '.team_name // "Team"' "$CONFIG_FILE")
    
    # Load member arrays from JSON
    local member_count
    member_count=$(jq '.members | length' "$CONFIG_FILE")
    
    if [ "$member_count" -eq 0 ]; then
        echo "❌ Error: No team members defined in $CONFIG_FILE" >&2
        return 1
    fi
    
    USERNAMES=()
    DISPLAY_NAMES=()
    
    for ((i=0; i<member_count; i++)); do
        local username display_name
        username=$(jq -r ".members[$i].github_username" "$CONFIG_FILE")
        display_name=$(jq -r ".members[$i].display_name" "$CONFIG_FILE")
        USERNAMES+=("$username")
        DISPLAY_NAMES+=("$display_name")
    done
    
    return 0
}

# Load configuration (fail fast if missing)
if ! load_team_config; then
    exit 1
fi

# Generate output filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ "$TEST_MODE" = true ]; then
    OUTPUT_FILE="$DATA_DIR/code_reviews_test.json"
else
    OUTPUT_FILE="$DATA_DIR/code_reviews_${TIMESTAMP}.json"
fi

# Validate arrays have same length
validate_arrays() {
    if [ ${#USERNAMES[@]} -ne ${#DISPLAY_NAMES[@]} ]; then
        echo "❌ Error: USERNAMES and DISPLAY_NAMES arrays have different lengths" >&2
        echo "   USERNAMES: ${#USERNAMES[@]}, DISPLAY_NAMES: ${#DISPLAY_NAMES[@]}" >&2
        return 1
    fi
    return 0
}

# Time periods
TODAY=$(date +%Y-%m-%d)

# macOS vs Linux date handling
get_date_offset() {
    local offset="$1"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        date -v"$offset" +%Y-%m-%d
    else
        date -d "$offset" +%Y-%m-%d
    fi
}

LAST_MONTH_START=$(get_date_offset "-1m")
THREE_MONTHS_START=$(get_date_offset "-3m")

H2_2025_START="2025-06-01"
H2_2025_END="2025-12-31"
FULL_2025_START="2025-01-01"
FULL_2025_END="2025-12-31"

# Validate date format (YYYY-MM-DD)
validate_date() {
    local date_str="$1"
    if [[ ! "$date_str" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        echo "❌ Error: Invalid date format: $date_str (expected YYYY-MM-DD)" >&2
        return 1
    fi
    return 0
}

# Check required dependencies
check_dependencies() {
    local missing=()
    
    if ! command -v gh &> /dev/null; then
        missing+=("gh (GitHub CLI)")
    fi
    
    if ! command -v jq &> /dev/null; then
        missing+=("jq")
    fi
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo "❌ Error: Missing dependencies:" >&2
        for dep in "${missing[@]}"; do
            echo "   - $dep" >&2
        done
        return 1
    fi
    return 0
}

# Check GitHub auth status
check_github_auth() {
    if [ "$TEST_MODE" = true ]; then
        return 0
    fi
    
    if ! gh auth status &>/dev/null; then
        echo "❌ Error: Not authenticated with GitHub CLI" >&2
        echo "   Run: gh auth login" >&2
        return 1
    fi
    return 0
}

# Helper function to get PR details with retry
# Arguments: user, start_date, end_date, period_name
# Returns: JSON array of PR details, also saves to details file
get_pr_details() {
    local user="$1"
    local start_date="$2"
    local end_date="$3"
    local period_name="$4"
    local retries=3
    local raw_output=""
    
    # Validate inputs
    if [ -z "$user" ]; then
        echo "[]"
        return 1
    fi
    
    if ! validate_date "$start_date" 2>/dev/null || ! validate_date "$end_date" 2>/dev/null; then
        echo "[]"
        return 1
    fi
    
    # Check date ordering (start should be before end)
    if [[ "$start_date" > "$end_date" ]]; then
        echo "[]"
        return 1
    fi
    
    # Test mode - return mock data (index-based to avoid hardcoding usernames)
    if [ "$TEST_MODE" = true ]; then
        local mock_count
        # Find user index in the array for deterministic mock data
        local user_index=-1
        for idx in "${!USERNAMES[@]}"; do
            if [ "${USERNAMES[$idx]}" = "$user" ]; then
                user_index=$idx
                break
            fi
        done
        
        # Generate mock counts based on index (for consistency in tests)
        case "$user_index" in
            0) mock_count=5 ;;
            1) mock_count=10 ;;
            2) mock_count=15 ;;
            3) mock_count=3 ;;
            4) mock_count=2 ;;
            5) mock_count=12 ;;
            6) mock_count=14 ;;
            -1) mock_count=0 ;;  # User not in config
            *) mock_count=$((user_index + 1)) ;;  # Fallback for larger teams
        esac
        
        # Generate mock PR data
        local mock_prs="["
        for ((i=1; i<=mock_count; i++)); do
            [ $i -gt 1 ] && mock_prs+=","
            mock_prs+="{\"number\":$((1000+i)),\"repository\":{\"nameWithOwner\":\"perimeter-81/mock-repo\"},\"url\":\"https://github.com/perimeter-81/mock-repo/pull/$((1000+i))\"}"
        done
        mock_prs+="]"
        echo "$mock_prs"
        return 0
    fi
    
    # Dry run mode
    if [ "$DRY_RUN" = true ]; then
        echo "[]"
        return 0
    fi
    
    for ((attempt=1; attempt<=retries; attempt++)); do
        # Add small delay to avoid rate limiting
        sleep 1
        
        # Run gh search and capture output with PR details
        raw_output=$(gh search prs \
            --reviewed-by="$user" \
            --created="$start_date..$end_date" \
            --limit=500 \
            --json number,repository,url 2>/dev/null) || true
        
        # Check if output is valid JSON array
        if [[ -n "$raw_output" ]] && echo "$raw_output" | jq empty 2>/dev/null; then
            # Save details to file if enabled
            if [ "$STORE_DETAILS" = true ] && [ "$TEST_MODE" = false ]; then
                local details_file="$DETAILS_DIR/${TIMESTAMP}_${user}_${period_name}.json"
                echo "$raw_output" > "$details_file"
            fi
            echo "$raw_output"
            return 0
        fi
        
        # Wait before retry
        if [[ $attempt -lt $retries ]]; then
            sleep 2
        fi
    done
    
    echo "[]"
    return 1
}

# Generate JSON output for a single user with PR details
generate_user_json() {
    local user="$1"
    local display_name="$2"
    local last_month_prs="$3"
    local last_3_months_prs="$4"
    local h2_2025_prs="$5"
    local full_2025_prs="$6"
    
    # Get counts from PR arrays
    local last_month_count=$(echo "$last_month_prs" | jq 'length')
    local last_3_months_count=$(echo "$last_3_months_prs" | jq 'length')
    local h2_2025_count=$(echo "$h2_2025_prs" | jq 'length')
    local full_2025_count=$(echo "$full_2025_prs" | jq 'length')
    
    # Extract just PR numbers and URLs for compact storage
    local last_month_refs=$(echo "$last_month_prs" | jq '[.[] | {pr: .number, repo: .repository.nameWithOwner, url: .url}]')
    local last_3_months_refs=$(echo "$last_3_months_prs" | jq '[.[] | {pr: .number, repo: .repository.nameWithOwner, url: .url}]')
    local h2_2025_refs=$(echo "$h2_2025_prs" | jq '[.[] | {pr: .number, repo: .repository.nameWithOwner, url: .url}]')
    local full_2025_refs=$(echo "$full_2025_prs" | jq '[.[] | {pr: .number, repo: .repository.nameWithOwner, url: .url}]')
    
    cat << EOF
    {
      "github_username": "$user",
      "display_name": "$display_name",
      "last_month": {
        "count": $last_month_count,
        "prs": $last_month_refs
      },
      "last_3_months": {
        "count": $last_3_months_count,
        "prs": $last_3_months_refs
      },
      "h2_2025": {
        "count": $h2_2025_count,
        "prs": $h2_2025_refs
      },
      "full_2025": {
        "count": $full_2025_count,
        "prs": $full_2025_refs
      }
    }
EOF
}

# Main execution
main() {
    # Validation phase
    if ! validate_arrays; then
        exit 1
    fi
    
    if ! check_dependencies; then
        exit 1
    fi
    
    if ! check_github_auth; then
        exit 1
    fi
    
    # Create directories
    mkdir -p "$DATA_DIR"
    mkdir -p "$DETAILS_DIR"
    
    echo "🔍 Fetching code review statistics..."
    [ "$TEST_MODE" = true ] && echo "🧪 TEST MODE - Using mock data"
    [ "$DRY_RUN" = true ] && echo "🔍 DRY RUN - No actual fetching"
    [ "$STORE_DETAILS" = true ] && echo "📋 Storing PR details for verification"
    if [ "$THROTTLE_DELAY" -gt 0 ] 2>/dev/null; then
        echo "⏱️  Throttle: ${THROTTLE_DELAY}s between users, ${PERIOD_DELAY}s between periods"
    fi
    echo "📅 Date: $(date)"
    echo "📁 Output: $OUTPUT_FILE"
    echo ""

    # Initialize JSON output
    cat > "$OUTPUT_FILE" << EOF
{
  "generated_at": "$(date -Iseconds)",
  "team": "$TEAM_NAME",
  "test_mode": $TEST_MODE,
  "include_pr_details": true,
  "periods": {
    "last_month": {"start": "$LAST_MONTH_START", "end": "$TODAY"},
    "last_3_months": {"start": "$THREE_MONTHS_START", "end": "$TODAY"},
    "h2_2025": {"start": "$H2_2025_START", "end": "$H2_2025_END"},
    "full_2025": {"start": "$FULL_2025_START", "end": "$FULL_2025_END"}
  },
  "reviews": [
EOF

    FIRST=true
    USER_COUNT=${#USERNAMES[@]}
    for i in "${!USERNAMES[@]}"; do
        user="${USERNAMES[$i]}"
        display_name="${DISPLAY_NAMES[$i]}"
        
        echo "📊 Fetching for $display_name ($user) [$(($i + 1))/$USER_COUNT]..."
        
        # Get PR details for each period with delays
        echo -n "   Last Month... "
        last_month_prs=$(get_pr_details "$user" "$LAST_MONTH_START" "$TODAY" "last_month")
        last_month_count=$(echo "$last_month_prs" | jq 'length')
        echo -n "$last_month_count"
        
        # Delay between periods
        if [ "$PERIOD_DELAY" -gt 0 ] 2>/dev/null && [ "$TEST_MODE" = false ]; then
            sleep "$PERIOD_DELAY"
        fi
        
        echo -n " | Last 3 Mo... "
        last_3_months_prs=$(get_pr_details "$user" "$THREE_MONTHS_START" "$TODAY" "last_3_months")
        last_3_months_count=$(echo "$last_3_months_prs" | jq 'length')
        echo -n "$last_3_months_count"
        
        if [ "$PERIOD_DELAY" -gt 0 ] 2>/dev/null && [ "$TEST_MODE" = false ]; then
            sleep "$PERIOD_DELAY"
        fi
        
        echo -n " | H2 2025... "
        h2_2025_prs=$(get_pr_details "$user" "$H2_2025_START" "$H2_2025_END" "h2_2025")
        h2_2025_count=$(echo "$h2_2025_prs" | jq 'length')
        echo -n "$h2_2025_count"
        
        if [ "$PERIOD_DELAY" -gt 0 ] 2>/dev/null && [ "$TEST_MODE" = false ]; then
            sleep "$PERIOD_DELAY"
        fi
        
        echo -n " | Full 2025... "
        full_2025_prs=$(get_pr_details "$user" "$FULL_2025_START" "$FULL_2025_END" "full_2025")
        full_2025_count=$(echo "$full_2025_prs" | jq 'length')
        echo "$full_2025_count"
        
        if [ "$FIRST" = true ]; then
            FIRST=false
        else
            echo "    ," >> "$OUTPUT_FILE"
        fi
        
        generate_user_json "$user" "$display_name" "$last_month_prs" "$last_3_months_prs" "$h2_2025_prs" "$full_2025_prs" >> "$OUTPUT_FILE"
        
        # Throttle between users (skip after last user)
        if [ "$THROTTLE_DELAY" -gt 0 ] 2>/dev/null && [ "$TEST_MODE" = false ] && [ $i -lt $((USER_COUNT - 1)) ]; then
            echo "   ⏳ Throttling: waiting ${THROTTLE_DELAY}s before next user..."
            sleep "$THROTTLE_DELAY"
        fi
    done

    cat >> "$OUTPUT_FILE" << EOF
  ]
}
EOF

    echo ""
    echo "✅ Done! Data saved to: $OUTPUT_FILE"
    echo ""

    # Also create/update latest symlink (skip for test mode)
    if [ "$TEST_MODE" = true ]; then
        echo "📎 Test mode: Skipping latest symlink update"
    else
        ln -sf "$OUTPUT_FILE" "$DATA_DIR/code_reviews_latest.json"
        echo "📎 Latest symlink: $DATA_DIR/code_reviews_latest.json"
    fi

    # Show details directory info
    if [ "$STORE_DETAILS" = true ] && [ "$TEST_MODE" = false ]; then
        local details_count=$(ls -1 "$DETAILS_DIR/${TIMESTAMP}_"* 2>/dev/null | wc -l | tr -d ' ')
        echo "📂 PR details saved: $DETAILS_DIR/ ($details_count files)"
    fi

    # Validate JSON
    if ! jq empty "$OUTPUT_FILE" 2>/dev/null; then
        echo "⚠️ Warning: JSON may be invalid"
        return 1
    else
        echo "✅ JSON validated"
    fi

    # Print summary table
    print_summary "$OUTPUT_FILE"
}

# Print summary table
print_summary() {
    local file="$1"
    
    echo ""
    echo "📊 Summary:"
    echo "┌────────────────────────┬────────────┬────────────┬──────────┬───────────┐"
    echo "│ Team Member            │ Last Month │ Last 3 Mo  │ H2 2025  │ Full 2025 │"
    echo "├────────────────────────┼────────────┼────────────┼──────────┼───────────┤"

    if command -v jq &> /dev/null; then
        jq -r '.reviews[] | "│ \(.display_name) \(" " * (22 - (.display_name | length)))│ \(" " * (10 - (.last_month.count | tostring | length)))\(.last_month.count) │ \(" " * (10 - (.last_3_months.count | tostring | length)))\(.last_3_months.count) │ \(" " * (8 - (.h2_2025.count | tostring | length)))\(.h2_2025.count) │ \(" " * (9 - (.full_2025.count | tostring | length)))\(.full_2025.count) │"' "$file" 2>/dev/null
    fi

    echo "└────────────────────────┴────────────┴────────────┴──────────┴───────────┘"

    # Calculate totals
    if command -v jq &> /dev/null; then
        total_last_month=$(jq '[.reviews[].last_month.count] | add' "$file")
        total_last_3_months=$(jq '[.reviews[].last_3_months.count] | add' "$file")
        total_h2_2025=$(jq '[.reviews[].h2_2025.count] | add' "$file")
        total_full_2025=$(jq '[.reviews[].full_2025.count] | add' "$file")
        echo ""
        echo "📈 Totals: Last Month: $total_last_month | Last 3 Mo: $total_last_3_months | H2 2025: $total_h2_2025 | Full 2025: $total_full_2025"
    fi
    
    # Show sample PR URLs
    echo ""
    echo "🔗 Sample PR URLs (for verification):"
    jq -r '.reviews[] | "   \(.display_name): \(.full_2025.prs[0].url // "no PRs")"' "$file" 2>/dev/null | head -3
    echo "   ..."
}

# Export functions for testing
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi
