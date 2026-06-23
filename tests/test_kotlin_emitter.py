"""Tests for the Kotlin emitter."""

import subprocess
import sys
import unittest
from pathlib import Path

from tdd_dsl.emitters.kotlin import emit_kotlin
from tdd_dsl.parser import parse_text

ROOT = Path(__file__).parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


class KotlinEmitterTests(unittest.TestCase):
    """Test suite for Kotlin code generation."""

    def test_emits_class_declaration(self) -> None:
        """Emitted code contains a class with Test suffix."""
        source = '''
suite "Calculator"
target kotlin "Calculator"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_kotlin(result.document, target_name="kotlin")

        self.assertIn("class CalculatorTest", output)
        self.assertIn("import org.junit.jupiter.api.Test", output)
        self.assertIn("import kotlin.test.assertEquals", output)

    def test_emits_test_method_with_backticks(self) -> None:
        """Test methods use backtick-wrapped names for readability."""
        source = '''
suite "Calculator"
target kotlin "calc"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_kotlin(result.document, target_name="kotlin")

        self.assertIn('fun `adds two numbers`()', output)

    def test_emits_package_declaration(self) -> None:
        """Emitted code includes package when module has dots."""
        source = '''
suite "Calculator"
target kotlin "com.example.Calculator"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_kotlin(result.document, target_name="kotlin")

        self.assertIn("package com.example", output)
        self.assertIn("class CalculatorTest", output)

    def test_emits_method_call_with_map_input(self) -> None:
        """Method calls with object input use mapOf()."""
        source = '''
suite "Calculator"
target kotlin "calc"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_kotlin(result.document, target_name="kotlin")

        self.assertIn('val input = mapOf("a" to 1, "b" to 2)', output)
        self.assertIn("val result = calc.add(input)", output)

    def test_emits_assertions_for_object_expected(self) -> None:
        """Object expected values generate multiple assertEquals calls."""
        source = '''
suite "Billing"
target kotlin "billing"

case "calculates total":
  given input:
    {"item": "widget"}
  when call "calculate"
  then equals:
    {"total": 100, "currency": "USD"}
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_kotlin(result.document, target_name="kotlin")

        self.assertIn("assertEquals(100, result.total)", output)
        self.assertIn('assertEquals("USD", result.currency)', output)

    def test_emits_scalar_assertion(self) -> None:
        """Scalar expected values generate single assertEquals."""
        source = '''
suite "Calculator"
target kotlin "calc"

case "returns constant":
  given input:
    5
  when call "getValue"
  then equals:
    42
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_kotlin(result.document, target_name="kotlin")

        self.assertIn("assertEquals(42, result)", output)

    def test_emits_list_literal(self) -> None:
        """List inputs use listOf()."""
        source = '''
suite "Sorter"
target kotlin "sorter"

case "sorts numbers":
  given input:
    [3, 1, 2]
  when call "sort"
  then equals:
    [1, 2, 3]
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_kotlin(result.document, target_name="kotlin")

        self.assertIn("val input = listOf(3, 1, 2)", output)

    def test_handles_null_values(self) -> None:
        """Null values emit as Kotlin null."""
        source = '''
suite "Maybe"
target kotlin "maybe"

case "returns null":
  given input:
    null
  when call "getOrNull"
  then equals:
    null
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_kotlin(result.document, target_name="kotlin")

        self.assertIn("assertEquals(null, result)", output)

    def test_emits_boolean_literals(self) -> None:
        """Boolean values emit as true/false."""
        source = '''
suite "Flag"
target kotlin "flag"

case "returns true":
  given input:
    true
  when call "isEnabled"
  then equals:
    false
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_kotlin(result.document, target_name="kotlin")

        self.assertIn("val result = flag.isEnabled(true)", output)
        self.assertIn("assertEquals(false, result)", output)

    def test_handles_special_characters_in_test_name(self) -> None:
        """Test names with special characters are sanitized."""
        source = '''
suite "Math"
target kotlin "math"

case "adds 2 + 2":
  given input:
    {"a": 2, "b": 2}
  when call "add"
  then equals:
    4
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_kotlin(result.document, target_name="kotlin")

        self.assertIn('fun `adds 2 + 2`()', output)

    def test_cli_emits_kotlin(self) -> None:
        """CLI supports --target kotlin for emit command."""
        import tempfile
        import os

        # Create a temporary file with Kotlin target
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tdd', delete=False) as f:
            f.write('''suite "Calculator"
target kotlin "Calculator"

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
                    "kotlin",
                    temp_path,
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("class CalculatorTest", completed.stdout)
            self.assertIn("@Test", completed.stdout)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()