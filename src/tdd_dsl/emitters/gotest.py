"""Go test emitter for tdd-dsl.

Generates idiomatic Go tests using the standard testing package with:
- Proper package declarations and imports
- CamelCase test function names following Go conventions
- Table-driven tests where appropriate
- JSON literals using structs or maps
- t.Errorf for assertions
"""

from __future__ import annotations

import json
import re

from pathlib import Path

from tdd_dsl.ast import Case, Document, Target


_GO_KEYWORDS = {
    "break", "case", "chan", "const", "continue", "default", "defer",
    "else", "fallthrough", "for", "func", "go", "goto", "if", "import",
    "interface", "map", "package", "range", "return", "select", "struct",
    "switch", "type", "var",
}


def emit_gotest(document: Document, target_name: str = "go", source_path: str | Path | None = None) -> str:
    """Emit Go test file from a TDD DSL document."""
    target = _find_target(document, target_name)
    package_name = _go_package_name(target.module)

    lines = [
        f"package {package_name}",
        "",
        "import (",
        '    "encoding/json"',
        '    "reflect"',
        '    "testing"',
        ")",
        "",
    ]

    for case in document.cases:
        func_name = _go_test_name(case.name)
        if source_path is not None:
            lines.append(_source_map_comment(source_path, case))
        lines.append(f"func {func_name}(t *testing.T) {{")
        lines.extend(_test_body(case, target))
        lines.append("}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _find_target(document: Document, language: str) -> Target:
    for target in document.targets:
        if target.language == language:
            return target
    raise ValueError(f"document does not declare target {language!r}")


def _go_package_name(module: str) -> str:
    """Extract a valid Go package name from the module path.
    
    Handles:
    - Simple names: "calculator" -> "calculator"
    - Full paths: "github.com/user/calculator" -> "calculator"
    - Domain-style: "example.com/package" -> "package"
    """
    # Take the last segment of the path
    parts = module.split("/")
    name = parts[-1] if parts else module
    
    # Sanitize to valid Go identifier
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = name.lower()
    
    # Ensure it starts with a letter
    if name and name[0].isdigit():
        name = "pkg_" + name
    
    # Avoid keywords
    if name in _GO_KEYWORDS:
        name = name + "_test"
    
    # Default fallback
    if not name or not _is_valid_go_identifier(name):
        name = "main"
    
    return name


def _go_test_name(case_name: str) -> str:
    """Convert a test case name to a valid Go test function name.
    
    Go convention: TestXxx where Xxx is PascalCase description.
    """
    # Remove special characters and normalize
    name = re.sub(r'[^\w\s]', ' ', case_name)
    words = name.split()
    
    # Capitalize each word and join
    pascal = ''.join(word.capitalize() for word in words if word)
    
    # Ensure valid identifier
    if not pascal:
        pascal = "Case"
    
    # Prefix with Test
    result = f"Test{pascal}"
    
    # Ensure it starts with letter
    if result[0].isdigit():
        result = "Test" + result
    
    return result


def _test_body(case: Case, target: Target) -> list[str]:
    """Generate the body of a Go test function."""
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
    input_literal = _go_literal(input_value)
    if '\n' in input_literal or len(input_literal) > 60:
        # Multi-line or long literal - use JSON unmarshaling
        lines.append(f"    inputJSON := `{_escape_backticks(json.dumps(input_value))}`")
        lines.append("    var input interface{}")
        lines.append("    if err := json.Unmarshal([]byte(inputJSON), &input); err != nil {")
        lines.append("        t.Fatalf(\"failed to unmarshal input: %v\", err)")
        lines.append("    }")
        input_arg = "input"
    else:
        lines.append(f"    input := {input_literal}")
        input_arg = "input"
    
    # Call the function under test
    lines.append(f"    result := {call_name}({input_arg})")
    lines.append("")
    
    # Generate expected and assertion
    expected_literal = _go_literal(expected_value)
    if '\n' in expected_literal or len(expected_literal) > 60:
        # Multi-line or long literal - use JSON unmarshaling
        lines.append(f"    expectedJSON := `{_escape_backticks(json.dumps(expected_value))}`")
        lines.append("    var expected interface{}")
        lines.append("    if err := json.Unmarshal([]byte(expectedJSON), &expected); err != nil {")
        lines.append("        t.Fatalf(\"failed to unmarshal expected: %v\", err)")
        lines.append("    }")
        lines.append("    if !reflect.DeepEqual(result, expected) {")
        lines.append('        t.Errorf("expected %v, got %v", expected, result)')
        lines.append("    }")
    else:
        # Simple comparison
        lines.append(f"    expected := {expected_literal}")
        lines.append("    if !reflect.DeepEqual(result, expected) {")
        lines.append('        t.Errorf("expected %v, got %v", expected, result)')
        lines.append("    }")
    
    return lines


def _call_name(case: Case) -> str:
    step = case.step("when_call")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing when call")
    value = str(step.value)
    if not _is_valid_go_identifier(value) or value in _GO_KEYWORDS:
        raise ValueError(f"case {case.name!r} has invalid Go call name {value!r}")
    return value


def _is_valid_go_identifier(value: str) -> bool:
    """Check if a string is a valid Go identifier."""
    if not value:
        return False
    if value in _GO_KEYWORDS:
        return False
    # Go identifier rules: start with letter or _, followed by letters, digits, or _
    return bool(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value))


def _go_literal(value: object) -> str:
    """Convert a Python value to a Go literal."""
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        # Use %g for compact representation
        return repr(value)
    if isinstance(value, str):
        return _go_string(value)
    if isinstance(value, (list, tuple)):
        return _go_slice_literal(value)
    if isinstance(value, dict):
        return _go_map_literal(value)
    return str(value)


def _go_string(value: str) -> str:
    """Return a Go string literal with proper escaping."""
    # Escape backslashes, quotes, and common control characters
    escaped = value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    return f'"{escaped}"'


def _go_slice_literal(value: list | tuple) -> str:
    """Convert a list to a Go slice literal."""
    if not value:
        return "[]interface{}{}"
    items = ", ".join(_go_literal(item) for item in value)
    return "[]interface{}{" + items + "}"


def _go_map_literal(value: dict) -> str:
    """Convert a dict to a Go map literal with string keys."""
    if not value:
        return "map[string]interface{}{}"
    pairs = ", ".join(f"{_go_string(str(k))}: {_go_literal(v)}" for k, v in value.items())
    return "map[string]interface{}{" + pairs + "}"


def _escape_backticks(s: str) -> str:
    """Escape backticks for raw string literals."""
    return s.replace('`', '` + "`" + `')


def _source_map_comment(source_path: str | Path, case: Case) -> str:
    return f"// Source: {source_path}:{case.line}"
