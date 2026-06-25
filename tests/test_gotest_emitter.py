"""Tests for the Go testing emitter."""

import subprocess
import sys
import unittest
from pathlib import Path

from tdd_dsl.emitters.gotest import emit_gotest
from tdd_dsl.parser import parse_text

ROOT = Path(__file__).parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


class GotestEmitterTests(unittest.TestCase):
    """Test suite for Go test code generation."""

    def test_emits_package_declaration(self) -> None:
        """Emitted code contains a package declaration."""
        source = '''
suite "Calculator"
target go "calculator"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn("package calculator", output)

    def test_emits_imports(self) -> None:
        """Emitted code includes necessary imports."""
        source = '''
suite "Calculator"
target go "calculator"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn('import (', output)
        self.assertIn('"testing"', output)
        self.assertIn('"reflect"', output)
        self.assertNotIn('"encoding/json"', output)

    def test_emits_test_function_with_test_prefix(self) -> None:
        """Test functions use TestXxx naming convention."""
        source = '''
suite "Calculator"
target go "calculator"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn("func TestAddsTwoNumbers(t *testing.T)", output)

    def test_emits_function_call(self) -> None:
        """Emitted code calls the function under test."""
        source = '''
suite "Calculator"
target go "calculator"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn("result := add(input)", output)

    def test_emits_deep_equal_assertion(self) -> None:
        """Emitted code uses reflect.DeepEqual for assertions."""
        source = '''
suite "Calculator"
target go "calculator"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn("if !reflect.DeepEqual(result, expected)", output)
        self.assertIn('t.Errorf(', output)

    def test_emits_map_literal_for_dict_input(self) -> None:
        """Dict inputs generate map[string]interface{} literals."""
        source = '''
suite "Calculator"
target go "calculator"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn('map[string]interface{}{"a": 1, "b": 2}', output)

    def test_emits_nested_map_literals_without_json_unmarshal(self) -> None:
        """Nested objects remain Go literals instead of lossy JSON interface{} values."""
        source = '''
suite "Billing"
target go "billing"

case "calculates total":
  given input:
    {"account": {"plan": "legacy", "yearsActive": 7}, "usage": {"projects": 18}}
  when call "quoteSubscription"
  then equals:
    {"tier": "pro", "monthlyUsd": 49}
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn('"account": map[string]interface{}{"plan": "legacy", "yearsActive": 7}', output)
        self.assertIn('"monthlyUsd": 49', output)
        self.assertNotIn("json.Unmarshal", output)

    def test_emits_slice_literal_for_list_input(self) -> None:
        """List inputs generate []interface{} literals."""
        source = '''
suite "Sorter"
target go "sorter"

case "sorts numbers":
  given input:
    [3, 1, 2]
  when call "sort"
  then equals:
    [1, 2, 3]
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn("[]interface{}{3, 1, 2}", output)
        self.assertIn("[]interface{}{1, 2, 3}", output)

    def test_handles_null_values(self) -> None:
        """Null values emit as Go nil."""
        source = '''
suite "Maybe"
target go "maybe"

case "returns null":
  given input:
    null
  when call "getOrNull"
  then equals:
    null
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn("input := nil", output)
        self.assertIn("expected := nil", output)

    def test_handles_string_values(self) -> None:
        """String values are properly escaped."""
        source = '''
suite "Greeter"
target go "greeter"

case "says hello":
  given input:
    "world"
  when call "greet"
  then equals:
    "hello world"
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn('input := "world"', output)
        self.assertIn('expected := "hello world"', output)

    def test_handles_boolean_values(self) -> None:
        """Boolean values emit as true/false."""
        source = '''
suite "Checker"
target go "checker"

case "checks condition":
  given input:
    true
  when call "isValid"
  then equals:
    false
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn("input := true", output)
        self.assertIn("expected := false", output)

    def test_extracts_package_from_full_path(self) -> None:
        """Package name is extracted from full import paths."""
        source = '''
suite "Calculator"
target go "github.com/user/calculator"

case "adds":
  given input:
    1
  when call "add"
  then equals:
    2
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn("package calculator", output)

    def test_generates_unique_test_function_names(self) -> None:
        """Similar names that normalize identically get deterministic suffixes."""
        source = '''
suite "Duplicates"
target go "duplicates"

case "same name":
  given input:
    1
  when call "identity"
  then equals:
    1

case "same_name":
  given input:
    2
  when call "identity"
  then equals:
    2
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_gotest(result.document, target_name="go")

        self.assertIn("func TestSameName(t *testing.T)", output)
        self.assertIn("func TestSameName2(t *testing.T)", output)

    def test_cli_emits_go(self) -> None:
        """CLI supports --target go for emit command."""
        import tempfile
        import os

        # Create a temporary file with Go target
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tdd', delete=False) as f:
            f.write('''suite "Calculator"
target go "calculator"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
''')
            temp_path = f.name

        try:
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "tdd_dsl",
                    "emit",
                    "--target",
                    "go",
                    temp_path,
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("package calculator", completed.stdout)
            self.assertIn("func TestAddsTwoNumbers", completed.stdout)
            self.assertIn("testing.T", completed.stdout)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
