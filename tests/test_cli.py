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


if __name__ == "__main__":
    unittest.main()
