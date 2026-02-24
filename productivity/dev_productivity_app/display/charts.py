"""Chart generation for productivity visualization using matplotlib."""
from typing import Dict, Any, List, Optional
import hashlib

try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# Color palette for team members
TEAM_COLORS = [
    "#1f77b4",  # Blue
    "#ff7f0e",  # Orange
    "#2ca02c",  # Green
    "#d62728",  # Red
    "#9467bd",  # Purple
    "#8c564b",  # Brown
    "#e377c2",  # Pink
    "#7f7f7f",  # Gray
    "#bcbd22",  # Olive
    "#17becf",  # Cyan
]

# Component colors for stacked charts
COMPONENT_COLORS = {
    "items": "#4CAF50",    # Green
    "prs": "#2196F3",      # Blue
    "reviews": "#FF9800",  # Orange
}


def get_member_color(name: str) -> str:
    """Get a consistent color for a team member.
    
    Args:
        name: Team member name
        
    Returns:
        Hex color string
    """
    # Use hash to get consistent color for same name
    hash_val = int(hashlib.md5(name.encode()).hexdigest(), 16)
    color_index = hash_val % len(TEAM_COLORS)
    return TEAM_COLORS[color_index]


def create_bar_chart(
    scores: Dict[str, Any],
    save_path: Optional[str] = None,
    title: str = "Team Productivity Scores"
) -> Optional[Any]:
    """Create a stacked bar chart showing score components.
    
    Args:
        scores: Dictionary of scores per team member
        save_path: Optional path to save the chart
        title: Chart title
        
    Returns:
        matplotlib Figure object, or None if no data
    """
    if not scores:
        return None
    
    if not MATPLOTLIB_AVAILABLE:
        print("Warning: matplotlib not available")
        return None
    
    names = list(scores.keys())
    items_data = [s.get("items_weighted", 0) for s in scores.values()]
    prs_data = [s.get("prs_weighted", 0) for s in scores.values()]
    reviews_data = [s.get("reviews_weighted", 0) for s in scores.values()]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(len(names))
    width = 0.6
    
    # Stacked bars
    bars1 = ax.bar(x, items_data, width, label='Items (50%)', color=COMPONENT_COLORS["items"])
    bars2 = ax.bar(x, prs_data, width, bottom=items_data, label='PRs (30%)', color=COMPONENT_COLORS["prs"])
    bars3 = ax.bar(x, reviews_data, width, bottom=np.array(items_data) + np.array(prs_data),
                   label='Reviews (20%)', color=COMPONENT_COLORS["reviews"])
    
    ax.set_xlabel('Team Member')
    ax.set_ylabel('Score')
    ax.set_title(title)
    plt.title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=45, ha='right')
    ax.legend()
    plt.legend()
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.close()
    
    return fig


def create_ranking_chart(
    ranked_data: List[Dict[str, Any]],
    save_path: Optional[str] = None,
    title: str = "Productivity Rankings"
) -> Optional[Any]:
    """Create a horizontal bar chart showing rankings.
    
    Args:
        ranked_data: List of ranked team members
        save_path: Optional path to save the chart
        title: Chart title
        
    Returns:
        matplotlib Figure object, or None if no data
    """
    if not ranked_data:
        return None
    
    if not MATPLOTLIB_AVAILABLE:
        print("Warning: matplotlib not available")
        return None
    
    # Sort by rank (ascending) for display
    sorted_data = sorted(ranked_data, key=lambda x: x["rank"])
    
    names = [f"#{d['rank']} {d['name']}" for d in sorted_data]
    totals = [d["total"] for d in sorted_data]
    colors = [get_member_color(d["name"]) for d in sorted_data]
    
    fig, ax = plt.subplots(figsize=(10, max(4, len(names) * 0.5)))
    
    y_pos = np.arange(len(names))
    bars = ax.barh(y_pos, totals, color=colors)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names)
    ax.invert_yaxis()  # Top rank at top
    ax.set_xlabel('Total Score')
    ax.set_title(title)
    
    # Add value labels on bars
    for i, (bar, total) in enumerate(zip(bars, totals)):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2,
                f'{total:.1f}', va='center', fontsize=9)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.close()
    
    return fig


def create_trend_chart(
    trend_data: Dict[str, List[float]],
    periods: List[str],
    save_path: Optional[str] = None,
    title: str = "Productivity Trend"
) -> Optional[Any]:
    """Create a line chart showing score trends over time.
    
    Args:
        trend_data: Dictionary mapping names to list of scores
        periods: List of period labels (x-axis)
        save_path: Optional path to save the chart
        title: Chart title
        
    Returns:
        matplotlib Figure object, or None if no data
    """
    if not trend_data or not periods:
        return None
    
    if not MATPLOTLIB_AVAILABLE:
        print("Warning: matplotlib not available")
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    for name, scores in trend_data.items():
        color = get_member_color(name)
        ax.plot(periods, scores, marker='o', label=name, color=color, linewidth=2)
    
    ax.set_xlabel('Period')
    ax.set_ylabel('Score')
    ax.set_title(title)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    
    plt.close()
    
    return fig
