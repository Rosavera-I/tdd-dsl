"""Kotlin emitter for tdd-dsl.

Generates idiomatic Kotlin tests with JUnit 5:
- Uses kotlin.test for assertions (assertEquals, etc.)
- Proper imports and package declarations
- Backtick-wrapped test method names for readability
- Type inference with `val`
- MapOf/listOf for collections
"""

from __future__ import annotations

import json
import re

from pathlib import Path

from tdd_dsl.ast import Case, Document, Target


# Kotlin keywords that cannot be used as identifiers
_KOTLIN_KEYWORDS = {
    "abstract", "actual", "annotation", "as", "break", "by", "catch",
    "class", "companion", "const", "constructor", "continue", "contract",
    "crossinline", "data", "delegate", "do", "dynamic", "else", "enum",
    "expect", "external", "field", "file", "final", "finally", "for",
    "fun", "get", "header", "if", "impl", "import", "in", "infix",
    "init", "inline", "inner", "interface", "internal", "is", "lateinit",
    "noinline", "null", "object", "open", "operator", "out", "override",
    "package", "param", "private", "property", "protected", "public",
    "receiver", "reified", "return", "sealed", "set", "setparam", "super",
    "suspend", "tailrec", "this", "throw", "true", "try", "typealias",
    "typeof", "val", "var", "vararg", "when", "where", "while",
}


def emit_kotlin(document: Document, target_name: str = "kotlin", source_path: str | Path | None = None) -> str:
    """Emit Kotlin JUnit 5 test class from a TDD DSL document."""
    target = _find_target(document, target_name)
    
    # Extract class name from module (handle both "ClassName" and "com.example.ClassName")
    module_parts = target.module.split(".")
    simple_class_name = module_parts[-1]  # Get last part (the actual class name)
    class_name = _pascal_case(simple_class_name) + "Test"
    
    lines: list[str] = []
    
    # Add package declaration if module contains dots
    if len(module_parts) > 1:
        package = ".".join(module_parts[:-1])
        lines.append(f"package {package}")
        lines.append("")
    
    # Imports
    lines.extend([
        "import org.junit.jupiter.api.Test",
        "import kotlin.test.assertEquals",
        "",
    ])
    
    # Class declaration
    lines.append(f"class {class_name} {{")
    lines.append("")
    
    for case in document.cases:
        method_name = _backtick_method_name(case.name)
        if source_path is not None:
            lines.append(_source_map_comment(source_path, case))
        lines.append(f"    @Test")
        lines.append(f"    fun `{method_name}`() {{")
        lines.extend(_method_body(case, target))
        lines.append("    }")
        lines.append("")
    
    lines.append("}")
    return "\n".join(lines)


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
    if not _is_valid_kotlin_identifier(value) or value in _KOTLIN_KEYWORDS:
        raise ValueError(f"case {case.name!r} has invalid Kotlin call name {value!r}")
    return value


def _method_body(case: Case, target: Target) -> list[str]:
    """Generate the method body for a test case."""
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
    
    # Get simple class name for static method call
    simple_class = target.module.split(".")[-1]
    
    # Declare input variable with appropriate type
    if isinstance(input_value, dict):
        lines.append(f"        // Input: {_kotlin_comment_repr(input_value)}")
        lines.append(f"        val input = {_kotlin_map_literal(input_value)}")
        input_arg = "input"
    elif isinstance(input_value, list):
        lines.append(f"        // Input: {_kotlin_comment_repr(input_value)}")
        lines.append(f"        val input = {_kotlin_list_literal(input_value)}")
        input_arg = "input"
    else:
        input_arg = _kotlin_literal(input_value)
    
    # Call the method under test
    lines.append(f"        val result = {simple_class}.{call_name}({input_arg})")
    
    # Assert expected value
    if isinstance(expected_value, dict):
        lines.append(f"        // Expected: {_kotlin_comment_repr(expected_value)}")
        for key, val in expected_value.items():
            accessor = _kotlin_accessor("result", key)
            lines.append(f"        assertEquals({_kotlin_literal(val)}, {accessor})")
    elif isinstance(expected_value, list):
        lines.append(f"        assertEquals({_kotlin_list_literal(expected_value)}, result)")
    else:
        lines.append(f"        assertEquals({_kotlin_literal(expected_value)}, result)")
    
    return lines


def _source_map_comment(source_path: str | Path, case: Case) -> str:
    return f"    // Source: {Path(source_path).as_posix()}:{case.line}"


def _pascal_case(value: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    parts = re.split(r'[_\-]', value)
    return ''.join(part.capitalize() for part in parts if part)


def _backtick_method_name(name: str) -> str:
    """Convert a test name to a valid backtick-wrapped Kotlin method name.
    
    Kotlin allows spaces and special characters in method names when wrapped in backticks.
    We sanitize the name to avoid issues with backticks or newlines inside the name.
    """
    # Replace backticks with single quotes to avoid breaking the backtick wrapper
    sanitized = name.replace('`', "'")
    # Replace newlines with spaces
    sanitized = sanitized.replace('\n', ' ').replace('\r', ' ')
    # Collapse multiple spaces
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # If the name is empty after sanitization, return a default
    if not sanitized:
        return "test"
    
    return sanitized


def _is_valid_kotlin_identifier(value: str) -> bool:
    """Check if value is a valid Kotlin identifier (without backticks)."""
    if not value:
        return False
    if value in _KOTLIN_KEYWORDS:
        return False
    # Kotlin identifier rules: start with letter or _, followed by letters, digits, or _
    # (simplified check - doesn't handle Unicode fully)
    return bool(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value))


def _kotlin_literal(value: object) -> str:
    """Convert a Python value to a Kotlin literal."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return _kotlin_string(value)
    if isinstance(value, (list, tuple)):
        return _kotlin_list_literal(value)
    if isinstance(value, dict):
        return _kotlin_map_literal(value)
    return str(value)


def _kotlin_string(value: str) -> str:
    """Return a Kotlin string literal with proper escaping."""
    # Escape backslashes, quotes, and special characters
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    escaped = escaped.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    return f'"{escaped}"'


def _kotlin_list_literal(value: list | tuple) -> str:
    """Convert a list to Kotlin listOf() call."""
    if not value:
        return "listOf()"
    items = ", ".join(_kotlin_literal(item) for item in value)
    return f"listOf({items})"


def _kotlin_map_literal(value: dict) -> str:
    """Convert a dict to Kotlin mapOf() call."""
    if not value:
        return "mapOf()"
    pairs = ", ".join(f"{_kotlin_literal(k)} to {_kotlin_literal(v)}" for k, v in value.items())
    return f"mapOf({pairs})"


def _kotlin_accessor(base: str, key: object) -> str:
    """Generate Kotlin accessor for a field/key."""
    # For maps, use indexer; for objects, use property accessor
    key_str = str(key)
    if _is_valid_kotlin_identifier(key_str) and key_str not in _KOTLIN_KEYWORDS:
        # Try property access first (e.g., result.total)
        return f"{base}.{key_str}"
    # Fall back to map access
    return f"{base}[{_kotlin_literal(key)}]"


def _kotlin_comment_repr(value: object) -> str:
    """Return a truncated string representation for comments."""
    s = repr(value)
    if len(s) > 60:
        s = s[:57] + "..."
    return s