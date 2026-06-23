"""Rust test emitter for tdd-dsl.

Generates idiomatic Rust tests using the standard `cargo test` / `#[test]` framework.
"""

from __future__ import annotations

import json
import re

from pathlib import Path

from tdd_dsl.ast import Case, Document, Target


_RUST_KEYWORDS = {
    "as", "async", "await", "break", "const", "continue", "crate", "dyn",
    "else", "enum", "extern", "false", "fn", "for", "if", "impl", "in",
    "let", "loop", "match", "mod", "move", "mut", "pub", "ref", "return",
    "self", "Self", "static", "struct", "super", "trait", "true", "type",
    "union", "unsafe", "use", "where", "while", "abstract", "become", "box",
    "do", "final", "macro", "override", "priv", "typeof", "unsized",
    "virtual", "yield", "try", "macro_rules", "include", "include_str",
    "include_bytes", "format", "println", "eprintln", "print", "eprint",
    "vec", "string", "option", "result", "box", "rc", "arc", "cell",
    "refcell", "mutex", "rwlock",
}


def emit_rust(document: Document, target_name: str = "rust", source_path: str | Path | None = None) -> str:
    """Emit Rust test module from a TDD DSL document."""
    target = _find_target(document, target_name)
    module_name = _snake_case(target.module)
    
    lines = [
        f"use {target.module}::*;",
        "",
    ]
    
    # Track used function names to avoid duplicates
    used_names: set[str] = set()
    
    for case in document.cases:
        function_name = _unique_name(_snake_case(f"test_{case.name}"), used_names)
        if source_path is not None:
            lines.append(_source_map_comment(source_path, case))
        lines.append(f"#[test]")
        lines.append(f"fn {function_name}() {{")
        lines.extend(_test_body(case))
        lines.append("}")
        lines.append("")
    
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
    if not _is_valid_rust_identifier(value) or value in _RUST_KEYWORDS:
        raise ValueError(f"case {case.name!r} has invalid Rust call name {value!r}")
    return value


def _test_body(case: Case) -> list[str]:
    """Generate the body of a test function."""
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
    
    # Generate input variable with type annotation if complex
    if isinstance(input_value, dict):
        lines.append(f"    // Input: {_rust_comment_repr(input_value)}")
        lines.append(f"    let input = {_rust_map_literal(input_value)};")
        input_arg = "&input"
    elif isinstance(input_value, list):
        lines.append(f"    // Input: {_rust_comment_repr(input_value)}")
        lines.append(f"    let input = {_rust_list_literal(input_value)};")
        input_arg = "&input"
    elif input_value is None:
        input_arg = "()"
    elif isinstance(input_value, (dict, list)):
        lines.append(f"    let input = {_rust_literal(input_value)};")
        input_arg = "&input"
    else:
        input_arg = _rust_literal(input_value)
    
    # Call the function under test
    lines.append(f"    let result = {call_name}({input_arg});")
    
    # Generate assertion
    expected_literal = _rust_literal(expected_value)
    if isinstance(expected_value, dict) and expected_value:
        # For expected objects, assert field by field for better error messages
        lines.append(f"    // Expected: {_rust_comment_repr(expected_value)}")
        for key, val in expected_value.items():
            field_accessor = f'result.{_snake_case(str(key))}'
            lines.append(f"    assert_eq!({_rust_literal(val)}, {field_accessor});")
    elif isinstance(expected_value, (list, tuple)) and len(expected_value) > 3:
        # For long lists, use a binding
        lines.append(f"    let expected = {expected_literal};")
        lines.append(f"    assert_eq!(expected, result);")
    else:
        lines.append(f"    assert_eq!({expected_literal}, result);")
    
    return lines


def _source_map_comment(source_path: str | Path, case: Case) -> str:
    return f"// Source: {Path(source_path).as_posix()}:{case.line}"


def _snake_case(value: str) -> str:
    """Convert a string to valid snake_case Rust identifier."""
    # Remove special characters and normalize whitespace
    value = re.sub(r'[^\w\s]', ' ', value)
    value = re.sub(r'\s+', '_', value.strip())
    
    # Convert camelCase/PascalCase to snake_case
    value = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', value)
    
    # Split on existing underscores and dashes, lowercase everything
    parts = re.split(r'[_\-]+', value.lower())
    result = '_'.join(p for p in parts if p)
    
    # Ensure valid Rust identifier
    if not result or (not result[0].isalpha() and result[0] != '_'):
        result = 'test_' + result if result else 'test'
    
    # Avoid keywords
    if result in _RUST_KEYWORDS:
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


def _is_valid_rust_identifier(value: str) -> bool:
    """Check if value is a valid Rust identifier."""
    if not value:
        return False
    # Rust identifiers start with letter or underscore, followed by alphanumeric or underscore
    # Unicode identifiers are supported but we stick to ASCII for safety
    return bool(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value))


def _rust_literal(value: object) -> str:
    """Convert a Python value to a Rust literal."""
    if value is None:
        return "()"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return _rust_string(value)
    if isinstance(value, (list, tuple)):
        return _rust_list_literal(value)
    if isinstance(value, dict):
        return _rust_map_literal(value)
    return str(value)


def _rust_string(value: str) -> str:
    """Return a Rust string literal with proper escaping."""
    # Escape backslashes and quotes
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    # Escape special characters
    escaped = escaped.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    return f'"{escaped}"'


def _rust_list_literal(value: list | tuple) -> str:
    """Convert a list to Rust vec![] macro."""
    if not value:
        return "vec![]"
    items = ", ".join(_rust_literal(item) for item in value)
    return f"vec![{items}]"


def _rust_map_literal(value: dict) -> str:
    """Convert a dict to Rust HashMap literal using maplit or manual construction.
    
    We use a Vec of tuples and collect() for better compatibility without extra deps.
    """
    if not value:
        return "std::collections::HashMap::new()"
    
    items = ", ".join(f"({_rust_literal(k)}, {_rust_literal(v)})" for k, v in value.items())
    return f"vec![{items}].into_iter().collect::<std::collections::HashMap<_, _>>()"


def _rust_comment_repr(value: object) -> str:
    """Return a truncated string representation for comments."""
    s = repr(value)
    if len(s) > 60:
        s = s[:57] + "..."
    return s