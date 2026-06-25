from __future__ import annotations

import re
from pathlib import Path

from tdd_dsl.ast import Case, Document, Target


_RUBY_KEYWORDS = {
    "alias",
    "and",
    "begin",
    "break",
    "case",
    "class",
    "def",
    "defined?",
    "do",
    "else",
    "elsif",
    "end",
    "ensure",
    "false",
    "for",
    "if",
    "in",
    "module",
    "next",
    "nil",
    "not",
    "or",
    "redo",
    "rescue",
    "retry",
    "return",
    "self",
    "super",
    "then",
    "true",
    "undef",
    "unless",
    "until",
    "when",
    "while",
    "yield",
}


def emit_rspec(document: Document, target_name: str = "ruby", source_path: str | Path | None = None) -> str:
    target = _find_target(document, target_name)
    lines = [
        f"require {_ruby_string(target.module)}",
        "",
        f"RSpec.describe {_ruby_string(document.suite)} do",
    ]

    for case in document.cases:
        if source_path is not None:
            lines.append(_source_map_comment(source_path, case))
        lines.append(f"  it {_ruby_string(case.name)} do")
        lines.append(f"    result = {_call_name(case)}({_call_arguments(case)})")
        lines.append(f"    expect(result).to eq({_ruby_literal(_expected_value(case))})")
        lines.append("  end")
    lines.append("end")

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
    if not _is_identifier(value) or value in _RUBY_KEYWORDS:
        raise ValueError(f"case {case.name!r} has invalid Ruby call name {value!r}")
    return value


def _call_arguments(case: Case) -> str:
    step = case.step("given_input")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing given input")
    value = step.value
    if isinstance(value, dict) and all(_is_symbol_key(key) for key in value):
        return ", ".join(f"{key}: {_ruby_literal(item)}" for key, item in value.items())
    return _ruby_literal(value)


def _expected_value(case: Case) -> object:
    step = case.step("then_equals")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing then equals")
    return step.value


def _ruby_literal(value: object) -> str:
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return _ruby_string(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_ruby_literal(item) for item in value) + "]"
    if isinstance(value, dict):
        if not value:
            return "{}"
        pairs = []
        for key, item in value.items():
            if _is_symbol_key(key):
                pairs.append(f"{key}: {_ruby_literal(item)}")
            else:
                pairs.append(f"{_ruby_string(str(key))} => {_ruby_literal(item)}")
        return "{ " + ", ".join(pairs) + " }"
    return str(value)


def _ruby_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _is_symbol_key(value: object) -> bool:
    text = str(value)
    return _is_identifier(text) and text not in _RUBY_KEYWORDS


def _is_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z_][0-9A-Za-z_]*[!?=]?", value))


def _source_map_comment(source_path: str | Path, case: Case) -> str:
    return f"  # Source: {Path(source_path).as_posix()}:{case.line}"
