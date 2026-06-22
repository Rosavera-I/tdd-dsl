from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class TestQualityTests(unittest.TestCase):
    def test_negative_fixtures_exist(self) -> None:
        invalid_fixtures = list((ROOT / "tests" / "fixtures").glob("invalid_*.tdd"))

        self.assertGreaterEqual(len(invalid_fixtures), 2)

    def test_tests_assert_diagnostics_not_just_exit_codes(self) -> None:
        parser_test = (ROOT / "tests" / "test_parser.py").read_text(encoding="utf-8")

        self.assertIn("diagnostic.message", parser_test)
        self.assertIn("invalid JSON", parser_test)
        self.assertIn("requires then equals", parser_test)
        self.assertIn("duplicate given input", parser_test)

    def test_emitter_tests_assert_generated_call_and_assertion(self) -> None:
        emitter_test = (ROOT / "tests" / "test_pytest_emitter.py").read_text(encoding="utf-8")

        self.assertIn("calculator.add(a=2, b=3)", emitter_test)
        self.assertIn("assert result == 5", emitter_test)

    def test_showcase_fixture_sells_polyglot_contracts_not_only_calculators(self) -> None:
        showcase = (ROOT / "tests" / "fixtures" / "valid_billing_policy.tdd").read_text(encoding="utf-8")

        self.assertIn('suite "Billing policy contract"', showcase)
        self.assertIn('target python "billing_policy"', showcase)
        self.assertIn('target typescript "billing-policy"', showcase)
        self.assertIn("requiresReview", showcase)
        self.assertIn("seat_count", showcase)

    def test_golden_suite_proves_one_contract_can_emit_two_ecosystems(self) -> None:
        python_golden = ROOT / "tests" / "goldens" / "python" / "valid_billing_policy.py"
        typescript_golden = ROOT / "tests" / "goldens" / "typescript" / "valid_billing_policy.test.ts"

        self.assertTrue(python_golden.exists())
        self.assertTrue(typescript_golden.exists())
        self.assertIn("quoteSubscription", python_golden.read_text(encoding="utf-8"))
        self.assertIn("quoteSubscription", typescript_golden.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
