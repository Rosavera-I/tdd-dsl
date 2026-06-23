# Odin Emitter (core:testing)

Generates idiomatic **Odin** tests using the `core:testing` package.

---

## Framework Overview

| Attribute | Value |
|-----------|-------|
| **Framework** | Odin Standard Library (`core:testing`) |
| **Test Runner** | `odin test` |
| **Minimum Odin Version** | dev-2024+ (latest compiler recommended) |
| **Assertion Style** | `testing.expect_value(t, result, expected)` |

---

## Target Declaration

```text
target odin "module_name"
```

The module name becomes the package name:
- `calculator` → `package calculator`
- `my_app/utils` → `package utils`
- `game.physics` → `package physics`

---

## Generated Test Structure

### Minimal Example

**Input (.tdd):**
```text
suite "Calculator"
target odin "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5
```

**Output (.odin):**
```odin
package calculator

import "core:testing"

@(test)
test_adds_two_numbers :: proc(t: ^testing.T) {
    input := {a = 2, b = 3}
    result := add(input)
    testing.expect_value(t, result, 5)
}

```

### Complex Example

**Input (.tdd):**
```text
suite "Billing policy"
target odin "billing"

case "calculates enterprise tier":
  given input:
    {
      "account": {"plan": "team", "yearsActive": 1},
      "usage": {"projects": 91, "seats": 42}
    }
  when call "quote_subscription"
  then equals:
    {
      "tier": "enterprise",
      "monthly_usd": null,
      "requires_review": true
    }
```

**Output (.odin):**
```odin
package billing

import "core:testing"

@(test)
test_calculates_enterprise_tier :: proc(t: ^testing.T) {
    // Input: {'account': {...}, 'usage': {...}}
    input := {
        account = {plan = "team", years_active = 1},
        usage = {projects = 91, seats = 42}
    }
    result := quote_subscription(input)

    // Expected: {...}
    testing.expect_value(t, result.tier, "enterprise")
    testing.expect_value(t, result.monthly_usd, nil)
    testing.expect_value(t, result.requires_review, true)
}

```

---

## Naming Conventions

### Procedure Names

Case names are converted to snake_case with `test_` prefix:

| Case Name | Procedure Name |
|-----------|----------------|
| `adds two numbers` | `test_adds_two_numbers` |
| `Handles edge!` | `test_handles_edge` |
| `Edge Case` | `test_edge_case` |
| `proc` (keyword) | `proc_test` |

If duplicate names would be generated, a numeric suffix is added:
- `test_case` → `test_case_2` → `test_case_3`

### Package Names

Package names are sanitized Odin identifiers:

| Target Declaration | Package Name |
|------------------|--------------|
| `target odin "calculator"` | `calculator` |
| `target odin "game/physics"` | `physics` |
| `target odin "my.lib.calc"` | `calc` |

---

## Data Structures

### Struct Literals

Dict inputs become Odin struct literals using field assignment syntax:

```odin
// JSON: {"a": 2, "b": 3}
input := {a = 2, b = 3}

// Nested JSON: {"user": {"name": "Alice", "active": true}}
input := {
    user = {name = "Alice", active = true}
}
```

### Array Literals

```odin
// JSON: [1, 2, 3]
input := []{1, 2, 3}

// Empty JSON: []
input := []
```

### Null Representation

JSON `null` becomes Odin's `nil`:

```odin
input := {monthly_usd = nil}
```

---

## Test Attribute

Tests are marked with the `@(test)` attribute for discovery:

```odin
@(test)
test_my_feature :: proc(t: ^testing.T) {
    // ...
}
```

This is Odin's equivalent of Go's `TestXxx(t *testing.T)` or Rust's `#[test]`.

---

## Assertions & Matchers

### expect_value

```odin
testing.expect_value(t, result, expected)
```

Compares `result` with `expected` and reports failure if they differ.

### Field-by-Field Assertions

For dict expected values, the emitter generates individual field assertions:

```odin
// Expected: {"tier": "enterprise", "monthly_usd": nil, "requires_review": true}
testing.expect_value(t, result.tier, "enterprise")
testing.expect_value(t, result.monthly_usd, nil)
testing.expect_value(t, result.requires_review, true)
```

This provides clear error messages showing which field failed.

---

## Running Tests

### All Tests in Package

```bash
odin test .
```

### Specific Package

```bash
odin test ./calculator
```

### With Verbose Output

```bash
odin test -v .
```

### Output Format

```bash
odin test -define:ODIN_TEST_LOG_LEVEL=debug .
```

---

## Project Structure

Typical Odin project with tests:

```
my_project/
├── main.odin           # Entry point
├── calculator/
│   ├── calculator.odin # Implementation
│   └── test_calculator.odin  # Generated tests
└── ols.json            # Language server config (optional)
```

---

## Source Map Comments

When source path is provided:

```odin
// Source: calculator.tdd:5
@(test)
test_adds_two_numbers :: proc(t: ^testing.T) { ... }
```

---

## Limitations

1. **Field Access Syntax**: For dict expected values, the emitter uses field access (`result.tier`). Your return type should be a struct with fields matching the expected JSON keys.

2. **snake_case Fields**: JSON keys are converted to snake_case field names. Ensure your Odin struct fields use snake_case:
   ```odin
   User :: struct {
       user_name: string,  // matches JSON "userName" -> "user_name"
   }
   ```

3. **Struct Assumption**: The generated code assumes you've defined appropriate struct types for your data. For map-based APIs, you'll need to adapt the generated code.

4. **No Types in Literals**: The generated struct literals use Odin's type inference. Explicit types may be needed for your specific use case.

---

## Integration Example

Suppose you have an Odin module `calculator/calculator.odin`:

```odin
package calculator

Add :: proc(input: struct {a: int, b: int}) -> int {
    return input.a + input.b
}
```

And a contract `calculator.tdd`:

```text
suite "Calculator"
target odin "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5
```

Emit and run:

```bash
PYTHONPATH=src python -m tdd_dsl emit --target odin calculator.tdd > calculator/test_calculator.odin
odin test ./calculator
```

---

## See Also

- [Odin Documentation](https://odin-lang.org/docs/)
- [Odin Core Library](https://pkg.odin-lang.org/core/)
- [Odin Testing](https://odin-lang.org/docs/overview/#testing)
