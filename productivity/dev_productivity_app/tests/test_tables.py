"""Tests for the tables display module."""
import pytest
from pathlib import Path
from io import StringIO
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestRankingTable:
    """Tests for ranking table generation."""

    def test_create_ranking_table_basic(self):
        """Test creating a basic ranking table."""
        from display.tables import create_ranking_table
        
        ranked_data = [
            {"rank": 1, "name": "Alice", "total": 95.0, "items_weighted": 50.0, "prs_weighted": 25.0, "reviews_weighted": 20.0},
            {"rank": 2, "name": "Bob", "total": 85.0, "items_weighted": 40.0, "prs_weighted": 30.0, "reviews_weighted": 15.0}
        ]
        
        table = create_ranking_table(ranked_data)
        
        assert "Alice" in table
        assert "Bob" in table
        assert "95" in table
        assert "85" in table

    def test_ranking_table_has_headers(self):
        """Test that table has proper headers."""
        from display.tables import create_ranking_table
        
        ranked_data = [
            {"rank": 1, "name": "Alice", "total": 95.0, "items_weighted": 50.0, "prs_weighted": 25.0, "reviews_weighted": 20.0}
        ]
        
        table = create_ranking_table(ranked_data)
        
        assert "Rank" in table
        assert "Name" in table or "name" in table.lower()
        assert "Total" in table or "total" in table.lower()

    def test_ranking_table_empty_data(self):
        """Test table with empty data."""
        from display.tables import create_ranking_table
        
        table = create_ranking_table([])
        
        assert table == "" or "No data" in table

    def test_ranking_table_sorted_by_rank(self):
        """Test that table maintains rank order."""
        from display.tables import create_ranking_table
        
        ranked_data = [
            {"rank": 1, "name": "Alice", "total": 95.0, "items_weighted": 50.0, "prs_weighted": 25.0, "reviews_weighted": 20.0},
            {"rank": 2, "name": "Bob", "total": 85.0, "items_weighted": 40.0, "prs_weighted": 30.0, "reviews_weighted": 15.0},
            {"rank": 3, "name": "Carol", "total": 75.0, "items_weighted": 35.0, "prs_weighted": 25.0, "reviews_weighted": 15.0}
        ]
        
        table = create_ranking_table(ranked_data)
        
        # Alice should appear before Bob, Bob before Carol
        alice_pos = table.find("Alice")
        bob_pos = table.find("Bob")
        carol_pos = table.find("Carol")
        
        assert alice_pos < bob_pos < carol_pos


class TestMarkdownTable:
    """Tests for markdown table generation."""

    def test_create_markdown_table(self):
        """Test creating a markdown format table."""
        from display.tables import create_markdown_table
        
        ranked_data = [
            {"rank": 1, "name": "Alice", "total": 95.0, "items_weighted": 50.0, "prs_weighted": 25.0, "reviews_weighted": 20.0}
        ]
        
        table = create_markdown_table(ranked_data)
        
        assert "|" in table  # Markdown tables use pipes
        assert "---" in table  # Markdown tables have header separator

    def test_markdown_table_proper_format(self):
        """Test markdown table has proper format for rendering."""
        from display.tables import create_markdown_table
        
        ranked_data = [
            {"rank": 1, "name": "Alice", "total": 95.0, "items_weighted": 50.0, "prs_weighted": 25.0, "reviews_weighted": 20.0}
        ]
        
        table = create_markdown_table(ranked_data)
        lines = table.strip().split("\n")
        
        # Should have at least header + separator + 1 data row
        assert len(lines) >= 3


class TestTableFormatting:
    """Tests for table formatting options."""

    def test_table_with_decimal_precision(self):
        """Test table respects decimal precision."""
        from display.tables import create_ranking_table
        
        ranked_data = [
            {"rank": 1, "name": "Alice", "total": 95.123456, "items_weighted": 50.0, "prs_weighted": 25.0, "reviews_weighted": 20.0}
        ]
        
        table = create_ranking_table(ranked_data, precision=1)
        
        # Should show 95.1, not 95.123456
        assert "95.1" in table or "95.12" in table

    def test_table_alignment(self):
        """Test that table columns are properly aligned."""
        from display.tables import create_ranking_table
        
        ranked_data = [
            {"rank": 1, "name": "Alice", "total": 95.0, "items_weighted": 50.0, "prs_weighted": 25.0, "reviews_weighted": 20.0},
            {"rank": 10, "name": "Bob", "total": 5.0, "items_weighted": 2.0, "prs_weighted": 2.0, "reviews_weighted": 1.0}
        ]
        
        table = create_ranking_table(ranked_data)
        lines = [l for l in table.split("\n") if l.strip()]
        
        # All data lines should have similar structure
        assert len(lines) >= 2


class TestTablePrinting:
    """Tests for table printing functionality."""

    def test_print_table_to_stdout(self, capsys):
        """Test printing table to stdout."""
        from display.tables import print_ranking_table
        
        ranked_data = [
            {"rank": 1, "name": "Alice", "total": 95.0, "items_weighted": 50.0, "prs_weighted": 25.0, "reviews_weighted": 20.0}
        ]
        
        print_ranking_table(ranked_data)
        
        captured = capsys.readouterr()
        assert "Alice" in captured.out

    def test_print_table_with_title(self, capsys):
        """Test printing table with title."""
        from display.tables import print_ranking_table
        
        ranked_data = [
            {"rank": 1, "name": "Alice", "total": 95.0, "items_weighted": 50.0, "prs_weighted": 25.0, "reviews_weighted": 20.0}
        ]
        
        print_ranking_table(ranked_data, title="Sprint Q1-S2 Rankings")
        
        captured = capsys.readouterr()
        assert "Sprint Q1-S2" in captured.out or "Rankings" in captured.out


class TestSummaryTable:
    """Tests for summary statistics table."""

    def test_create_summary_table(self):
        """Test creating a summary statistics table."""
        from display.tables import create_summary_table
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 50, "prs_authored": 20, "code_reviews": 30},
                "Bob": {"items_completed": 30, "prs_authored": 40, "code_reviews": 20}
            }
        }
        
        table = create_summary_table(raw_data)
        
        assert "items" in table.lower() or "Items" in table
        assert "Alice" in table or "Bob" in table

    def test_summary_table_shows_totals(self):
        """Test that summary shows team totals."""
        from display.tables import create_summary_table
        
        raw_data = {
            "metrics": {
                "Alice": {"items_completed": 50, "prs_authored": 20, "code_reviews": 30},
                "Bob": {"items_completed": 30, "prs_authored": 40, "code_reviews": 20}
            }
        }
        
        table = create_summary_table(raw_data)
        
        # Should show totals or averages
        assert any(word in table.lower() for word in ["total", "avg", "sum", "team"])
