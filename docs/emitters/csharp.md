# C# / xUnit Emitter

The C# emitter generates idiomatic xUnit test classes from TDD DSL contracts.

## Target Declaration

```text
target csharp "Namespace.ClassName"
```

The module path is used to:
- Generate the test class name (`ClassNameTests`)
- Add namespace `using` statements for qualified module paths
- Reference the class under test in method calls

## Generated Code Structure

### Class Declaration

```csharp
using Xunit;
using MyApp.Services;  // if module is "MyApp.Services.Calculator"

public class CalculatorTests
{
    // test methods
}
```

### Test Methods

Each case generates a test method with:
- `[Fact]` attribute (xUnit's standard test attribute)
- camelCase method name derived from the case name
- Source map comment with file and line information

```csharp
[Fact]
public void testAddsTwoNumbers()
{
    // test body
}
```

## Input Handling

### Object Input (Dictionary)

```text
given input:
  {"a": 1, "b": 2}
```

Generates:

```csharp
var input = new Dictionary<string, object> { { "a", 1 }, { "b", 2 } };
var result = Calculator.add(input);
```

### List Input

```text
given input:
  [1, 2, 3]
```

Generates:

```csharp
var input = new List<object> { 1, 2, 3 };
var result = Calculator.process(input);
```

### Scalar Input

```text
given input:
  42
```

Generates:

```csharp
var result = Calculator.getValue(42);
```

## Assertion Patterns

### Object Expected Value

```text
then equals:
  {"total": 100, "currency": "USD"}
```

Generates multiple `Assert.Equal` calls:

```csharp
Assert.Equal(100, result["total"]);
Assert.Equal("USD", result["currency"]);
```

### List Expected Value

```text
then equals:
  [1, 2, 3]
```

Generates:

```csharp
var expected = new List<object> { 1, 2, 3 };
Assert.Equal(expected, result);
```

### Scalar Expected Value

```text
then equals:
  42
```

Generates:

```csharp
Assert.Equal(42, result);
```

## Data Type Mapping

| JSON Type | C# Literal |
|-----------|------------|
| `null` | `null` |
| `true`/`false` | `true`/`false` |
| Number | Literal integer or float |
| String | `"escaped string"` |
| Array | `new List<object> { ... }` |
| Object | `new Dictionary<string, object> { ... }` |

## Running Generated Tests

1. Create a .NET test project:

```bash
dotnet new xunit -n MyProject.Tests
cd MyProject.Tests
```

2. Add a reference to your implementation project:

```bash
dotnet add reference ../MyProject/MyProject.csproj
```

3. Copy the generated test file into the test project

4. Run tests:

```bash
dotnet test
```

## Example Contract

```text
suite "Billing policy contract"
target csharp "BillingPolicy"

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

Generates:

```csharp
using Xunit;

public class BillingPolicyTests
{
    [Fact]
    public void testFlagsEnterpriseUsageBeforeCharging()
    {
        var input = new Dictionary<string, object>
        {
            { "account", new Dictionary<string, object> { { "plan", "team" }, { "yearsActive", 1 } } },
            { "usage", new Dictionary<string, object> { { "projects", 91 }, { "seats", 42 } } }
        };
        var result = BillingPolicy.quoteSubscription(input);
        Assert.Equal("enterprise", result["tier"]);
        Assert.Equal(null, result["monthlyUsd"]);
        Assert.Equal(true, result["requiresReview"]);
        Assert.Equal("seat_count", result["reason"]);
    }
}
```

## Limitations

- Generated code uses `Dictionary<string, object>` and `List<object>` for collections; you may want to use typed alternatives in production
- Nested objects in expected values use dictionary indexing (`result["key"]`) rather than property accessors
- The emitter assumes static method calls on the target class