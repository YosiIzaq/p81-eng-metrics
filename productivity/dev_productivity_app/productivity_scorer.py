#!/usr/bin/env python3
"""
Productivity Scorer CLI - Team productivity scoring tool.

Usage:
    python productivity_scorer.py fetch --period sprint --config config.json
    python productivity_scorer.py score --data raw.json --config config.json
    python productivity_scorer.py display --type bar --data scores.json
    python productivity_scorer.py run --period sprint --output report.md
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fetchers.base_fetcher import (
    TeamMember, Period, MetricData, 
    load_config, validate_config, load_team_members, ConfigError
)
from fetchers.github_fetcher import GitHubFetcher
from fetchers.jira_fetcher import JiraFetcher
from calculator.score_calculator import calculate_scores, rank_scores
from display.charts import create_bar_chart, create_ranking_chart
from display.tables import create_ranking_table, create_markdown_table, print_ranking_table


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command line arguments.
    
    Args:
        args: List of arguments (defaults to sys.argv[1:])
        
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Team Productivity Scoring Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch raw data from Jira and GitHub")
    fetch_parser.add_argument("--period", default="sprint", help="Period name from config")
    fetch_parser.add_argument("--config", default="config/default_config.json", help="Config file path")
    fetch_parser.add_argument("--output", help="Output file path for raw data")
    fetch_parser.add_argument("--test", action="store_true", help="Use mock data instead of API calls")
    
    # Score command
    score_parser = subparsers.add_parser("score", help="Calculate scores from raw data")
    score_parser.add_argument("--data", required=True, help="Raw data JSON file")
    score_parser.add_argument("--config", default="config/default_config.json", help="Config file path")
    score_parser.add_argument("--output", help="Output file path for scores")
    
    # Display command
    display_parser = subparsers.add_parser("display", help="Display scores as charts or tables")
    display_parser.add_argument("--type", choices=["bar", "ranking", "trend", "table"], default="table")
    display_parser.add_argument("--data", required=True, help="Scores JSON file")
    display_parser.add_argument("--output", help="Output file path for chart")
    
    # Run command (all-in-one)
    run_parser = subparsers.add_parser("run", help="Fetch, score, and display in one command")
    run_parser.add_argument("--period", default="sprint", help="Period name from config")
    run_parser.add_argument("--config", default="config/default_config.json", help="Config file path")
    run_parser.add_argument("--output", help="Output markdown report path")
    run_parser.add_argument("--test", action="store_true", help="Use mock data instead of API calls")
    
    return parser.parse_args(args)


def load_cli_config(config_path: Optional[str]) -> Dict[str, Any]:
    """Load configuration for CLI.
    
    Args:
        config_path: Path to config file, or None for default
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        # Try default config
        default_path = Path(__file__).parent / "config" / "default_config.json"
        if default_path.exists():
            config_path = str(default_path)
        else:
            raise ConfigError("No config file specified and default not found")
    
    return load_config(config_path)


def run_fetch(
    config: Dict[str, Any],
    period: str = "sprint",
    test_mode: bool = False,
    output_dir: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Run the fetch command.
    
    Args:
        config: Configuration dictionary
        period: Period name to fetch
        test_mode: If True, use mock data
        output_dir: Directory to save raw data
        
    Returns:
        Raw data dictionary
    """
    # Get period config
    periods_config = config.get("periods", {})
    if period not in periods_config:
        print(f"Error: Period '{period}' not found in config")
        return None
    
    period_config = periods_config[period]
    period_obj = Period.from_config(period, period_config)
    
    # Get team members
    members = load_team_members(config)
    
    if not members:
        print("Warning: No team members configured")
        return {"metrics": {}}
    
    # Initialize fetchers
    jira_config = config.get("jira", {})
    jira_fetcher = JiraFetcher(
        project=jira_config.get("project", "P81"),
        done_statuses=jira_config.get("done_statuses", ["Done"]),
        cloud_id=jira_config.get("cloud_id"),
        test_mode=test_mode
    )
    
    github_fetcher = GitHubFetcher(
        org=config.get("github", {}).get("org"),
        test_mode=test_mode
    )
    
    # Fetch data for each member
    metrics = {}
    
    for member in members:
        print(f"Fetching data for {member.name}...")
        
        # Fetch from Jira
        jira_data = jira_fetcher.fetch(member, period_obj)
        
        # Fetch from GitHub
        github_data = github_fetcher.fetch(member, period_obj)
        
        # Merge data
        metrics[member.name] = {
            "items_completed": jira_data.items_completed,
            "story_points": jira_data.story_points,
            "prs_authored": github_data.prs_authored,
            "code_reviews": github_data.code_reviews
        }
    
    # Build raw data
    raw_data = {
        "generated_at": datetime.now().isoformat(),
        "config_version": config.get("version", "1.0"),
        "period": {
            "name": period,
            "start": period_obj.start_date.isoformat(),
            "end": period_obj.end_date.isoformat()
        },
        "metrics": metrics
    }
    
    # Save to file if requested
    if output_dir:
        output_path = Path(output_dir) / f"raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(raw_data, f, indent=2)
        print(f"Saved raw data to {output_path}")
    
    return raw_data


def run_score(
    raw_data: Dict[str, Any],
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """Run the score command.
    
    Args:
        raw_data: Raw metrics data
        config: Configuration with weights
        
    Returns:
        Scores dictionary
    """
    return calculate_scores(raw_data, config)


def run_display(
    scores: Dict[str, Any],
    display_type: str = "table",
    output_path: Optional[str] = None
) -> None:
    """Run the display command.
    
    Args:
        scores: Calculated scores
        display_type: Type of display (bar, ranking, trend, table)
        output_path: Path to save output
    """
    ranked = rank_scores(scores)
    
    if display_type == "bar":
        create_bar_chart(scores, save_path=output_path)
        if output_path:
            print(f"Saved bar chart to {output_path}")
    
    elif display_type == "ranking":
        create_ranking_chart(ranked, save_path=output_path)
        if output_path:
            print(f"Saved ranking chart to {output_path}")
    
    elif display_type == "table":
        print_ranking_table(ranked)
    
    else:
        print_ranking_table(ranked)


def run_full_pipeline(
    config: Dict[str, Any],
    period: str = "sprint",
    test_mode: bool = False,
    output_dir: Optional[str] = None,
    output_file: Optional[str] = None
) -> Dict[str, Any]:
    """Run the full fetch-score-display pipeline.
    
    Args:
        config: Configuration dictionary
        period: Period name
        test_mode: If True, use mock data
        output_dir: Directory for intermediate files
        output_file: Path for final markdown report
        
    Returns:
        Results dictionary with raw_data, scores, and ranked
    """
    # Get period details for display
    periods_config = config.get("periods", {})
    period_config = periods_config.get(period, {})
    period_label = period_config.get("label", period)
    period_start = period_config.get("start", "N/A")
    period_end = period_config.get("end", "N/A")
    
    # Fetch
    print(f"\n=== Fetching data for period: {period_label} ===")
    print(f"    Date range: {period_start} to {period_end}")
    raw_data = run_fetch(config, period, test_mode, output_dir)
    
    if raw_data is None:
        return {"error": "Fetch failed"}
    
    # Score
    print("\n=== Calculating scores ===")
    scores = run_score(raw_data, config)
    ranked = rank_scores(scores)
    
    # Display
    print("\n=== Results ===")
    print_ranking_table(ranked, title=f"Productivity Rankings - {period_label}")
    
    # Generate markdown report
    if output_file:
        generate_markdown_report(raw_data, scores, ranked, output_file, config, period)
    
    return {
        "raw_data": raw_data,
        "scores": scores,
        "ranked": ranked
    }


def generate_markdown_report(
    raw_data: Dict[str, Any],
    scores: Dict[str, Any],
    ranked: List[Dict[str, Any]],
    output_path: str,
    config: Dict[str, Any],
    period: str
) -> None:
    """Generate a markdown report file.
    
    Args:
        raw_data: Raw metrics data
        scores: Calculated scores
        ranked: Ranked list
        output_path: Path to save report
        config: Configuration
        period: Period name
    """
    period_info = raw_data.get("period", {})
    team_name = config.get("team", {}).get("name", "Team")
    
    lines = [
        f"# {team_name} Productivity Report",
        "",
        f"**Period:** {period}",
        f"**Start:** {period_info.get('start', 'N/A')}",
        f"**End:** {period_info.get('end', 'N/A')}",
        f"**Generated:** {raw_data.get('generated_at', 'N/A')}",
        "",
        "---",
        "",
        "## Rankings",
        "",
        create_markdown_table(ranked),
        "",
        "---",
        "",
        "## Formula",
        "",
        "```",
        "Productivity Score = (Items × 0.50) + (PRs × 0.30) + (Reviews × 0.20)",
        "```",
        "",
        "Each component normalized to 0-100 scale relative to team maximum.",
        ""
    ]
    
    Path(output_path).write_text("\n".join(lines))
    print(f"\nSaved report to {output_path}")


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.command is None:
        print("Error: No command specified. Use --help for usage.")
        sys.exit(1)
    
    try:
        config = load_cli_config(getattr(args, 'config', None))
        
        if args.command == "fetch":
            run_fetch(config, args.period, args.test, 
                     output_dir=Path(args.output).parent if args.output else None)
        
        elif args.command == "score":
            with open(args.data, "r") as f:
                raw_data = json.load(f)
            scores = run_score(raw_data, config)
            ranked = rank_scores(scores)
            print_ranking_table(ranked)
        
        elif args.command == "display":
            with open(args.data, "r") as f:
                scores = json.load(f)
            run_display(scores, args.type, args.output)
        
        elif args.command == "run":
            run_full_pipeline(
                config, 
                args.period, 
                args.test,
                output_dir=Path(args.output).parent if args.output else None,
                output_file=args.output
            )
    
    except ConfigError as e:
        print(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
