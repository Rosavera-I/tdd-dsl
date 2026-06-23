"""Odin test emitter for tdd-dsl.

Generates idiomatic Odin tests using the core:testing framework with:
- Proper package declarations and imports
- snake_case test procedure names following Odin conventions
- @(test) attributes for test discovery
- testing.expect_value() for value assertions
- Odin struct literals for object inputs
"""

from __future__ import annotations

import json
import re

from pathlib import Path

from tdd_dsl.ast import Case, Document, Target


_ODIN_KEYWORDS = {
    "align_of", "asm", "auto_cast", "bit_field", "bit_set", "break", "case",
    "cast", "context", "continue", "defer", "distinct", "do", "dynamic",
    "else", "enum", "fallthrough", "for", "foreign", "if", "import",
    "in", "inline", "map", "not_in", "offset_of", "or_else", "or_return",
    "package", "proc", "return", "size_of", "struct", "switch", "transmute",
    "typeid", "union", "using", "when", "where",
    # Types
    "bool", "b8", "b16", "b32", "b64",
    "i8", "i16", "i32", "i64", "i128", "int",
    "u8", "u16", "u32", "u64", "u128", "uint", "uintptr",
    "f16", "f32", "f64", "f16le", "f16be", "f32le", "f32be", "f64le", "f64be",
    "complex32", "complex64", "complex128",
    "quaternion64", "quaternion128", "quaternion256",
    "rune", "string", "cstring", "rawptr", "any",
    # Built-in procedures
    "len", "cap", "assert", "panic", "unimplemented", "unreachable",
}


def emit_odin(document: Document, target_name: str = "odin", source_path: str | Path | None = None) -> str:
    """Emit Odin test file from a TDD DSL document."""
    target = _find_target(document, target_name)
    package_name = _odin_package_name(target.module)

    lines = [
        f"package {package_name}",
        "",
        'import "core:testing"',
        "",
    ]

    # Track used procedure names to avoid duplicates
    used_names: set[str] = set()

    for case in document.cases:
        proc_name = _unique_name(_snake_case(f"test_{case.name}"), used_names)
        if source_path is not None:
            lines.append(_source_map_comment(source_path, case))
        lines.append(f"@(test)")
        lines.append(f"{proc_name} :: proc(t: ^testing.T) {{")
        lines.extend(_test_body(case, target))
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _find_target(document: Document, language: str) -> Target:
    for target in document.targets:
        if target.language == language:
            return target
    raise ValueError(f"document does not declare target {language!r}")


def _odin_package_name(module: str) -> str:
    """Extract a valid Odin package name from the module path.
    
    Handles:
    - Simple names: "calculator" -> "calculator"
    - Paths with slashes: "src/calculator" -> "calculator"
    - Dotted paths: "my.lib.calculator" -> "calculator"
    """
    # Take the last segment (handle both / and . separators)
    parts = re.split(r'[/\.]', module)
    name = parts[-1] if parts else module
    
    # Sanitize to valid Odin identifier
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = name.lower()
    
    # Ensure it starts with a letter
    if name and name[0].isdigit():
        name = "pkg_" + name
    
    # Avoid keywords
    if name in _ODIN_KEYWORDS:
        name = name + "_test"
    
    # Default fallback
    if not name or not _is_valid_odin_identifier(name):
        name = "main"
    
    return name


def _snake_case(value: str) -> str:
    """Convert a string to valid snake_case Odin identifier."""
    # Remove special characters and normalize whitespace
    value = re.sub(r'[^\w\s]', ' ', value)
    value = re.sub(r'\s+', '_', value.strip())
    
    # Convert camelCase/PascalCase to snake_case
    value = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', value)
    
    # Split on existing underscores and dashes, lowercase everything
    parts = re.split(r'[_\-]+', value.lower())
    result = '_'.join(p for p in parts if p)
    
    # Ensure valid Odin identifier
    if not result or (not result[0].isalpha() and result[0] != '_'):
        result = 'test_' + result if result else 'test'
    
    # Avoid keywords
    if result in _ODIN_KEYWORDS:
        result = result + "_test"
    
    return result


def _unique_name(base: str, used: set[str]) -> str:
    """Generate a unique name by appending a number if needed."""
    if base not in used:
        used.add(base)
        return base
    index = 2
    while f"{base}_{index}" in used:
        index += 1
    name = f"{base}_{index}"
    used.add(name)
    return name


def _test_body(case: Case, target: Target) -> list[str]:
    """Generate the body of an Odin test procedure."""
    lines = []
    
    input_step = case.step("given_input")
    expected_step = case.step("then_equals")
    call_name = _call_name(case)
    
    if input_step is None:
        raise ValueError(f"case {case.name!r} is missing given input")
    if expected_step is None:
        raise ValueError(f"case {case.name!r} is missing then equals")
    
    input_value = input_step.value
    expected_value = expected_step.value
    
    # Generate input variable
    if isinstance(input_value, dict):
        if input_value:
            lines.append(f"    // Input: {_odin_comment_repr(input_value)}")
            lines.append(f"    input := {_odin_struct_literal(input_value)}")
            input_arg = "input"
        else:
            input_arg = "{}"
    elif isinstance(input_value, (list, tuple)):
        if input_value:
            lines.append(f"    // Input: {_odin_comment_repr(input_value)}")
            lines.append(f"    input := {_odin_array_literal(input_value)}")
            input_arg = "input"
        else:
            input_arg = "[]"
    elif input_value is None:
        input_arg = "nil"
    else:
        input_arg = _odin_literal(input_value)
    
    # Call the function under test
    lines.append(f"    result := {call_name}({input_arg})")
    lines.append("")
    
    # Generate assertion
    if isinstance(expected_value, dict) and expected_value:
        # For expected structs, assert field by field for better error messages
        lines.append(f"    // Expected: {_odin_comment_repr(expected_value)}")
        for key, val in expected_value.items():
            field_name = _snake_case(str(key))
            lines.append(f"    testing.expect_value(t, result.{field_name}, {_odin_literal(val)})")
    elif isinstance(expected_value, (list, tuple)) and len(expected_value) > 3:
        # For long arrays, use a binding
        lines.append(f"    expected := {_odin_literal(expected_value)}")
        lines.append(f"    testing.expect_value(t, result, expected)")
    else:
        lines.append(f"    testing.expect_value(t, result, {_odin_literal(expected_value)})")
    
    return lines


def _call_name(case: Case) -> str:
    step = case.step("when_call")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing when call")
    value = str(step.value)
    if not _is_valid_odin_identifier(value) or value in _ODIN_KEYWORDS:
        raise ValueError(f"case {case.name!r} has invalid Odin call name {value!r}")
    return value


def _is_valid_odin_identifier(value: str) -> bool:
    """Check if a string is a valid Odin identifier."""
    if not value:
        return False
    if value in _ODIN_KEYWORDS:
        return False
    # Odin identifier rules: start with letter or _, followed by letters, digits, or _
    return bool(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value))


def _odin_literal(value: object) -> str:
    """Convert a Python value to an Odin literal."""
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return _odin_string(value)
    if isinstance(value, (list, tuple)):
        return _odin_array_literal(value)
    if isinstance(value, dict):
        return _odin_struct_literal(value)
    return str(value)


def _odin_string(value: str) -> str:
    """Return an Odin string literal with proper escaping."""
    # Escape backslashes and quotes
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    # Escape special characters
    escaped = escaped.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    return f'"{escaped}"'


def _odin_array_literal(value: list | tuple) -> str:
    """Convert a list to an Odin array literal."""
    if not value:
        return "[]"
    items = ", ".join(_odin_literal(item) for item in value)
    return f"[]{{{items}}}"


def _odin_struct_literal(value: dict) -> str:
    """Convert a dict to an Odin struct literal.
    
    In Odin, struct literals use field = value syntax.
    We assume the user has defined appropriate struct types.
    """
    if not value:
        return "{}"
    pairs = ", ".join(f"{_snake_case(str(k))} = {_odin_literal(v)}" for k, v in value.items())
    return f"{{{pairs}}}"


def _odin_comment_repr(value: object) -> str:
    """Return a truncated string representation for comments."""
    s = repr(value)
    if len(s) > 60:
        s = s[:57] + "..."
    return s


def _source_map_comment(source_path: str | Path, case: Case) -> str:
    return f"// Source: {Path(source_path).as_posix()}:{case.line}"
