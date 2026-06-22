from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .ast import Diagnostic
from .emitters.pytest import emit_pytest
from .emitters.vitest import emit_vitest
from .parser import parse_text


@dataclass(frozen=True)
class RunResult:
    exit_code: int
    output: str
    diagnostics: tuple[Diagnostic, ...] = ()


def run_file(path: Path, target: str, cwd: Path | None = None) -> RunResult:
    source = path.read_text(encoding="utf-8")
    result = parse_text(source)
    if result.diagnostics:
        return RunResult(exit_code=1, output=_format_diagnostics(path, result.diagnostics), diagnostics=result.diagnostics)

    assert result.document is not None
    run_cwd = cwd or path.parent
    if target == "python":
        return _run_python(path, emit_pytest(result.document, source_path=path), run_cwd)
    if target == "typescript":
        return _run_typescript(path, emit_vitest(result.document), run_cwd)

    diagnostic = Diagnostic(1, 1, f"unsupported run target: {target}")
    return RunResult(exit_code=2, output=_format_diagnostics(path, (diagnostic,)), diagnostics=(diagnostic,))


def _run_python(source_path: Path, generated: str, cwd: Path) -> RunResult:
    with tempfile.TemporaryDirectory(prefix="tdd-dsl-run-") as temp_dir:
        generated_path = Path(temp_dir) / f"{source_path.stem}_test.py"
        generated_path.write_text(_python_executable_source(generated), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(generated_path)],
            cwd=cwd,
            env=_subprocess_env_with_pythonpath(cwd),
            text=True,
            capture_output=True,
            check=False,
        )
        output = completed.stdout + completed.stderr
        if completed.returncode == 0:
            return RunResult(exit_code=0, output=f"{source_path}: ok\n{output}")
        return RunResult(exit_code=completed.returncode, output=_map_python_failure(generated_path, output))


def _run_typescript(source_path: Path, generated: str, cwd: Path) -> RunResult:
    with tempfile.TemporaryDirectory(prefix="tdd-dsl-run-") as temp_dir:
        generated_path = Path(temp_dir) / f"{source_path.stem}.test.ts"
        generated_path.write_text(generated, encoding="utf-8")
        completed = subprocess.run(
            ["npx", "vitest", "run", str(generated_path)],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
        output = completed.stdout + completed.stderr
        if completed.returncode == 0:
            return RunResult(exit_code=0, output=f"{source_path}: ok\n{output}")
        return RunResult(exit_code=completed.returncode, output=output)


def _python_executable_source(generated: str) -> str:
    return (
        generated
        + "\n\n"
        + "if __name__ == \"__main__\":\n"
        + "    for _name, _value in sorted(globals().items()):\n"
        + "        if _name.startswith(\"test_\") and callable(_value):\n"
        + "            _value()\n"
    )


def _subprocess_env_with_pythonpath(cwd: Path) -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    entries = [str(cwd)]
    if existing:
        entries.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(entries)
    return env


def _map_python_failure(generated_path: Path, output: str) -> str:
    match = None
    for candidate in re.finditer(r'File "([^"]+)", line ([0-9]+), in (test_[A-Za-z0-9_]+)', output):
        if Path(candidate.group(1)) == generated_path:
            match = candidate
    if match is None:
        return output

    generated_line = int(match.group(2))
    mapped = _source_comment_before(generated_path, generated_line)
    if mapped is None:
        return output
    return f"{mapped}: generated test failed\n{output}"


def _source_comment_before(generated_path: Path, line: int) -> str | None:
    comment_re = re.compile(r"^# tdd-dsl: source=(?P<source>.+) line=(?P<line>[0-9]+) case=(?P<case>.+)$")
    comments: list[tuple[int, str]] = []
    for number, text in enumerate(generated_path.read_text(encoding="utf-8").splitlines(), start=1):
        match = comment_re.match(text)
        if match:
            comments.append((number, f"{match.group('source')}:{match.group('line')}:1: case {match.group('case')}"))
    prior = [mapped for number, mapped in comments if number <= line]
    if not prior:
        return None
    return prior[-1]


def _format_diagnostics(path: Path, diagnostics: tuple[Diagnostic, ...]) -> str:
    return "".join(f"{path}:{diagnostic.line}:{diagnostic.column}: {diagnostic.message}\n" for diagnostic in diagnostics)
