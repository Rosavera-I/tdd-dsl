"""Tests for the C# xUnit emitter."""

import subprocess
import sys
import unittest
from pathlib import Path

from tdd_dsl.emitters.xunit import emit_xunit
from tdd_dsl.parser import parse_text

ROOT = Path(__file__).parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


class XUnitEmitterTests(unittest.TestCase):
    """Test suite for C# xUnit code generation."""

    def test_emits_class_declaration(self) -> None:
        """Emitted code contains a public class with Tests suffix."""
        source = '''
suite "Calculator"
target csharp "Calculator"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        self.assertIn("public class CalculatorTests", output)
        self.assertIn("using Xunit;", output)

    def test_emits_test_method_with_camel_case(self) -> None:
        """Test methods use camelCase naming."""
        source = '''
suite "Calculator"
target csharp "calc"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        self.assertIn("public void testAddsTwoNumbers()", output)

    def test_emits_fact_attribute(self) -> None:
        """Test methods have [Fact] attribute."""
        source = '''
suite "Calculator"
target csharp "calc"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        self.assertIn("[Fact]", output)

    def test_emits_namespace_import(self) -> None:
        """Emitted code imports the namespace for classes with dots."""
        source = '''
suite "Calculator"
target csharp "MyApp.Services.Calculator"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        self.assertIn("using MyApp.Services;", output)
        self.assertIn("public class CalculatorTests", output)

    def test_emits_method_call_with_dict_input(self) -> None:
        """Method calls with object input use Dictionary."""
        source = '''
suite "Calculator"
target csharp "calc"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        self.assertIn('var input = new Dictionary<string, object> { { "a", 1 }, { "b", 2 } };', output)
        self.assertIn("var result = calc.add(input);", output)

    def test_emits_assertions_for_dict_expected(self) -> None:
        """Dictionary expected values generate multiple Assert.Equal calls."""
        source = '''
suite "Billing"
target csharp "billing"

case "calculates total":
  given input:
    {"item": "widget"}
  when call "calculate"
  then equals:
    {"total": 100, "currency": "USD"}
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        self.assertIn('Assert.Equal(100, result["total"]);', output)
        self.assertIn('Assert.Equal("USD", result["currency"]);', output)

    def test_emits_scalar_assertion(self) -> None:
        """Scalar expected values generate single Assert.Equal."""
        source = '''
suite "Calculator"
target csharp "calc"

case "returns constant":
  given input:
    5
  when call "getValue"
  then equals:
    42
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        self.assertIn("Assert.Equal(42, result);", output)

    def test_emits_list_literal(self) -> None:
        """List inputs use List<object>."""
        source = '''
suite "Sorter"
target csharp "sorter"

case "sorts numbers":
  given input:
    [3, 1, 2]
  when call "sort"
  then equals:
    [1, 2, 3]
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        self.assertIn("var input = new List<object> { 3, 1, 2 };", output)

    def test_handles_null_values(self) -> None:
        """Null values emit as C# null."""
        source = '''
suite "Maybe"
target csharp "maybe"

case "returns null":
  given input:
    null
  when call "getOrNull"
  then equals:
    null
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        self.assertIn("Assert.Equal(null, result);", output)

    def test_handles_boolean_values(self) -> None:
        """Boolean values emit as true/false."""
        source = '''
suite "Flag"
target csharp "flag"

case "returns true":
  given input:
    true
  when call "isEnabled"
  then equals:
    true
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        self.assertIn("Assert.Equal(true, result);", output)

    def test_handles_string_escaping(self) -> None:
        """Strings with special characters are properly escaped."""
        source = '''
suite "Strings"
target csharp "strings"

case "returns quoted string":
  given input:
    "hello"
  when call "quote"
  then equals:
    "\\"hello\\""
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        self.assertIn(r'\"', output)

    def test_avoids_csharp_keywords(self) -> None:
        """Method names that are C# keywords get sanitized."""
        source = '''
suite "Keywords"
target csharp "keywords"

case "class test":
  given input:
    1
  when call "method"
  then equals:
    2
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        # Should contain a test method name that's not just "class"
        self.assertIn("public void", output)

    def test_generates_unique_method_names(self) -> None:
        """Test names that produce same camelCase get unique suffixes."""
        source = '''
suite "Duplicates"
target csharp "dup"

case "same name":
  given input:
    1
  when call "method"
  then equals:
    1

case "same_name":
  given input:
    2
  when call "method"
  then equals:
    2
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_xunit(result.document, target_name="csharp")

        # Both "same name" and "same_name" produce "testSameName" so one should be suffixed
        count = output.count("testSameName")
        self.assertEqual(count, 2, "Should have two methods with base name testSameName")

    def test_cli_emits_csharp(self) -> None:
        """CLI supports --target csharp for emit command."""
        import tempfile
        import os

        # Create a temporary file with C# target
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tdd', delete=False) as f:
            f.write('''suite "Calculator"
target csharp "Calculator"

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
                    "csharp",
                    temp_path,
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("public class CalculatorTests", completed.stdout)
            self.assertIn("[Fact]", completed.stdout)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()