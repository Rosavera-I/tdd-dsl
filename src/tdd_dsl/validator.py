from __future__ import annotations

import keyword

from .ast import Case, Diagnostic, Document


SUPPORTED_TARGETS = frozenset({"python", "typescript", "java"})


def validate_document(document: Document) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    diagnostics.extend(_duplicate_case_diagnostics(document.cases))
    diagnostics.extend(_unsupported_target_diagnostics(document))
    diagnostics.extend(_backend_input_shape_diagnostics(document))
    return tuple(diagnostics)


def _duplicate_case_diagnostics(cases: tuple[Case, ...]) -> tuple[Diagnostic, ...]:
    seen: dict[str, Case] = {}
    diagnostics: list[Diagnostic] = []
    for case in cases:
        first = seen.get(case.name)
        if first is None:
            seen[case.name] = case
            continue
        diagnostics.append(
            Diagnostic(
                case.line,
                case.column,
                f"duplicate case name {case.name!r}; first declared at line {first.line}",
            )
        )
    return tuple(diagnostics)


def _unsupported_target_diagnostics(document: Document) -> tuple[Diagnostic, ...]:
    return tuple(
        Diagnostic(target.line, target.column, f"unsupported target {target.language!r}")
        for target in document.targets
        if target.language not in SUPPORTED_TARGETS
    )


def _backend_input_shape_diagnostics(document: Document) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    target_languages = {target.language for target in document.targets}
    if "python" in target_languages:
        diagnostics.extend(_python_input_shape_diagnostics(document.cases))
    return tuple(diagnostics)


def _python_input_shape_diagnostics(cases: tuple[Case, ...]) -> tuple[Diagnostic, ...]:
    diagnostics: list[Diagnostic] = []
    for case in cases:
        step = case.step("given_input")
        if step is None or not isinstance(step.value, dict):
            continue
        invalid_keys = [
            key
            for key in step.value
            if not isinstance(key, str) or not key.isidentifier() or keyword.iskeyword(key)
        ]
        if invalid_keys:
            diagnostics.append(
                Diagnostic(
                    step.line,
                    step.column,
                    f"python target requires object input keys to be valid parameter names in case {case.name!r}",
                )
            )
    return tuple(diagnostics)
