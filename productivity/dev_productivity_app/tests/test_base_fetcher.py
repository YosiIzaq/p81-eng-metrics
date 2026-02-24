"""Tests for the base fetcher abstract class and common utilities."""
import pytest
from datetime import date, datetime, timedelta
from dataclasses import dataclass
from typing import Any
import json
from pathlib import Path

# Import after implementation exists
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTeamMemberDataclass:
    """Tests for TeamMember dataclass."""

    def test_create_team_member(self):
        """Test creating a TeamMember with all fields."""
        from fetchers.base_fetcher import TeamMember
        
        member = TeamMember(
            name="Alice Developer",
            github_username="alice-dev",
            jira_account_id="test-alice-123"
        )
        
        assert member.name == "Alice Developer"
        assert member.github_username == "alice-dev"
        assert member.jira_account_id == "test-alice-123"

    def test_team_member_from_dict(self):
        """Test creating TeamMember from dictionary."""
        from fetchers.base_fetcher import TeamMember
        
        data = {
            "name": "Bob Engineer",
            "github_username": "bob-eng",
            "jira_account_id": "test-bob-456"
        }
        
        member = TeamMember.from_dict(data)
        
        assert member.name == "Bob Engineer"
        assert member.github_username == "bob-eng"
        assert member.jira_account_id == "test-bob-456"

    def test_team_member_to_dict(self):
        """Test converting TeamMember to dictionary."""
        from fetchers.base_fetcher import TeamMember
        
        member = TeamMember(
            name="Carol Coder",
            github_username="carol-code",
            jira_account_id="test-carol-789"
        )
        
        result = member.to_dict()
        
        assert result == {
            "name": "Carol Coder",
            "github_username": "carol-code",
            "jira_account_id": "test-carol-789"
        }


class TestPeriodDataclass:
    """Tests for Period dataclass."""

    def test_create_fixed_period(self):
        """Test creating a fixed date range period."""
        from fetchers.base_fetcher import Period
        
        period = Period(
            name="sprint",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 21)
        )
        
        assert period.name == "sprint"
        assert period.start_date == date(2026, 1, 1)
        assert period.end_date == date(2026, 1, 21)

    def test_period_from_config_fixed(self):
        """Test creating Period from fixed config."""
        from fetchers.base_fetcher import Period
        
        config = {
            "type": "fixed",
            "start": "2026-01-01",
            "end": "2026-01-21"
        }
        
        period = Period.from_config("sprint", config)
        
        assert period.name == "sprint"
        assert period.start_date == date(2026, 1, 1)
        assert period.end_date == date(2026, 1, 21)

    def test_period_from_config_relative(self):
        """Test creating Period from relative config (days_back)."""
        from fetchers.base_fetcher import Period
        
        config = {
            "type": "relative",
            "days_back": 30
        }
        
        period = Period.from_config("last_month", config)
        
        assert period.name == "last_month"
        assert period.end_date == date.today()
        assert period.start_date == date.today() - timedelta(days=30)

    def test_period_to_jira_jql_dates(self):
        """Test converting Period to Jira JQL date format."""
        from fetchers.base_fetcher import Period
        
        period = Period(
            name="sprint",
            start_date=date(2026, 1, 18),
            end_date=date(2026, 2, 7)
        )
        
        start_str, end_str = period.to_jql_dates()
        
        assert start_str == "2026-01-18"
        assert end_str == "2026-02-07"

    def test_period_to_github_date_range(self):
        """Test converting Period to GitHub CLI date format."""
        from fetchers.base_fetcher import Period
        
        period = Period(
            name="sprint",
            start_date=date(2026, 1, 18),
            end_date=date(2026, 2, 7)
        )
        
        date_range = period.to_github_date_range()
        
        assert date_range == "2026-01-18..2026-02-07"

    def test_period_duration_days(self):
        """Test calculating period duration in days."""
        from fetchers.base_fetcher import Period
        
        period = Period(
            name="sprint",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 21)
        )
        
        assert period.duration_days == 20


class TestMetricDataDataclass:
    """Tests for MetricData dataclass."""

    def test_create_metric_data(self):
        """Test creating MetricData with all fields."""
        from fetchers.base_fetcher import MetricData
        
        data = MetricData(
            items_completed=30,
            story_points=15,
            prs_authored=20,
            code_reviews=40
        )
        
        assert data.items_completed == 30
        assert data.story_points == 15
        assert data.prs_authored == 20
        assert data.code_reviews == 40

    def test_metric_data_defaults(self):
        """Test MetricData default values."""
        from fetchers.base_fetcher import MetricData
        
        data = MetricData()
        
        assert data.items_completed == 0
        assert data.story_points == 0
        assert data.prs_authored == 0
        assert data.code_reviews == 0

    def test_metric_data_to_dict(self):
        """Test converting MetricData to dictionary."""
        from fetchers.base_fetcher import MetricData
        
        data = MetricData(
            items_completed=50,
            story_points=25,
            prs_authored=20,
            code_reviews=30
        )
        
        result = data.to_dict()
        
        assert result == {
            "items_completed": 50,
            "story_points": 25,
            "prs_authored": 20,
            "code_reviews": 30
        }

    def test_metric_data_merge(self):
        """Test merging two MetricData objects."""
        from fetchers.base_fetcher import MetricData
        
        data1 = MetricData(items_completed=10, story_points=5)
        data2 = MetricData(prs_authored=20, code_reviews=30)
        
        merged = data1.merge(data2)
        
        assert merged.items_completed == 10
        assert merged.story_points == 5
        assert merged.prs_authored == 20
        assert merged.code_reviews == 30


class TestBaseFetcher:
    """Tests for BaseFetcher abstract class."""

    def test_cannot_instantiate_base_fetcher(self):
        """Test that BaseFetcher cannot be instantiated directly."""
        from fetchers.base_fetcher import BaseFetcher
        
        with pytest.raises(TypeError):
            BaseFetcher()

    def test_concrete_fetcher_must_implement_fetch(self):
        """Test that concrete fetchers must implement fetch method."""
        from fetchers.base_fetcher import BaseFetcher, TeamMember, Period, MetricData
        
        class IncompleteFetcher(BaseFetcher):
            pass
        
        with pytest.raises(TypeError):
            IncompleteFetcher()

    def test_concrete_fetcher_implementation(self):
        """Test that a complete concrete fetcher can be instantiated."""
        from fetchers.base_fetcher import BaseFetcher, TeamMember, Period, MetricData
        
        class MockFetcher(BaseFetcher):
            def fetch(self, member: TeamMember, period: Period) -> MetricData:
                return MetricData(items_completed=10)
            
            def fetch_test_data(self, member: TeamMember) -> MetricData:
                return MetricData(items_completed=5)
        
        fetcher = MockFetcher()
        member = TeamMember("Test", "test-user", "test-id")
        period = Period("test", date.today(), date.today())
        
        result = fetcher.fetch(member, period)
        
        assert result.items_completed == 10


class TestConfigLoader:
    """Tests for configuration loading utilities."""

    def test_load_config_from_file(self, tmp_path):
        """Test loading configuration from JSON file."""
        from fetchers.base_fetcher import load_config
        
        config_data = {
            "version": "1.0",
            "team": {"name": "Test", "members": []},
            "weights": {"items_completed": 0.5, "prs_authored": 0.3, "code_reviews": 0.2},
            "periods": {},
            "jira": {"project": "TEST", "done_statuses": ["Done"]}
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        result = load_config(str(config_file))
        
        assert result["version"] == "1.0"
        assert result["team"]["name"] == "Test"

    def test_load_config_file_not_found(self):
        """Test loading config from non-existent file."""
        from fetchers.base_fetcher import load_config, ConfigError
        
        with pytest.raises(ConfigError) as exc_info:
            load_config("/nonexistent/path/config.json")
        
        assert "not found" in str(exc_info.value).lower()

    def test_load_config_invalid_json(self, tmp_path):
        """Test loading config with invalid JSON."""
        from fetchers.base_fetcher import load_config, ConfigError
        
        config_file = tmp_path / "bad_config.json"
        config_file.write_text("{ invalid json }")
        
        with pytest.raises(ConfigError) as exc_info:
            load_config(str(config_file))
        
        assert "json" in str(exc_info.value).lower() or "parse" in str(exc_info.value).lower()

    def test_validate_config_valid(self):
        """Test validating a valid configuration."""
        from fetchers.base_fetcher import validate_config
        
        config = {
            "version": "1.0",
            "team": {
                "name": "Test Team",
                "members": [{"name": "Alice", "github_username": "alice", "jira_account_id": "123"}]
            },
            "weights": {"items_completed": 0.5, "prs_authored": 0.3, "code_reviews": 0.2},
            "periods": {"sprint": {"type": "fixed", "start": "2026-01-01", "end": "2026-01-21"}},
            "jira": {"project": "TEST", "done_statuses": ["Done"]}
        }
        
        # Should not raise
        validate_config(config)

    def test_validate_config_missing_required_field(self):
        """Test validating config with missing required field."""
        from fetchers.base_fetcher import validate_config, ConfigError
        
        config = {
            "version": "1.0",
            # Missing 'team'
            "weights": {"items_completed": 0.5, "prs_authored": 0.3, "code_reviews": 0.2}
        }
        
        with pytest.raises(ConfigError):
            validate_config(config)

    def test_validate_config_invalid_weight_sum(self):
        """Test that weights validation catches non-summing weights (warning, not error)."""
        from fetchers.base_fetcher import validate_config
        
        config = {
            "version": "1.0",
            "team": {
                "name": "Test",
                "members": [{"name": "Alice", "github_username": "alice", "jira_account_id": "123"}]
            },
            "weights": {"items_completed": 0.5, "prs_authored": 0.5, "code_reviews": 0.5},  # Sum = 1.5
            "periods": {},
            "jira": {"project": "TEST", "done_statuses": ["Done"]}
        }
        
        # Should not raise but may log warning - weights are normalized at calculation time
        validate_config(config)


class TestTeamMemberLoading:
    """Tests for loading team members from config."""

    def test_load_team_members_from_config(self):
        """Test loading team members from configuration."""
        from fetchers.base_fetcher import load_team_members, TeamMember
        
        config = {
            "team": {
                "name": "Test Team",
                "members": [
                    {"name": "Alice", "github_username": "alice", "jira_account_id": "123"},
                    {"name": "Bob", "github_username": "bob", "jira_account_id": "456"}
                ]
            }
        }
        
        members = load_team_members(config)
        
        assert len(members) == 2
        assert all(isinstance(m, TeamMember) for m in members)
        assert members[0].name == "Alice"
        assert members[1].name == "Bob"

    def test_load_team_members_empty_list(self):
        """Test loading empty team members list."""
        from fetchers.base_fetcher import load_team_members
        
        config = {"team": {"name": "Empty Team", "members": []}}
        
        members = load_team_members(config)
        
        assert members == []
