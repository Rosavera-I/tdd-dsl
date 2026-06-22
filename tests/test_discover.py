"""Tests for the discover command."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


class DiscoverTests(unittest.TestCase):
    """Test suite for tdd-dsl discover command."""

    def test_discover_finds_matching_files(self) -> None:
        """discover finds all .tdd files matching the pattern."""
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tdd_dsl",
                "discover",
                "tests/fixtures/valid*.tdd",
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("valid_minimal.tdd: OK (1 case(s))", completed.stdout)
        self.assertIn("valid_billing_policy.tdd: OK (2 case(s))", completed.stdout)

    def test_discover_reports_failures_with_nonzero_exit(self) -> None:
        """discover returns non-zero exit code when files have errors."""
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tdd_dsl",
                "discover",
                "tests/fixtures/invalid*.tdd",
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("FAILED", completed.stdout)
        self.assertIn("diagnostic(s)", completed.stdout)

    def test_discover_json_format(self) -> None:
        """discover --format json outputs valid JSON with correct structure."""
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tdd_dsl",
                "discover",
                "tests/fixtures/valid*.tdd",
                "--format",
                "json",
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertIn("files", payload)
        self.assertIn("total", payload)
        self.assertIn("failed", payload)
        self.assertEqual(payload["total"], 3)
        self.assertEqual(payload["failed"], 0)

        # Check file entry structure
        for file_entry in payload["files"]:
            self.assertIn("file", file_entry)
            self.assertIn("status", file_entry)
            if file_entry["status"] == "ok":
                self.assertIn("case_count", file_entry)

    def test_discover_json_format_includes_diagnostics_for_failures(self) -> None:
        """discover --format json includes diagnostic details for failed files."""
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tdd_dsl",
                "discover",
                "tests/fixtures/invalid_missing_then.tdd",
                "--format",
                "json",
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["failed"], 1)

        file_entry = payload["files"][0]
        self.assertEqual(file_entry["status"], "error")
        self.assertIn("diagnostics", file_entry)
        self.assertGreater(len(file_entry["diagnostics"]), 0)

        # Check diagnostic structure
        diagnostic = file_entry["diagnostics"][0]
        self.assertIn("line", diagnostic)
        self.assertIn("column", diagnostic)
        self.assertIn("message", diagnostic)

    def test_discover_recursive_glob(self) -> None:
        """discover supports recursive glob patterns with **."""
        # Note: recursive ** glob support is basic; test with known fixture structure
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tdd_dsl",
                "discover",
                "tests/**/*.tdd",
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        # Should find fixture files (they're in tests/fixtures/)
        self.assertIn("Total:", completed.stdout)
        self.assertGreater(len(completed.stdout.splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
