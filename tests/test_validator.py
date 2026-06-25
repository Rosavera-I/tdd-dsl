from pathlib import Path
import unittest

from tdd_dsl.parser import parse_text


FIXTURES = Path(__file__).parent / "fixtures"


class ValidatorTests(unittest.TestCase):
    def test_semantic_validator_reports_all_diagnostics_in_one_pass(self) -> None:
        result = parse_text((FIXTURES / "invalid_semantics.tdd").read_text(encoding="utf-8"))

        self.assertFalse(result.ok)
        self.assertIsNone(result.document)
        messages = [diagnostic.message for diagnostic in result.diagnostics]
        self.assertIn("unsupported target 'php'", messages)
        self.assertIn("duplicate case name 'adds two numbers'; first declared at line 5", messages)
        self.assertIn(
            "python target requires object input keys to be valid parameter names in case 'adds two numbers'",
            messages,
        )
        self.assertEqual(len(messages), 3)


if __name__ == "__main__":
    unittest.main()
