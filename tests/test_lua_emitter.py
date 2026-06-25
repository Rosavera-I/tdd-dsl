from pathlib import Path
import subprocess
import sys
import unittest

from tdd_dsl.emitters.lua import emit_lua
from tdd_dsl.parser import parse_text


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class LuaEmitterTests(unittest.TestCase):
    def test_emit_lua_for_minimal_fixture(self) -> None:
        result = parse_text((FIXTURES / "valid_minimal.tdd").read_text(encoding="utf-8"))
        assert result.document is not None

        output = emit_lua(result.document)

        self.assertIn('local subject = require("calculator")', output)
        self.assertIn('describe("Calculator", function()', output)
        self.assertIn('it("adds two numbers", function()', output)
        self.assertIn("local result = subject.add({ a = 2, b = 3 })", output)
        self.assertIn("assert.are.same(5, result)", output)

    def test_cli_emit_lua_outputs_busted_source(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tdd_dsl",
                "emit",
                "--target",
                "lua",
                str(FIXTURES / "valid_minimal.tdd"),
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn('local subject = require("calculator")', completed.stdout)
        self.assertIn("assert.are.same(5, result)", completed.stdout)


if __name__ == "__main__":
    unittest.main()
