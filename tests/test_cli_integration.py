"""
Comprehensive CLI integration tests.
"""

import json
import pytest
from subprocess import run, PIPE
import sys


class TestCLIIntegration:
    """Test CLI interface comprehensively."""

    def test_cli_basic_usage(self):
        """Test basic CLI usage with standard parameters."""
        result = run(
            [
                sys.executable,
                "-m",
                "dpw",
                "200",
                "1000x2000",
                "scribe=50x50",
                "edge=3",
                "yield=80",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 0
        assert "total_dies=" in result.stdout
        assert "yield_dies=" in result.stdout
        assert "utilization=" in result.stdout
        assert "method=corner" in result.stdout
        assert "notch=none" in result.stdout

    def test_cli_json_output(self):
        """Test JSON output format."""
        result = run(
            [
                sys.executable,
                "-m",
                "dpw",
                "--json",
                "200",
                "1000x2000",
                "scribe=50x50",
                "edge=3",
                "yield=80",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 0

        # Parse JSON output
        output_data = json.loads(result.stdout)

        # Verify required fields
        assert "total_dies" in output_data
        assert "yield_dies" in output_data
        assert "wafer_utilization" in output_data
        assert "calculation_method" in output_data
        assert "parameters" in output_data

        # Verify data types
        assert isinstance(output_data["total_dies"], int)
        assert isinstance(output_data["yield_dies"], int)
        assert isinstance(output_data["wafer_utilization"], (int, float))
        assert isinstance(output_data["calculation_method"], str)
        assert isinstance(output_data["parameters"], dict)

    def test_cli_all_validation_methods(self):
        """Test CLI with all validation methods."""
        methods = ["center", "corner", "area", "strict"]

        for method in methods:
            result = run(
                [sys.executable, "-m", "dpw", "200", "1000x2000", f"method={method}"],
                capture_output=True,
                text=True,
                cwd="/Users/dean/Documents/git/dpw",
            )

            assert result.returncode == 0
            assert f"method={method}" in result.stdout

    def test_cli_all_notch_types(self):
        """Test CLI with all notch types."""
        notch_types = ["none", "v90", "flat"]

        for notch in notch_types:
            result = run(
                [sys.executable, "-m", "dpw", "200", "1000x2000", f"notch={notch}"],
                capture_output=True,
                text=True,
                cwd="/Users/dean/Documents/git/dpw",
            )

            assert result.returncode == 0
            assert f"notch={notch}" in result.stdout

    def test_cli_edge_cases(self):
        """Test CLI edge cases."""

        # Test minimum parameters
        result = run(
            [sys.executable, "-m", "dpw", "50", "100x100"],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 0
        assert "total_dies=" in result.stdout

        # Test large parameters
        result = run(
            [sys.executable, "-m", "dpw", "300", "10000x10000", "scribe=100x100"],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 0

    def test_cli_error_conditions(self):
        """Test CLI error handling."""

        # Test insufficient arguments
        result = run(
            [sys.executable, "-m", "dpw"],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 2  # argparse error code

        # Test invalid die format
        result = run(
            [sys.executable, "-m", "dpw", "200", "invalid"],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 2
        assert "bad arguments" in result.stderr

        # Test invalid wafer diameter
        result = run(
            [sys.executable, "-m", "dpw", "invalid", "1000x2000"],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 2
        assert "bad arguments" in result.stderr

    def test_cli_parameter_validation(self):
        """Test CLI parameter validation."""

        # Test negative yield
        result = run(
            [sys.executable, "-m", "dpw", "200", "1000x2000", "yield=-10"],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 1  # Calculation failed
        assert "calculation failed" in result.stderr

        # Test excessive edge exclusion
        result = run(
            [sys.executable, "-m", "dpw", "200", "1000x2000", "edge=150"],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 1
        assert "calculation failed" in result.stderr

    def test_cli_complex_parameters(self):
        """Test CLI with complex parameter combinations."""

        # Test with all parameters
        result = run(
            [
                sys.executable,
                "-m",
                "dpw",
                "200",
                "1500x2500",
                "scribe=75x75",
                "edge=5",
                "yield=95",
                "method=area",
                "notch=v90",
                "notch_depth=2.5",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 0
        assert "total_dies=" in result.stdout
        assert "yield_dies=" in result.stdout
        assert "utilization=" in result.stdout
        assert "method=area" in result.stdout
        assert "notch=v90" in result.stdout

    def test_cli_help(self):
        """Test CLI help functionality."""

        # Test help flag
        result = run(
            [sys.executable, "-m", "dpw", "--help"],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 0
        assert "Die per wafer calculator" in result.stdout
        assert "--json" in result.stdout
        assert "scribe=" in result.stdout
        assert "edge=" in result.stdout
        assert "yield=" in result.stdout
        assert "method=" in result.stdout
        assert "notch=" in result.stdout

    def test_cli_json_vs_text_consistency(self):
        """Test that JSON and text outputs are consistent."""

        # Run same command with JSON and text output
        json_result = run(
            [
                sys.executable,
                "-m",
                "dpw",
                "--json",
                "200",
                "1000x2000",
                "scribe=50x50",
                "edge=3",
                "yield=80",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        text_result = run(
            [
                sys.executable,
                "-m",
                "dpw",
                "200",
                "1000x2000",
                "scribe=50x50",
                "edge=3",
                "yield=80",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert json_result.returncode == 0
        assert text_result.returncode == 0

        # Parse JSON
        json_data = json.loads(json_result.stdout)

        # Extract values from text output (simple parsing)
        text_lines = text_result.stdout.strip().split(", ")
        text_values = {}
        for line in text_lines:
            if "=" in line:
                key, value = line.split("=", 1)
                text_values[key] = value

        # Compare key values
        assert str(json_data["total_dies"]) in text_values.get("total_dies", "")
        assert str(json_data["yield_dies"]) in text_values.get("yield_dies", "")
        assert str(json_data["wafer_utilization"]).split(".")[0] in text_values.get(
            "utilization", ""
        )

    def test_cli_performance_with_large_wafers(self):
        """Test CLI performance with large wafer calculations."""

        # This should complete quickly even with large parameters
        result = run(
            [
                sys.executable,
                "-m",
                "dpw",
                "300",
                "500x500",  # Small dies on large wafer
                "edge=0",
                "yield=100",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
            timeout=30,
        )

        assert result.returncode == 0
        assert result.stdout.strip()  # Should have some output


class TestCLIParameterParsing:
    """Test specific CLI parameter parsing edge cases."""

    def test_parameter_case_sensitivity(self):
        """Test that parameters are case insensitive."""

        # Test uppercase parameters
        result = run(
            [
                sys.executable,
                "-m",
                "dpw",
                "200",
                "1000x2000",
                "SCRIBE=50x50",
                "EDGE=3",
                "YIELD=80",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 0
        assert "total_dies=" in result.stdout

    def test_parameter_spacing(self):
        """Test parameter parsing with various spacing."""

        # Test extra spaces
        result = run(
            [
                sys.executable,
                "-m",
                "dpw",
                "200",
                "1000x2000",
                "  scribe=50x50  ",
                "  edge=3  ",
                "  yield=80  ",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 0
        assert "total_dies=" in result.stdout

    def test_invalid_parameters_ignored(self):
        """Test that invalid parameters are ignored."""

        # Test with invalid parameter
        result = run(
            [
                sys.executable,
                "-m",
                "dpw",
                "200",
                "1000x2000",
                "scribe=50x50",
                "invalid_param=value",
                "edge=3",
            ],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 0  # Should still work
        assert "total_dies=" in result.stdout

    def test_die_size_format_variations(self):
        """Test various die size format variations."""

        # Test decimal values
        result = run(
            [sys.executable, "-m", "dpw", "200", "1000.5x2000.5"],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 0
        assert "total_dies=" in result.stdout

        # Test integer values
        result = run(
            [sys.executable, "-m", "dpw", "200", "1000x2000"],
            capture_output=True,
            text=True,
            cwd="/Users/dean/Documents/git/dpw",
        )

        assert result.returncode == 0
        assert "total_dies=" in result.stdout
