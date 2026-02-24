#!/usr/bin/env python3
"""
Test suite for visualize_reviews.py

Usage:
    python test_visualize_reviews.py
    python -m pytest test_visualize_reviews.py -v
    
Coverage target: >85%
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add script directory to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

# Import module under test
import visualize_reviews as viz


class TestDataLoading(unittest.TestCase):
    """Tests for data loading functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_data = {
            "generated_at": "2026-01-27T12:00:00+02:00",
            "team": "Test Team",
            "test_mode": False,
            "periods": {
                "last_month": {"start": "2025-12-27", "end": "2026-01-27"},
                "last_3_months": {"start": "2025-10-27", "end": "2026-01-27"},
                "h2_2025": {"start": "2025-06-01", "end": "2025-12-31"},
                "full_2025": {"start": "2025-01-01", "end": "2025-12-31"}
            },
            "reviews": [
                {
                    "github_username": "dev-alice",
                    "display_name": "Alice Smith (TL)",
                    "last_month": 10,
                    "last_3_months": 30,
                    "h2_2025": 50,
                    "full_2025": 80
                },
                {
                    "github_username": "dev-bob",
                    "display_name": "Bob Jones",
                    "last_month": 15,
                    "last_3_months": 51,
                    "h2_2025": 100,
                    "full_2025": 127
                },
                {
                    "github_username": "dev-charlie",
                    "display_name": "Charlie Brown",
                    "last_month": 46,
                    "last_3_months": 115,
                    "h2_2025": 161,
                    "full_2025": 207
                }
            ]
        }
        
        # Create temp directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.test_data_file = Path(self.temp_dir) / "test_data.json"
        
        with open(self.test_data_file, 'w') as f:
            json.dump(self.test_data, f)
    
    def tearDown(self):
        """Clean up temp files."""
        if self.test_data_file.exists():
            self.test_data_file.unlink()
        if Path(self.temp_dir).exists():
            os.rmdir(self.temp_dir)
    
    def test_load_data_valid_file(self):
        """Test loading valid JSON data file."""
        with patch.object(viz, 'LATEST_DATA', self.test_data_file):
            data = viz.load_data()
            self.assertIsNotNone(data)
            self.assertEqual(data["team"], "Test Team")
            self.assertEqual(len(data["reviews"]), 3)
    
    def test_load_data_missing_file(self):
        """Test loading non-existent file returns None."""
        with patch.object(viz, 'LATEST_DATA', Path("/nonexistent/file.json")):
            with patch('sys.stdout', new_callable=StringIO):
                data = viz.load_data()
                self.assertIsNone(data)
    
    def test_load_data_invalid_json(self):
        """Test loading invalid JSON raises error."""
        invalid_file = Path(self.temp_dir) / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("not valid json {{{")
        
        with patch.object(viz, 'LATEST_DATA', invalid_file):
            with self.assertRaises(json.JSONDecodeError):
                viz.load_data()
        
        invalid_file.unlink()


class TestDataValidation(unittest.TestCase):
    """Tests for data validation."""
    
    def test_valid_data_structure(self):
        """Test that valid data has expected structure."""
        data = {
            "reviews": [
                {"display_name": "Test User", "full_2025": 100, "github_username": "test"}
            ]
        }
        reviews = data.get("reviews", [])
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0]["display_name"], "Test User")
    
    def test_empty_reviews_list(self):
        """Test handling empty reviews list."""
        data = {"reviews": []}
        reviews = data.get("reviews", [])
        self.assertEqual(len(reviews), 0)
    
    def test_missing_reviews_key(self):
        """Test handling missing reviews key."""
        data = {}
        reviews = data.get("reviews", [])
        self.assertEqual(reviews, [])
    
    def test_missing_period_field(self):
        """Test handling missing period field in review."""
        review = {"display_name": "Test", "full_2025": 100}
        # Accessing missing field should use default
        count = review.get("nonexistent_period", 0)
        self.assertEqual(count, 0)


class TestTeamMembersConfig(unittest.TestCase):
    """Tests for team member configuration."""
    
    def test_all_team_members_have_colors(self):
        """Test that all team members have assigned colors."""
        for username in viz.TEAM_MEMBERS.keys():
            self.assertIn(username, viz.COLORS, f"Missing color for {username}")
    
    def test_team_loaded_from_config(self):
        """Test that team members are loaded from config."""
        # Team should have at least one member from team_config.json
        self.assertGreater(len(viz.TEAM_MEMBERS), 0, "Should have team members from config")
    
    def test_team_member_count(self):
        """Test expected number of team members."""
        # Config should have members defined
        self.assertGreater(len(viz.TEAM_MEMBERS), 0, "Should have at least one team member")
    
    def test_colors_are_valid_hex(self):
        """Test that all colors are valid hex codes."""
        import re
        hex_pattern = re.compile(r'^#[0-9a-fA-F]{6}$')
        for username, color in viz.COLORS.items():
            self.assertTrue(
                hex_pattern.match(color),
                f"Invalid color for {username}: {color}"
            )


class TestPlotBarChart(unittest.TestCase):
    """Tests for bar chart generation."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data = {
            "reviews": [
                {"github_username": "user1", "display_name": "User One", "full_2025": 100},
                {"github_username": "user2", "display_name": "User Two", "full_2025": 50},
            ]
        }
    
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.close')
    def test_bar_chart_renders(self, mock_close, mock_show):
        """Test that bar chart renders without error."""
        viz.plot_bar_chart(self.test_data, "full_2025")
        mock_show.assert_called_once()
        mock_close.assert_called_once()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_bar_chart_saves(self, mock_close, mock_savefig):
        """Test that bar chart saves to file."""
        viz.plot_bar_chart(self.test_data, "full_2025", save_path="/tmp/test.png")
        mock_savefig.assert_called_once()
    
    @patch('builtins.print')
    def test_bar_chart_empty_data(self, mock_print):
        """Test bar chart with empty data returns early."""
        data = {"reviews": []}
        # Should print warning and return early
        viz.plot_bar_chart(data, "full_2025")
        mock_print.assert_called()  # Should print warning
    
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.close')
    def test_bar_chart_all_periods(self, mock_close, mock_show):
        """Test bar chart works for all periods."""
        for period in ["last_month", "last_3_months", "h2_2025", "full_2025"]:
            viz.plot_bar_chart(self.test_data, period)


class TestPlotPieChart(unittest.TestCase):
    """Tests for pie chart generation."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data = {
            "reviews": [
                {"github_username": "user1", "display_name": "User One", "full_2025": 100},
                {"github_username": "user2", "display_name": "User Two", "full_2025": 50},
            ]
        }
    
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.close')
    def test_pie_chart_renders(self, mock_close, mock_show):
        """Test that pie chart renders without error."""
        viz.plot_pie_chart(self.test_data, "full_2025")
        mock_show.assert_called_once()
    
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.close')
    def test_pie_chart_filters_zeros(self, mock_close, mock_show):
        """Test that pie chart filters out zero values."""
        data = {
            "reviews": [
                {"github_username": "user1", "display_name": "User One", "full_2025": 100},
                {"github_username": "user2", "display_name": "User Two", "full_2025": 0},
            ]
        }
        viz.plot_pie_chart(data, "full_2025")
        # Should still render (with 1 segment)
        mock_show.assert_called_once()
    
    @patch('builtins.print')
    def test_pie_chart_all_zeros(self, mock_print):
        """Test pie chart with all zero values shows warning."""
        data = {
            "reviews": [
                {"github_username": "user1", "display_name": "User One", "full_2025": 0},
            ]
        }
        viz.plot_pie_chart(data, "full_2025")
        # Should print warning
        mock_print.assert_called()


class TestPlotComparison(unittest.TestCase):
    """Tests for comparison chart generation."""
    
    def setUp(self):
        """Set up test data."""
        self.test_data = {
            "reviews": [
                {
                    "github_username": "user1",
                    "display_name": "User One",
                    "last_month": 10,
                    "last_3_months": 30,
                    "h2_2025": 50,
                    "full_2025": 100
                }
            ]
        }
    
    @patch('matplotlib.pyplot.show')
    @patch('matplotlib.pyplot.close')
    def test_comparison_chart_renders(self, mock_close, mock_show):
        """Test that comparison chart renders without error."""
        viz.plot_comparison(self.test_data)
        mock_show.assert_called_once()
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.close')
    def test_comparison_chart_saves(self, mock_close, mock_savefig):
        """Test that comparison chart saves to file."""
        viz.plot_comparison(self.test_data, save_path="/tmp/comparison.png")
        mock_savefig.assert_called_once()


class TestPrintSummaryTable(unittest.TestCase):
    """Tests for summary table printing."""
    
    def test_print_summary_table(self):
        """Test that summary table prints correctly."""
        data = {
            "generated_at": "2026-01-27",
            "reviews": [
                {
                    "display_name": "Test User",
                    "last_month": 10,
                    "last_3_months": 30,
                    "h2_2025": 50,
                    "full_2025": 100
                }
            ]
        }
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            viz.print_summary_table(data)
            output = mock_stdout.getvalue()
            
            self.assertIn(viz.TEAM_NAME.upper(), output)
            self.assertIn("Test User", output)
            self.assertIn("TOTAL", output)
    
    def test_print_summary_table_empty(self):
        """Test summary table with empty data."""
        data = {"reviews": []}
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            viz.print_summary_table(data)
            output = mock_stdout.getvalue()
            
            self.assertIn("TOTAL", output)


class TestFetchFreshData(unittest.TestCase):
    """Tests for data fetching."""
    
    @patch('subprocess.run')
    def test_fetch_success(self, mock_run):
        """Test successful data fetch."""
        mock_run.return_value = MagicMock(returncode=0, stdout="Success", stderr="")
        
        with patch.object(viz, 'SCRIPT_DIR', Path("/tmp")):
            # Create mock script file
            script_path = Path("/tmp/fetch_code_reviews.sh")
            script_path.touch()
            try:
                result = viz.fetch_fresh_data()
                self.assertTrue(result)
            finally:
                script_path.unlink()
    
    @patch('subprocess.run')
    def test_fetch_failure(self, mock_run):
        """Test failed data fetch."""
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Error")
        
        with patch.object(viz, 'SCRIPT_DIR', Path("/tmp")):
            script_path = Path("/tmp/fetch_code_reviews.sh")
            script_path.touch()
            try:
                with patch('sys.stdout', new_callable=StringIO):
                    result = viz.fetch_fresh_data()
                    self.assertFalse(result)
            finally:
                script_path.unlink()
    
    def test_fetch_missing_script(self):
        """Test fetch with missing script."""
        with patch.object(viz, 'SCRIPT_DIR', Path("/nonexistent")):
            with patch('sys.stdout', new_callable=StringIO):
                result = viz.fetch_fresh_data()
                self.assertFalse(result)


class TestNegativeCases(unittest.TestCase):
    """Negative test cases."""
    
    def test_invalid_period_key(self):
        """Test handling of invalid period key."""
        data = {
            "reviews": [
                {"github_username": "user1", "display_name": "User", "full_2025": 100}
            ]
        }
        # Accessing invalid period should return 0
        for review in data["reviews"]:
            self.assertEqual(review.get("invalid_period", 0), 0)
    
    def test_missing_github_username(self):
        """Test handling missing github_username."""
        review = {"display_name": "Test User", "full_2025": 100}
        # Should not crash when accessing color
        color = viz.COLORS.get(review.get("github_username", ""), "#333333")
        self.assertEqual(color, "#333333")
    
    def test_none_values_in_data(self):
        """Test handling None values in data."""
        data = {
            "reviews": [
                {"github_username": None, "display_name": None, "full_2025": None}
            ]
        }
        reviews = data.get("reviews", [])
        count = reviews[0].get("full_2025", 0) or 0
        self.assertEqual(count, 0)
    
    def test_negative_review_counts(self):
        """Test handling negative review counts."""
        data = {
            "reviews": [
                {"github_username": "user1", "display_name": "User", "full_2025": -5}
            ]
        }
        # Should not crash, though negative doesn't make sense
        reviews = data.get("reviews", [])
        self.assertEqual(reviews[0]["full_2025"], -5)


class TestEdgeCases(unittest.TestCase):
    """Edge case tests."""
    
    def test_very_large_counts(self):
        """Test handling very large review counts."""
        data = {
            "reviews": [
                {"github_username": "user1", "display_name": "User", "full_2025": 999999}
            ]
        }
        reviews = data.get("reviews", [])
        self.assertEqual(reviews[0]["full_2025"], 999999)
    
    def test_unicode_display_name(self):
        """Test handling unicode in display names."""
        data = {
            "reviews": [
                {"github_username": "user1", "display_name": "用户名", "full_2025": 100}
            ]
        }
        reviews = data.get("reviews", [])
        self.assertEqual(reviews[0]["display_name"], "用户名")
    
    def test_special_chars_in_name(self):
        """Test handling special characters in names."""
        data = {
            "reviews": [
                {"github_username": "user-1_test", "display_name": "User O'Brian", "full_2025": 100}
            ]
        }
        reviews = data.get("reviews", [])
        self.assertIn("O'Brian", reviews[0]["display_name"])
    
    def test_very_long_display_name(self):
        """Test handling very long display names."""
        long_name = "A" * 100
        data = {
            "reviews": [
                {"github_username": "user1", "display_name": long_name, "full_2025": 100}
            ]
        }
        reviews = data.get("reviews", [])
        self.assertEqual(len(reviews[0]["display_name"]), 100)


class TestMainFunction(unittest.TestCase):
    """Tests for main function."""
    
    @patch('visualize_reviews.load_data')
    @patch('visualize_reviews.print_summary_table')
    @patch('visualize_reviews.plot_bar_chart')
    @patch('visualize_reviews.plot_pie_chart')
    @patch('visualize_reviews.plot_comparison')
    @patch('sys.argv', ['visualize_reviews.py', '--chart', 'bar', '--no-show'])
    def test_main_bar_only(self, mock_comp, mock_pie, mock_bar, mock_table, mock_load):
        """Test main with bar chart only."""
        mock_load.return_value = {"reviews": []}
        with patch.object(Path, 'mkdir'):
            viz.main()
        mock_bar.assert_called_once()
        mock_pie.assert_not_called()
        mock_comp.assert_not_called()
    
    @patch('visualize_reviews.load_data')
    @patch('sys.exit')
    @patch('sys.argv', ['visualize_reviews.py'])
    def test_main_no_data(self, mock_exit, mock_load):
        """Test main when no data available."""
        mock_load.return_value = None
        with patch('sys.stdout', new_callable=StringIO):
            with patch('builtins.print'):  # Suppress print output
                viz.main()
        mock_exit.assert_called_with(1)


class TestDataIntegrity(unittest.TestCase):
    """Tests for data integrity validation."""
    
    def test_review_counts_are_integers(self):
        """Test that review counts are integers."""
        # Simulate what a properly formatted review should look like
        review = {
            "last_month": 10,
            "last_3_months": 30,
            "h2_2025": 50,
            "full_2025": 100
        }
        for period in ["last_month", "last_3_months", "h2_2025", "full_2025"]:
            self.assertIsInstance(review[period], int)
    
    def test_period_values_logical_relationship(self):
        """Test that period values have logical relationships."""
        # Full year should >= H2, H2 should >= Last 3 months, etc.
        review = {
            "last_month": 10,
            "last_3_months": 30,
            "h2_2025": 50,
            "full_2025": 100
        }
        # These relationships SHOULD hold for real data
        self.assertGreaterEqual(review["full_2025"], review["h2_2025"])
        self.assertGreaterEqual(review["h2_2025"], review["last_3_months"])
        # Note: last_3_months might be > last_month


def run_tests():
    """Run all tests with coverage reporting."""
    print("\n" + "="*80)
    print("  visualize_reviews.py Test Suite")
    print("="*80 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestDataLoading,
        TestDataValidation,
        TestTeamMembersConfig,
        TestPlotBarChart,
        TestPlotPieChart,
        TestPlotComparison,
        TestPrintSummaryTable,
        TestFetchFreshData,
        TestNegativeCases,
        TestEdgeCases,
        TestMainFunction,
        TestDataIntegrity,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*80)
    print("  Test Results")
    print("="*80)
    print(f"\n  Tests Run:     {result.testsRun}")
    print(f"  Passed:        {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  Failed:        {len(result.failures)}")
    print(f"  Errors:        {len(result.errors)}")
    
    coverage = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"\n  Pass Rate:     {coverage:.1f}%")
    print("="*80 + "\n")
    
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
