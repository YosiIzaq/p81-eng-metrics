#!/usr/bin/env python3
"""
MCP Data Fetcher Helper

This script is designed to be used with data fetched via MCP (Model Context Protocol).
Since MCP runs in the agent context (Claude/Cursor), this script processes pre-fetched data.

Usage:
1. Agent fetches Jira data via MCP and saves to JSON
2. This script processes that JSON alongside GitHub data

Example workflow:
    # Agent runs MCP query and saves result:
    # CallMcpTool(searchJiraIssuesUsingJql, {jql: "...", cloudId: "..."})
    # Agent saves result to: data/jira_raw.json
    
    # Then run:
    python fetch_via_mcp.py --jira-data data/jira_raw.json --period sprint
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fetchers.base_fetcher import (
    TeamMember, Period, MetricData,
    load_config, load_team_members
)
from fetchers.github_fetcher import GitHubFetcher
from calculator.score_calculator import calculate_scores, rank_scores
from display.tables import print_ranking_table, create_markdown_table


def parse_mcp_jira_response(mcp_response: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Parse MCP Jira response into per-member metrics.
    
    Args:
        mcp_response: Raw MCP response containing issues
        
    Returns:
        Dict mapping member names to their metrics
    """
    issues = mcp_response.get("issues", [])
    
    # Group by assignee
    by_assignee: Dict[str, List[Dict]] = {}
    for issue in issues:
        fields = issue.get("fields", {})
        assignee = fields.get("assignee", {})
        if assignee:
            account_id = assignee.get("accountId", "unknown")
            display_name = assignee.get("displayName", "Unknown")
            
            key = f"{display_name}|{account_id}"
            if key not in by_assignee:
                by_assignee[key] = []
            by_assignee[key].append(issue)
    
    # Calculate metrics per member
    metrics = {}
    for key, member_issues in by_assignee.items():
        display_name = key.split("|")[0]
        
        items_completed = len(member_issues)
        story_points = 0
        
        for issue in member_issues:
            fields = issue.get("fields", {})
            # Try common story points field names
            sp = fields.get("customfield_10016") or fields.get("storyPoints") or 0
            if sp:
                story_points += int(sp)
        
        metrics[display_name] = {
            "items_completed": items_completed,
            "story_points": story_points
        }
    
    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="Process MCP-fetched Jira data with GitHub data"
    )
    parser.add_argument("--jira-data", required=True, help="Path to MCP Jira JSON response")
    parser.add_argument("--config", default="config/default_config.json", help="Config file")
    parser.add_argument("--period", default="sprint", help="Period name")
    parser.add_argument("--output", help="Output markdown report path")
    
    args = parser.parse_args()
    
    # Load config
    config = load_config(args.config)
    members = load_team_members(config)
    
    # Load MCP Jira data
    with open(args.jira_data, "r") as f:
        mcp_response = json.load(f)
    
    jira_metrics = parse_mcp_jira_response(mcp_response)
    
    # Get period for GitHub fetching
    periods_config = config.get("periods", {})
    period_config = periods_config.get(args.period, {})
    period_label = period_config.get("label", args.period)
    period_obj = Period.from_config(args.period, period_config)
    
    print(f"\n=== Processing data for period: {period_label} ===")
    print(f"    Date range: {period_obj.start_date} to {period_obj.end_date}")
    
    # Fetch GitHub data
    github_fetcher = GitHubFetcher(
        org=config.get("github", {}).get("org"),
        test_mode=False
    )
    
    # Combine metrics
    metrics = {}
    for member in members:
        print(f"Processing {member.name}...")
        
        # Get Jira metrics from MCP data
        jira_data = jira_metrics.get(member.name, {"items_completed": 0, "story_points": 0})
        
        # Fetch GitHub metrics
        github_data = github_fetcher.fetch(member, period_obj)
        
        metrics[member.name] = {
            "items_completed": jira_data.get("items_completed", 0),
            "story_points": jira_data.get("story_points", 0),
            "prs_authored": github_data.prs_authored,
            "code_reviews": github_data.code_reviews
        }
    
    # Build raw data structure
    raw_data = {
        "generated_at": datetime.now().isoformat(),
        "period": {
            "name": args.period,
            "label": period_label,
            "start": period_obj.start_date.isoformat(),
            "end": period_obj.end_date.isoformat()
        },
        "metrics": metrics
    }
    
    # Calculate scores
    print("\n=== Calculating scores ===")
    scores = calculate_scores(raw_data, config)
    ranked = rank_scores(scores)
    
    # Display
    print("\n=== Results ===")
    print_ranking_table(ranked, title=f"Productivity Rankings - {period_label}")
    
    # Save report if requested
    if args.output:
        lines = [
            f"# {config.get('team', {}).get('name', 'Team')} Productivity Report",
            "",
            f"**Period:** {period_label}",
            f"**Date Range:** {period_obj.start_date} to {period_obj.end_date}",
            f"**Generated:** {datetime.now().isoformat()}",
            "",
            "---",
            "",
            "## Rankings",
            "",
            create_markdown_table(ranked),
            "",
        ]
        Path(args.output).write_text("\n".join(lines))
        print(f"\nSaved report to {args.output}")


if __name__ == "__main__":
    main()
