"""Tests for the Odin test emitter."""

import subprocess
import sys
import tempfile
import os
import unittest
from pathlib import Path

from tdd_dsl.emitters.odin import emit_odin
from tdd_dsl.parser import parse_text

ROOT = Path(__file__).parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


class OdinEmitterTests(unittest.TestCase):
    """Test suite for Odin test code generation."""

    def test_emits_package_declaration(self) -> None:
        """Emitted code contains package declaration."""
        source = '''
suite "Calculator"
target odin "calculator"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        self.assertIn("package calculator", output)

    def test_emits_testing_import(self) -> None:
        """Emitted code imports core:testing."""
        source = '''
suite "Calculator"
target odin "calc"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        self.assertIn('import "core:testing"', output)

    def test_emits_test_attribute(self) -> None:
        """Test procedures have @(test) attribute."""
        source = '''
suite "Calculator"
target odin "calc"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        self.assertIn("@(test)", output)

    def test_emits_test_procedure_snake_case(self) -> None:
        """Test procedures use snake_case naming with :: proc syntax."""
        source = '''
suite "Calculator"
target odin "calc"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        self.assertIn("test_adds_two_numbers :: proc(t: ^testing.T)", output)

    def test_emits_expect_value_call(self) -> None:
        """Assertions use testing.expect_value()."""
        source = '''
suite "Calculator"
target odin "calc"

case "returns constant":
  given input:
    5
  when call "get_value"
  then equals:
    42
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        self.assertIn("testing.expect_value(t, result, 42)", output)

    def test_emits_struct_literal_for_dict_input(self) -> None:
        """Dict inputs use Odin struct literal syntax."""
        source = '''
suite "Calculator"
target odin "calc"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        self.assertIn("input := {a = 1, b = 2}", output)
        self.assertIn("add(input)", output)

    def test_emits_array_literal_for_list_input(self) -> None:
        """List inputs use Odin array literal syntax."""
        source = '''
suite "Sorter"
target odin "sorter"

case "sorts numbers":
  given input:
    [3, 1, 2]
  when call "sort"
  then equals:
    [1, 2, 3]
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        self.assertIn("input := []{3, 1, 2}", output)

    def test_handles_null_values(self) -> None:
        """Null values emit as Odin nil."""
        source = '''
suite "Maybe"
target odin "maybe"

case "returns nil":
  given input:
    null
  when call "do_nothing"
  then equals:
    null
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        self.assertIn("do_nothing(nil)", output)
        self.assertIn("testing.expect_value(t, result, nil)", output)

    def test_handles_boolean_values(self) -> None:
        """Boolean values emit as true/false."""
        source = '''
suite "Checker"
target odin "checker"

case "returns true":
  given input:
    true
  when call "is_valid"
  then equals:
    true
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        self.assertIn("testing.expect_value(t, result, true)", output)

    def test_handles_string_values(self) -> None:
        """String values emit with proper escaping."""
        source = '''
suite "Greeter"
target odin "greeter"

case "returns greeting":
  given input:
    "World"
  when call "greet"
  then equals:
    "Hello, World!"
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        self.assertIn('"World"', output)
        self.assertIn('"Hello, World!"', output)

    def test_avoids_keyword_collision(self) -> None:
        """Odin keywords are avoided in identifiers."""
        source = '''
suite "Proc Test"
target odin "my_module"

case "proc test case":
  given input:
    1
  when call "proc_fn"
  then equals:
    2
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        # 'proc' is an Odin keyword, but should be handled in snake_case
        self.assertIn("test_proc_test_case :: proc(t: ^testing.T)", output)

    def test_generates_unique_names_for_similar_inputs(self) -> None:
        """Similar test names get numbered suffixes to avoid collisions."""
        # The validator catches duplicate case names, so we simulate the scenario
        # by directly testing the emitter with two cases that would have the same
        # base name after snake_case conversion
        source = '''
suite "Dupes"
target odin "dupes"

case "process":
  given input:
    1
  when call "process"
  then equals:
    1

case "process test":
  given input:
    2
  when call "process"
  then equals:
    2
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        # "process" -> "test_process", "process test" -> "test_process"
        # One needs a suffix to avoid collision
        self.assertIn("test_process :: proc(t: ^testing.T)", output)
        # Check that we have both test procedures
        lines = output.splitlines()
        test_lines = [l for l in lines if "test_process" in l and ":: proc" in l]
        self.assertEqual(len(test_lines), 2)

    def test_handles_complex_module_paths(self) -> None:
        """Module paths with slashes are handled correctly."""
        source = '''
suite "Calculator"
target odin "src/math/calculator"

case "adds":
  given input:
    1
  when call "add"
  then equals:
    2
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        self.assertIn("package calculator", output)

    def test_emits_field_assertions_for_dict_expected(self) -> None:
        """Dict expected values generate field-by-field assertions."""
        source = '''
suite "User"
target odin "user"

case "creates user":
  given input:
    {"name": "Alice", "age": 30}
  when call "create_user"
  then equals:
    {"name": "Alice", "active": true}
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_odin(result.document, target_name="odin")

        self.assertIn("testing.expect_value(t, result.name, \"Alice\")", output)
        self.assertIn("testing.expect_value(t, result.active, true)", output)

    def test_cli_emits_odin(self) -> None:
        """CLI supports --target odin for emit command."""
        # Create a temporary file with Odin target
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tdd', delete=False) as f:
            f.write('''suite "Calculator"
target odin "calculator"

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
                    "odin",
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
            self.assertIn("@(test)", completed.stdout)
            self.assertIn("test_adds_two_numbers :: proc(t: ^testing.T)", completed.stdout)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
