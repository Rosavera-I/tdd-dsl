"""Swift XCTest emitter for tdd-dsl.

Generates idiomatic Swift tests using the XCTest framework with:
- XCTestCase subclasses for test organization
- test method naming with descriptive names
- XCTAssertEqual assertions
- Proper imports and type annotations
"""

from __future__ import annotations

import re
from pathlib import Path

from tdd_dsl.ast import Case, Document, Target


_SWIFT_KEYWORDS = {
    "associatedtype", "class", "deinit", "enum", "extension", "fileprivate",
    "func", "import", "init", "inout", "internal", "let", "open",
    "operator", "private", "precedencegroup", "protocol", "public",
    "rethrows", "static", "struct", "subscript", "typealias", "var",
    "break", "case", "catch", "continue", "default", "defer", "do",
    "else", "fallthrough", "for", "guard", "if", "in", "repeat",
    "return", "switch", "throw", "throws", "try", "where", "while",
    "as", "Any", "await", "catch", "false", "is", "nil", "self", "Self",
    "super", "true", "try", "_",
}


def emit_swift(document: Document, target_name: str = "swift", source_path: str | Path | None = None) -> str:
    """Emit Swift XCTest class from a TDD DSL document."""
    target = _find_target(document, target_name)
    # Extract module name - could be "MyModule" or "MyKit.MyClass"  
    module_parts = target.module.split(".")
    module_name = module_parts[0]  # Use first part for @testable import
    
    # Generate test class name from suite
    test_class_name = _pascal_case(document.suite) + "Tests"
    
    lines = [
        "import XCTest",
        f"@testable import {module_name}",
        "",
        f"final class {test_class_name}: XCTestCase {{",
        ""
    ]
    
    # Track used method names to avoid duplicates
    used_names: set[str] = set()
    
    for case in document.cases:
        method_name = _unique_name(_swift_test_method_name(case.name), used_names)
        if source_path is not None:
            lines.append(_source_map_comment(source_path, case))
        lines.extend(_test_method(case, target, method_name))
        lines.append("")
    
    lines.append("}")
    return "\n".join(lines).rstrip() + "\n"


def _find_target(document: Document, language: str) -> Target:
    for target in document.targets:
        if target.language == language:
            return target
    raise ValueError(f"document does not declare target {language!r}")


def _test_method(case: Case, target: Target, method_name: str) -> list[str]:
    """Generate a single test method."""
    input_step = case.step("given_input")
    expected_step = case.step("then_equals")
    call_name = _call_name(case)
    
    if input_step is None:
        raise ValueError(f"case {case.name!r} is missing given input")
    if expected_step is None:
        raise ValueError(f"case {case.name!r} is missing then equals")
    
    input_value = input_step.value
    expected_value = expected_step.value
    simple_call = _swift_identifier(call_name)
    
    lines = [
        f"    func {method_name}() throws {{",
    ]
    
    # Generate input and call
    if isinstance(input_value, dict):
        lines.append(f"        // Input: {_swift_comment_repr(input_value)}")
        struct_name = _swift_identifier(_call_name(case)).replace("make", "").replace("create", "").replace("build", "")
        struct_name = struct_name[0].upper() + struct_name[1:] if struct_name else "Input"
        lines.append(f"        let input = {_swift_struct_literal(input_value, struct_name)}")
        lines.append(f"        let result = {simple_call}(input: input)")
    elif isinstance(input_value, list):
        lines.append(f"        // Input: {_swift_comment_repr(input_value)}")
        lines.append(f"        let input = {_swift_array_literal(input_value)}")
        lines.append(f"        let result = {simple_call}(input: input)")
    else:
        input_arg = _swift_literal(input_value)
        if input_arg != "()":
            lines.append(f"        let result = {simple_call}({input_arg})")
        else:
            lines.append(f"        let result = {simple_call}()")
    
    # Generate assertions
    if isinstance(expected_value, dict) and expected_value:
        lines.append(f"        // Expected: {_swift_comment_repr(expected_value)}")
        for key, val in expected_value.items():
            swift_key = _swift_identifier(str(key))
            lines.append(f"        XCTAssertEqual(result.{swift_key}, {_swift_literal(val)})")
    elif isinstance(expected_value, list):
        lines.append(f"        XCTAssertEqual(result, {_swift_array_literal(expected_value)})")
    else:
        lines.append(f"        XCTAssertEqual(result, {_swift_literal(expected_value)})")
    
    lines.append("    }")
    
    return lines


def _call_name(case: Case) -> str:
    step = case.step("when_call")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing when call")
    value = str(step.value)
    if not _is_valid_swift_identifier(value) or value in _SWIFT_KEYWORDS:
        raise ValueError(f"case {case.name!r} has invalid Swift call name {value!r}")
    return value


def _swift_test_method_name(name: str) -> str:
    """Convert a test case name to a valid Swift test method name.
    
    Swift test methods must start with 'test' and use camelCase.
    """
    # Remove special characters and normalize
    normalized = re.sub(r'[^\w\s]', ' ', name)
    normalized = re.sub(r'\s+', '_', normalized.strip())
    
    # Convert to camelCase with 'test' prefix
    parts = normalized.split('_')
    if not parts:
        return "testExample"
    
    # Start with 'test', then lowercase first word, capitalize rest
    first = parts[0].lower()
    rest = [p.capitalize() for p in parts[1:] if p]
    result = 'test' + first.capitalize() + ''.join(rest)
    
    # Clean up - ensure valid identifier
    result = re.sub(r'[^A-Za-z0-9]', '', result)
    
    # Ensure starts with 'test'
    if not result.startswith('test'):
        result = 'test' + result
    
    # Remove trailing underscores and ensure we have something after 'test'
    result = result.rstrip('_')
    if len(result) <= 4:  # Just 'test' or 'test_'
        result = "testExample"
    
    return result


def _pascal_case(value: str) -> str:
    """Convert a string to PascalCase for Swift type names."""
    # Remove special characters
    normalized = re.sub(r'[^\w\s]', ' ', value)
    normalized = re.sub(r'\s+', '_', normalized.strip())
    parts = normalized.split('_')
    return ''.join(part.capitalize() for part in parts if part)


def _swift_identifier(value: str) -> str:
    """Convert a string to a valid Swift identifier (camelCase)."""
    # Remove special characters
    normalized = re.sub(r'[^\w\s]', ' ', value)
    normalized = re.sub(r'\s+', '_', normalized.strip())
    parts = normalized.split('_')
    if not parts or not parts[0]:
        return "value"
    
    # First part lowercase, rest capitalized
    first = parts[0].lower()
    rest = [p.capitalize() for p in parts[1:] if p]
    result = first + ''.join(rest)
    
    # Escape if keyword
    if result in _SWIFT_KEYWORDS:
        return f"`{result}`"
    
    return result


def _is_valid_swift_identifier(value: str) -> bool:
    """Check if value is a valid Swift identifier."""
    if not value:
        return False
    # Swift identifiers: start with letter or _, followed by alphanumerics or _
    return bool(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value))


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


def _swift_literal(value: object) -> str:
    """Convert a Python value to a Swift literal."""
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return _swift_string(value)
    if isinstance(value, (list, tuple)):
        return _swift_array_literal(value)
    if isinstance(value, dict):
        return _swift_dict_literal(value)
    return str(value)


def _swift_string(value: str) -> str:
    """Return a Swift string literal with proper escaping."""
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    escaped = escaped.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    return f'"{escaped}"'


def _swift_array_literal(value: list | tuple) -> str:
    """Convert a list/tuple to Swift array literal."""
    if not value:
        return "[]"
    items = ", ".join(_swift_literal(item) for item in value)
    return f"[{items}]"


def _swift_dict_literal(value: dict) -> str:
    """Convert a dict to Swift dictionary literal."""
    if not value:
        return "[:]"
    pairs = ", ".join(f"{_swift_string(k)}: {_swift_literal(v)}" for k, v in value.items())
    return f"[{pairs}]"


def _swift_struct_literal(value: dict, struct_name: str) -> str:
    """Generate a Swift struct literal based on dict values."""
    if not value:
        return f"{struct_name}()"
    
    args = []
    for k, v in value.items():
        swift_key = _swift_identifier(str(k))
        args.append(f"{swift_key}: {_swift_literal(v)}")
    
    return f"{struct_name}({', '.join(args)})"


def _swift_comment_repr(value: object) -> str:
    """Return a truncated string representation for comments."""
    s = repr(value)
    if len(s) > 60:
        s = s[:57] + "..."
    return s


def _source_map_comment(source_path: str | Path, case: Case) -> str:
    return f"    // Source: {Path(source_path).as_posix()}:{case.line}"
