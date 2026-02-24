"""Tests for the Jira fetcher (items completed and story points)."""
import pytest
import json
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetchers.base_fetcher import TeamMember, Period, MetricData


class TestJiraFetcherInit:
    """Tests for JiraFetcher initialization."""

    def test_create_jira_fetcher(self):
        """Test creating a JiraFetcher instance."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81")
        
        assert fetcher is not None
        assert fetcher.project == "P81"

    def test_create_jira_fetcher_with_statuses(self):
        """Test creating a JiraFetcher with custom done statuses."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(
            project="TEST",
            done_statuses=["Done", "Closed", "Released"]
        )
        
        assert fetcher.done_statuses == ["Done", "Closed", "Released"]

    def test_create_jira_fetcher_test_mode(self):
        """Test creating a JiraFetcher in test mode."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81", test_mode=True)
        
        assert fetcher.test_mode is True


class TestJiraFetcherJqlBuilder:
    """Tests for JQL query building."""

    def test_build_jql_basic(self):
        """Test building basic JQL query."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81")
        member = TeamMember("Alice", "alice-dev", "test-alice-123")
        period = Period("sprint", date(2026, 1, 18), date(2026, 2, 7))
        
        jql = fetcher.build_jql(member, period)
        
        assert "project = P81" in jql
        assert "assignee = 'test-alice-123'" in jql
        assert "status IN" in jql
        assert "2026-01-18" in jql

    def test_build_jql_with_custom_statuses(self):
        """Test JQL with custom done statuses."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(
            project="TEST",
            done_statuses=["Done", "Closed"]
        )
        member = TeamMember("Bob", "bob-eng", "test-bob-456")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        jql = fetcher.build_jql(member, period)
        
        assert "status IN ('Done', 'Closed')" in jql


class TestJiraFetcherParseResponse:
    """Tests for parsing Jira API responses."""

    def test_parse_jira_response_with_items(self):
        """Test parsing Jira response with issues."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81")
        
        response = {
            "issues": [
                {
                    "key": "P81-101",
                    "fields": {
                        "summary": "Task 1",
                        "customfield_10016": 5
                    }
                },
                {
                    "key": "P81-102",
                    "fields": {
                        "summary": "Task 2",
                        "customfield_10016": 3
                    }
                },
                {
                    "key": "P81-103",
                    "fields": {
                        "summary": "Task 3",
                        "customfield_10016": None
                    }
                }
            ]
        }
        
        items, points = fetcher.parse_response(response)
        
        assert items == 3
        assert points == 8  # 5 + 3 + 0

    def test_parse_jira_response_empty(self):
        """Test parsing empty Jira response."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81")
        
        response = {"issues": []}
        
        items, points = fetcher.parse_response(response)
        
        assert items == 0
        assert points == 0

    def test_parse_jira_response_no_issues_key(self):
        """Test parsing response without issues key."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81")
        
        response = {}
        
        items, points = fetcher.parse_response(response)
        
        assert items == 0
        assert points == 0

    def test_parse_jira_response_null_story_points(self):
        """Test handling of null story points."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81")
        
        response = {
            "issues": [
                {"key": "P81-1", "fields": {"customfield_10016": None}},
                {"key": "P81-2", "fields": {"customfield_10016": 5}},
                {"key": "P81-3", "fields": {}}
            ]
        }
        
        items, points = fetcher.parse_response(response)
        
        assert items == 3
        assert points == 5


class TestJiraFetcherFetch:
    """Tests for the main fetch method."""

    def test_fetch_returns_metric_data(self):
        """Test that fetch returns MetricData with items and points."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81")
        member = TeamMember("Alice", "alice-dev", "test-123")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        mock_response = {
            "issues": [
                {"key": "P81-1", "fields": {"customfield_10016": 5}},
                {"key": "P81-2", "fields": {"customfield_10016": 3}}
            ]
        }
        
        with patch.object(fetcher, "_execute_jql", return_value=mock_response):
            result = fetcher.fetch(member, period)
        
        assert isinstance(result, MetricData)
        assert result.items_completed == 2
        assert result.story_points == 8
        assert result.prs_authored == 0  # Jira fetcher doesn't set this
        assert result.code_reviews == 0

    def test_fetch_handles_api_error(self):
        """Test fetch handles API errors gracefully."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81")
        member = TeamMember("Bob", "bob-eng", "test-456")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        with patch.object(fetcher, "_execute_jql", side_effect=Exception("API Error")):
            result = fetcher.fetch(member, period)
        
        assert result.items_completed == 0
        assert result.story_points == 0


class TestJiraFetcherTestMode:
    """Tests for test mode functionality."""

    def test_fetch_test_data_returns_mock_data(self):
        """Test that test mode returns deterministic mock data."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81", test_mode=True)
        member = TeamMember("Alice", "alice-dev", "test-123")
        
        result = fetcher.fetch_test_data(member)
        
        assert isinstance(result, MetricData)
        assert result.items_completed > 0
        assert result.story_points > 0

    def test_fetch_test_data_deterministic(self):
        """Test that test mode returns same data for same user."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81", test_mode=True)
        member = TeamMember("Alice", "alice-dev", "test-123")
        
        result1 = fetcher.fetch_test_data(member)
        result2 = fetcher.fetch_test_data(member)
        
        assert result1.items_completed == result2.items_completed
        assert result1.story_points == result2.story_points

    def test_fetch_in_test_mode_uses_mock_data(self):
        """Test that fetch uses mock data when in test mode."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81", test_mode=True)
        member = TeamMember("Bob", "bob-eng", "test-456")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        # Should NOT call actual API in test mode
        with patch.object(fetcher, "_execute_jql") as mock_jql:
            result = fetcher.fetch(member, period)
            mock_jql.assert_not_called()
        
        assert result.items_completed > 0


class TestJiraFetcherGhCli:
    """Tests for GitHub CLI-based Jira fetching (using subprocess)."""

    def test_execute_jql_via_subprocess(self):
        """Test executing JQL query via subprocess."""
        from fetchers.jira_fetcher import JiraFetcher
        
        fetcher = JiraFetcher(project="P81", cloud_id="test.atlassian.net")
        
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "issues": [
                {"key": "P81-1", "fields": {"customfield_10016": 5}}
            ]
        })
        
        # Note: In real implementation, this would call the Atlassian MCP or subprocess
        # For now, we test the parsing logic
        member = TeamMember("Alice", "alice-dev", "test-123")
        period = Period("sprint", date(2026, 1, 1), date(2026, 1, 21))
        
        with patch.object(fetcher, "_execute_jql", return_value={"issues": [
            {"key": "P81-1", "fields": {"customfield_10016": 5}}
        ]}):
            result = fetcher.fetch(member, period)
        
        assert result.items_completed == 1
        assert result.story_points == 5
