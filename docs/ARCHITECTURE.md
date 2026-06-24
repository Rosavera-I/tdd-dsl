# Architecture

## Goal

Create a tiny, reliable contract language for test-first development across languages. The DSL should be friendly to LLM generation, review, and repair: explicit sections, stable syntax, useful diagnostics, and deterministic generated tests.

## Core Pipeline

```text
.tdd file
  -> lexer/parser
  -> AST with source spans
  -> semantic validation
  -> backend emitters
  -> executable test files
```

## MVP Boundaries

The MVP supports:

- One `suite` per file.
- One or more `target` declarations.
- One or more `case` blocks.
- `given input`, `when call`, and `then equals` steps.
- JSON payloads for inputs and expected values.
- Validation diagnostics with line and column.
- Python pytest and TypeScript Vitest emitters.
- A Python runner that executes generated tests with source-mapped failure output.

The MVP intentionally does not support:

- Natural-language step matching.
- Arbitrary fixtures or setup hooks.
- Snapshot files.
- Multiple assertion styles per case.
- Runtime execution adapters beyond the small Python runner.

## Modules

- `tdd_dsl.ast`: immutable dataclasses for suite, target, case, steps, and diagnostics.
- `tdd_dsl.parser`: line-oriented parser and semantic validation.
- `tdd_dsl.emitters.pytest`: deterministic pytest code generation.
- `tdd_dsl.emitters.vitest`: deterministic Vitest code generation.
- `tdd_dsl.runner`: temporary-file execution for generated tests.
- `tdd_dsl.runtime`: HTTP mock server lifecycle harness for generated tests.
- `tdd_dsl.cli`: `validate`, `emit`, and `run` commands.

## LLM-Friendly Constraints

- Keywords are short and literal.
- All structured values are JSON.
- Blocks are indentation-based with two spaces recommended.
- Diagnostics mention the expected next construct.
- Generated output includes stable names and no timestamps.

## Polyglot Strategy

Backends should be small, pure functions over the AST. Each backend owns language idioms, but the AST stays language-neutral. Planned backends:

- Python pytest: implemented.
- TypeScript Vitest: implemented.
- Java JUnit: planned.

## Testing Strategy

- Parser unit tests cover valid AST shape and invalid diagnostics.
- Fixture tests keep DSL examples realistic.
- Meta-tests assert the suite contains negative fixtures and diagnostic assertions.
- Emitter tests compare deterministic output substrings and generated syntax shape.
- Runner tests execute generated tests against temporary target modules and assert DSL source mapping on failure.
- Runtime tests exercise mock server start, stop, verify, teardown, JSON request matching, and unmatched-request reporting. Socket-backed tests are skipped only when the sandbox blocks loopback sockets.
