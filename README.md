# TDD DSL

An LLM-friendly test-first DSL for describing behavior once and emitting executable tests for multiple language ecosystems.

The project starts with a deliberately small core:

- A line-oriented DSL that is easy for humans and LLMs to produce.
- A parser that returns a stable AST plus precise diagnostics.
- Generators that turn the AST into idiomatic test files for Python, TypeScript, Java, C#, Rust, Go, and Odin.
- Meta-tests that check the test suite includes failure fixtures, not just happy paths.

## Quick Start

```bash
PYTHONPATH=src python -m tdd_dsl validate tests/fixtures/valid_minimal.tdd
PYTHONPATH=src python -m tdd_dsl emit --target python tests/fixtures/valid_minimal.tdd
PYTHONPATH=src python -m tdd_dsl emit --target java tests/fixtures/valid_minimal.tdd
PYTHONPATH=src python -m unittest discover -s tests
```

Golden emitter fixtures are checked by the unit suite. Refresh them only when an
intentional emitter change needs new expected output:

```bash
PYTHONPATH=src TDD_DSL_UPDATE_GOLDENS=1 python -m unittest tests.test_golden_fixtures
```

Mutation smoke fixtures intentionally break valid DSL examples by removing
`then`, corrupting JSON, and renaming `when`. They prove common malformed edits
produce targeted parser diagnostics; they do not prove generated tests catch
implementation-level code mutations.

## Example

```text
suite "Billing policy contract"
target python "billing_policy"
target typescript "billing-policy"
target java "com.example.BillingPolicy"

case "flags enterprise usage before charging":
  given input:
    {
      "account": {"plan": "team", "yearsActive": 1},
      "usage": {"projects": 91, "seats": 42}
    }
  when call "quoteSubscription"
  then equals:
    {
      "tier": "enterprise",
      "monthlyUsd": null,
      "requiresReview": true,
      "reason": "seat_count"
    }
```

That single contract emits executable pytest and Vitest tests. The fixtures under
`tests/fixtures/` intentionally include both tiny parser examples and richer
showcase contracts so the test suite doubles as adoption documentation.

The runner can also execute a contract against local implementation code:

```bash
PYTHONPATH=src python -m tdd_dsl run --target python --cwd path/to/project path/to/project/contract.tdd
```

When generated Python assertions fail, the runner prefixes the traceback with the
DSL case line that produced the failed test.

## Documentation

- **[docs/README.md](docs/README.md)** — Documentation overview, quickstart, and emitter comparison
- [docs/SPEC.md](docs/SPEC.md) — DSL specification and grammar
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — System architecture
- [docs/TICKETS.md](docs/TICKETS.md) — Development tickets
- [docs/emitters/python.md](docs/emitters/python.md) — Python/pytest documentation
- [docs/emitters/typescript.md](docs/emitters/typescript.md) — TypeScript/Vitest documentation
- [docs/emitters/java.md](docs/emitters/java.md) — Java/JUnit 5 documentation
- [docs/emitters/csharp.md](docs/emitters/csharp.md) — C#/xUnit documentation
- [docs/emitters/rust.md](docs/emitters/rust.md) — Rust/std test documentation
- [docs/emitters/go.md](docs/emitters/go.md) — Go/testing documentation
- [docs/emitters/odin.md](docs/emitters/odin.md) — Odin/core:testing documentation
- [docs/emitters/zig.md](docs/emitters/zig.md) — Zig/std.testing documentation (planned)

## Status

This repo has reached an initial implementation milestone: parser, validator,
emitters for Python, TypeScript, Java, C#, Go, Rust, and Odin, golden fixtures,
validation JSON, and a Python runner are covered by tests.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design and
[docs/TICKETS.md](docs/TICKETS.md) for development backlog.
