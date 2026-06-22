# DSL Spec

## Grammar Sketch

```text
document      = suite target* case+
suite         = "suite" quoted
target        = "target" identifier quoted
case          = "case" quoted ":" step+
step          = given-input | when-call | then-equals
given-input   = indent "given input:" json-block
when-call     = indent "when call" quoted
then-equals   = indent "then equals:" json-block
json-block    = one-or-more indented lines parsed as JSON
quoted        = JSON string literal
identifier    = [A-Za-z_][A-Za-z0-9_-]*
```

## Example

```text
suite "Billing policy contract"
target python "billing_policy"
target typescript "billing-policy"

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

## Semantics

- A file must declare exactly one suite before any cases.
- A file must declare at least one target before any cases.
- A case must contain exactly one `given input`, one `when call`, and one `then equals`.
- JSON payloads must parse successfully.
- `given input` may be any JSON value, but emitters can restrict what they support.
- `then equals` may be any JSON value.

## Source Compatibility

The parser should preserve line and column for every diagnostic. Future AST spans can extend this without changing emitted JSON field names.

## Validation Output

`validate` defaults to human-readable diagnostics:

```text
tests/fixtures/invalid_missing_then.tdd:4:1: case 'adds two numbers' requires then equals
```

`validate --json` is reserved for the parsed AST of valid documents.

`validate --format json` is reserved for editor and tool diagnostics. It emits a stable LSP-compatible payload:

```json
{
  "uri": "file:///workspace/tests/fixtures/invalid_missing_then.tdd",
  "diagnostics": [
    {
      "range": {
        "start": {"line": 3, "character": 0},
        "end": {"line": 3, "character": 1}
      },
      "severity": 1,
      "source": "tdd-dsl",
      "message": "case 'adds two numbers' requires then equals"
    }
  ]
}
```

Valid files return the same envelope with an empty `diagnostics` array. Parser diagnostics use one-based line and column values internally. The JSON diagnostics convert those locations to LSP's zero-based `line` and `character` fields.

## CLI Commands

```bash
tdd-dsl validate [--json] [--format text|json] FILE
tdd-dsl emit --target python|typescript|java FILE
tdd-dsl run --target python|typescript [--cwd DIR] FILE
tdd-dsl discover PATTERN [--format text|json]
```

The Python runner writes a temporary generated test file, prepends `--cwd` to
`PYTHONPATH`, and maps generated assertion failures back to the nearest DSL case
line. The TypeScript runner shells out to `npx vitest run` and expects Vitest to
be available in the selected working directory.

## Java Output

The Java emitter generates JUnit 5 tests with idiomatic naming:

```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.assertEquals;

import com.example.BillingPolicy;

public class BillingPolicyTest {

    @Test
    @DisplayName("flags enterprise usage before charging")
    public void testFlagsEnterpriseUsageBeforeCharging() {
        var input = java.util.Map.of(
            "account", java.util.Map.of("plan", "team", "yearsActive", 1),
            "usage", java.util.Map.of("projects", 91, "seats", 42)
        );
        var result = BillingPolicy.quoteSubscription(input);
        assertEquals("enterprise", result.getTier());
        assertEquals(null, result.getMonthlyUsd());
        assertEquals(true, result.getRequiresReview());
        assertEquals("seat_count", result.getReason());
    }
}
```
