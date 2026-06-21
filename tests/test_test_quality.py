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


if __name__ == "__main__":
    unittest.main()
