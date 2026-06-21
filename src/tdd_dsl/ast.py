from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


StepKind = Literal["given_input", "when_call", "then_equals"]


@dataclass(frozen=True)
class Diagnostic:
    line: int
    column: int
    message: str


@dataclass(frozen=True)
class Target:
    language: str
    module: str
    line: int
    column: int


@dataclass(frozen=True)
class Step:
    kind: StepKind
    value: Any
    line: int
    column: int


@dataclass(frozen=True)
class Case:
    name: str
    steps: tuple[Step, ...]
    line: int
    column: int

    def step(self, kind: StepKind) -> Step | None:
        return next((step for step in self.steps if step.kind == kind), None)


@dataclass(frozen=True)
class Document:
    suite: str
    targets: tuple[Target, ...]
    cases: tuple[Case, ...]
