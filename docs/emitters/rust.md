# Rust Emitter (std test)

Generates idiomatic **Rust** tests using the standard `#[test]` framework with `cargo test`.

---

## Framework Overview

| Attribute | Value |
|-----------|-------|
| **Framework** | Rust Standard Library (`std::test`) |
| **Test Runner** | `cargo test` |
| **Minimum Rust Version** | 1.60+ recommended (for modern features) |
| **Assertion Style** | `assert_eq!(expected, actual)` |

---

## Target Declaration

```text
target rust "module_name"
```

The module name is used for the use statement:
- Simple name: `calculator` → `use calculator::*;`
- Path: `my_crate::auth` → `use my_crate::auth::*;`

---

## Generated Test Structure

### Minimal Example

**Input (.tdd):**
```text
suite "Calculator"
target rust "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5
```

**Output (.rs):**
```rust
use calculator::*;

#[test]
fn test_adds_two_numbers() {
    // Input: {'a': 2, 'b': 3}
    let input = vec![("a", 2), ("b", 3)].into_iter().collect::<std::collections::HashMap<_, _>>();
    let result = add(&input);
    assert_eq!(5, result);
}

```

### Complex Example

**Input (.tdd):**
```text
suite "Billing policy"
target rust "billing"

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

**Output (.rs):**
```rust
use billing::*;

#[test]
fn test_calculates_enterprise_tier() {
    // Input: {'account': {...}, 'usage': {...}}
    let input = vec![
        ("account", vec![("plan", "team"), ("yearsActive", 1)].into_iter().collect::<std::collections::HashMap<_, _>>()),
        ("usage", vec![("projects", 91), ("seats", 42)].into_iter().collect::<std::collections::HashMap<_, _>>())
    ].into_iter().collect::<std::collections::HashMap<_, _>>();
    let result = quote_subscription(&input);
    // Expected: {'tier': 'enterprise', 'monthly_usd': None, 'requires_review': True}
    assert_eq!("enterprise", result.tier);
    assert_eq!((), result.monthly_usd);
    assert_eq!(true, result.requires_review);
}

```

---

## Naming Conventions

### Function Names

Case names are converted to snake_case:

| Case Name | Function Name |
|-----------|---------------|
| `adds two numbers` | `test_adds_two_numbers` |
| `Handles special!` | `test_handles_special` |
| `Edge Case` | `test_edge_case` |
| `async` (keyword) | `async_test` |

If duplicate names would be generated, a numeric suffix is added:
- `test_case` → `test_case_2` → `test_case_3`

---

## Data Structures

### HashMap Construction

The emitter generates `HashMap` literals using `vec![]` and `collect()`:

```rust
// Simple map
let input = vec![("key", "value")].into_iter().collect::<std::collections::HashMap<_, _>>();

// Nested map
let input = vec![
    ("account", vec![("plan", "team")].into_iter().collect::<std::collections::HashMap<_, _>>()),
    ("usage", vec![("seats", 5)].into_iter().collect::<std::collections::HashMap<_, _>>())
].into_iter().collect::<std::collections::HashMap<_, _>>();
```

### Vec Construction

```rust
let input = vec![1, 2, 3];
```

### Null Representation

JSON `null` becomes Rust's unit type `()`:

```rust
// Input: {"value": null}
let input = vec![("value", ())].into_iter().collect::<std::collections::HashMap<_, _>>();
```

---

## Assertions & Matchers

### assert_eq!

```rust
assert_eq!(expected, actual);
```

The standard Rust assertion macro. On failure, it prints a colorful diff.

### Field-by-Field Assertions

For dict expected values, the emitter generates individual field assertions:

```rust
assert_eq!("enterprise", result.tier);
assert_eq!((), result.monthly_usd);
assert_eq!(true, result.requires_review);
```

This provides better error messages showing exactly which field failed.

### Other Standard Assertions

You can manually add other assertions:

```rust
assert_ne!(left, right);          // not equal
assert!(condition);               // boolean true
assert!(!condition);              // boolean false
assert!(result.is_ok());          // Result is Ok
assert!(result.is_some());        // Option is Some
```

---

## Running Tests

### All Tests

```bash
cargo test
```

### Single Test

```bash
cargo test test_adds_two_numbers
```

### With Output

```bash
cargo test -- --nocapture
```

### Filtering

```bash
cargo test calculator  # runs tests with "calculator" in the name
```

---

## Test Organization

### Inline Tests

Place generated tests in your source file:

```rust
// src/calculator.rs
pub fn add(a: i32, b: i32) -> i32 {
    a + b
}

#[cfg(test)]
mod tests {
    use super::*;

    // tdd-dsl generated tests here
    #[test]
    fn test_adds_two_numbers() {
        let input = vec![("a", 2), ("b", 3)].into_iter().collect::<std::collections::HashMap<_, _>>();
        let result = add(&input);
        assert_eq!(5, result);
    }
}
```

### Separate Test File

Or place in `tests/` directory as integration tests:

```rust
// tests/integration_test.rs
use my_crate::*;

#[test]
fn test_adds_two_numbers() { ... }
```

---

## Source Map Comments

When source path is provided:

```rust
// Source: calculator.tdd:5
#[test]
fn test_adds_two_numbers() { ... }
```

---

## Limitations

1. **Field Access Syntax**: For dict expected values, the emitter uses field access syntax (`result.tier`). Your return type must be a struct with public fields, not a `HashMap`.

2. **Reference Passing**: Complex inputs are passed by reference (`&input`). Primitive values are passed by value.

3. **JSON null as ()**: JSON `null` becomes the Rust unit type `()`, which may not match your function signature if using `Option<T>`.

4. **No Async**: Synchronous tests only. Wrap async calls manually:
   ```rust
   #[test]
   fn test_async_op() {
       let result = tokio_test::block_on(async_function());
       assert_eq!(expected, result);
   }
   ```

---

## Integration Example

Suppose you have a Rust crate `calculator/src/lib.rs`:

```rust
use std::collections::HashMap;

pub fn add(input: &HashMap<&str, i32>) -> i32 {
    input.get("a").unwrap_or(&0) + input.get("b").unwrap_or(&0)
}
```

And a contract `calculator.tdd`:

```text
suite "Calculator"
target rust "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5
```

Emit and place:

```bash
PYTHONPATH=src python -m tdd_dsl emit --target rust calculator.tdd > tests/test_calculator.rs
cargo test
```

---

## See Also

- [The Rust Programming Language - Testing](https://doc.rust-lang.org/book/ch11-00-testing.html)
- [Rust By Example - Testing](https://doc.rust-lang.org/rust-by-example/testing.html)
- [assert_eq! documentation](https://doc.rust-lang.org/std/macro.assert_eq.html)
