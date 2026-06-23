"""Tests for the Rust test emitter."""

import subprocess
import sys
import tempfile
import os
import unittest
from pathlib import Path

from tdd_dsl.emitters.rust import emit_rust
from tdd_dsl.parser import parse_text

ROOT = Path(__file__).parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


class RustEmitterTests(unittest.TestCase):
    """Test suite for Rust test code generation."""

    def test_emits_use_statement(self) -> None:
        """Emitted code contains use statement for the module."""
        source = '''
suite "Calculator"
target rust "calculator"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_rust(result.document, target_name="rust")

        self.assertIn("use calculator::*;", output)

    def test_emits_test_attribute(self) -> None:
        """Test functions have #[test] attribute."""
        source = '''
suite "Calculator"
target rust "calc"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_rust(result.document, target_name="rust")

        self.assertIn("#[test]", output)

    def test_emits_test_function_snake_case(self) -> None:
        """Test functions use snake_case naming."""
        source = '''
suite "Calculator"
target rust "calc"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_rust(result.document, target_name="rust")

        self.assertIn("fn test_adds_two_numbers()", output)

    def test_emits_assert_eq_macro(self) -> None:
        """Assertions use assert_eq! macro."""
        source = '''
suite "Calculator"
target rust "calc"

case "returns constant":
  given input:
    5
  when call "get_value"
  then equals:
    42
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_rust(result.document, target_name="rust")

        self.assertIn("assert_eq!(42, result);", output)

    def test_emits_map_literal_for_dict_input(self) -> None:
        """Dict inputs use HashMap construction."""
        source = '''
suite "Calculator"
target rust "calc"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_rust(result.document, target_name="rust")

        self.assertIn("let input = vec!", output)
        self.assertIn(".into_iter().collect::<std::collections::HashMap<_, _>>();", output)
        self.assertIn("add(&input)", output)

    def test_emits_vec_literal_for_list_input(self) -> None:
        """List inputs use vec! macro."""
        source = '''
suite "Sorter"
target rust "sorter"

case "sorts numbers":
  given input:
    [3, 1, 2]
  when call "sort"
  then equals:
    [1, 2, 3]
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_rust(result.document, target_name="rust")

        self.assertIn("let input = vec![3, 1, 2];", output)

    def test_handles_null_values_as_unit(self) -> None:
        """Null values emit as Rust unit type."""
        source = '''
suite "Maybe"
target rust "maybe"

case "returns unit":
  given input:
    null
  when call "do_nothing"
  then equals:
    null
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_rust(result.document, target_name="rust")

        self.assertIn("do_nothing(())", output)
        self.assertIn("assert_eq!((), result);", output)

    def test_handles_boolean_values(self) -> None:
        """Boolean values emit as true/false."""
        source = '''
suite "Checker"
target rust "checker"

case "returns true":
  given input:
    true
  when call "is_valid"
  then equals:
    true
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_rust(result.document, target_name="rust")

        self.assertIn("assert_eq!(true, result);", output)

    def test_handles_string_values(self) -> None:
        """String values emit with proper escaping."""
        source = '''
suite "Greeter"
target rust "greeter"

case "returns greeting":
  given input:
    "World"
  when call "greet"
  then equals:
    "Hello, World!"
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_rust(result.document, target_name="rust")

        self.assertIn('"World"', output)
        self.assertIn('"Hello, World!"', output)

    def test_avoids_keyword_collision(self) -> None:
        """Rust keywords are avoided in identifiers."""
        source = '''
suite "Loop Test"
target rust "my_module"

case "loop test case":
  given input:
    1
  when call "loop_fn"
  then equals:
    2
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_rust(result.document, target_name="rust")

        # 'loop' is a Rust keyword, so should be suffixed when part of snake_case name
        self.assertIn("fn test_loop_test_case()", output)

    def test_generates_unique_names_for_similar_inputs(self) -> None:
        """Similar test names get numbered suffixes to avoid collisions."""
        source = '''
suite "Dupes"
target rust "dupes"

case "same name":
  given input:
    1
  when call "process"
  then equals:
    1

case "same name again":
  given input:
    2
  when call "process"
  then equals:
    2
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_rust(result.document, target_name="rust")

        # Both should produce "test_same_name" - one needs a suffix
        self.assertIn("fn test_same_name()", output)

    def test_cli_emits_rust(self) -> None:
        """CLI supports --target rust for emit command."""
        # Create a temporary file with Rust target
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tdd', delete=False) as f:
            f.write('''suite "Calculator"
target rust "calculator"

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
                    "rust",
                    temp_path,
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("use calculator::*;", completed.stdout)
            self.assertIn("#[test]", completed.stdout)
            self.assertIn("fn test_adds_two_numbers()", completed.stdout)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()