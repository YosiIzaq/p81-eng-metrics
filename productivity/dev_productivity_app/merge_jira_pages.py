#!/usr/bin/env python3
"""Merge multiple Jira JSON page files into a single file."""

import json
import sys
from pathlib import Path


def merge_jira_pages(data_dir: str, output_file: str):
    """Merge all jira_year_page*.json files into one."""
    data_path = Path(data_dir)
    
    all_issues = []
    
    # Find all page files
    page_files = sorted(data_path.glob("jira_year_page*.json"))
    
    print(f"Found {len(page_files)} page files")
    
    for page_file in page_files:
        print(f"  Processing {page_file.name}...")
        with open(page_file, "r") as f:
            data = json.load(f)
            issues = data.get("issues", [])
            all_issues.extend(issues)
            print(f"    Added {len(issues)} issues (total: {len(all_issues)})")
    
    # Also check for jira_raw.json (sprint data)
    raw_file = data_path / "jira_raw.json"
    if raw_file.exists():
        print(f"  Processing {raw_file.name}...")
        with open(raw_file, "r") as f:
            data = json.load(f)
            # Don't add if already merged from year pages
            # Just note it
            print(f"    (Sprint data available: {len(data.get('issues', []))} issues)")
    
    # Create merged output
    merged = {
        "issues": all_issues,
        "total_count": len(all_issues),
        "merged_from": [f.name for f in page_files]
    }
    
    output_path = data_path / output_file
    with open(output_path, "w") as f:
        json.dump(merged, f, indent=2)
    
    print(f"\nMerged {len(all_issues)} issues to {output_path}")
    
    # Print breakdown by assignee
    by_assignee = {}
    for issue in all_issues:
        assignee = issue.get("fields", {}).get("assignee", {})
        if assignee:
            name = assignee.get("displayName", "Unknown")
            by_assignee[name] = by_assignee.get(name, 0) + 1
    
    print("\nBreakdown by assignee:")
    for name, count in sorted(by_assignee.items(), key=lambda x: -x[1]):
        print(f"  {name}: {count}")


if __name__ == "__main__":
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "data"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "jira_year_merged.json"
    merge_jira_pages(data_dir, output_file)
