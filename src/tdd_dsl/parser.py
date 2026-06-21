from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .ast import Case, Diagnostic, Document, Step, Target


_TARGET_RE = re.compile(r"^target\s+([A-Za-z_][A-Za-z0-9_-]*)\s+(.+)$")
_CASE_RE = re.compile(r"^case\s+(.+):$")
_WHEN_RE = re.compile(r"^when\s+call\s+(.+)$")


@dataclass(frozen=True)
class ParseResult:
    document: Document | None
    diagnostics: tuple[Diagnostic, ...]

    @property
    def ok(self) -> bool:
        return self.document is not None and not self.diagnostics


@dataclass(frozen=True)
class _Line:
    number: int
    indent: int
    text: str


def parse_text(text: str) -> ParseResult:
    parser = _Parser(_logical_lines(text))
    return parser.parse()


def _logical_lines(text: str) -> list[_Line]:
    lines: list[_Line] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        lines.append(_Line(number=number, indent=indent, text=raw.strip()))
    return lines


def _parse_json_string(raw: str, line: int, column: int) -> tuple[str | None, Diagnostic | None]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, Diagnostic(line, column + exc.pos, f"expected quoted string: {exc.msg}")
    if not isinstance(value, str):
        return None, Diagnostic(line, column, "expected quoted string")
    return value, None


class _Parser:
    def __init__(self, lines: list[_Line]) -> None:
        self.lines = lines
        self.index = 0
        self.diagnostics: list[Diagnostic] = []

    def parse(self) -> ParseResult:
        suite = ""
        targets: list[Target] = []
        cases: list[Case] = []

        while self.index < len(self.lines):
            line = self._peek()
            if line.indent != 0:
                self._error(line, "expected top-level 'suite', 'target', or 'case'")
                self.index += 1
                continue

            if line.text.startswith("suite "):
                if suite:
                    self._error(line, "only one suite is allowed")
                    self.index += 1
                    continue
                parsed, diagnostic = _parse_json_string(line.text.removeprefix("suite ").strip(), line.number, line.indent + 7)
                if diagnostic:
                    self.diagnostics.append(diagnostic)
                else:
                    suite = parsed or ""
                self.index += 1
                continue

            target_match = _TARGET_RE.match(line.text)
            if target_match:
                language, raw_module = target_match.groups()
                module, diagnostic = _parse_json_string(raw_module.strip(), line.number, line.indent + line.text.index(raw_module) + 1)
                if diagnostic:
                    self.diagnostics.append(diagnostic)
                else:
                    targets.append(Target(language=language, module=module or "", line=line.number, column=1))
                self.index += 1
                continue

            case_match = _CASE_RE.match(line.text)
            if case_match:
                if not suite:
                    self._error(line, "case requires a preceding suite")
                if not targets:
                    self._error(line, "case requires at least one preceding target")
                case = self._parse_case(line, case_match.group(1))
                if case:
                    cases.append(case)
                continue

            self._error(line, "expected top-level 'suite', 'target', or 'case'")
            self.index += 1

        if not suite:
            self.diagnostics.append(Diagnostic(1, 1, "document requires a suite"))
        if not targets:
            self.diagnostics.append(Diagnostic(1, 1, "document requires at least one target"))
        if not cases:
            self.diagnostics.append(Diagnostic(1, 1, "document requires at least one case"))

        document = None if self.diagnostics else Document(suite=suite, targets=tuple(targets), cases=tuple(cases))
        return ParseResult(document=document, diagnostics=tuple(self.diagnostics))

    def _parse_case(self, header: _Line, raw_name: str) -> Case | None:
        name, diagnostic = _parse_json_string(raw_name.strip(), header.number, header.indent + 6)
        if diagnostic:
            self.diagnostics.append(diagnostic)
            name = ""

        self.index += 1
        steps: list[Step] = []
        while self.index < len(self.lines):
            line = self._peek()
            if line.indent == 0:
                break
            if line.indent != 2:
                self._error(line, "case steps must be indented by two spaces")
                self.index += 1
                continue

            if line.text == "given input:":
                value = self._parse_json_block(line, "given input")
                if value is not _Missing:
                    steps.append(Step("given_input", value, line.number, line.indent + 1))
                continue

            when_match = _WHEN_RE.match(line.text)
            if when_match:
                call, when_diag = _parse_json_string(when_match.group(1).strip(), line.number, line.indent + line.text.index(when_match.group(1)) + 1)
                if when_diag:
                    self.diagnostics.append(when_diag)
                else:
                    steps.append(Step("when_call", call or "", line.number, line.indent + 1))
                self.index += 1
                continue

            if line.text == "then equals:":
                value = self._parse_json_block(line, "then equals")
                if value is not _Missing:
                    steps.append(Step("then_equals", value, line.number, line.indent + 1))
                continue

            self._error(line, "expected 'given input:', 'when call \"name\"', or 'then equals:'")
            self.index += 1

        found = {step.kind for step in steps}
        for kind, label in (
            ("given_input", "given input"),
            ("when_call", "when call"),
            ("then_equals", "then equals"),
        ):
            if kind not in found:
                self.diagnostics.append(Diagnostic(header.number, header.indent + 1, f"case '{name}' requires {label}"))

        return Case(name=name or "<invalid>", steps=tuple(steps), line=header.number, column=header.indent + 1)

    def _parse_json_block(self, header: _Line, label: str) -> object:
        self.index += 1
        payload: list[str] = []
        while self.index < len(self.lines):
            line = self._peek()
            if line.indent <= header.indent:
                break
            if line.indent < header.indent + 2:
                self._error(line, f"{label} JSON must be indented below the step")
                self.index += 1
                continue
            payload.append(" " * (line.indent - header.indent - 2) + line.text)
            self.index += 1

        if not payload:
            self._error(header, f"{label} requires an indented JSON payload")
            return _Missing

        raw = "\n".join(payload)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            self.diagnostics.append(Diagnostic(header.number + 1, exc.pos + 1, f"invalid JSON for {label}: {exc.msg}"))
            return _Missing

    def _peek(self) -> _Line:
        return self.lines[self.index]

    def _error(self, line: _Line, message: str) -> None:
        self.diagnostics.append(Diagnostic(line.number, line.indent + 1, message))


class _MissingValue:
    pass


_Missing = _MissingValue()
