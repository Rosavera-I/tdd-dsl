# Two-Point Tickets

## Ticket 1: Parser, AST, CLI Validation

Acceptance:

- Parse the MVP grammar into stable AST dataclasses.
- Return diagnostics instead of tracebacks for invalid DSL.
- Provide `python -m tdd_dsl validate FILE`.
- Include valid and invalid fixtures.
- Include meta-tests proving negative fixtures and diagnostic assertions exist.

## Ticket 2: Python Pytest Emitter

Acceptance:

- Emit deterministic pytest code from a valid AST.
- Support object input as keyword args and scalar/list input as one positional arg.
- Provide `python -m tdd_dsl emit --target python FILE`.
- Include tests for generated imports, function calls, and assertions.

## Ticket 3: TypeScript Vitest Emitter

Status: queued

Acceptance:

- Emit deterministic Vitest code.
- Support object input as destructured argument object or keyword-like object calls.
- Include tests for generated imports and `expect(...).toEqual(...)`.

## Ticket 4: Semantic Validator Expansion

Status: queued

Acceptance:

- Detect duplicate case names.
- Detect unsupported target names.
- Detect unsupported JSON input shape per backend.
- Return all diagnostics in one pass where practical.

## Ticket 5: Golden Fixture Harness

Status: queued

Acceptance:

- Add golden output files per backend.
- Add an update workflow that is explicit and opt-in.
- Ensure generated files are stable across repeated runs.

## Ticket 6: Mutation Smoke Tests

Status: queued

Acceptance:

- Add simple mutation fixtures that remove `then`, corrupt JSON, and rename `when`.
- Verify each mutation fails for the intended reason.
- Document what this does and does not prove.

## Ticket 7: Project Metadata and Local Workflow

Status: done

Acceptance:

- Add Python project metadata for future packaging.
- Expose the intended `tdd-dsl` console script in metadata.
- Document the no-install local workflow that works with standard-library Python.
- Include a test that checks packaging metadata and script registration.
