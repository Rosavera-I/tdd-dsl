import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class CliTests(unittest.TestCase):
    def test_validate_success(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "tdd_dsl", "validate", str(FIXTURES / "valid_minimal.tdd")],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("ok", completed.stdout)

    def test_validate_failure_prints_location(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "tdd_dsl", "validate", str(FIXTURES / "invalid_missing_then.tdd")],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        self.assertIn("invalid_missing_then.tdd:4:1", completed.stdout)
        self.assertIn("requires then equals", completed.stdout)

    def test_validate_format_json_prints_lsp_compatible_diagnostics(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tdd_dsl",
                "validate",
                str(FIXTURES / "invalid_missing_then.tdd"),
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
        self.assertEqual(payload["diagnostics"][0]["file"], str(FIXTURES / "invalid_missing_then.tdd"))
        diagnostic = payload["diagnostics"][0]
        self.assertEqual(diagnostic["line"], 4)
        self.assertEqual(diagnostic["column"], 1)
        self.assertEqual(diagnostic["severity"], "error")
        self.assertIn("requires then equals", diagnostic["message"])
        self.assertIn("then equals", diagnostic["suggestedFix"])

    def test_validate_format_json_success_prints_empty_diagnostics(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tdd_dsl",
                "validate",
                str(FIXTURES / "valid_minimal.tdd"),
                "--format",
                "json",
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertEqual(json.loads(completed.stdout), {"diagnostics": []})

    def test_validate_json_ast_output_stays_compatible(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "tdd_dsl", "validate", str(FIXTURES / "valid_minimal.tdd"), "--json"],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["suite"], "Calculator")
        self.assertEqual(payload["targets"][0]["language"], "python")

    def test_validate_rejects_json_ast_and_diagnostic_formats_together(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tdd_dsl",
                "validate",
                str(FIXTURES / "valid_minimal.tdd"),
                "--json",
                "--format",
                "json",
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertIn("cannot be combined", completed.stderr)


if __name__ == "__main__":
    unittest.main()
