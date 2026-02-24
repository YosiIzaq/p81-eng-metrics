"""Tests for the GitHub fetcher (PRs authored and code reviews)."""
import pytest
import json
import subprocess
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetchers.base_fetcher import TeamMember, Period, MetricData


class TestGitHubFetcherInit:
    """Tests for GitHubFetcher initialization."""

    def test_create_github_fetcher(self):
        """Test creating a GitHubFetcher instance."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher()
        
        assert fetcher is not None

    def test_create_github_fetcher_with_org(self):
        """Test creating a GitHubFetcher with organization."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher(org="perimeter-81")
        
        assert fetcher.org == "perimeter-81"

    def test_create_github_fetcher_test_mode(self):
        """Test creating a GitHubFetcher in test mode."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher(test_mode=True)
        
        assert fetcher.test_mode is True


class TestGitHubFetcherPRsAuthored:
    """Tests for fetching PRs authored by a team member."""

    def test_fetch_prs_authored_success(self):
        """Test successful fetch of PRs authored."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher()
        member = TeamMember("Alice", "alice-dev", "test-123")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        # Mock the subprocess call
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([
            {"number": 1}, {"number": 2}, {"number": 3}
        ])
        
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            count = fetcher.fetch_prs_authored(member, period)
        
        assert count == 3
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "gh" in call_args
        assert "search" in call_args
        assert "prs" in call_args
        assert "--author=alice-dev" in call_args

    def test_fetch_prs_authored_empty_result(self):
        """Test fetch PRs when user has no PRs."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher()
        member = TeamMember("Bob", "bob-eng", "test-456")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        
        with patch("subprocess.run", return_value=mock_result):
            count = fetcher.fetch_prs_authored(member, period)
        
        assert count == 0

    def test_fetch_prs_authored_command_failure(self):
        """Test handling of command failure."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher()
        member = TeamMember("Carol", "carol-code", "test-789")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Error: rate limit exceeded"
        
        with patch("subprocess.run", return_value=mock_result):
            count = fetcher.fetch_prs_authored(member, period)
        
        # Should return 0 on failure, not raise
        assert count == 0

    def test_fetch_prs_authored_invalid_json(self):
        """Test handling of invalid JSON response."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher()
        member = TeamMember("Dave", "dave-dev", "test-111")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "not valid json"
        
        with patch("subprocess.run", return_value=mock_result):
            count = fetcher.fetch_prs_authored(member, period)
        
        # Should return 0 on parse error
        assert count == 0


class TestGitHubFetcherCodeReviews:
    """Tests for fetching code reviews performed by a team member."""

    def test_fetch_code_reviews_success(self):
        """Test successful fetch of code reviews."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher()
        member = TeamMember("Alice", "alice-dev", "test-123")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps([
            {"number": 10}, {"number": 11}, {"number": 12}, {"number": 13}, {"number": 14}
        ])
        
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            count = fetcher.fetch_code_reviews(member, period)
        
        assert count == 5
        call_args = mock_run.call_args[0][0]
        assert "--reviewed-by=alice-dev" in call_args

    def test_fetch_code_reviews_empty_result(self):
        """Test fetch code reviews when user has no reviews."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher()
        member = TeamMember("Bob", "bob-eng", "test-456")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        
        with patch("subprocess.run", return_value=mock_result):
            count = fetcher.fetch_code_reviews(member, period)
        
        assert count == 0


class TestGitHubFetcherCombined:
    """Tests for the combined fetch method."""

    def test_fetch_returns_metric_data(self):
        """Test that fetch returns MetricData with PRs and reviews."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher()
        member = TeamMember("Alice", "alice-dev", "test-123")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        # Mock both calls
        mock_prs = MagicMock()
        mock_prs.returncode = 0
        mock_prs.stdout = json.dumps([{"number": 1}, {"number": 2}])
        
        mock_reviews = MagicMock()
        mock_reviews.returncode = 0
        mock_reviews.stdout = json.dumps([{"number": 10}, {"number": 11}, {"number": 12}])
        
        with patch("subprocess.run", side_effect=[mock_prs, mock_reviews]):
            result = fetcher.fetch(member, period)
        
        assert isinstance(result, MetricData)
        assert result.prs_authored == 2
        assert result.code_reviews == 3
        assert result.items_completed == 0  # GitHub fetcher doesn't set this
        assert result.story_points == 0


class TestGitHubFetcherTestMode:
    """Tests for test mode functionality."""

    def test_fetch_test_data_returns_mock_data(self):
        """Test that test mode returns deterministic mock data."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher(test_mode=True)
        member = TeamMember("Alice", "alice-dev", "test-123")
        
        result = fetcher.fetch_test_data(member)
        
        assert isinstance(result, MetricData)
        assert result.prs_authored > 0
        assert result.code_reviews > 0

    def test_fetch_test_data_deterministic(self):
        """Test that test mode returns same data for same user."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher(test_mode=True)
        member = TeamMember("Alice", "alice-dev", "test-123")
        
        result1 = fetcher.fetch_test_data(member)
        result2 = fetcher.fetch_test_data(member)
        
        assert result1.prs_authored == result2.prs_authored
        assert result1.code_reviews == result2.code_reviews

    def test_fetch_in_test_mode_uses_mock_data(self):
        """Test that fetch uses mock data when in test mode."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher(test_mode=True)
        member = TeamMember("Bob", "bob-eng", "test-456")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        # Should NOT call subprocess in test mode
        with patch("subprocess.run") as mock_run:
            result = fetcher.fetch(member, period)
            mock_run.assert_not_called()
        
        assert result.prs_authored > 0


class TestGitHubFetcherRateLimiting:
    """Tests for rate limiting and retry behavior."""

    def test_retry_on_rate_limit(self):
        """Test that fetcher retries on rate limit error."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher(retry_count=3, retry_delay=0.01)
        member = TeamMember("Alice", "alice-dev", "test-123")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        # First call fails with rate limit, second succeeds
        fail_result = MagicMock()
        fail_result.returncode = 1
        fail_result.stderr = "rate limit exceeded"
        
        success_result = MagicMock()
        success_result.returncode = 0
        success_result.stdout = json.dumps([{"number": 1}])
        
        with patch("subprocess.run", side_effect=[fail_result, success_result]) as mock_run:
            count = fetcher.fetch_prs_authored(member, period)
        
        assert count == 1
        assert mock_run.call_count == 2

    def test_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher(retry_count=2, retry_delay=0.01)
        member = TeamMember("Alice", "alice-dev", "test-123")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        fail_result = MagicMock()
        fail_result.returncode = 1
        fail_result.stderr = "rate limit exceeded"
        
        with patch("subprocess.run", return_value=fail_result) as mock_run:
            count = fetcher.fetch_prs_authored(member, period)
        
        assert count == 0
        assert mock_run.call_count == 2  # Initial + 1 retry


class TestGitHubFetcherDateFormats:
    """Tests for date format handling."""

    def test_date_range_format_for_merged_prs(self):
        """Test that date range is correctly formatted for merged PRs search."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher()
        member = TeamMember("Alice", "alice-dev", "test-123")
        period = Period("sprint", date(2026, 1, 18), date(2026, 2, 7))
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            fetcher.fetch_prs_authored(member, period)
        
        call_args = " ".join(mock_run.call_args[0][0])
        assert "2026-01-18" in call_args or ">2026-01-17" in call_args

    def test_uses_created_date_for_search(self):
        """Test that search uses created date filter."""
        from fetchers.github_fetcher import GitHubFetcher
        
        fetcher = GitHubFetcher()
        member = TeamMember("Alice", "alice-dev", "test-123")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"
        
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            fetcher.fetch_prs_authored(member, period)
        
        call_args = mock_run.call_args[0][0]
        # Should use --created flag
        created_args = [a for a in call_args if a.startswith("--created")]
        assert len(created_args) == 1
