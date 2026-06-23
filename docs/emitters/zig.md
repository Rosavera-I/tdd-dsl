# Zig Emitter (std.testing)

> **Status: Planned** - This emitter is on the roadmap but not yet implemented.
>
> The tdd-dsl CLI does not currently support `--target zig`.

---

## Framework Overview

| Attribute | Planned Value |
|-----------|---------------|
| **Framework** | [Zig Standard Library](https://ziglang.org/documentation/master/std/) (`std.testing`) |
| **Test Runner** | `zig test` |
| **Minimum Zig Version** | 0.12+ recommended |
| **Assertion Style** | `try std.testing.expectEqual(expected, actual)` |

---

## Planned Target Declaration

```text
target zig "module_name"
```

The module name would be used for imports:
- `calculator` → `@import("calculator")`
- `my_app/utils` → `@import("utils")`

---

## Planned Generated Test Structure

### Minimal Example (Planned)

**Input (.tdd):**
```text
suite "Calculator"
target zig "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5
```

**Expected Output (.zig):**
```zig
const std = @import("std");
const calculator = @import("calculator");

test "adds two numbers" {
    const input = .{ .a = 2, .b = 3 };
    const result = calculator.add(input);
    try std.testing.expectEqual(@as(i32, 5), result);
}
```

### Complex Example (Planned)

**Input (.tdd):**
```text
suite "Billing policy"
target zig "billing"

case "calculates enterprise tier":
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

**Expected Output (.zig):**
```zig
const std = @import("std");
const billing = @import("billing");

test "calculates enterprise tier" {
    const input = .{
        .account = .{ .plan = "team", .yearsActive = 1 },
        .usage = .{ .projects = 91, .seats = 42 },
    };
    const result = billing.quoteSubscription(input);
    
    try std.testing.expectEqualStrings("enterprise", result.tier);
    try std.testing.expectEqual(@as(?i32, null), result.monthlyUsd);
    try std.testing.expectEqual(true, result.requiresReview);
}
```

---

## Planned Naming Conventions

### Test Names

Zig uses string literals for test names (unlike function name conventions):

| Case Name | Test Declaration |
|-----------|------------------|
| `adds two numbers` | `test "adds two numbers" { ... }` |
| `handles special!` | `test "handles special!" { ... }` |
| `Edge Case` | `test "Edge Case" { ... }` |

Test names preserve the exact case name from the `.tdd` file.

---

## Planned Data Structures

### Anonymous Struct Literals

Zig's anonymous structs would map naturally to JSON objects:

```zig
// JSON: {"a": 2, "b": 3}
const input = .{ .a = 2, .b = 3 };

// Nested JSON: {"user": {"name": "Alice"}}
const input = .{ .user = .{ .name = "Alice" } };
```

### Arrays

```zig
// JSON: [1, 2, 3]
const input = .{ 1, 2, 3 };

// Or using explicit array syntax
const input = [_]i32{ 1, 2, 3 };
```

### Optional Types

JSON `null` would map to Zig's optional types:

```zig
// JSON: {"value": null}
const input = .{ .value = @as(?i32, null) };
```

---

## Planned Assertions

### expectEqual

```zig
try std.testing.expectEqual(expected, actual);
```

### expectEqualStrings

```zig
try std.testing.expectEqualStrings("expected", result);
```

### Field-by-Field Assertions

For dict expected values:

```zig
try std.testing.expectEqualStrings("enterprise", result.tier);
try std.testing.expectEqual(@as(?i32, null), result.monthlyUsd);
try std.testing.expectEqual(true, result.requiresReview);
```

---

## Planned Running Tests

### All Tests

```bash
zig test src/main.zig
```

### Single File

```bash
zig test calculator_test.zig
```

### With Release Mode

```bash
zig test -O ReleaseSafe calculator_test.zig
```

---

## Implementation Notes

To implement the Zig emitter, the following would need to be added to `src/tdd_dsl/emitters/`:

1. **`zig.py`** - New emitter module following the pattern of `rust.py` or `odin.py`
2. **CLI registration** - Add `"zig"` to the target choices in `cli.py`
3. **Golden tests** - Add expected output fixtures in `tests/goldens/zig/`
4. **Unit tests** - Test the emitter in `tests/test_emitters.py`

### Key Design Decisions Needed

1. **Struct literals**: Anonymous structs (`.{...}`) vs explicit struct types
2. **Allocator handling**: Whether to support allocator-aware functions
3. **Error unions**: How to handle functions returning `!T`
4. **comptime**: When to use comptime-known values

---

## See Also

- [Zig Language Reference](https://ziglang.org/documentation/master/)
- [Zig Standard Library Documentation](https://ziglang.org/documentation/master/std/)
- [Zig Test Documentation](https://ziglang.org/documentation/master/#Test)
