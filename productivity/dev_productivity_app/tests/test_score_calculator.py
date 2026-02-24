"""Tests for the score calculator."""
import pytest
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestScoreCalculatorBasic:
    """Tests for basic score calculation functionality."""

    def test_calculate_scores_simple(self):
        """Test basic score calculation with simple data."""
        from calculator.score_calculator import calculate_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 50, "prs_authored": 20, "code_reviews": 30},
                "Bob": {"items_completed": 25, "prs_authored": 40, "code_reviews": 15}
            }
        }
        
        config = {
            "weights": {
                "items_completed": 0.50,
                "prs_authored": 0.30,
                "code_reviews": 0.20
            }
        }
        
        scores = calculate_scores(raw_data, config)
        
        assert "Alice" in scores
        assert "Bob" in scores
        assert "total" in scores["Alice"]
        assert "total" in scores["Bob"]

    def test_calculate_scores_normalized_to_100(self):
        """Test that component scores are normalized to 0-100."""
        from calculator.score_calculator import calculate_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 100, "prs_authored": 50, "code_reviews": 25},
                "Bob": {"items_completed": 50, "prs_authored": 25, "code_reviews": 50}
            }
        }
        
        config = {
            "weights": {
                "items_completed": 0.50,
                "prs_authored": 0.30,
                "code_reviews": 0.20
            }
        }
        
        scores = calculate_scores(raw_data, config)
        
        # Alice has max items, so items_score should be 100
        assert scores["Alice"]["items_score"] == 100.0
        # Bob has half of max items, so items_score should be 50
        assert scores["Bob"]["items_score"] == 50.0
        
        # Alice has max PRs
        assert scores["Alice"]["prs_score"] == 100.0

    def test_calculate_scores_weighted_total(self):
        """Test that total is correctly weighted."""
        from calculator.score_calculator import calculate_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 100, "prs_authored": 100, "code_reviews": 100}
            }
        }
        
        config = {
            "weights": {
                "items_completed": 0.50,
                "prs_authored": 0.30,
                "code_reviews": 0.20
            }
        }
        
        scores = calculate_scores(raw_data, config)
        
        # Single person with all max values should have total = 100
        assert scores["Alice"]["total"] == 100.0


class TestScoreCalculatorEdgeCases:
    """Tests for edge cases in score calculation."""

    def test_calculate_scores_all_zeros(self):
        """Test handling of all zero metrics."""
        from calculator.score_calculator import calculate_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 0, "prs_authored": 0, "code_reviews": 0},
                "Bob": {"items_completed": 0, "prs_authored": 0, "code_reviews": 0}
            }
        }
        
        config = {
            "weights": {
                "items_completed": 0.50,
                "prs_authored": 0.30,
                "code_reviews": 0.20
            }
        }
        
        scores = calculate_scores(raw_data, config)
        
        assert scores["Alice"]["total"] == 0.0
        assert scores["Bob"]["total"] == 0.0

    def test_calculate_scores_single_person(self):
        """Test calculation with only one person."""
        from calculator.score_calculator import calculate_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 50, "prs_authored": 30, "code_reviews": 20}
            }
        }
        
        config = {
            "weights": {
                "items_completed": 0.50,
                "prs_authored": 0.30,
                "code_reviews": 0.20
            }
        }
        
        scores = calculate_scores(raw_data, config)
        
        # Single person is always "max", so all scores should be 100
        assert scores["Alice"]["items_score"] == 100.0
        assert scores["Alice"]["prs_score"] == 100.0
        assert scores["Alice"]["reviews_score"] == 100.0
        assert scores["Alice"]["total"] == 100.0

    def test_calculate_scores_tied_values(self):
        """Test handling of tied values."""
        from calculator.score_calculator import calculate_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 50, "prs_authored": 30, "code_reviews": 40},
                "Bob": {"items_completed": 50, "prs_authored": 30, "code_reviews": 40}
            }
        }
        
        config = {
            "weights": {
                "items_completed": 0.50,
                "prs_authored": 0.30,
                "code_reviews": 0.20
            }
        }
        
        scores = calculate_scores(raw_data, config)
        
        # Tied values should result in equal scores
        assert scores["Alice"]["total"] == scores["Bob"]["total"]
        assert scores["Alice"]["items_score"] == 100.0
        assert scores["Bob"]["items_score"] == 100.0

    def test_calculate_scores_missing_metric(self):
        """Test handling of missing metrics in raw data."""
        from calculator.score_calculator import calculate_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 50, "prs_authored": 30},  # Missing code_reviews
                "Bob": {"items_completed": 25, "prs_authored": 15, "code_reviews": 40}
            }
        }
        
        config = {
            "weights": {
                "items_completed": 0.50,
                "prs_authored": 0.30,
                "code_reviews": 0.20
            }
        }
        
        scores = calculate_scores(raw_data, config)
        
        # Should handle missing metric gracefully (treat as 0)
        assert scores["Alice"]["reviews_score"] == 0.0

    def test_calculate_scores_empty_metrics(self):
        """Test handling of empty metrics dict."""
        from calculator.score_calculator import calculate_scores
        
        raw_data = {"metrics": {}}
        
        config = {
            "weights": {
                "items_completed": 0.50,
                "prs_authored": 0.30,
                "code_reviews": 0.20
            }
        }
        
        scores = calculate_scores(raw_data, config)
        
        assert scores == {}


class TestScoreCalculatorWeights:
    """Tests for weight handling."""

    def test_different_weights(self):
        """Test calculation with different weight configurations."""
        from calculator.score_calculator import calculate_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 100, "prs_authored": 0, "code_reviews": 0},
                "Bob": {"items_completed": 0, "prs_authored": 100, "code_reviews": 0}
            }
        }
        
        # Heavy items weight
        config = {
            "weights": {
                "items_completed": 0.80,
                "prs_authored": 0.10,
                "code_reviews": 0.10
            }
        }
        
        scores = calculate_scores(raw_data, config)
        
        # Alice should score higher with heavy items weight
        assert scores["Alice"]["total"] > scores["Bob"]["total"]

    def test_weights_normalized_if_not_summing_to_one(self):
        """Test that weights are normalized if they don't sum to 1."""
        from calculator.score_calculator import calculate_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 100, "prs_authored": 100, "code_reviews": 100}
            }
        }
        
        # Weights that sum to 2.0 (not 1.0)
        config = {
            "weights": {
                "items_completed": 1.0,
                "prs_authored": 0.6,
                "code_reviews": 0.4
            }
        }
        
        scores = calculate_scores(raw_data, config)
        
        # Total should still be 100 after normalization
        assert scores["Alice"]["total"] == 100.0


class TestScoreCalculatorRanking:
    """Tests for ranking functionality."""

    def test_rank_by_total_score(self):
        """Test ranking team members by total score."""
        from calculator.score_calculator import calculate_scores, rank_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 50, "prs_authored": 20, "code_reviews": 30},
                "Bob": {"items_completed": 30, "prs_authored": 40, "code_reviews": 20},
                "Carol": {"items_completed": 40, "prs_authored": 30, "code_reviews": 50}
            }
        }
        
        config = {
            "weights": {
                "items_completed": 0.50,
                "prs_authored": 0.30,
                "code_reviews": 0.20
            }
        }
        
        scores = calculate_scores(raw_data, config)
        ranked = rank_scores(scores)
        
        # Should be sorted by total score descending
        assert len(ranked) == 3
        assert ranked[0]["rank"] == 1
        assert ranked[1]["rank"] == 2
        assert ranked[2]["rank"] == 3
        assert ranked[0]["total"] >= ranked[1]["total"]
        assert ranked[1]["total"] >= ranked[2]["total"]

    def test_rank_handles_ties(self):
        """Test ranking with tied scores."""
        from calculator.score_calculator import calculate_scores, rank_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 50, "prs_authored": 30, "code_reviews": 40},
                "Bob": {"items_completed": 50, "prs_authored": 30, "code_reviews": 40}
            }
        }
        
        config = {
            "weights": {
                "items_completed": 0.50,
                "prs_authored": 0.30,
                "code_reviews": 0.20
            }
        }
        
        scores = calculate_scores(raw_data, config)
        ranked = rank_scores(scores)
        
        # Both should have rank 1 for tie
        assert ranked[0]["rank"] == 1
        assert ranked[1]["rank"] == 1


class TestScoreCalculatorOutput:
    """Tests for score output formatting."""

    def test_scores_include_component_breakdown(self):
        """Test that scores include component breakdown."""
        from calculator.score_calculator import calculate_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 50, "prs_authored": 20, "code_reviews": 30}
            }
        }
        
        config = {
            "weights": {
                "items_completed": 0.50,
                "prs_authored": 0.30,
                "code_reviews": 0.20
            }
        }
        
        scores = calculate_scores(raw_data, config)
        
        assert "items_score" in scores["Alice"]
        assert "prs_score" in scores["Alice"]
        assert "reviews_score" in scores["Alice"]
        assert "total" in scores["Alice"]

    def test_scores_include_weighted_contribution(self):
        """Test that scores include weighted contribution values."""
        from calculator.score_calculator import calculate_scores
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 100, "prs_authored": 100, "code_reviews": 100}
            }
        }
        
        config = {
            "weights": {
                "items_completed": 0.50,
                "prs_authored": 0.30,
                "code_reviews": 0.20
            }
        }
        
        scores = calculate_scores(raw_data, config)
        
        # Should include weighted contributions
        assert "items_weighted" in scores["Alice"]
        assert scores["Alice"]["items_weighted"] == 50.0  # 100 * 0.50
        assert scores["Alice"]["prs_weighted"] == 30.0  # 100 * 0.30
        assert scores["Alice"]["reviews_weighted"] == 20.0  # 100 * 0.20


class TestComponentContributions:
    """Tests for calculate_component_contributions function."""
    
    def test_component_contributions_basic(self):
        """Test basic component contribution calculation."""
        from calculator.score_calculator import calculate_component_contributions
        
        scores = {
            "Alice": {
                "items_weighted": 50.0,
                "prs_weighted": 30.0,
                "reviews_weighted": 20.0,
                "total": 100.0
            }
        }
        
        result = calculate_component_contributions(scores)
        
        assert result["Alice"]["items_pct"] == 50.0
        assert result["Alice"]["prs_pct"] == 30.0
        assert result["Alice"]["reviews_pct"] == 20.0
    
    def test_component_contributions_zero_total(self):
        """Test contributions when total is zero."""
        from calculator.score_calculator import calculate_component_contributions
        
        scores = {
            "Alice": {
                "items_weighted": 0.0,
                "prs_weighted": 0.0,
                "reviews_weighted": 0.0,
                "total": 0.0
            }
        }
        
        result = calculate_component_contributions(scores)
        
        assert result["Alice"]["items_pct"] == 0.0
        assert result["Alice"]["prs_pct"] == 0.0
        assert result["Alice"]["reviews_pct"] == 0.0
    
    def test_component_contributions_multiple_members(self):
        """Test contributions for multiple team members."""
        from calculator.score_calculator import calculate_component_contributions
        
        scores = {
            "Alice": {
                "items_weighted": 40.0,
                "prs_weighted": 30.0,
                "reviews_weighted": 10.0,
                "total": 80.0
            },
            "Bob": {
                "items_weighted": 25.0,
                "prs_weighted": 15.0,
                "reviews_weighted": 20.0,
                "total": 60.0
            }
        }
        
        result = calculate_component_contributions(scores)
        
        assert len(result) == 2
        # Alice: 40/80 = 50%
        assert result["Alice"]["items_pct"] == 50.0
        # Bob: 20/60 = 33.33%
        assert abs(result["Bob"]["reviews_pct"] - 33.33) < 0.1


class TestComparePeriods:
    """Tests for compare_periods function."""
    
    def test_compare_periods_basic(self):
        """Test basic period comparison."""
        from calculator.score_calculator import compare_periods
        
        current = {
            "Alice": {"total": 85.0},
            "Bob": {"total": 70.0}
        }
        
        previous = {
            "Alice": {"total": 80.0},
            "Bob": {"total": 75.0}
        }
        
        result = compare_periods(current, previous)
        
        assert result["Alice"]["current"] == 85.0
        assert result["Alice"]["previous"] == 80.0
        assert result["Alice"]["change"] == 5.0
        assert result["Alice"]["trend"] == "up"
        
        assert result["Bob"]["change"] == -5.0
        assert result["Bob"]["trend"] == "down"
    
    def test_compare_periods_stable(self):
        """Test comparison with stable (minimal change)."""
        from calculator.score_calculator import compare_periods
        
        current = {"Alice": {"total": 80.0}}
        previous = {"Alice": {"total": 80.3}}
        
        result = compare_periods(current, previous)
        
        assert result["Alice"]["trend"] == "stable"
    
    def test_compare_periods_new_member(self):
        """Test comparison when member is new (not in previous)."""
        from calculator.score_calculator import compare_periods
        
        current = {
            "Alice": {"total": 85.0},
            "NewGuy": {"total": 60.0}
        }
        
        previous = {
            "Alice": {"total": 80.0}
        }
        
        result = compare_periods(current, previous)
        
        assert "NewGuy" in result
        assert result["NewGuy"]["previous"] == 0
        assert result["NewGuy"]["change"] == 60.0
        assert result["NewGuy"]["trend"] == "up"
    
    def test_compare_periods_left_member(self):
        """Test comparison when member left (not in current)."""
        from calculator.score_calculator import compare_periods
        
        current = {"Alice": {"total": 85.0}}
        previous = {
            "Alice": {"total": 80.0},
            "LeftGuy": {"total": 70.0}
        }
        
        result = compare_periods(current, previous)
        
        assert "LeftGuy" in result
        assert result["LeftGuy"]["current"] == 0
        assert result["LeftGuy"]["previous"] == 70.0
        assert result["LeftGuy"]["trend"] == "down"
