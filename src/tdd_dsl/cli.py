from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from .emitters.pytest import emit_pytest
from .emitters.vitest import emit_vitest
from .parser import parse_text
from .runner import run_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tdd-dsl")
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate", help="validate a .tdd file")
    validate.add_argument("file", type=Path)
    validate.add_argument("--json", action="store_true", help="print parsed AST as JSON")
    validate.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="print validation diagnostics as text or LSP-compatible JSON",
    )

    emit = subcommands.add_parser("emit", help="emit tests from a .tdd file")
    emit.add_argument("file", type=Path)
    emit.add_argument("--target", choices=["python", "typescript"], required=True)

    run = subcommands.add_parser("run", help="generate and run tests from a .tdd file")
    run.add_argument("file", type=Path)
    run.add_argument("--target", choices=["python", "typescript"], required=True)
    run.add_argument("--cwd", type=Path, default=None, help="working directory for the generated test process")

    args = parser.parse_args(argv)
    if args.command == "validate":
        if args.json and args.format == "json":
            parser.error("validate --json cannot be combined with --format json")
        return _validate(args.file, args.json, args.format)
    if args.command == "emit":
        return _emit(args.file, args.target)
    if args.command == "run":
        return _run(args.file, args.target, args.cwd)

    parser.error(f"unknown command: {args.command}")
    return 2


def _validate(path: Path, print_json: bool, output_format: str) -> int:
    result = parse_text(path.read_text(encoding="utf-8"))
    if result.diagnostics:
        if output_format == "json":
            print(json.dumps(_lsp_diagnostics_payload(path, result.diagnostics), indent=2, sort_keys=True))
            return 1
        for diagnostic in result.diagnostics:
            print(f"{path}:{diagnostic.line}:{diagnostic.column}: {diagnostic.message}")
        return 1

    if output_format == "json":
        print(json.dumps(_lsp_diagnostics_payload(path, ()), indent=2, sort_keys=True))
        return 0

    if print_json and result.document is not None:
        print(json.dumps(_to_jsonable(result.document), indent=2, sort_keys=True))
    else:
        print(f"{path}: ok")
    return 0


def _emit(path: Path, target: str) -> int:
    result = parse_text(path.read_text(encoding="utf-8"))
    if result.diagnostics:
        for diagnostic in result.diagnostics:
            print(f"{path}:{diagnostic.line}:{diagnostic.column}: {diagnostic.message}")
        return 1

    assert result.document is not None
    if target == "python":
        print(emit_pytest(result.document), end="")
        return 0
    if target == "typescript":
        print(emit_vitest(result.document), end="")
        return 0

    print(f"unsupported target: {target}")
    return 2


def _run(path: Path, target: str, cwd: Path | None) -> int:
    result = run_file(path, target, cwd=cwd)
    print(result.output, end="")
    return result.exit_code


def _lsp_diagnostics_payload(path: Path, diagnostics: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "diagnostics": [_to_lsp_diagnostic(path, diagnostic) for diagnostic in diagnostics],
    }


def _to_lsp_diagnostic(path: Path, diagnostic: Any) -> dict[str, Any]:
    return {
        "file": str(path),
        "line": diagnostic.line,
        "column": diagnostic.column,
        "severity": "error",
        "message": diagnostic.message,
        "suggestedFix": _suggested_fix(diagnostic.message),
    }


def _suggested_fix(message: str) -> str:
    if "requires then equals" in message:
        return "Add a 'then equals:' step with the expected JSON payload."
    if "requires given input" in message:
        return "Add a 'given input:' step with a JSON payload."
    if "requires when call" in message:
        return 'Add a \'when call "functionName"\' step.'
    if "invalid JSON" in message:
        return "Fix the JSON payload so it parses cleanly."
    if "duplicate" in message:
        return "Keep one declaration and remove or rename the duplicate."
    if "unsupported target" in message:
        return "Use one of the supported targets: python or typescript."
    return "Review the DSL syntax near this location."


def _to_jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _to_jsonable(asdict(value))
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [_to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    return value
