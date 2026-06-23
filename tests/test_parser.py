from pathlib import Path
import unittest

from tdd_dsl.parser import parse_text


FIXTURES = Path(__file__).parent / "fixtures"


class ParserTests(unittest.TestCase):
    def test_valid_minimal_fixture_parses_to_ast(self) -> None:
        result = parse_text((FIXTURES / "valid_minimal.tdd").read_text(encoding="utf-8"))

        self.assertTrue(result.ok)
        self.assertEqual(result.diagnostics, ())
        self.assertIsNotNone(result.document)
        assert result.document is not None
        self.assertEqual(result.document.suite, "Calculator")
        self.assertEqual(result.document.targets[0].language, "python")
        self.assertEqual(result.document.targets[0].module, "calculator")
        case = result.document.cases[0]
        self.assertEqual(case.name, "adds two numbers")
        self.assertEqual(case.step("given_input").value, {"a": 2, "b": 3})
        self.assertEqual(case.step("when_call").value, "add")
        self.assertEqual(case.step("then_equals").value, 5)

    def test_showcase_fixture_reads_like_a_real_contract(self) -> None:
        result = parse_text((FIXTURES / "valid_billing_policy.tdd").read_text(encoding="utf-8"))

        self.assertTrue(result.ok)
        self.assertIsNotNone(result.document)
        assert result.document is not None
        self.assertEqual(result.document.suite, "Billing policy contract")
        self.assertEqual(
            [(target.language, target.module) for target in result.document.targets],
            [("python", "billing_policy"), ("typescript", "billing-policy"), ("java", "com.example.BillingPolicy"), ("odin", "billing_policy")],
        )
        self.assertEqual(
            [case.name for case in result.document.cases],
            [
                "grandfathers loyal customers onto the pro cap",
                "flags enterprise usage before charging",
            ],
        )
        review_case = result.document.cases[1]
        self.assertEqual(review_case.step("then_equals").value["requiresReview"], True)
        self.assertEqual(review_case.step("then_equals").value["reason"], "seat_count")

    def test_missing_then_reports_diagnostic(self) -> None:
        result = parse_text((FIXTURES / "invalid_missing_then.tdd").read_text(encoding="utf-8"))

        self.assertFalse(result.ok)
        self.assertIsNone(result.document)
        messages = [diagnostic.message for diagnostic in result.diagnostics]
        self.assertIn("case 'adds two numbers' requires then equals", messages)

    def test_duplicate_steps_report_targeted_diagnostics(self) -> None:
        result = parse_text((FIXTURES / "invalid_duplicate_steps.tdd").read_text(encoding="utf-8"))

        self.assertFalse(result.ok)
        self.assertIsNone(result.document)
        messages = [diagnostic.message for diagnostic in result.diagnostics]
        self.assertIn("case 'adds two numbers' has duplicate given input; first declared at line 5", messages)
        self.assertIn("case 'adds two numbers' has duplicate when call; first declared at line 9", messages)
        self.assertIn("case 'adds two numbers' has duplicate then equals; first declared at line 11", messages)

    def test_bad_json_reports_diagnostic_without_traceback(self) -> None:
        result = parse_text((FIXTURES / "invalid_bad_json.tdd").read_text(encoding="utf-8"))

        self.assertFalse(result.ok)
        self.assertIsNone(result.document)
        self.assertTrue(any("invalid JSON for given input" in diagnostic.message for diagnostic in result.diagnostics))


if __name__ == "__main__":
    unittest.main()
