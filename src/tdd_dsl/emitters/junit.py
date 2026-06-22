"""Java JUnit 5 emitter for tdd-dsl.

Generates idiomatic JUnit 5 tests with:
- Proper imports and static imports for assertions
- CamelCase test method names
- @DisplayName annotations for readable test names
- Parameterized tests for multiple cases (if applicable)
"""

from __future__ import annotations

import json
import keyword
import re

from pathlib import Path

from tdd_dsl.ast import Case, Document, Target


_JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new",
    "package", "private", "protected", "public", "return", "short", "static",
    "strictfp", "super", "switch", "synchronized", "this", "throw", "throws",
    "transient", "try", "void", "volatile", "while", "true", "false", "null",
    "var", "yield", "record", "sealed", "permits", "non-sealed",
}


def emit_junit(document: Document, target_name: str = "java", source_path: str | Path | None = None) -> str:
    """Emit JUnit 5 test class from a TDD DSL document."""
    target = _find_target(document, target_name)
    # Extract class name from module (handle both "ClassName" and "com.example.ClassName")
    module_parts = target.module.split(".")
    simple_class_name = module_parts[-1]  # Get last part (the actual class name)
    class_name = _pascal_case(simple_class_name) + "Test"

    lines = [
        "import org.junit.jupiter.api.Test;",
        "import org.junit.jupiter.api.DisplayName;",
        "import static org.junit.jupiter.api.Assertions.assertEquals;",
        "",
    ]

    # Add import for the class under test
    lines.append(f"import {target.module};")
    lines.append("")
    lines.append(f"public class {class_name} {{")
    lines.append("")

    for case in document.cases:
        method_name = _camel_case(f"test_{case.name}")
        if source_path is not None:
            lines.append(_source_map_comment(source_path, case))
        lines.append(f"    @Test")
        lines.append(f'    @DisplayName({_java_string(case.name)})')
        lines.append(f"    public void {method_name}() {{")
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
    if not _is_valid_java_identifier(value) or value in _JAVA_KEYWORDS:
        raise ValueError(f"case {case.name!r} has invalid Java call name {value!r}")
    return value


def _method_body(case: Case, target: Target) -> list[str]:
    """Generate the method body for a test case."""
    lines = []

    # Get input and expected values
    input_step = case.step("given_input")
    expected_step = case.step("then_equals")
    call_name = _call_name(case)

    if input_step is None:
        raise ValueError(f"case {case.name!r} is missing given input")
    if expected_step is None:
        raise ValueError(f"case {case.name!r} is missing then equals")

    input_value = input_step.value
    expected_value = expected_step.value

    # Declare input variable with appropriate type
    if isinstance(input_value, dict):
        lines.append(f"        // Input: {_java_comment_repr(input_value)}")
        lines.append(f"        var input = {_java_map_literal(input_value)};")
        input_arg = "input"
    elif isinstance(input_value, list):
        lines.append(f"        // Input: {_java_comment_repr(input_value)}")
        lines.append(f"        var input = {_java_list_literal(input_value)};")
        input_arg = "input"
    else:
        input_arg = _java_literal(input_value)

    # Call the method under test (use simple class name for static method call)
    simple_class = target.module.split(".")[-1]
    lines.append(f"        var result = {simple_class}.{call_name}({input_arg});")

    # Assert expected value
    if isinstance(expected_value, dict):
        lines.append(f"        // Expected: {_java_comment_repr(expected_value)}")
        for key, val in expected_value.items():
            accessor = _java_accessor("result", key)
            lines.append(f"        assertEquals({_java_literal(val)}, {accessor});")
    elif isinstance(expected_value, list):
        lines.append(f"        assertEquals({_java_list_literal(expected_value)}, result);")
    else:
        lines.append(f"        assertEquals({_java_literal(expected_value)}, result);")

    return lines


def _source_map_comment(source_path: str | Path, case: Case) -> str:
    return f"    // Source: {source_path}:{case.line}"


def _pascal_case(value: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    parts = re.split(r'[_\-]', value)
    return ''.join(part.capitalize() for part in parts if part)


def _camel_case(value: str) -> str:
    """Convert a test name to valid camelCase Java method name."""
    # Remove special characters and normalize
    value = re.sub(r'[^\w\s]', ' ', value)
    value = re.sub(r'\s+', '_', value.strip())
    parts = value.split('_')

    # First part lowercase, rest PascalCase
    if not parts:
        return "test"

    first = parts[0].lower()
    rest = [p.capitalize() for p in parts[1:] if p]

    result = first + ''.join(rest)

    # Ensure valid Java identifier
    if result and result[0].isdigit():
        result = 'test' + result
    if not result or not _is_valid_java_identifier(result):
        result = 'test'

    # Avoid keywords
    if result in _JAVA_KEYWORDS:
        result = result + "Test"

    return result


def _is_valid_java_identifier(value: str) -> bool:
    if not value:
        return False
    if value in _JAVA_KEYWORDS:
        return False
    # Java identifier rules: start with letter, $, or _, followed by letters, digits, $, or _
    return bool(re.fullmatch(r'[A-Za-z_$][A-Za-z0-9_$]*', value))


def _java_string(value: str) -> str:
    """Return a Java string literal with proper escaping."""
    escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    return f'"{escaped}"'


def _java_literal(value: object) -> str:
    """Convert a Python value to a Java literal."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return _java_string(value)
    if isinstance(value, (list, tuple)):
        return _java_list_literal(value)
    if isinstance(value, dict):
        return _java_map_literal(value)
    return str(value)


def _java_list_literal(value: list | tuple) -> str:
    """Convert a list to Java List.of() call."""
    if not value:
        return "java.util.List.of()"
    items = ", ".join(_java_literal(item) for item in value)
    return f"java.util.List.of({items})"


def _java_map_literal(value: dict) -> str:
    """Convert a dict to Java Map.of() call."""
    if not value:
        return "java.util.Map.of()"
    # Map.of has a 10-entry limit, but for tests we assume small maps
    pairs = ", ".join(f"{_java_literal(k)}, {_java_literal(v)}" for k, v in value.items())
    return f"java.util.Map.of({pairs})"


def _java_accessor(base: str, key: str) -> str:
    """Generate Java accessor for a field/key."""
    # Assume getter pattern for POJOs, or map access
    method_name = "get" + _pascal_case(str(key))
    return f"{base}.{method_name}()"


def _java_comment_repr(value: object) -> str:
    """Return a truncated string representation for comments."""
    s = repr(value)
    if len(s) > 60:
        s = s[:57] + "..."
    return s
