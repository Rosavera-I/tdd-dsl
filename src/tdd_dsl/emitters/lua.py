from __future__ import annotations

import re
from pathlib import Path

from tdd_dsl.ast import Case, Document, Target


_LUA_KEYWORDS = {
    "and",
    "break",
    "do",
    "else",
    "elseif",
    "end",
    "false",
    "for",
    "function",
    "goto",
    "if",
    "in",
    "local",
    "nil",
    "not",
    "or",
    "repeat",
    "return",
    "then",
    "true",
    "until",
    "while",
}


def emit_lua(document: Document, target_name: str = "lua", source_path: str | Path | None = None) -> str:
    target = _find_target(document, target_name)
    lines = [
        f"local subject = require({_lua_string(target.module)})",
        "",
        f"describe({_lua_string(document.suite)}, function()",
    ]

    for case in document.cases:
        if source_path is not None:
            lines.append(_source_map_comment(source_path, case))
        lines.append(f"  it({_lua_string(case.name)}, function()")
        lines.append(f"    local result = subject.{_call_name(case)}({_call_arguments(case)})")
        lines.extend(_assertion(_expected_value(case)))
        lines.append("  end)")
    lines.append("end)")

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
    if not _is_identifier(value) or value in _LUA_KEYWORDS:
        raise ValueError(f"case {case.name!r} has invalid Lua call name {value!r}")
    return value


def _call_arguments(case: Case) -> str:
    step = case.step("given_input")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing given input")
    return _lua_literal(step.value)


def _expected_value(case: Case) -> object:
    step = case.step("then_equals")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing then equals")
    return step.value


def _assertion(expected: object) -> list[str]:
    if isinstance(expected, dict):
        lines: list[str] = []
        for key, value in expected.items():
            lines.extend(_assert_field("result", key, value))
        return lines
    return [f"    assert.are.same({_lua_literal(expected)}, result)"]


def _assert_field(base: str, key: object, value: object) -> list[str]:
    accessor = f"{base}{_lua_accessor(key)}"
    if isinstance(value, dict):
        lines: list[str] = []
        for child_key, child_value in value.items():
            lines.extend(_assert_field(accessor, child_key, child_value))
        return lines
    return [f"    assert.are.same({_lua_literal(value)}, {accessor})"]


def _lua_literal(value: object, indent: int = 0) -> str:
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return _lua_string(value)
    if isinstance(value, (list, tuple)):
        if not value:
            return "{}"
        return "{ " + ", ".join(_lua_literal(item, indent) for item in value) + " }"
    if isinstance(value, dict):
        if not value:
            return "{}"
        pairs = []
        for key, item in value.items():
            pairs.append(f"{_lua_key(key)} = {_lua_literal(item, indent)}")
        return "{ " + ", ".join(pairs) + " }"
    return str(value)


def _lua_key(key: object) -> str:
    text = str(key)
    if _is_identifier(text) and text not in _LUA_KEYWORDS:
        return text
    return f"[{_lua_string(text)}]"


def _lua_accessor(key: object) -> str:
    text = str(key)
    if _is_identifier(text) and text not in _LUA_KEYWORDS:
        return f".{text}"
    return f"[{_lua_string(text)}]"


def _lua_string(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


def _is_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][0-9A-Za-z_]*", value))


def _source_map_comment(source_path: str | Path, case: Case) -> str:
    return f"  -- Source: {Path(source_path).as_posix()}:{case.line}"
