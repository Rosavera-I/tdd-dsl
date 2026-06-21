from __future__ import annotations

import json
import keyword
import re

from tdd_dsl.ast import Case, Document, Target


_TS_KEYWORDS = {
    "break",
    "case",
    "catch",
    "class",
    "const",
    "continue",
    "debugger",
    "default",
    "delete",
    "do",
    "else",
    "enum",
    "export",
    "extends",
    "false",
    "finally",
    "for",
    "function",
    "if",
    "import",
    "in",
    "instanceof",
    "new",
    "null",
    "return",
    "super",
    "switch",
    "this",
    "throw",
    "true",
    "try",
    "typeof",
    "var",
    "void",
    "while",
    "with",
    "as",
    "implements",
    "interface",
    "let",
    "package",
    "private",
    "protected",
    "public",
    "static",
    "yield",
}


def emit_vitest(document: Document, target_name: str = "typescript") -> str:
    target = _find_target(document, target_name)
    calls = [_call_name(case) for case in document.cases]
    imports = ", ".join(_unique_ordered(calls))
    lines = [
        'import { describe, expect, test } from "vitest";',
        f"import {{ {imports} }} from {_js_literal(target.module)};",
        "",
        f"describe({_js_literal(document.suite)}, () => {{",
    ]

    for case in document.cases:
        lines.append(f"  test({_js_literal(case.name)}, () => {{")
        lines.append(f"    const result = {_call_name(case)}({_call_arguments(case)});")
        lines.append(f"    expect(result).toEqual({_js_literal(_expected_value(case))});")
        lines.append("  });")
    lines.append("});")

    return "\n".join(lines).rstrip() + "\n"


def _find_target(document: Document, language: str) -> Target:
    for target in document.targets:
        if target.language == language:
            return target
    raise ValueError(f"document does not declare target {language!r}")


def _call_name(case: Case) -> str:
    step = case.step("when_call")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing when call")
    value = str(step.value)
    if not _is_identifier(value) or value in _TS_KEYWORDS:
        raise ValueError(f"case {case.name!r} has invalid TypeScript call name {value!r}")
    return value


def _call_arguments(case: Case) -> str:
    step = case.step("given_input")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing given input")
    return _js_literal(step.value)


def _expected_value(case: Case) -> object:
    step = case.step("then_equals")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing then equals")
    return step.value


def _js_literal(value: object) -> str:
    raw = json.dumps(value, ensure_ascii=False, indent=2)
    raw = re.sub(r'^(\s*)"([A-Za-z_$][0-9A-Za-z_$]*)":', r"\1\2:", raw, flags=re.MULTILINE)
    if "\n" not in raw:
        return raw
    return "\n".join("    " + line for line in raw.splitlines()).lstrip()


def _is_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_$][0-9A-Za-z_$]*", value)) and not keyword.iskeyword(value)


def _unique_ordered(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered
