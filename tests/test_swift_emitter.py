"""Tests for the Swift XCTest emitter."""

import subprocess
import sys
import unittest
from pathlib import Path

from tdd_dsl.emitters.swift import emit_swift
from tdd_dsl.parser import parse_text

ROOT = Path(__file__).parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


class SwiftEmitterTests(unittest.TestCase):
    """Test suite for Swift XCTest code generation."""

    def test_emits_test_class_declaration(self) -> None:
        """Emitted code contains a final XCTestCase subclass."""
        source = '''
suite "Calculator"
target swift "Calculator"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_swift(result.document, target_name="swift")

        self.assertIn("import XCTest", output)
        self.assertIn("@testable import Calculator", output)
        self.assertIn("final class CalculatorTests: XCTestCase", output)

    def test_emits_test_method_with_test_prefix(self) -> None:
        """Test methods start with 'test' prefix."""
        source = '''
suite "Math"
target swift "math"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_swift(result.document, target_name="swift")

        self.assertIn("func testAddsTwoNumbers() throws", output)

    def test_emits_import_for_module(self) -> None:
        """Emitted code imports the module under test with @testable."""
        source = '''
suite "Calculator"
target swift "com.example.Calculator"

case "adds two numbers":
  given input:
    1
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_swift(result.document, target_name="swift")

        self.assertIn("@testable import com", output)

    def test_emits_method_call_with_struct_input(self) -> None:
        """Method calls with dict input use struct literals."""
        source = '''
suite "Calculator"
target swift "calculator"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_swift(result.document, target_name="swift")

        self.assertIn("let input = Add(a: 1, b: 2)", output)
        self.assertIn("let result = add(input: input)", output)

    def test_emits_assertion_for_scalar_expected(self) -> None:
        """Scalar expected values generate single XCTAssertEqual."""
        source = '''
suite "Calculator"
target swift "calc"

case "returns constant":
  given input:
    5
  when call "getValue"
  then equals:
    42
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_swift(result.document, target_name="swift")

        self.assertIn("XCTAssertEqual(result, 42)", output)

    def test_emits_array_literal(self) -> None:
        """List inputs use Swift array literals."""
        source = '''
suite "Sorter"
target swift "sorter"

case "sorts numbers":
  given input:
    [3, 1, 2]
  when call "sort"
  then equals:
    [1, 2, 3]
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_swift(result.document, target_name="swift")

        self.assertIn("let input = [3, 1, 2]", output)

    def test_handles_null_values(self) -> None:
        """Null values emit as Swift nil."""
        source = '''
suite "Maybe"
target swift "maybe"

case "returns nil":
  given input:
    null
  when call "getOrNull"
  then equals:
    null
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_swift(result.document, target_name="swift")

        self.assertIn("XCTAssertEqual(result, nil)", output)

    def test_emits_assertions_for_object_expected(self) -> None:
        """Object expected values generate multiple XCTAssertEqual calls."""
        source = '''
suite "Billing"
target swift "billing"

case "calculates total":
  given input:
    {"item": "widget"}
  when call "calculate"
  then equals:
    {"total": 100, "currency": "USD"}
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_swift(result.document, target_name="swift")

        self.assertIn("XCTAssertEqual(result.total, 100)", output)
        self.assertIn('XCTAssertEqual(result.currency, "USD")', output)

    def test_handles_multiple_cases(self) -> None:
        """Multiple cases generate multiple test methods."""
        source = '''
suite "Math"
target swift "math"

case "adds two numbers":
  given input:
    {"a": 1, "b": 2}
  when call "add"
  then equals:
    3

case "multiplies two numbers":
  given input:
    {"a": 3, "b": 4}
  when call "multiply"
  then equals:
    12
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_swift(result.document, target_name="swift")

        self.assertIn("func testAddsTwoNumbers() throws", output)
        self.assertIn("func testMultipliesTwoNumbers() throws", output)

    def test_generates_unique_names_for_similar_cases(self) -> None:
        """Similar case names get unique method names via deduplication."""
        source = '''
suite "Math"
target swift "math"

case "adds numbers":
  given input:
    1
  when call "add"
  then equals:
    2

case "adds numbers once more":
  given input:
    3
  when call "add"
  then equals:
    6
'''
        result = parse_text(source)
        self.assertIsNotNone(result.document)
        output = emit_swift(result.document, target_name="swift")

        self.assertIn("func testAddsNumbers() throws", output)
        self.assertIn("func testAddsNumbersOnceMore() throws", output)

    def test_cli_emits_swift(self) -> None:
        """CLI supports --target swift for emit command."""
        import tempfile
        import os

        # Create a temporary file with Swift target
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tdd', delete=False) as f:
            f.write('''suite "Calculator"
target swift "Calculator"

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
                    "swift",
                    temp_path,
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(ROOT / "src")},
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("final class CalculatorTests: XCTestCase", completed.stdout)
            self.assertIn("func testAddsTwoNumbers() throws", completed.stdout)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
