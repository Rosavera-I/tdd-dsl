"""C# xUnit emitter for tdd-dsl.

Generates idiomatic C# xUnit tests with:
- Proper using statements
- PascalCase class names with Test suffix
- Fact attributes for test methods
- camelCase test method names
- Proper C# null handling and literal generation
"""

from __future__ import annotations

import re

from pathlib import Path

from tdd_dsl.ast import Case, Document, Target


# Reserved keywords that cannot be used as identifiers in C#
# Excludes contextual keywords like 'add', 'get', 'set', 'where', etc.
# which can be used as identifiers in most contexts
_CSHARP_KEYWORDS = {
    "abstract", "as", "base", "bool", "break", "byte", "case", "catch",
    "char", "checked", "class", "const", "continue", "decimal", "default",
    "delegate", "do", "double", "else", "enum", "event", "explicit",
    "extern", "false", "finally", "fixed", "float", "for", "foreach",
    "goto", "if", "implicit", "in", "int", "interface", "internal",
    "is", "lock", "long", "namespace", "new", "null", "object", "operator",
    "out", "override", "params", "private", "protected", "public",
    "readonly", "ref", "return", "sbyte", "sealed", "short", "sizeof",
    "stackalloc", "static", "string", "struct", "switch", "this", "throw",
    "true", "try", "typeof", "uint", "ulong", "unchecked", "unsafe",
    "ushort", "using", "virtual", "void", "volatile", "while",
}


def emit_xunit(document: Document, target_name: str = "csharp", source_path: str | Path | None = None) -> str:
    """Emit C# xUnit test class from a TDD DSL document."""
    target = _find_target(document, target_name)
    
    # Extract class name from module (handle both "ClassName" and "Namespace.ClassName")
    module_parts = target.module.split(".")
    simple_class_name = module_parts[-1]  # Get last part (the actual class name)
    class_name = _pascal_case(simple_class_name) + "Tests"
    
    lines = [
        "using System.Collections.Generic;",
        "using Xunit;",
        "",
    ]
    
    # Add namespace if module contains dots
    if len(module_parts) > 1:
        namespace = ".".join(module_parts[:-1])
        lines.append(f"using {namespace};")
        lines.append("")
    
    lines.append(f"public class {class_name}")
    lines.append("{")
    lines.append("")
    
    # Track used method names to avoid duplicates
    used_names: set[str] = set()
    
    for case in document.cases:
        method_name = _unique_name(_camel_case(f"test_{case.name}"), used_names)
        if source_path is not None:
            lines.append(_source_map_comment(source_path, case))
        lines.append(f"    [Fact]")
        lines.append(f"    public void {method_name}()")
        lines.append("    {")
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
    if not _is_valid_csharp_identifier(value) or value in _CSHARP_KEYWORDS:
        raise ValueError(f"case {case.name!r} has invalid C# call name {value!r}")
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
        lines.append(f"        // Input: {_csharp_comment_repr(input_value)}")
        lines.append(f"        var input = {_csharp_map_literal(input_value)};")
        input_arg = "input"
    elif isinstance(input_value, list):
        lines.append(f"        // Input: {_csharp_comment_repr(input_value)}")
        lines.append(f"        var input = {_csharp_list_literal(input_value)};")
        input_arg = "input"
    else:
        input_arg = _csharp_literal(input_value)
    
    # Call the method under test
    lines.append(f"        var result = {simple_class}.{call_name}({input_arg});")
    
    # Assert expected value
    if isinstance(expected_value, dict):
        lines.append(f"        // Expected: {_csharp_comment_repr(expected_value)}")
        for key, val in expected_value.items():
            accessor = _csharp_accessor("result", key)
            lines.append(f"        Assert.Equal({_csharp_literal(val)}, {accessor});")
    elif isinstance(expected_value, list):
        lines.append(f"        var expected = {_csharp_list_literal(expected_value)};")
        lines.append(f"        Assert.Equal(expected, result);")
    else:
        lines.append(f"        Assert.Equal({_csharp_literal(expected_value)}, result);")
    
    return lines


def _source_map_comment(source_path: str | Path, case: Case) -> str:
    return f"    // Source: {Path(source_path).as_posix()}:{case.line}"


def _pascal_case(value: str) -> str:
    """Convert snake_case or kebab-case to PascalCase."""
    value = re.sub(r'[^\w\s\-]', ' ', value)
    parts = re.split(r'[\s_\-]+', value.strip())
    result = ''.join(part.capitalize() for part in parts if part)
    if not result:
        return "Generated"
    if result[0].isdigit():
        result = "Generated" + result
    if result in _CSHARP_KEYWORDS:
        result += "Tests"
    return result


def _camel_case(value: str) -> str:
    """Convert a test name to valid camelCase C# method name."""
    # Remove special characters and normalize
    value = re.sub(r'[_\-]+', ' ', value)
    value = re.sub(r'[^\w\s]', ' ', value)
    value = re.sub(r'\s+', '_', value.strip())
    parts = value.split('_')
    
    # First part lowercase, rest PascalCase
    if not parts:
        return "test"
    
    first = parts[0].lower()
    rest = [p.capitalize() for p in parts[1:] if p]
    
    result = first + ''.join(rest)
    
    # Ensure valid C# identifier
    if result and result[0].isdigit():
        result = 'test' + result
    if not result or not _is_valid_csharp_identifier(result):
        result = 'test'
    
    # Avoid keywords
    if result in _CSHARP_KEYWORDS:
        result = result + "Test"
    
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


def _is_valid_csharp_identifier(value: str) -> bool:
    """Check if value is a valid C# identifier."""
    if not value:
        return False
    if value in _CSHARP_KEYWORDS:
        return False
    # C# identifier rules: start with letter or _, followed by letters, digits, or _
    return bool(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value))


def _csharp_literal(value: object) -> str:
    """Convert a Python value to a C# literal."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        return _csharp_string(value)
    if isinstance(value, (list, tuple)):
        return _csharp_list_literal(value)
    if isinstance(value, dict):
        return _csharp_map_literal(value)
    return str(value)


def _csharp_string(value: str) -> str:
    """Return a C# string literal with proper escaping."""
    # Escape backslashes and quotes
    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    # Escape special characters
    escaped = escaped.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
    return f'"{escaped}"'


def _csharp_list_literal(value: list | tuple) -> str:
    """Convert a list to C# array or List literal."""
    if not value:
        return "new List<object>()"
    items = ", ".join(_csharp_literal(item) for item in value)
    return f"new List<object> {{ {items} }}"


def _csharp_map_literal(value: dict) -> str:
    """Convert a dict to C# Dictionary literal."""
    if not value:
        return "new Dictionary<string, object>()"
    
    items = ", ".join(f"{{ {_csharp_string(str(k))}, {_csharp_literal(v)} }}" for k, v in value.items())
    return f"new Dictionary<string, object> {{ {items} }}"


def _csharp_accessor(base: str, key: object) -> str:
    """Generate C# accessor for a field/key."""
    # For dictionaries, use indexer; for objects, use property accessor
    key_str = str(key)
    if _is_valid_csharp_identifier(key_str) and key_str not in _CSHARP_KEYWORDS:
        return f"{base}[{_csharp_string(key_str)}]"
    return f"{base}[{_csharp_literal(key)}]"


def _csharp_comment_repr(value: object) -> str:
    """Return a truncated string representation for comments."""
    s = repr(value)
    if len(s) > 60:
        s = s[:57] + "..."
    return s
