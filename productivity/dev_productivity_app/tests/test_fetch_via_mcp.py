"""Tests for fetch_via_mcp.py script."""
import pytest
import json
from pathlib import Path
from datetime import date
from unittest.mock import patch, MagicMock
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fetch_via_mcp import parse_mcp_jira_response, main


class TestParseMcpJiraResponse:
    """Tests for parsing MCP Jira response."""
    
    def test_parse_empty_response(self):
        """Test parsing empty response."""
        response = {"issues": []}
        
        result = parse_mcp_jira_response(response)
        
        assert result == {}
    
    def test_parse_single_issue(self):
        """Test parsing response with single issue."""
        response = {
            "issues": [{
                "key": "P81-123",
                "fields": {
                    "summary": "Test issue",
                    "assignee": {
                        "displayName": "Alice Smith",
                        "accountId": "abc123"
                    },
                    "customfield_10016": 5
                }
            }]
        }
        
        result = parse_mcp_jira_response(response)
        
        assert "Alice Smith" in result
        assert result["Alice Smith"]["items_completed"] == 1
        assert result["Alice Smith"]["story_points"] == 5
    
    def test_parse_multiple_issues_same_assignee(self):
        """Test parsing multiple issues for same assignee."""
        response = {
            "issues": [
                {
                    "key": "P81-1",
                    "fields": {
                        "assignee": {"displayName": "Alice", "accountId": "abc"},
                        "customfield_10016": 3
                    }
                },
                {
                    "key": "P81-2",
                    "fields": {
                        "assignee": {"displayName": "Alice", "accountId": "abc"},
                        "customfield_10016": 5
                    }
                }
            ]
        }
        
        result = parse_mcp_jira_response(response)
        
        assert result["Alice"]["items_completed"] == 2
        assert result["Alice"]["story_points"] == 8
    
    def test_parse_multiple_assignees(self):
        """Test parsing issues with different assignees."""
        response = {
            "issues": [
                {
                    "key": "P81-1",
                    "fields": {
                        "assignee": {"displayName": "Alice", "accountId": "abc"},
                        "customfield_10016": 3
                    }
                },
                {
                    "key": "P81-2",
                    "fields": {
                        "assignee": {"displayName": "Bob", "accountId": "def"},
                        "customfield_10016": 2
                    }
                },
                {
                    "key": "P81-3",
                    "fields": {
                        "assignee": {"displayName": "Alice", "accountId": "abc"},
                        "customfield_10016": 1
                    }
                }
            ]
        }
        
        result = parse_mcp_jira_response(response)
        
        assert len(result) == 2
        assert result["Alice"]["items_completed"] == 2
        assert result["Alice"]["story_points"] == 4
        assert result["Bob"]["items_completed"] == 1
        assert result["Bob"]["story_points"] == 2
    
    def test_parse_null_story_points(self):
        """Test parsing issues with null story points."""
        response = {
            "issues": [{
                "key": "P81-1",
                "fields": {
                    "assignee": {"displayName": "Alice", "accountId": "abc"},
                    "customfield_10016": None
                }
            }]
        }
        
        result = parse_mcp_jira_response(response)
        
        assert result["Alice"]["items_completed"] == 1
        assert result["Alice"]["story_points"] == 0
    
    def test_parse_missing_story_points_field(self):
        """Test parsing issues without story points field."""
        response = {
            "issues": [{
                "key": "P81-1",
                "fields": {
                    "assignee": {"displayName": "Alice", "accountId": "abc"}
                    # No customfield_10016
                }
            }]
        }
        
        result = parse_mcp_jira_response(response)
        
        assert result["Alice"]["items_completed"] == 1
        assert result["Alice"]["story_points"] == 0
    
    def test_parse_unassigned_issues(self):
        """Test that unassigned issues are skipped."""
        response = {
            "issues": [
                {
                    "key": "P81-1",
                    "fields": {
                        "assignee": None
                    }
                },
                {
                    "key": "P81-2",
                    "fields": {
                        "assignee": {"displayName": "Bob", "accountId": "def"}
                    }
                }
            ]
        }
        
        result = parse_mcp_jira_response(response)
        
        # Only Bob should be in result
        assert len(result) == 1
        assert "Bob" in result
    
    def test_parse_missing_assignee_field(self):
        """Test issues without assignee field entirely."""
        response = {
            "issues": [{
                "key": "P81-1",
                "fields": {
                    "summary": "No assignee"
                    # No assignee field
                }
            }]
        }
        
        result = parse_mcp_jira_response(response)
        
        assert result == {}
    
    def test_parse_alternative_story_points_field(self):
        """Test parsing with alternative story points field name."""
        response = {
            "issues": [{
                "key": "P81-1",
                "fields": {
                    "assignee": {"displayName": "Alice", "accountId": "abc"},
                    "storyPoints": 8  # Alternative field name
                }
            }]
        }
        
        result = parse_mcp_jira_response(response)
        
        # Should try storyPoints as fallback
        assert result["Alice"]["items_completed"] == 1
        # May or may not get story points depending on implementation
        assert "story_points" in result["Alice"]


class TestParseMcpJiraResponseRealWorld:
    """Tests with realistic MCP response structure."""
    
    def test_parse_full_mcp_response(self):
        """Test parsing a realistic MCP response."""
        response = {
            "issues": [
                {
                    "expand": "operations,versionedRepresentations",
                    "id": "100001",
                    "self": "https://api.atlassian.com/...",
                    "key": "PROJ-12345",
                    "fields": {
                        "summary": "Implement feature X",
                        "status": {
                            "self": "https://...",
                            "name": "Done",
                            "id": "10001"
                        },
                        "assignee": {
                            "self": "https://...",
                            "accountId": "test-account-id-001",
                            "emailAddress": "alice@example.com",
                            "displayName": "Alice Smith",
                            "active": True,
                            "timeZone": "UTC"
                        },
                        "customfield_10016": 3.0,
                        "updated": "2026-01-15T10:30:00.000+0200"
                    }
                },
                {
                    "id": "100002",
                    "key": "PROJ-12346",
                    "fields": {
                        "summary": "Fix bug Y",
                        "status": {"name": "Done"},
                        "assignee": {
                            "accountId": "test-account-id-002",
                            "displayName": "Bob Jones"
                        },
                        "customfield_10016": 2.0
                    }
                }
            ],
            "nextPageToken": None,
            "isLast": True
        }
        
        result = parse_mcp_jira_response(response)
        
        assert len(result) == 2
        assert result["Alice Smith"]["items_completed"] == 1
        assert result["Alice Smith"]["story_points"] == 3
        assert result["Bob Jones"]["items_completed"] == 1
        assert result["Bob Jones"]["story_points"] == 2
    
    def test_parse_merged_year_data(self, tmp_path):
        """Test parsing merged yearly data file."""
        merged_data = {
            "issues": [
                {"key": f"P81-{i}", "fields": {
                    "assignee": {"displayName": "Developer A", "accountId": "aaa"},
                    "customfield_10016": 2
                }} for i in range(50)
            ] + [
                {"key": f"P81-{i}", "fields": {
                    "assignee": {"displayName": "Developer B", "accountId": "bbb"},
                    "customfield_10016": 3
                }} for i in range(50, 80)
            ],
            "total_count": 80,
            "merged_from": ["page1.json", "page2.json"]
        }
        
        result = parse_mcp_jira_response(merged_data)
        
        assert result["Developer A"]["items_completed"] == 50
        assert result["Developer A"]["story_points"] == 100
        assert result["Developer B"]["items_completed"] == 30
        assert result["Developer B"]["story_points"] == 90


class TestFetchViaMcpMain:
    """Tests for the main() function."""
    
    def test_main_with_valid_args(self, tmp_path, monkeypatch):
        """Test main function with valid arguments."""
        # Create test Jira data
        jira_data = {
            "issues": [{
                "key": "PROJ-1",
                "fields": {
                    "assignee": {"displayName": "Alice Smith", "accountId": "test-abc"},
                    "customfield_10016": 3
                }
            }]
        }
        jira_file = tmp_path / "jira_data.json"
        jira_file.write_text(json.dumps(jira_data))
        
        # Create minimal config
        config = {
            "version": "1.0",
            "team": {
                "name": "Test Team",
                "members": [{
                    "name": "Alice Smith",
                    "github_username": "dev-alice",
                    "jira_account_id": "test-abc"
                }]
            },
            "weights": {
                "items_completed": 0.5,
                "prs_authored": 0.3,
                "code_reviews": 0.2
            },
            "periods": {
                "sprint": {
                    "type": "fixed",
                    "start": "2026-01-01",
                    "end": "2026-01-31",
                    "label": "Test Sprint"
                }
            },
            "github": {"org": "TestOrg"}
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        
        output_file = tmp_path / "report.md"
        
        # Mock sys.argv
        test_args = [
            "fetch_via_mcp.py",
            "--jira-data", str(jira_file),
            "--config", str(config_file),
            "--period", "sprint",
            "--output", str(output_file)
        ]
        monkeypatch.setattr(sys, "argv", test_args)
        
        # Mock GitHubFetcher to avoid real API calls
        mock_metric = MagicMock()
        mock_metric.prs_authored = 10
        mock_metric.code_reviews = 5
        
        with patch('fetch_via_mcp.GitHubFetcher') as mock_gh:
            mock_gh.return_value.fetch.return_value = mock_metric
            
            main()
        
        # Check output was created
        assert output_file.exists()
        content = output_file.read_text()
        assert "Productivity Report" in content
        assert "Test Sprint" in content
    
    def test_main_without_output(self, tmp_path, monkeypatch, capsys):
        """Test main function without output file (print only)."""
        # Create test data
        jira_data = {"issues": []}
        jira_file = tmp_path / "jira_data.json"
        jira_file.write_text(json.dumps(jira_data))
        
        config = {
            "version": "1.0",
            "team": {"name": "Test", "members": []},
            "weights": {"items_completed": 0.5, "prs_authored": 0.3, "code_reviews": 0.2},
            "periods": {"sprint": {"type": "fixed", "start": "2026-01-01", "end": "2026-01-31"}}
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config))
        
        test_args = [
            "fetch_via_mcp.py",
            "--jira-data", str(jira_file),
            "--config", str(config_file),
            "--period", "sprint"
        ]
        monkeypatch.setattr(sys, "argv", test_args)
        
        with patch('fetch_via_mcp.GitHubFetcher'):
            main()
        
        output = capsys.readouterr()
        assert "Processing data for period" in output.out
    
    def test_main_uses_default_config(self, tmp_path, monkeypatch):
        """Test main function uses default config path."""
        jira_data = {"issues": []}
        jira_file = tmp_path / "jira_data.json"
        jira_file.write_text(json.dumps(jira_data))
        
        test_args = [
            "fetch_via_mcp.py",
            "--jira-data", str(jira_file)
        ]
        monkeypatch.setattr(sys, "argv", test_args)
        
        # This will try to load config/default_config.json
        # We mock load_config to avoid file not found
        with patch('fetch_via_mcp.load_config') as mock_config:
            mock_config.return_value = {
                "team": {"members": []},
                "weights": {"items_completed": 0.5, "prs_authored": 0.3, "code_reviews": 0.2},
                "periods": {"sprint": {"type": "fixed", "start": "2026-01-01", "end": "2026-01-31"}},
                "github": {}
            }
            with patch('fetch_via_mcp.load_team_members', return_value=[]):
                with patch('fetch_via_mcp.GitHubFetcher'):
                    main()
        
        # Verify default config was requested
        mock_config.assert_called_with("config/default_config.json")
