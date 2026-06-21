from __future__ import annotations

import keyword
import re
from pprint import pformat

from tdd_dsl.ast import Case, Document, Target


def emit_pytest(document: Document, target_name: str = "python") -> str:
    target = _find_target(document, target_name)
    lines = [
        f"import {target.module}",
        "",
        "",
    ]

    used_names: set[str] = set()
    for case in document.cases:
        function_name = _unique_name(f"test_{_slug(case.name)}", used_names)
        lines.append(f"def {function_name}():")
        lines.append(f"    result = {target.module}.{_call_name(case)}({_call_arguments(case)})")
        lines.append(f"    assert result == {_python_literal(_expected_value(case))}")
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


def _call_arguments(case: Case) -> str:
    step = case.step("given_input")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing given input")
    value = step.value
    if isinstance(value, dict) and all(isinstance(key, str) and key.isidentifier() and not keyword.iskeyword(key) for key in value):
        return ", ".join(f"{key}={_python_literal(item)}" for key, item in value.items())
    return _python_literal(value)


def _expected_value(case: Case) -> object:
    step = case.step("then_equals")
    if step is None:
        raise ValueError(f"case {case.name!r} is missing then equals")
    return step.value


def _python_literal(value: object) -> str:
    return pformat(value, width=88, sort_dicts=False)


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
