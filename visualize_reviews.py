#!/usr/bin/env python3
"""
Code Review Statistics Visualization

Usage:
    python visualize_reviews.py                          # Show all graphs
    python visualize_reviews.py --period full_2025       # Specific period
    python visualize_reviews.py --start 2025-06-01 --end 2025-12-31  # Custom range
    python visualize_reviews.py --fetch                  # Fetch fresh data first
    python visualize_reviews.py --export png             # Export as PNG

Configuration:
    Requires team_config.json in the same directory. Copy team_config.example.json
    and fill in your team's GitHub usernames, display names, and optional colors.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
except ImportError:
    print("❌ Missing dependencies. Install with:")
    print("   pip install matplotlib numpy")
    sys.exit(1)

# Configuration
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
LATEST_DATA = DATA_DIR / "code_reviews_latest.json"
CONFIG_FILE = SCRIPT_DIR / "team_config.json"

# Default matplotlib color cycle for teams without custom colors
DEFAULT_COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
]


def load_team_config() -> tuple[dict, dict, str]:
    """
    Load team configuration from team_config.json.
    
    Returns:
        tuple: (TEAM_MEMBERS dict, COLORS dict, TEAM_NAME str)
    """
    if not CONFIG_FILE.exists():
        print(f"❌ Error: Team configuration file not found: {CONFIG_FILE}")
        print()
        print("To set up:")
        print("  1. Copy team_config.example.json to team_config.json")
        print("  2. Fill in your team's GitHub usernames and display names")
        print()
        print("Example:")
        print("  cp team_config.example.json team_config.json")
        print("  # Edit team_config.json with your team's info")
        sys.exit(1)
    
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    
    team_name = config.get("team_name", "Team")
    members = config.get("members", [])
    
    if not members:
        print(f"❌ Error: No team members defined in {CONFIG_FILE}")
        sys.exit(1)
    
    team_members = {}
    colors = {}
    
    for i, member in enumerate(members):
        username = member.get("github_username")
        display_name = member.get("display_name", username)
        color = member.get("color", DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
        
        if username:
            team_members[username] = display_name
            colors[username] = color
    
    return team_members, colors, team_name


# Load configuration at module level
TEAM_MEMBERS, COLORS, TEAM_NAME = load_team_config()


def fetch_fresh_data():
    """Run the shell script to fetch fresh data."""
    print("🔄 Fetching fresh data...")
    script = SCRIPT_DIR / "fetch_code_reviews.sh"
    if not script.exists():
        print(f"❌ Script not found: {script}")
        return False
    
    result = subprocess.run(["bash", str(script)], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Error fetching data: {result.stderr}")
        return False
    
    print(result.stdout)
    return True


def get_count(review: dict, period: str) -> int:
    """
    Get count from review data, handling both old and new formats.
    
    Old format: {"full_2025": 100}
    New format: {"full_2025": {"count": 100, "prs": [...]}}
    """
    value = review.get(period, 0)
    if isinstance(value, dict):
        return value.get("count", 0)
    elif isinstance(value, int):
        return value
    return 0


def get_prs(review: dict, period: str) -> list:
    """Get PR list from review data (new format only)."""
    value = review.get(period, {})
    if isinstance(value, dict):
        return value.get("prs", [])
    return []


def load_data():
    """Load the latest data file."""
    if not LATEST_DATA.exists():
        print(f"❌ No data file found at {LATEST_DATA}")
        print("   Run: ./fetch_code_reviews.sh first")
        return None
    
    with open(LATEST_DATA) as f:
        return json.load(f)


def fetch_detailed_data(start_date: str, end_date: str) -> dict:
    """Fetch detailed PR review data for a custom date range."""
    print(f"🔍 Fetching detailed data from {start_date} to {end_date}...")
    
    results = {}
    for username, display_name in TEAM_MEMBERS.items():
        print(f"   📊 {display_name}...", end=" ", flush=True)
        
        try:
            cmd = [
                "gh", "search", "prs",
                f"--reviewed-by={username}",
                f"--created={start_date}..{end_date}",
                "--limit=500",
                "--json", "number,title,repository,createdAt,closedAt"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                prs = json.loads(result.stdout)
                results[username] = {
                    "display_name": display_name,
                    "count": len(prs),
                    "prs": prs
                }
                print(f"{len(prs)} reviews")
            else:
                results[username] = {"display_name": display_name, "count": 0, "prs": []}
                print("0 reviews")
        except Exception as e:
            print(f"error: {e}")
            results[username] = {"display_name": display_name, "count": 0, "prs": []}
    
    return results


def plot_bar_chart(data: dict, period: str = "full_2025", save_path: str = None):
    """Create a bar chart for code reviews by team member."""
    if data is None:
        print("⚠️ No data to display")
        return
    
    reviews = data.get("reviews", [])
    
    if not reviews:
        print("⚠️ No reviews data to display")
        return
    
    names = [r["display_name"] for r in reviews]
    counts = [get_count(r, period) for r in reviews]
    colors = [COLORS.get(r.get("github_username", ""), "#333333") for r in reviews]
    
    # Sort by count descending
    sorted_data = sorted(zip(names, counts, colors), key=lambda x: x[1], reverse=True)
    names, counts, colors = zip(*sorted_data)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(names, counts, color=colors, edgecolor='black', linewidth=0.5)
    
    # Add value labels on bars
    for bar, count in zip(bars, counts):
        height = bar.get_height()
        ax.annotate(f'{count}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    period_labels = {
        "last_month": "Last Month",
        "last_3_months": "Last 3 Months",
        "h2_2025": "H2 2025 (Jun-Dec)",
        "full_2025": "Full Year 2025"
    }
    
    ax.set_xlabel('Team Member', fontsize=12)
    ax.set_ylabel('Number of Code Reviews', fontsize=12)
    ax.set_title(f'Code Reviews by Team Member - {period_labels.get(period, period)}', fontsize=14, fontweight='bold')
    ax.set_xticklabels(names, rotation=15, ha='right')
    
    # Add total
    total = sum(counts)
    ax.text(0.98, 0.98, f'Total: {total}', transform=ax.transAxes, 
            ha='right', va='top', fontsize=11, 
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"📊 Saved: {save_path}")
    else:
        plt.show()
    
    plt.close()


def plot_pie_chart(data: dict, period: str = "full_2025", save_path: str = None):
    """Create a pie chart showing distribution of code reviews."""
    if data is None:
        print("⚠️ No data to display")
        return
    
    reviews = data.get("reviews", [])
    
    names = [r["display_name"] for r in reviews]
    counts = [get_count(r, period) for r in reviews]
    colors = [COLORS.get(r.get("github_username", ""), "#333333") for r in reviews]
    
    # Filter out zeros
    filtered = [(n, c, col) for n, c, col in zip(names, counts, colors) if c > 0]
    if not filtered:
        print("⚠️ No data to display")
        return
    
    names, counts, colors = zip(*filtered)
    total = sum(counts)
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    wedges, texts, autotexts = ax.pie(
        counts,
        labels=names,
        colors=colors,
        autopct=lambda pct: f'{pct:.1f}%\n({int(pct/100*total)})',
        startangle=90,
        explode=[0.02] * len(counts),
        shadow=True
    )
    
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_fontweight('bold')
    
    period_labels = {
        "last_month": "Last Month",
        "last_3_months": "Last 3 Months",
        "h2_2025": "H2 2025 (Jun-Dec)",
        "full_2025": "Full Year 2025"
    }
    
    ax.set_title(f'Code Review Distribution - {period_labels.get(period, period)}\n(Total: {total})', 
                 fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"📊 Saved: {save_path}")
    else:
        plt.show()
    
    plt.close()


def plot_comparison(data: dict, save_path: str = None):
    """Create a grouped bar chart comparing all periods."""
    if data is None:
        print("⚠️ No data to display")
        return
    
    reviews = data.get("reviews", [])
    
    if not reviews:
        print("⚠️ No reviews data to display")
        return
    
    periods = ["last_month", "last_3_months", "h2_2025", "full_2025"]
    period_labels = ["Last Month", "Last 3 Mo", "H2 2025", "Full 2025"]
    
    names = [r["display_name"].split()[0] for r in reviews]  # First name only
    
    x = np.arange(len(names))
    width = 0.2
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    for i, (period, label) in enumerate(zip(periods, period_labels)):
        counts = [get_count(r, period) for r in reviews]
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, counts, width, label=label, alpha=0.8)
        
        # Add value labels
        for bar, count in zip(bars, counts):
            if count > 0:
                ax.annotate(f'{count}',
                            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                            xytext=(0, 2),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8)
    
    ax.set_xlabel('Team Member', fontsize=12)
    ax.set_ylabel('Number of Code Reviews', fontsize=12)
    ax.set_title('Code Reviews Comparison Across Periods', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(names)
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"📊 Saved: {save_path}")
    else:
        plt.show()
    
    plt.close()


def print_summary_table(data: dict):
    """Print a summary table to console."""
    if data is None:
        print("⚠️ No data to display")
        return
    
    reviews = data.get("reviews", [])
    
    print("\n" + "="*80)
    print(f"CODE REVIEW STATISTICS - {TEAM_NAME.upper()}")
    print("="*80)
    print(f"Generated: {data.get('generated_at', 'Unknown')}")
    print("-"*80)
    print(f"{'Team Member':<22} {'Last Month':>12} {'Last 3 Mo':>12} {'H2 2025':>10} {'Full 2025':>11}")
    print("-"*80)
    
    totals = {"last_month": 0, "last_3_months": 0, "h2_2025": 0, "full_2025": 0}
    
    for r in reviews:
        lm = get_count(r, 'last_month')
        l3m = get_count(r, 'last_3_months')
        h2 = get_count(r, 'h2_2025')
        full = get_count(r, 'full_2025')
        print(f"{r['display_name']:<22} {lm:>12} {l3m:>12} {h2:>10} {full:>11}")
        totals['last_month'] += lm
        totals['last_3_months'] += l3m
        totals['h2_2025'] += h2
        totals['full_2025'] += full
    
    print("-"*80)
    print(f"{'TOTAL':<22} {totals['last_month']:>12} {totals['last_3_months']:>12} "
          f"{totals['h2_2025']:>10} {totals['full_2025']:>11}")
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Visualize code review statistics")
    parser.add_argument("--fetch", action="store_true", help="Fetch fresh data first")
    parser.add_argument("--period", choices=["last_month", "last_3_months", "h2_2025", "full_2025"],
                        default="full_2025", help="Period to display")
    parser.add_argument("--start", help="Custom start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="Custom end date (YYYY-MM-DD)")
    parser.add_argument("--export", choices=["png", "pdf"], help="Export format")
    parser.add_argument("--no-show", action="store_true", help="Don't show plots (for export only)")
    parser.add_argument("--chart", choices=["bar", "pie", "comparison", "all"], default="all",
                        help="Chart type to display")
    
    args = parser.parse_args()
    
    # Fetch fresh data if requested
    if args.fetch:
        if not fetch_fresh_data():
            sys.exit(1)
    
    # Load data
    data = load_data()
    if not data:
        print("💡 Tip: Run with --fetch to get fresh data")
        sys.exit(1)
    
    # Print summary table
    print_summary_table(data)
    
    # Determine output path
    output_dir = DATA_DIR / "charts"
    output_dir.mkdir(exist_ok=True)
    
    suffix = f".{args.export}" if args.export else None
    
    # Generate charts
    if args.chart in ["bar", "all"]:
        save_path = str(output_dir / f"bar_{args.period}{suffix}") if suffix else None
        plot_bar_chart(data, args.period, save_path)
    
    if args.chart in ["pie", "all"]:
        save_path = str(output_dir / f"pie_{args.period}{suffix}") if suffix else None
        plot_pie_chart(data, args.period, save_path)
    
    if args.chart in ["comparison", "all"]:
        save_path = str(output_dir / f"comparison{suffix}") if suffix else None
        plot_comparison(data, save_path)
    
    if args.export:
        print(f"\n✅ Charts exported to: {output_dir}/")


if __name__ == "__main__":
    main()
