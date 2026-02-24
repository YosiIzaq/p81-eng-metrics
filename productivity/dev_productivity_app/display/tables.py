"""Table generation for terminal and markdown output."""
from typing import Dict, Any, List, Optional


def create_ranking_table(
    ranked_data: List[Dict[str, Any]],
    precision: int = 1
) -> str:
    """Create a text table showing rankings.
    
    Args:
        ranked_data: List of ranked team members
        precision: Decimal precision for numbers
        
    Returns:
        Formatted table string
    """
    if not ranked_data:
        return ""
    
    # Column widths
    rank_w = 4
    name_w = max(len(d["name"]) for d in ranked_data) + 2
    score_w = 8
    
    # Header
    header = (
        f"{'Rank':<{rank_w}} "
        f"{'Name':<{name_w}} "
        f"{'Items':<{score_w}} "
        f"{'PRs':<{score_w}} "
        f"{'Reviews':<{score_w}} "
        f"{'Total':<{score_w}}"
    )
    
    separator = "-" * len(header)
    
    lines = [header, separator]
    
    for d in ranked_data:
        items = d.get("items_weighted", 0)
        prs = d.get("prs_weighted", 0)
        reviews = d.get("reviews_weighted", 0)
        total = d.get("total", 0)
        
        line = (
            f"{d['rank']:<{rank_w}} "
            f"{d['name']:<{name_w}} "
            f"{items:<{score_w}.{precision}f} "
            f"{prs:<{score_w}.{precision}f} "
            f"{reviews:<{score_w}.{precision}f} "
            f"{total:<{score_w}.{precision}f}"
        )
        lines.append(line)
    
    return "\n".join(lines)


def create_markdown_table(
    ranked_data: List[Dict[str, Any]],
    precision: int = 1
) -> str:
    """Create a markdown format table.
    
    Args:
        ranked_data: List of ranked team members
        precision: Decimal precision for numbers
        
    Returns:
        Markdown table string
    """
    if not ranked_data:
        return ""
    
    # Header
    header = "| Rank | Name | Items (50%) | PRs (30%) | Reviews (20%) | **Total** |"
    separator = "|:----:|------|:-----------:|:---------:|:-------------:|:---------:|"
    
    lines = [header, separator]
    
    for d in ranked_data:
        items = d.get("items_weighted", 0)
        prs = d.get("prs_weighted", 0)
        reviews = d.get("reviews_weighted", 0)
        total = d.get("total", 0)
        
        line = (
            f"| {d['rank']} "
            f"| {d['name']} "
            f"| {items:.{precision}f} "
            f"| {prs:.{precision}f} "
            f"| {reviews:.{precision}f} "
            f"| **{total:.{precision}f}** |"
        )
        lines.append(line)
    
    return "\n".join(lines)


def print_ranking_table(
    ranked_data: List[Dict[str, Any]],
    title: Optional[str] = None,
    precision: int = 1
) -> None:
    """Print ranking table to stdout.
    
    Args:
        ranked_data: List of ranked team members
        title: Optional title to print above table
        precision: Decimal precision for numbers
    """
    if title:
        print(f"\n{title}")
        print("=" * len(title))
    
    table = create_ranking_table(ranked_data, precision)
    print(table)


def create_summary_table(raw_data: Dict[str, Any]) -> str:
    """Create a summary statistics table.
    
    Args:
        raw_data: Raw metrics data
        
    Returns:
        Formatted summary table string
    """
    metrics = raw_data.get("metrics", {})
    
    if not metrics:
        return "No data available"
    
    # Calculate totals and averages
    total_items = sum(m.get("items_completed", 0) for m in metrics.values())
    total_prs = sum(m.get("prs_authored", 0) for m in metrics.values())
    total_reviews = sum(m.get("code_reviews", 0) for m in metrics.values())
    
    num_members = len(metrics)
    avg_items = total_items / num_members if num_members else 0
    avg_prs = total_prs / num_members if num_members else 0
    avg_reviews = total_reviews / num_members if num_members else 0
    
    # Build table
    name_w = max(len(name) for name in metrics.keys()) + 2
    num_w = 10
    
    header = (
        f"{'Name':<{name_w}} "
        f"{'Items':<{num_w}} "
        f"{'PRs':<{num_w}} "
        f"{'Reviews':<{num_w}}"
    )
    separator = "-" * len(header)
    
    lines = [header, separator]
    
    for name, data in metrics.items():
        items = data.get("items_completed", 0)
        prs = data.get("prs_authored", 0)
        reviews = data.get("code_reviews", 0)
        
        line = (
            f"{name:<{name_w}} "
            f"{items:<{num_w}} "
            f"{prs:<{num_w}} "
            f"{reviews:<{num_w}}"
        )
        lines.append(line)
    
    lines.append(separator)
    
    # Totals row
    totals_line = (
        f"{'TOTAL':<{name_w}} "
        f"{total_items:<{num_w}} "
        f"{total_prs:<{num_w}} "
        f"{total_reviews:<{num_w}}"
    )
    lines.append(totals_line)
    
    # Averages row
    avg_line = (
        f"{'AVG':<{name_w}} "
        f"{avg_items:<{num_w}.1f} "
        f"{avg_prs:<{num_w}.1f} "
        f"{avg_reviews:<{num_w}.1f}"
    )
    lines.append(avg_line)
    
    return "\n".join(lines)
