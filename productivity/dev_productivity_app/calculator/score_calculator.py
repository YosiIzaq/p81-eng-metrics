"""Score calculator for team productivity metrics."""
from typing import Dict, Any, List


def calculate_scores(raw_data: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate productivity scores for all team members.
    
    Args:
        raw_data: Raw metrics data with structure:
            {"metrics": {"Name": {"items_completed": N, "prs_authored": N, "code_reviews": N}}}
        config: Configuration with weights:
            {"weights": {"items_completed": 0.5, "prs_authored": 0.3, "code_reviews": 0.2}}
    
    Returns:
        Dictionary of scores per team member with structure:
            {"Name": {"items_score": N, "prs_score": N, "reviews_score": N,
                     "items_weighted": N, "prs_weighted": N, "reviews_weighted": N,
                     "total": N}}
    """
    metrics = raw_data.get("metrics", {})
    
    if not metrics:
        return {}
    
    weights = config.get("weights", {})
    
    # Normalize weights if they don't sum to 1
    weight_sum = sum(weights.values())
    if weight_sum > 0 and abs(weight_sum - 1.0) > 0.01:
        weights = {k: v / weight_sum for k, v in weights.items()}
    
    # Find max values for normalization
    max_items = max(
        (m.get("items_completed", 0) for m in metrics.values()),
        default=0
    )
    max_prs = max(
        (m.get("prs_authored", 0) for m in metrics.values()),
        default=0
    )
    max_reviews = max(
        (m.get("code_reviews", 0) for m in metrics.values()),
        default=0
    )
    
    scores = {}
    
    for name, data in metrics.items():
        items = data.get("items_completed", 0)
        prs = data.get("prs_authored", 0)
        reviews = data.get("code_reviews", 0)
        
        # Normalize to 0-100 scale
        items_score = (items / max_items * 100) if max_items > 0 else 0.0
        prs_score = (prs / max_prs * 100) if max_prs > 0 else 0.0
        reviews_score = (reviews / max_reviews * 100) if max_reviews > 0 else 0.0
        
        # Apply weights
        items_weight = weights.get("items_completed", 0.5)
        prs_weight = weights.get("prs_authored", 0.3)
        reviews_weight = weights.get("code_reviews", 0.2)
        
        items_weighted = items_score * items_weight
        prs_weighted = prs_score * prs_weight
        reviews_weighted = reviews_score * reviews_weight
        
        total = items_weighted + prs_weighted + reviews_weighted
        
        scores[name] = {
            "items_score": items_score,
            "prs_score": prs_score,
            "reviews_score": reviews_score,
            "items_weighted": items_weighted,
            "prs_weighted": prs_weighted,
            "reviews_weighted": reviews_weighted,
            "total": total
        }
    
    return scores


def rank_scores(scores: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Rank team members by total score.
    
    Args:
        scores: Dictionary of scores per team member
        
    Returns:
        List of ranked members with structure:
            [{"rank": 1, "name": "Alice", "total": 95.0, ...}, ...]
        
        Ties are handled by assigning the same rank.
    """
    if not scores:
        return []
    
    # Sort by total score descending
    sorted_members = sorted(
        scores.items(),
        key=lambda x: x[1]["total"],
        reverse=True
    )
    
    ranked = []
    current_rank = 1
    prev_total = None
    
    for i, (name, score_data) in enumerate(sorted_members):
        # Handle ties - same score gets same rank
        if prev_total is not None and score_data["total"] < prev_total:
            current_rank = i + 1
        
        ranked.append({
            "rank": current_rank,
            "name": name,
            **score_data
        })
        
        prev_total = score_data["total"]
    
    return ranked


def calculate_component_contributions(scores: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """Calculate the percentage contribution of each component to total score.
    
    Args:
        scores: Dictionary of scores per team member
        
    Returns:
        Dictionary with component contributions as percentages:
            {"Alice": {"items_pct": 50.0, "prs_pct": 30.0, "reviews_pct": 20.0}}
    """
    contributions = {}
    
    for name, data in scores.items():
        total = data.get("total", 0)
        
        if total > 0:
            items_pct = (data.get("items_weighted", 0) / total) * 100
            prs_pct = (data.get("prs_weighted", 0) / total) * 100
            reviews_pct = (data.get("reviews_weighted", 0) / total) * 100
        else:
            items_pct = prs_pct = reviews_pct = 0.0
        
        contributions[name] = {
            "items_pct": items_pct,
            "prs_pct": prs_pct,
            "reviews_pct": reviews_pct
        }
    
    return contributions


def compare_periods(current_scores: Dict[str, Any], previous_scores: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Compare scores between two periods to identify trends.
    
    Args:
        current_scores: Scores from current period
        previous_scores: Scores from previous period
        
    Returns:
        Dictionary with trend data:
            {"Alice": {"current": 85.0, "previous": 80.0, "change": 5.0, "trend": "up"}}
    """
    comparison = {}
    
    all_names = set(current_scores.keys()) | set(previous_scores.keys())
    
    for name in all_names:
        current = current_scores.get(name, {}).get("total", 0)
        previous = previous_scores.get(name, {}).get("total", 0)
        change = current - previous
        
        if change > 0.5:
            trend = "up"
        elif change < -0.5:
            trend = "down"
        else:
            trend = "stable"
        
        comparison[name] = {
            "current": current,
            "previous": previous,
            "change": change,
            "trend": trend
        }
    
    return comparison
