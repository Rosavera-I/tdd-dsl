# TDD DSL Documentation

Welcome to the **tdd-dsl** documentation — a test-driven development DSL that generates idiomatic test scaffolding across multiple language ecosystems from a single, LLM-friendly contract.

## What is TDD DSL?

TDD DSL is a line-oriented, human-readable language for describing test contracts once and emitting executable tests for:

- **Python** (pytest)
- **TypeScript** (Vitest)
- **Java** (JUnit 5)
- **Rust** (std test)
- **Go** (testing package)
- **Odin** (core:testing)

The DSL is designed to be:
- **LLM-friendly**: Explicit sections, stable syntax, deterministic output
- **Human-readable**: Clear structure with keywords like `suite`, `case`, `given`, `when`, `then`
- **Polyglot**: One contract, multiple language targets
- **Precise**: Validation diagnostics with line and column information

## Supported Languages

- **Python** (pytest)
- **TypeScript** (Vitest)
- **Java** (JUnit 5)
- **C#** (xUnit)
- **Rust** (std test)
- **Go** (testing package)
- **Odin** (core:testing)

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd tdd-dsl

# Run with Python directly
PYTHONPATH=src python -m tdd_dsl --help
```

### Write Your First Contract

Create a file named `calculator.tdd`:

```text
suite "Calculator"
target python "calculator"
target typescript "calculator"
target java "Calculator"
target go "calculator"
target rust "calculator"
target odin "calculator"
target csharp "Calculator"
target lua "calculator"
target ruby "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5
```

### Validate the Contract

```bash
PYTHONPATH=src python -m tdd_dsl validate calculator.tdd
```

### Emit Tests

```bash
# Python
PYTHONPATH=src python -m tdd_dsl emit --target python calculator.tdd > test_calculator.py

# TypeScript
PYTHONPATH=src python -m tdd_dsl emit --target typescript calculator.tdd > calculator.test.ts

# Java
PYTHONPATH=src python -m tdd_dsl emit --target java calculator.tdd > CalculatorTest.java

# Rust
PYTHONPATH=src python -m tdd_dsl emit --target rust calculator.tdd > calculator_test.rs

# Go
PYTHONPATH=src python -m tdd_dsl emit --target go calculator.tdd > calculator_test.go

# Odin
PYTHONPATH=src python -m tdd_dsl emit --target odin calculator.tdd > calculator_test.odin

# C#
PYTHONPATH=src python -m tdd_dsl emit --target csharp calculator.tdd > CalculatorTests.cs

# Lua
PYTHONPATH=src python -m tdd_dsl emit --target lua calculator.tdd > calculator_spec.lua

# Ruby
PYTHONPATH=src python -m tdd_dsl emit --target ruby calculator.tdd > calculator_spec.rb
```

### Run the Tests

```bash
# Python
PYTHONPATH=src python -m tdd_dsl run --target python calculator.tdd

# TypeScript (requires Vitest in working directory)
PYTHONPATH=src python -m tdd_dsl run --target typescript --cwd ./my-project calculator.tdd
```

---

## Documentation Structure

| Document | Description |
|----------|-------------|
| [`SPEC.md`](SPEC.md) | Complete DSL specification, grammar, and semantics |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | System architecture and design decisions |
| [`emitters/python.md`](emitters/python.md) | Python/pytest bindings and examples |
| [`emitters/typescript.md`](emitters/typescript.md) | TypeScript/Vitest bindings and examples |
| [`emitters/java.md`](emitters/java.md) | Java/JUnit 5 bindings and examples |
| [`emitters/rust.md`](emitters/rust.md) | Rust/std test bindings and examples |
| [`emitters/go.md`](emitters/go.md) | Go/testing bindings and examples |
| [`emitters/odin.md`](emitters/odin.md) | Odin/core:testing bindings and examples |
| [`emitters/csharp.md`](emitters/csharp.md) | C#/xUnit bindings and examples |
| [`emitters/zig.md`](emitters/zig.md) | Zig/std.testing bindings *(planned)* |

---

## DSL Syntax Overview

### Suite Declaration

Every contract starts with a suite name:

```text
suite "Billing policy contract"
```

### Target Declarations

Declare one or more language targets before any cases:

```text
target python "billing_policy"
target typescript "billing-policy"
target java "com.example.BillingPolicy"
target rust "billing"
target go "github.com/user/billing"
target odin "billing"
target csharp "Billing"
```

### Case Blocks

Each test case has a name and three required steps:

```text
case "flags enterprise usage":
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
      "requiresReview": true
    }
```

---

## Emitter Comparison

| Feature | Python | TypeScript | Java | C# | Rust | Go | Odin |
|---------|--------|------------|------|-----|------|-----|------|
|---------|--------|------------|------|------|-----|------|
| **Framework** | pytest | Vitest | JUnit 5 | xUnit | std test | testing | core:testing |
| **Test Discovery** | `pytest` | `vitest run` | `mvn test` | `dotnet test` | `cargo test` | `go test` | `odin test` |
| **Assertion Style** | `assert` | `expect().toEqual` | `assertEquals` | `Assert.Equal` | `assert_eq!` | `reflect.DeepEqual` | `expect_value` |
| **Nested Objects** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Source Mapping** | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Null Handling** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## CLI Reference

### `validate`

Check a `.tdd` file for syntax and semantic errors:

```bash
tdd-dsl validate FILE
tdd-dsl validate --format json FILE  # LSP-compatible output
```

### `emit`

Generate test code for a specific target:

```bash
tdd-dsl emit --target python|typescript|java|csharp|go|rust|odin|lua|ruby FILE
```

### `run`

Generate and execute tests (Python and TypeScript only):

```bash
tdd-dsl run --target python FILE
tdd-dsl run --target typescript --cwd DIR FILE
```

### `discover`

Find and validate multiple `.tdd` files:

```bash
tdd-dsl discover "tests/**/*.tdd"
tdd-dsl discover "contracts/*.tdd" --format json
```

---

## Advanced Example

Here's a richer contract with multiple cases and complex JSON:

```text
suite "User authentication"
target python "auth_service"
target typescript "auth-service"
target java "com.example.AuthService"
target rust "auth"
target go "example.com/auth"
target odin "auth"
target csharp "AuthService"

case "valid credentials grant access":
  given input:
    {
      "username": "alice",
      "password": "correct-horse-battery-staple",
      "mfaToken": null
    }
  when call "authenticate"
  then equals:
    {
      "success": true,
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
      "permissions": ["read", "write"],
      "expiresAt": null
    }

case "invalid password rejects login":
  given input:
    {"username": "alice", "password": "wrong", "mfaToken": null}
  when call "authenticate"
  then equals:
    {"success": false, "error": "invalid_credentials", "token": null}

case "mfa required for admin accounts":
  given input:
    {"username": "admin", "password": "admin123", "mfaToken": "123456"}
  when call "authenticate"
  then equals:
    {"success": true, "token": "admin-jwt-token", "requiresMfa": false}
```

---

## Contributing

See the main [README.md](../README.md) for development setup and the [ARCHITECTURE.md](ARCHITECTURE.md) for system design.

---

## License

See the project's main license file.
