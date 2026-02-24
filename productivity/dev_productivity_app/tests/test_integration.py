"""Integration tests for the productivity scorer end-to-end workflow."""
import pytest
import json
from pathlib import Path
from datetime import date

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEndToEndWorkflow:
    """Test complete workflows from fetch to display."""

    def test_complete_pipeline_test_mode(self, tmp_path):
        """Test complete pipeline in test mode."""
        from productivity_scorer import run_full_pipeline
        
        config = {
            "version": "1.0",
            "team": {
                "name": "Test Team",
                "members": [
                    {"name": "Alice", "github_username": "alice", "jira_account_id": "123"},
                    {"name": "Bob", "github_username": "bob", "jira_account_id": "456"}
                ]
            },
            "weights": {"items_completed": 0.50, "prs_authored": 0.30, "code_reviews": 0.20},
            "periods": {"sprint": {"type": "fixed", "start": "2026-01-01", "end": "2026-01-21"}},
            "jira": {"project": "TEST", "done_statuses": ["Done"]},
            "output": {"data_dir": str(tmp_path)}
        }
        
        result = run_full_pipeline(config, period="sprint", test_mode=True, output_dir=str(tmp_path))
        
        assert "raw_data" in result
        assert "scores" in result
        assert "ranked" in result
        assert len(result["ranked"]) == 2

    def test_pipeline_generates_correct_scores(self, tmp_path):
        """Test that pipeline generates correctly calculated scores."""
        from productivity_scorer import run_full_pipeline
        
        config = {
            "version": "1.0",
            "team": {
                "name": "Test Team",
                "members": [
                    {"name": "Alice", "github_username": "alice", "jira_account_id": "123"}
                ]
            },
            "weights": {"items_completed": 0.50, "prs_authored": 0.30, "code_reviews": 0.20},
            "periods": {"sprint": {"type": "fixed", "start": "2026-01-01", "end": "2026-01-21"}},
            "jira": {"project": "TEST", "done_statuses": ["Done"]}
        }
        
        result = run_full_pipeline(config, period="sprint", test_mode=True)
        
        # Single person should have total = 100 (normalized to max)
        assert result["ranked"][0]["total"] == 100.0

    def test_pipeline_with_markdown_output(self, tmp_path):
        """Test pipeline generates markdown report."""
        from productivity_scorer import run_full_pipeline
        
        config = {
            "version": "1.0",
            "team": {
                "name": "Test Team",
                "members": [
                    {"name": "Alice", "github_username": "alice", "jira_account_id": "123"}
                ]
            },
            "weights": {"items_completed": 0.50, "prs_authored": 0.30, "code_reviews": 0.20},
            "periods": {"sprint": {"type": "fixed", "start": "2026-01-01", "end": "2026-01-21"}},
            "jira": {"project": "TEST", "done_statuses": ["Done"]}
        }
        
        output_file = tmp_path / "report.md"
        
        run_full_pipeline(
            config, 
            period="sprint", 
            test_mode=True,
            output_file=str(output_file)
        )
        
        assert output_file.exists()
        content = output_file.read_text()
        assert "Test Team" in content
        assert "Rankings" in content


class TestFetcherIntegration:
    """Test fetcher components working together."""

    def test_fetchers_return_compatible_data(self):
        """Test that Jira and GitHub fetchers return compatible MetricData."""
        from fetchers.jira_fetcher import JiraFetcher
        from fetchers.github_fetcher import GitHubFetcher
        from fetchers.base_fetcher import TeamMember, Period, MetricData
        
        member = TeamMember("Alice", "alice", "123")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        jira_fetcher = JiraFetcher(project="TEST", test_mode=True)
        github_fetcher = GitHubFetcher(test_mode=True)
        
        jira_data = jira_fetcher.fetch(member, period)
        github_data = github_fetcher.fetch(member, period)
        
        assert isinstance(jira_data, MetricData)
        assert isinstance(github_data, MetricData)
        
        # Jira provides items and story points
        assert jira_data.items_completed > 0
        assert jira_data.story_points >= 0
        
        # GitHub provides PRs and reviews
        assert github_data.prs_authored > 0
        assert github_data.code_reviews > 0

    def test_fetcher_data_can_be_merged(self):
        """Test that data from multiple fetchers can be combined."""
        from fetchers.jira_fetcher import JiraFetcher
        from fetchers.github_fetcher import GitHubFetcher
        from fetchers.base_fetcher import TeamMember, Period
        
        member = TeamMember("Alice", "alice", "123")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        jira_fetcher = JiraFetcher(project="TEST", test_mode=True)
        github_fetcher = GitHubFetcher(test_mode=True)
        
        jira_data = jira_fetcher.fetch(member, period)
        github_data = github_fetcher.fetch(member, period)
        
        # Merge should combine metrics
        merged = jira_data.merge(github_data)
        
        assert merged.items_completed > 0
        assert merged.prs_authored > 0


class TestCalculatorIntegration:
    """Test calculator with real-ish data."""

    def test_calculator_with_fetched_data_format(self):
        """Test calculator works with fetcher output format."""
        from calculator.score_calculator import calculate_scores, rank_scores
        
        # Simulate fetched data format
        raw_data = {
            "generated_at": "2026-01-21T12:00:00Z",
            "period": {"name": "sprint", "start": "2026-01-01", "end": "2026-01-21"},
            "metrics": {
                "Alice": {"items_completed": 50, "story_points": 25, "prs_authored": 20, "code_reviews": 30},
                "Bob": {"items_completed": 30, "story_points": 15, "prs_authored": 40, "code_reviews": 20}
            }
        }
        
        config = {"weights": {"items_completed": 0.5, "prs_authored": 0.3, "code_reviews": 0.2}}
        
        scores = calculate_scores(raw_data, config)
        ranked = rank_scores(scores)
        
        assert len(ranked) == 2
        assert ranked[0]["rank"] == 1
        assert ranked[0]["total"] >= ranked[1]["total"]


class TestDisplayIntegration:
    """Test display components with calculator output."""

    def test_tables_with_ranked_scores(self):
        """Test table generation with ranked scores."""
        from calculator.score_calculator import calculate_scores, rank_scores
        from display.tables import create_ranking_table, create_markdown_table
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 50, "prs_authored": 20, "code_reviews": 30},
                "Bob": {"items_completed": 30, "prs_authored": 40, "code_reviews": 20}
            }
        }
        config = {"weights": {"items_completed": 0.5, "prs_authored": 0.3, "code_reviews": 0.2}}
        
        scores = calculate_scores(raw_data, config)
        ranked = rank_scores(scores)
        
        table = create_ranking_table(ranked)
        markdown = create_markdown_table(ranked)
        
        assert "Alice" in table
        assert "Bob" in table
        assert "|" in markdown

    def test_charts_with_calculator_output(self):
        """Test chart generation with calculator output."""
        from calculator.score_calculator import calculate_scores
        from display.charts import create_bar_chart
        from unittest.mock import patch
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 50, "prs_authored": 20, "code_reviews": 30}
            }
        }
        config = {"weights": {"items_completed": 0.5, "prs_authored": 0.3, "code_reviews": 0.2}}
        
        scores = calculate_scores(raw_data, config)
        
        with patch("matplotlib.pyplot.savefig"):
            with patch("matplotlib.pyplot.close"):
                fig = create_bar_chart(scores)
        
        assert fig is not None


class TestConfigIntegration:
    """Test configuration loading and validation."""

    def test_default_config_is_valid(self):
        """Test that default config passes validation."""
        from fetchers.base_fetcher import load_config, validate_config
        
        config_path = Path(__file__).parent.parent / "config" / "default_config.json"
        
        if config_path.exists():
            config = load_config(str(config_path))
            # Should not raise
            validate_config(config)

    def test_config_team_members_loadable(self):
        """Test that team members can be loaded from config."""
        from fetchers.base_fetcher import load_config, load_team_members
        
        config_path = Path(__file__).parent.parent / "config" / "default_config.json"
        
        if config_path.exists():
            config = load_config(str(config_path))
            members = load_team_members(config)
            
            assert len(members) > 0
            assert all(hasattr(m, "name") for m in members)


class TestDataPersistence:
    """Test data saving and loading."""

    def test_raw_data_can_be_saved_and_loaded(self, tmp_path):
        """Test raw data JSON persistence."""
        from productivity_scorer import run_fetch
        
        config = {
            "version": "1.0",
            "team": {
                "name": "Test",
                "members": [{"name": "Alice", "github_username": "alice", "jira_account_id": "123"}]
            },
            "weights": {"items_completed": 0.5, "prs_authored": 0.3, "code_reviews": 0.2},
            "periods": {"sprint": {"type": "fixed", "start": "2026-01-01", "end": "2026-01-21"}},
            "jira": {"project": "TEST", "done_statuses": ["Done"]}
        }
        
        raw_data = run_fetch(config, period="sprint", test_mode=True, output_dir=str(tmp_path))
        
        # Check files were created
        files = list(tmp_path.glob("raw_*.json"))
        assert len(files) == 1
        
        # Verify can be loaded
        with open(files[0]) as f:
            loaded = json.load(f)
        
        assert loaded["metrics"]["Alice"]["items_completed"] > 0
