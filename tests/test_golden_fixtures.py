from pathlib import Path
import os
import unittest

from tdd_dsl.emitters.gotest import emit_gotest
from tdd_dsl.emitters.kotlin import emit_kotlin
from tdd_dsl.emitters.odin import emit_odin
from tdd_dsl.emitters.pytest import emit_pytest
from tdd_dsl.emitters.rust import emit_rust
from tdd_dsl.emitters.swift import emit_swift
from tdd_dsl.emitters.vitest import emit_vitest
from tdd_dsl.emitters.xunit import emit_xunit
from tdd_dsl.parser import parse_text


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
GOLDENS = ROOT / "tests" / "goldens"
UPDATE_ENV = "TDD_DSL_UPDATE_GOLDENS"


class GoldenFixtureTests(unittest.TestCase):
    def test_python_golden_matches_minimal_fixture(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_minimal.tdd", "python"),
            golden=GOLDENS / "python" / "valid_minimal.py",
        )

    def test_typescript_golden_matches_typescript_fixture(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_typescript.tdd", "typescript"),
            golden=GOLDENS / "typescript" / "valid_typescript.test.ts",
        )

    def test_go_golden_matches_minimal_fixture(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_minimal.tdd", "go"),
            golden=GOLDENS / "go" / "valid_minimal_test.go",
        )

    def test_go_golden_matches_billing_policy_fixture(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_billing_policy.tdd", "go"),
            golden=GOLDENS / "go" / "valid_billing_policy_test.go",
        )

    def test_showcase_contract_emits_documentary_python(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_billing_policy.tdd", "python"),
            golden=GOLDENS / "python" / "valid_billing_policy.py",
        )

    def test_showcase_python_output_compiles(self) -> None:
        source = _emit_fixture("valid_billing_policy.tdd", "python")

        compile(source, "valid_billing_policy.py", "exec")

    def test_showcase_contract_emits_documentary_typescript(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_billing_policy.tdd", "typescript"),
            golden=GOLDENS / "typescript" / "valid_billing_policy.test.ts",
        )

    def test_python_output_is_stable_across_repeated_emits(self) -> None:
        first = _emit_fixture("valid_minimal.tdd", "python")
        second = _emit_fixture("valid_minimal.tdd", "python")

        self.assertEqual(first, second)

    def test_showcase_contract_is_stable_across_repeated_emits(self) -> None:
        for target in ("python", "typescript"):
            with self.subTest(target=target):
                first = _emit_fixture("valid_billing_policy.tdd", target)
                second = _emit_fixture("valid_billing_policy.tdd", target)

                self.assertEqual(first, second)

    def test_rust_golden_matches_minimal_fixture(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_minimal.tdd", "rust"),
            golden=GOLDENS / "rust" / "valid_minimal.rs",
        )

    def test_rust_output_is_stable_across_repeated_emits(self) -> None:
        first = _emit_fixture("valid_minimal.tdd", "rust")
        second = _emit_fixture("valid_minimal.tdd", "rust")

        self.assertEqual(first, second)

    def test_odin_golden_matches_minimal_fixture(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_minimal.tdd", "odin"),
            golden=GOLDENS / "odin" / "valid_minimal.odin",
        )

    def test_odin_output_is_stable_across_repeated_emits(self) -> None:
        first = _emit_fixture("valid_minimal.tdd", "odin")
        second = _emit_fixture("valid_minimal.tdd", "odin")

        self.assertEqual(first, second)

    def test_csharp_golden_matches_minimal_fixture(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_minimal.tdd", "csharp"),
            golden=GOLDENS / "csharp" / "valid_minimal.cs",
        )

    def test_csharp_golden_matches_billing_policy_fixture(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_billing_policy.tdd", "csharp"),
            golden=GOLDENS / "csharp" / "valid_billing_policy.cs",
        )

    def test_csharp_output_is_stable_across_repeated_emits(self) -> None:
        first = _emit_fixture("valid_minimal.tdd", "csharp")
        second = _emit_fixture("valid_minimal.tdd", "csharp")

        self.assertEqual(first, second)

    def test_swift_golden_matches_minimal_fixture(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_minimal.tdd", "swift"),
            golden=GOLDENS / "swift" / "valid_minimal.swift",
        )

    def test_swift_golden_matches_billing_policy_fixture(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_billing_policy.tdd", "swift"),
            golden=GOLDENS / "swift" / "valid_billing_policy.swift",
        )

    def test_swift_output_is_stable_across_repeated_emits(self) -> None:
        first = _emit_fixture("valid_minimal.tdd", "swift")
        second = _emit_fixture("valid_minimal.tdd", "swift")

        self.assertEqual(first, second)

    def test_kotlin_golden_matches_minimal_fixture(self) -> None:
        self.assertGolden(
            actual=_emit_fixture("valid_minimal.tdd", "kotlin"),
            golden=GOLDENS / "kotlin" / "valid_minimal.kt",
        )

    def test_kotlin_output_is_stable_across_repeated_emits(self) -> None:
        first = _emit_fixture("valid_minimal.tdd", "kotlin")
        second = _emit_fixture("valid_minimal.tdd", "kotlin")

        self.assertEqual(first, second)

    def assertGolden(self, actual: str, golden: Path) -> None:
        if os.environ.get(UPDATE_ENV) == "1":
            golden.parent.mkdir(parents=True, exist_ok=True)
            golden.write_text(actual, encoding="utf-8")

        self.assertEqual(golden.read_text(encoding="utf-8"), actual)


def _emit_fixture(name: str, target: str) -> str:
    result = parse_text((FIXTURES / name).read_text(encoding="utf-8"))
    assert result.document is not None
    if target == "python":
        return emit_pytest(result.document)
    if target == "typescript":
        return emit_vitest(result.document)
    if target == "go":
        return emit_gotest(result.document, target_name="go", source_path=f"tests/fixtures/{name}")
    if target == "rust":
        return emit_rust(result.document, target_name="rust", source_path=f"tests/fixtures/{name}")
    if target == "odin":
        return emit_odin(result.document, target_name="odin", source_path=f"tests/fixtures/{name}")
    if target == "csharp":
        return emit_xunit(result.document, target_name="csharp", source_path=f"tests/fixtures/{name}")
    if target == "swift":
        return emit_swift(result.document, target_name="swift", source_path=f"tests/fixtures/{name}")
    if target == "kotlin":
        return emit_kotlin(result.document, target_name="kotlin", source_path=f"tests/fixtures/{name}")
    raise ValueError(f"unsupported test target: {target}")


if __name__ == "__main__":
    unittest.main()
