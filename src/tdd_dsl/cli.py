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

    discover = subcommands.add_parser("discover", help="discover and validate .tdd files matching a pattern")
    discover.add_argument("pattern", help="glob pattern to match .tdd files (e.g., 'tests/**/*.tdd')")
    discover.add_argument("--format", choices=["text", "json"], default="text", help="output format")

    args = parser.parse_args(argv)
    if args.command == "validate":
        if args.json and args.format == "json":
            parser.error("validate --json cannot be combined with --format json")
        return _validate(args.file, args.json, args.format)
    if args.command == "emit":
        return _emit(args.file, args.target)
    if args.command == "run":
        return _run(args.file, args.target, args.cwd)
    if args.command == "discover":
        return _discover(args.pattern, args.format)

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


def _discover(pattern: str, output_format: str) -> int:
    import fnmatch
    import os

    # Find all matching .tdd files
    matched_files: list[Path] = []
    if "**" in pattern:
        # Recursive glob
        base_dir = Path(pattern.split("/**")[0]) if pattern.startswith("/") else Path(".")
        rest_pattern = pattern.split("/**", 1)[1] if "/**" in pattern else ""
        for root, _dirs, files in os.walk(base_dir):
            for filename in files:
                if fnmatch.fnmatch(filename, "*.tdd"):
                    full_path = Path(root) / filename
                    # Check if it matches the full pattern
                    try:
                        rel_path = full_path.relative_to(Path.cwd())
                        if fnmatch.fnmatch(str(rel_path), pattern) or fnmatch.fnmatch(str(full_path), pattern):
                            matched_files.append(full_path)
                    except ValueError:
                        # Path not relative to cwd, use absolute check only
                        if fnmatch.fnmatch(str(full_path), pattern):
                            matched_files.append(full_path)
    else:
        # Simple glob
        base_dir = Path(pattern).parent if not pattern.endswith("/") else Path(pattern)
        if not base_dir.exists():
            base_dir = Path(".")
        glob_pattern = Path(pattern).name if not pattern.endswith("/") else "*.tdd"
        matched_files = list(Path(base_dir).glob(glob_pattern))

    # Validate each file
    results: list[dict[str, Any]] = []
    any_failed = False

    for file_path in sorted(matched_files):
        result = parse_text(file_path.read_text(encoding="utf-8"))
        if result.diagnostics:
            any_failed = True
            results.append({
                "file": str(file_path),
                "status": "error",
                "diagnostics": [
                    {
                        "line": d.line,
                        "column": d.column,
                        "message": d.message,
                    }
                    for d in result.diagnostics
                ],
            })
        else:
            results.append({
                "file": str(file_path),
                "status": "ok",
                "case_count": len(result.document.cases) if result.document else 0,
            })

    # Output results
    if output_format == "json":
        print(json.dumps({"files": results, "total": len(results), "failed": sum(1 for r in results if r["status"] == "error")}, indent=2, sort_keys=True))
    else:
        for r in results:
            if r["status"] == "error":
                print(f"{r['file']}: FAILED ({len(r['diagnostics'])} diagnostic(s))")
                for d in r["diagnostics"]:
                    print(f"  {d['line']}:{d['column']}: {d['message']}")
            else:
                print(f"{r['file']}: OK ({r['case_count']} case(s))")
        print(f"\nTotal: {len(results)} file(s), {sum(1 for r in results if r['status'] == 'error')} failed")

    return 1 if any_failed else 0


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
