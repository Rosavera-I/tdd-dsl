from pathlib import Path
import subprocess
import sys
import unittest

from tdd_dsl.emitters.ruby import emit_rspec
from tdd_dsl.parser import parse_text


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class RubyEmitterTests(unittest.TestCase):
    def test_emit_rspec_for_minimal_fixture(self) -> None:
        result = parse_text((FIXTURES / "valid_minimal.tdd").read_text(encoding="utf-8"))
        assert result.document is not None

        output = emit_rspec(result.document)

        self.assertIn('require "calculator"', output)
        self.assertIn('RSpec.describe "Calculator" do', output)
        self.assertIn('it "adds two numbers" do', output)
        self.assertIn("result = add(a: 2, b: 3)", output)
        self.assertIn("expect(result).to eq(5)", output)

    def test_cli_emit_ruby_outputs_rspec_source(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "tdd_dsl",
                "emit",
                "--target",
                "ruby",
                str(FIXTURES / "valid_minimal.tdd"),
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(ROOT / "src")},
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn('require "calculator"', completed.stdout)
        self.assertIn("expect(result).to eq(5)", completed.stdout)


if __name__ == "__main__":
    unittest.main()
