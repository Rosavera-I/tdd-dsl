from pathlib import Path
import unittest

from tdd_dsl.parser import parse_text


FIXTURES = Path(__file__).parent / "fixtures"


class MutationSmokeTests(unittest.TestCase):
    def test_missing_then_mutation_fails_for_missing_then(self) -> None:
        messages = _diagnostic_messages("mutation_missing_then.tdd")

        self.assertIn("case 'adds two numbers' requires then equals", messages)

    def test_corrupt_json_mutation_fails_for_json_error(self) -> None:
        messages = _diagnostic_messages("mutation_corrupt_json.tdd")

        self.assertTrue(any("invalid JSON for given input" in message for message in messages))

    def test_renamed_when_mutation_fails_for_unrecognized_step(self) -> None:
        messages = _diagnostic_messages("mutation_renamed_when.tdd")

        self.assertIn("expected 'given input:', 'when call \"name\"', or 'then equals:'", messages)
        self.assertIn("case 'adds two numbers' requires when call", messages)


def _diagnostic_messages(fixture_name: str) -> list[str]:
    result = parse_text((FIXTURES / fixture_name).read_text(encoding="utf-8"))
    assert not result.ok
    assert result.document is None
    return [diagnostic.message for diagnostic in result.diagnostics]


if __name__ == "__main__":
    unittest.main()
