from __future__ import annotations

import keyword
import re
from pprint import pformat

from pathlib import Path

from tdd_dsl.ast import Case, Document, Target


def emit_pytest(document: Document, target_name: str = "python", source_path: str | Path | None = None) -> str:
    target = _find_target(document, target_name)
    lines = [
        f"import {target.module}",
        "",
        "",
    ]

    used_names: set[str] = set()
    for case in document.cases:
        function_name = _unique_name(f"test_{_slug(case.name)}", used_names)
        if source_path is not None:
            lines.append(_source_map_comment(source_path, case))
        lines.append(f"def {function_name}():")
        lines.extend(_result_assignment(target, case))
        lines.extend(_assertion(_expected_value(case)))
        lines.append("")
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
    if not value.isidentifier() or keyword.iskeyword(value):
        raise ValueError(f"case {case.name!r} has invalid Python call name {value!r}")
    return value


def _result_assignment(target: Target, case: Case) -> list[str]:
    call = f"{target.module}.{_call_name(case)}"
    arguments = _call_arguments(case)
    inline = f"    result = {call}({', '.join(arguments)})"
    if len(inline) <= 88 and all("\n" not in argument for argument in arguments):
        return [inline]

    lines = [f"    result = {call}("]
    for argument in arguments:
        rendered = argument.splitlines()
        lines.append(f"        {rendered[0]}")
        lines.extend(f"        {line}" for line in rendered[1:])
        lines[-1] += ","
    lines.append("    )")
    return lines


def _assertion(expected: object) -> list[str]:
    literal = _python_literal(expected)
    inline = f"    assert result == {literal}"
    if len(inline) <= 88 and "\n" not in literal:
        return [inline]

    if isinstance(expected, (dict, list, tuple)):
        literal = _python_block_literal(expected)
    else:
        literal = _python_literal(expected, width=72)
    literal_lines = literal.splitlines()
    return [
        f"    assert result == {literal_lines[0]}",
        *[f"    {line}" for line in literal_lines[1:]],
    ]


def _call_arguments(case: Case) -> list[str]:
    step = case.step("given_input")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing given input")
    value = step.value
    if isinstance(value, dict) and all(isinstance(key, str) and key.isidentifier() and not keyword.iskeyword(key) for key in value):
        return [f"{key}={_python_literal(item)}" for key, item in value.items()]
    return [_python_literal(value)]


def _expected_value(case: Case) -> object:
    step = case.step("then_equals")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing then equals")
    return step.value


def _python_literal(value: object, width: int = 88) -> str:
    return pformat(value, width=width, sort_dicts=False)


def _python_block_literal(value: object, indent: int = 0) -> str:
    spaces = " " * indent
    child_spaces = " " * (indent + 4)

    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = ["{"]
        for key, item in value.items():
            rendered = _python_block_literal(item, indent + 4).splitlines()
            lines.append(f"{child_spaces}{key!r}: {rendered[0]}")
            lines.extend(f"{child_spaces}{line}" for line in rendered[1:])
            lines[-1] += ","
        lines.append(f"{spaces}}}")
        return "\n".join(lines)

    if isinstance(value, list):
        if not value:
            return "[]"
        lines = ["["]
        for item in value:
            rendered = _python_block_literal(item, indent + 4).splitlines()
            lines.append(f"{child_spaces}{rendered[0]}")
            lines.extend(f"{child_spaces}{line}" for line in rendered[1:])
            lines[-1] += ","
        lines.append(f"{spaces}]")
        return "\n".join(lines)

    if isinstance(value, tuple):
        if not value:
            return "()"
        lines = ["("]
        for item in value:
            rendered = _python_block_literal(item, indent + 4).splitlines()
            lines.append(f"{child_spaces}{rendered[0]}")
            lines.extend(f"{child_spaces}{line}" for line in rendered[1:])
            lines[-1] += ","
        lines.append(f"{spaces})")
        return "\n".join(lines)

    return repr(value)


def _slug(value: str) -> str:
    slug = re.sub(r"[^0-9A-Za-z_]+", "_", value.strip().lower()).strip("_")
    if not slug:
        slug = "case"
    if slug[0].isdigit():
        slug = f"case_{slug}"
    if keyword.iskeyword(slug):
        slug = f"{slug}_case"
    return slug


def _unique_name(base: str, used: set[str]) -> str:
    if base not in used:
        used.add(base)
        return base
    index = 2
    while f"{base}_{index}" in used:
        index += 1
    name = f"{base}_{index}"
    used.add(name)
    return name


def _source_map_comment(source_path: str | Path, case: Case) -> str:
    return f"# tdd-dsl: source={Path(source_path).as_posix()} line={case.line} case={case.name!r}"
