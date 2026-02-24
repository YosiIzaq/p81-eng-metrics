"""Tests for merge_jira_pages.py script."""
import pytest
import json
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from merge_jira_pages import merge_jira_pages


class TestMergeJiraPages:
    """Tests for merging paginated Jira responses."""
    
    def test_merge_single_page(self, tmp_path):
        """Test merging a single page file."""
        # Create a single page file
        page1 = {
            "issues": [
                {"key": "P81-1", "fields": {"summary": "Issue 1", "assignee": {"displayName": "Alice"}}},
                {"key": "P81-2", "fields": {"summary": "Issue 2", "assignee": {"displayName": "Bob"}}}
            ]
        }
        
        page_file = tmp_path / "jira_year_page1.json"
        page_file.write_text(json.dumps(page1))
        
        # Run merge
        merge_jira_pages(str(tmp_path), "merged.json")
        
        # Check output
        output_file = tmp_path / "merged.json"
        assert output_file.exists()
        
        with open(output_file, "r") as f:
            merged = json.load(f)
        
        assert merged["total_count"] == 2
        assert len(merged["issues"]) == 2
        assert "jira_year_page1.json" in merged["merged_from"]
    
    def test_merge_multiple_pages(self, tmp_path):
        """Test merging multiple page files."""
        # Create multiple page files
        page1 = {
            "issues": [
                {"key": "P81-1", "fields": {"assignee": {"displayName": "Alice"}}}
            ]
        }
        page2 = {
            "issues": [
                {"key": "P81-2", "fields": {"assignee": {"displayName": "Bob"}}},
                {"key": "P81-3", "fields": {"assignee": {"displayName": "Alice"}}}
            ]
        }
        page3 = {
            "issues": [
                {"key": "P81-4", "fields": {"assignee": {"displayName": "Charlie"}}}
            ]
        }
        
        (tmp_path / "jira_year_page1.json").write_text(json.dumps(page1))
        (tmp_path / "jira_year_page2.json").write_text(json.dumps(page2))
        (tmp_path / "jira_year_page3.json").write_text(json.dumps(page3))
        
        merge_jira_pages(str(tmp_path), "merged.json")
        
        with open(tmp_path / "merged.json", "r") as f:
            merged = json.load(f)
        
        assert merged["total_count"] == 4
        assert len(merged["merged_from"]) == 3
    
    def test_merge_empty_directory(self, tmp_path, capsys):
        """Test merging when no page files exist."""
        merge_jira_pages(str(tmp_path), "merged.json")
        
        output = capsys.readouterr()
        assert "Found 0 page files" in output.out
        
        # Should still create output file with empty issues
        with open(tmp_path / "merged.json", "r") as f:
            merged = json.load(f)
        
        assert merged["total_count"] == 0
        assert merged["issues"] == []
    
    def test_merge_preserves_issue_structure(self, tmp_path):
        """Test that full issue structure is preserved."""
        page1 = {
            "issues": [{
                "key": "P81-123",
                "id": "10001",
                "fields": {
                    "summary": "Test issue",
                    "status": {"name": "Done"},
                    "assignee": {"displayName": "Alice", "accountId": "abc123"},
                    "customfield_10016": 5  # Story points
                }
            }]
        }
        
        (tmp_path / "jira_year_page1.json").write_text(json.dumps(page1))
        
        merge_jira_pages(str(tmp_path), "merged.json")
        
        with open(tmp_path / "merged.json", "r") as f:
            merged = json.load(f)
        
        issue = merged["issues"][0]
        assert issue["key"] == "P81-123"
        assert issue["fields"]["customfield_10016"] == 5
        assert issue["fields"]["assignee"]["accountId"] == "abc123"
    
    def test_merge_counts_by_assignee(self, tmp_path, capsys):
        """Test that breakdown by assignee is printed."""
        page1 = {
            "issues": [
                {"key": "P81-1", "fields": {"assignee": {"displayName": "Alice"}}},
                {"key": "P81-2", "fields": {"assignee": {"displayName": "Alice"}}},
                {"key": "P81-3", "fields": {"assignee": {"displayName": "Bob"}}}
            ]
        }
        
        (tmp_path / "jira_year_page1.json").write_text(json.dumps(page1))
        
        merge_jira_pages(str(tmp_path), "merged.json")
        
        output = capsys.readouterr()
        assert "Alice: 2" in output.out
        assert "Bob: 1" in output.out
    
    def test_merge_ignores_non_page_files(self, tmp_path):
        """Test that non-page JSON files are not merged."""
        # Create a page file
        page1 = {"issues": [{"key": "P81-1", "fields": {}}]}
        (tmp_path / "jira_year_page1.json").write_text(json.dumps(page1))
        
        # Create a non-page file (should be ignored)
        other = {"issues": [{"key": "P81-99", "fields": {}}]}
        (tmp_path / "other_data.json").write_text(json.dumps(other))
        (tmp_path / "jira_raw.json").write_text(json.dumps(other))
        
        merge_jira_pages(str(tmp_path), "merged.json")
        
        with open(tmp_path / "merged.json", "r") as f:
            merged = json.load(f)
        
        # Only page1 should be merged
        assert merged["total_count"] == 1
        assert len(merged["merged_from"]) == 1


class TestMergeJiraPagesEdgeCases:
    """Edge case tests for merge_jira_pages."""
    
    def test_merge_with_missing_assignee(self, tmp_path):
        """Test handling issues without assignee."""
        page1 = {
            "issues": [
                {"key": "P81-1", "fields": {"assignee": None}},
                {"key": "P81-2", "fields": {}}  # No assignee key at all
            ]
        }
        
        (tmp_path / "jira_year_page1.json").write_text(json.dumps(page1))
        
        # Should not crash
        merge_jira_pages(str(tmp_path), "merged.json")
        
        with open(tmp_path / "merged.json", "r") as f:
            merged = json.load(f)
        
        assert merged["total_count"] == 2
    
    def test_merge_sorted_output(self, tmp_path, capsys):
        """Test that page files are processed in sorted order."""
        # Create files in reverse order
        (tmp_path / "jira_year_page3.json").write_text(json.dumps({"issues": [{"key": "P81-3", "fields": {}}]}))
        (tmp_path / "jira_year_page1.json").write_text(json.dumps({"issues": [{"key": "P81-1", "fields": {}}]}))
        (tmp_path / "jira_year_page2.json").write_text(json.dumps({"issues": [{"key": "P81-2", "fields": {}}]}))
        
        merge_jira_pages(str(tmp_path), "merged.json")
        
        output = capsys.readouterr()
        
        # Check processing order
        pos1 = output.out.find("jira_year_page1.json")
        pos2 = output.out.find("jira_year_page2.json")
        pos3 = output.out.find("jira_year_page3.json")
        
        assert pos1 < pos2 < pos3  # Processed in sorted order
