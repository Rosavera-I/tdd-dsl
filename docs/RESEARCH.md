# Research Notes

This project is adjacent to BDD feature formats, test result protocols, and language-specific test frameworks. The design borrows the useful parts while staying focused on TDD generation for LLM coding loops.

## Sources Checked

- Cucumber Gherkin reference: line-oriented executable specifications, `Feature`, `Rule`, `Scenario`, `Given/When/Then`, data tables, doc strings, and tags. Important lesson: readable examples work best when they stay concrete and observable. Source: https://cucumber.io/docs/gherkin/reference/
- TAP 13 specification: language-agnostic test result streams. Important lesson: cross-language test tooling benefits from stable intermediate protocols. Source: https://testanything.org/tap-version-13-specification.html
- pytest assertions docs: Python tests can rely on plain `assert` statements with rich introspection and explicit exception assertions. Source: https://docs.pytest.org/en/stable/how-to/assert.html
- JUnit user guide: mature ecosystems organize tests around annotations, assertions, lifecycle hooks, and display names. Source: https://docs.junit.org/6.1.0/overview.html

## Design Implications

- Keep the DSL line-oriented and indentation-aware, but smaller than Gherkin.
- Use explicit machine-readable payload blocks instead of unconstrained prose for inputs and expected values.
- Treat test generation as a compiler backend problem: parse once, emit many.
- Keep output deterministic so LLM agents can diff, patch, and repair it.
- Preserve source locations in diagnostics and AST nodes.

## Bridge Note

The Rosie Codex Bridge was invoked for the initial partner pass, but command-level network access is disabled in this sandbox. The launcher reached `codex exec` and failed connecting to `api.openai.com` with `Operation not permitted`. Work continued locally with that blocker recorded here.
