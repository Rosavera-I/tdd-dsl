from pathlib import Path
import subprocess
import sys
import unittest

from tdd_dsl.emitters.pytest import emit_pytest
from tdd_dsl.parser import parse_text


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class PytestEmitterTests(unittest.TestCase):
    def test_emit_pytest_for_minimal_fixture(self) -> None:
        result = parse_text((FIXTURES / "valid_minimal.tdd").read_text(encoding="utf-8"))
        assert result.document is not None

        output = emit_pytest(result.document)

        self.assertIn("import calculator", output)
        self.assertIn("def test_adds_two_numbers():", output)
        self.assertIn("result = calculator.add(a=2, b=3)", output)
        self.assertIn("assert result == 5", output)

    def test_cli_emit_python_outputs_pytest_source(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tdd_dsl",
                "emit",
                "--target",
                "python",
                str(FIXTURES / "valid_minimal.tdd"),
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("import calculator", completed.stdout)
        self.assertIn("assert result == 5", completed.stdout)


if __name__ == "__main__":
    unittest.main()
