# Go Emitter (testing package)

Generates idiomatic **Go** tests using the standard `testing` package.

---

## Framework Overview

| Attribute | Value |
|-----------|-------|
| **Framework** | Go Standard Library (`testing`) |
| **Test Runner** | `go test` |
| **Minimum Go Version** | 1.18+ recommended (for generics support) |
| **Assertion Style** | `reflect.DeepEqual` with `t.Errorf` |

---

## Target Declaration

```text
target go "module/path"
```

The module path is converted to a package name:
- `calculator` → `package calculator`
- `github.com/user/calculator` → `package calculator`
- `example.com/my-app/utils` → `package utils`

---

## Generated Test Structure

### Minimal Example

**Input (.tdd):**
```text
suite "Calculator"
target go "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "Add"
  then equals:
    5
```

**Output (_test.go):**
```go
package calculator

import (
    "encoding/json"
    "reflect"
    "testing"
)

func TestAddsTwoNumbers(t *testing.T) {
    input := map[string]interface{}{"a": 2, "b": 3}
    result := Add(input)

    expected := 5
    if !reflect.DeepEqual(result, expected) {
        t.Errorf("expected %v, got %v", expected, result)
    }
}
```

### Complex Example

**Input (.tdd):**
```text
suite "Billing policy"
target go "github.com/example/billing"

case "calculates enterprise tier":
  given input:
    {
      "account": {"plan": "team", "yearsActive": 1},
      "usage": {"projects": 91, "seats": 42}
    }
  when call "QuoteSubscription"
  then equals:
    {
      "tier": "enterprise",
      "monthlyUsd": null,
      "requiresReview": true
    }
```

**Output (_test.go):**
```go
package billing

import (
    "encoding/json"
    "reflect"
    "testing"
)

// Source: billing.tdd:4
func TestCalculatesEnterpriseTier(t *testing.T) {
    inputJSON := `{"account":{"plan":"team","yearsActive":1},"usage":{"projects":91,"seats":42}}`
    var input interface{}
    if err := json.Unmarshal([]byte(inputJSON), &input); err != nil {
        t.Fatalf("failed to unmarshal input: %v", err)
    }
    result := QuoteSubscription(input)

    expectedJSON := `{"tier":"enterprise","monthlyUsd":null,"requiresReview":true}`
    var expected interface{}
    if err := json.Unmarshal([]byte(expectedJSON), &expected); err != nil {
        t.Fatalf("failed to unmarshal expected: %v", err)
    }
    if !reflect.DeepEqual(result, expected) {
        t.Errorf("expected %v, got %v", expected, result)
    }
}
```

---

## Naming Conventions

### Test Function Names

Case names are converted to PascalCase with `Test` prefix (following Go conventions):

| Case Name | Function Name |
|-----------|---------------|
| `adds two numbers` | `TestAddsTwoNumbers` |
| `handles edge cases` | `TestHandlesEdgeCases` |
| `123 starts numeric` | `Test123StartsNumeric` |

### Package Names

Package names are derived from the last path segment:

| Target Declaration | Package Name |
|--------------------|--------------|
| `target go "calculator"` | `calculator` |
| `target go "github.com/user/calc"` | `calc` |
| `target go "example.com/v2/api"` | `api` |

---

## JSON Handling

### Small Values

Simple values use Go literals:

```go
input := map[string]interface{}{"a": 2, "b": 3}
expected := 5
```

### Large/Complex Values

Complex nested structures use JSON unmarshaling for readability:

```go
inputJSON := `{"account":{"plan":"team","yearsActive":1},...}`
var input interface{}
if err := json.Unmarshal([]byte(inputJSON), &input); err != nil {
    t.Fatalf("failed to unmarshal input: %v", err)
}
```

This is used when:
- The JSON representation exceeds 60 characters
- The JSON spans multiple lines

---

## Assertions & Matchers

### reflect.DeepEqual

The Go emitter uses `reflect.DeepEqual` for comparing complex structures:

```go
if !reflect.DeepEqual(result, expected) {
    t.Errorf("expected %v, got %v", expected, result)
}
```

This correctly handles:
- Maps with any keys
- Nested structures
- Slices and arrays
- nil values

### Why not testify/assert?

The emitter uses only standard library packages. You can optionally add `github.com/stretchr/testify` after generation:

```go
import "github.com/stretchr/testify/assert"

func TestWithTestify(t *testing.T) {
    result := Add(input)
    assert.Equal(t, expected, result)
}
```

---

## Running Tests

### All Tests

```bash
go test ./...
```

### Single Package

```bash
go test ./calculator
```

### Single Test

```bash
go test -run TestAddsTwoNumbers
```

### Verbose Output

```bash
go test -v
```

### With Coverage

```bash
go test -cover
```

---

## Project Structure

Generated tests typically live in `*_test.go` files:

```
calculator/
├── calculator.go      # Implementation
├── calculator_test.go # Generated tests
└── go.mod
```

---

## Module Setup

### go.mod

```go
module github.com/example/calculator

go 1.21
```

No external test dependencies required.

---

## Source Map Comments

When source path is provided:

```go
// Source: calculator.tdd:5
func TestAddsTwoNumbers(t *testing.T) { ... }
```

---

## Limitations

1. **interface{} Types**: Complex values use `interface{}` (untyped) because the emitter doesn't know your specific struct types. For typed tests, you'll need to adapt the generated code.

2. **CamelCase Function Names**: Go exports require PascalCase function names. Ensure your `when call` values match your Go function names.

3. **No Generic Types**: The generated code doesn't use Go generics.

4. **JSON Encoding**: `json.Unmarshal` uses float64 for numbers. Very large integers may lose precision.

---

## Integration Example

Suppose you have a Go module `calculator/calculator.go`:

```go
package calculator

func Add(input map[string]interface{}) int {
    a := input["a"].(int)
    b := input["b"].(int)
    return a + b
}
```

And a contract `calculator.tdd`:

```text
suite "Calculator"
target go "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "Add"
  then equals:
    5
```

Emit and run:

```bash
PYTHONPATH=src python -m tdd_dsl emit --target go calculator.tdd > calculator/calculator_test.go
go test ./calculator
```

---

## See Also

- [Go Testing Package](https://pkg.go.dev/testing)
- [Go Test Documentation](https://go.dev/doc/code#Testing)
- [Effective Go - Testing](https://go.dev/doc/effective_go#testing)
