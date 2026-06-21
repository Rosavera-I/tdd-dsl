# TDD DSL

An LLM-friendly test-first DSL for describing behavior once and emitting executable tests for multiple language ecosystems.

The project starts with a deliberately small core:

- A line-oriented DSL that is easy for humans and LLMs to produce.
- A parser that returns a stable AST plus precise diagnostics.
- Generators that turn the AST into idiomatic test files.
- Meta-tests that check the test suite includes failure fixtures, not just happy paths.

## Quick Start

```bash
python -m tdd_dsl validate tests/fixtures/valid_minimal.tdd
python -m unittest discover -s tests
```

## Example

```text
suite "Calculator"
target python "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5
```

## Status

This is an initial spike repo. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/SPEC.md](docs/SPEC.md), and [docs/TICKETS.md](docs/TICKETS.md).
