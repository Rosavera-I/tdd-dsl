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

    emit = subcommands.add_parser("emit", help="emit tests from a .tdd file")
    emit.add_argument("file", type=Path)
    emit.add_argument("--target", choices=["python", "typescript"], required=True)

    run = subcommands.add_parser("run", help="generate and run tests from a .tdd file")
    run.add_argument("file", type=Path)
    run.add_argument("--target", choices=["python", "typescript"], required=True)
    run.add_argument("--cwd", type=Path, default=None, help="working directory for the generated test process")

    args = parser.parse_args(argv)
    if args.command == "validate":
        return _validate(args.file, args.json)
    if args.command == "emit":
        return _emit(args.file, args.target)
    if args.command == "run":
        return _run(args.file, args.target, args.cwd)

    parser.error(f"unknown command: {args.command}")
    return 2


def _validate(path: Path, print_json: bool) -> int:
    result = parse_text(path.read_text(encoding="utf-8"))
    if result.diagnostics:
        for diagnostic in result.diagnostics:
            print(f"{path}:{diagnostic.line}:{diagnostic.column}: {diagnostic.message}")
        return 1

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
