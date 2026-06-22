from pathlib import Path
import tempfile
import textwrap
import unittest

from tdd_dsl.runner import run_file


class RunnerTests(unittest.TestCase):
    def test_python_runner_imports_target_module_from_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "calculator.py").write_text(
                "def add(a, b):\n"
                "    return a + b\n",
                encoding="utf-8",
            )
            contract = _write_contract(root, expected=5)

            result = run_file(contract, "python", cwd=root)

            self.assertEqual(result.exit_code, 0, result.output)
            self.assertIn(f"{contract}: ok", result.output)

    def test_python_runner_maps_assertion_failure_back_to_dsl_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "calculator.py").write_text(
                "def add(a, b):\n"
                "    return a + b\n",
                encoding="utf-8",
            )
            contract = _write_contract(root, expected=6)

            result = run_file(contract, "python", cwd=root)

            self.assertNotEqual(result.exit_code, 0)
            self.assertIn(f"{contract}:4:1: case 'adds two numbers': generated test failed", result.output)
            self.assertIn("AssertionError", result.output)


def _write_contract(root: Path, expected: int) -> Path:
    contract = root / "contract.tdd"
    contract.write_text(
        textwrap.dedent(
            f"""\
            suite "Calculator"
            target python "calculator"

            case "adds two numbers":
              given input:
                {{"a": 2, "b": 3}}
              when call "add"
              then equals:
                {expected}
            """
        ),
        encoding="utf-8",
    )
    return contract


if __name__ == "__main__":
    unittest.main()
