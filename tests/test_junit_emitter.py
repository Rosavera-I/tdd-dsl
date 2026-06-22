"""Tests for the Java JUnit emitter."""

import subprocess
import sys
import unittest
from pathlib import Path

from tdd_dsl.emitters.junit import emit_junit
from tdd_dsl.parser import parse_text

ROOT = Path(__file__).parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


class JUnitEmitterTests(unittest.TestCase):
    """Test suite for Java JUnit code generation."""

    def test_emits_class_declaration(self) -> None:
        """Emitted code contains a public class with Test suffix."""
        source = '''
suite "Calculator"
target java "com.example.Calculator"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_junit(result.document, target_name="java")

        self.assertIn("public class CalculatorTest", output)
        self.assertIn("import org.junit.jupiter.api.Test;", output)
        self.assertIn("import static org.junit.jupiter.api.Assertions.assertEquals;", output)

    def test_emits_test_method_with_camel_case(self) -> None:
        """Test methods use camelCase naming."""
        source = '''
suite "Calculator"
target java "calc"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_junit(result.document, target_name="java")

        self.assertIn("public void testAddsTwoNumbers()", output)

    def test_emits_display_name_annotation(self) -> None:
        """Test methods have @DisplayName with original case name."""
        source = '''
suite "Calculator"
target java "calc"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_junit(result.document, target_name="java")

        self.assertIn('@DisplayName("adds two numbers")', output)

    def test_emits_import_for_module(self) -> None:
        """Emitted code imports the class under test."""
        source = '''
suite "Calculator"
target java "com.example.Calculator"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_junit(result.document, target_name="java")

        self.assertIn("import com.example.Calculator;", output)

    def test_emits_method_call_with_map_input(self) -> None:
        """Method calls with object input use Map.of()."""
        source = '''
suite "Calculator"
target java "calc"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_junit(result.document, target_name="java")

        self.assertIn("var input = java.util.Map.of(\"a\", 1, \"b\", 2);", output)
        self.assertIn("var result = calc.add(input);", output)

    def test_emits_assertions_for_object_expected(self) -> None:
        """Object expected values generate multiple assertEquals calls."""
        source = '''
suite "Billing"
target java "billing"

case "calculates total":
  given input:
    {"item": "widget"}
  when call "calculate"
  then equals:
    {"total": 100, "currency": "USD"}
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_junit(result.document, target_name="java")

        self.assertIn("assertEquals(100, result.getTotal());", output)
        self.assertIn('assertEquals("USD", result.getCurrency());', output)

    def test_emits_scalar_assertion(self) -> None:
        """Scalar expected values generate single assertEquals."""
        source = '''
suite "Calculator"
target java "calc"

case "returns constant":
  given input:
    5
  when call "getValue"
  then equals:
    42
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_junit(result.document, target_name="java")

        self.assertIn("assertEquals(42, result);", output)

    def test_emits_list_literal(self) -> None:
        """List inputs use List.of()."""
        source = '''
suite "Sorter"
target java "sorter"

case "sorts numbers":
  given input:
    [3, 1, 2]
  when call "sort"
  then equals:
    [1, 2, 3]
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_junit(result.document, target_name="java")

        self.assertIn("var input = java.util.List.of(3, 1, 2);", output)

    def test_handles_null_values(self) -> None:
        """Null values emit as Java null."""
        source = '''
suite "Maybe"
target java "maybe"

case "returns null":
  given input:
    null
  when call "getOrNull"
  then equals:
    null
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_junit(result.document, target_name="java")

        self.assertIn("assertEquals(null, result);", output)

    def test_cli_emits_java(self) -> None:
        """CLI supports --target java for emit command."""
        import tempfile
        import os

        # Create a temporary file with Java target
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tdd', delete=False) as f:
            f.write('''suite "Calculator"
target java "Calculator"

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
                    "java",
                    temp_path,
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("public class CalculatorTest", completed.stdout)
            self.assertIn("@Test", completed.stdout)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
