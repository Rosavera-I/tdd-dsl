from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from .parser import parse_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tdd-dsl")
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate = subcommands.add_parser("validate", help="validate a .tdd file")
    validate.add_argument("file", type=Path)
    validate.add_argument("--json", action="store_true", help="print parsed AST as JSON")

    args = parser.parse_args(argv)
    if args.command == "validate":
        return _validate(args.file, args.json)

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
