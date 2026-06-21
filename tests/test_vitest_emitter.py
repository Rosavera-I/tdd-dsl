from pathlib import Path
import subprocess
import sys
import unittest

from tdd_dsl.emitters.vitest import emit_vitest
from tdd_dsl.parser import parse_text


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class VitestEmitterTests(unittest.TestCase):
    def test_emit_vitest_for_typescript_fixture(self) -> None:
        result = parse_text((FIXTURES / "valid_typescript.tdd").read_text(encoding="utf-8"))
        assert result.document is not None

        output = emit_vitest(result.document)

        self.assertIn('import { describe, expect, test } from "vitest";', output)
        self.assertIn('import { add } from "calculator";', output)
        self.assertIn('test("adds two numbers", () => {', output)
        self.assertIn("const result = add({", output)
        self.assertIn("a: 2", output)
        self.assertIn("b: 3", output)
        self.assertIn("expect(result).toEqual(5);", output)

    def test_cli_emit_typescript_outputs_vitest_source(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tdd_dsl",
                "emit",
                "--target",
                "typescript",
                str(FIXTURES / "valid_typescript.tdd"),
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn('import { add } from "calculator";', completed.stdout)
        self.assertIn("expect(result).toEqual(5);", completed.stdout)


if __name__ == "__main__":
    unittest.main()
