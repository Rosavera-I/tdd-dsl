# Java Emitter (JUnit 5)

Generates idiomatic **JUnit 5** test classes from TDD DSL contracts.

---

## Framework Overview

| Attribute | Value |
|-----------|-------|
| **Framework** | [JUnit 5](https://junit.org/junit5/) (Jupiter) |
| **Minimum Version** | 5.8+ recommended |
| **Build Tools** | Maven, Gradle, or direct compilation |
| **Test Discovery** | `mvn test`, `gradle test`, or IDE runner |
| **Assertion Style** | `assertEquals(expected, actual)` |

---

## Target Declaration

```text
target java "ClassName"
target java "com.example.package.ClassName"
```

The module is interpreted as:
- Simple name: `BillingPolicy` → class name `BillingPolicyTest`
- Full class path: `com.example.BillingPolicy` → import `com.example.BillingPolicy`

The generated test class name is derived from the simple class name:
- `Calculator` → `CalculatorTest`
- `com.example.BillingPolicy` → `BillingPolicyTest`

---

## Generated Test Structure

### Minimal Example

**Input (.tdd):**
```text
suite "Calculator"
target java "Calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5
```

**Output (.java):**
```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.assertEquals;

import Calculator;

public class CalculatorTest {

    @Test
    @DisplayName("adds two numbers")
    public void testAddsTwoNumbers() {
        // Input: {'a': 2, 'b': 3}
        var input = java.util.Map.of("a", 2, "b", 3);
        var result = Calculator.add(input);
        assertEquals(5, result);
    }

}
```

### Complex Example with Package

**Input (.tdd):**
```text
suite "Billing policy contract"
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

**Output (.java):**
```java
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.assertEquals;

import com.example.BillingPolicy;

public class BillingPolicyTest {

    // Source: billing.tdd:4
    @Test
    @DisplayName("flags enterprise usage before charging")
    public void testFlagsEnterpriseUsageBeforeCharging() {
        // Input: {'account': {'plan': 'team', 'yearsActive': 1}, ...}
        var input = java.util.Map.of(
            "account", java.util.Map.of("plan", "team", "yearsActive", 1),
            "usage", java.util.Map.of("projects", 91, "seats", 42)
        );
        var result = BillingPolicy.quoteSubscription(input);
        // Expected: {'tier': 'enterprise', 'monthlyUsd': None, ...}
        assertEquals("enterprise", result.getTier());
        assertEquals(null, result.getMonthlyUsd());
        assertEquals(true, result.getRequiresReview());
        assertEquals("seat_count", result.getReason());
    }

}
```

---

## Naming Conventions

### Test Method Names

Case names are converted to camelCase method names:

| Case Name | Method Name |
|-----------|-------------|
| `adds two numbers` | `testAddsTwoNumbers` |
| `Handles edge case` | `testHandlesEdgeCase` |
| `123 starts numeric` | `test123StartsNumeric` |
| `class` (keyword) | `testClassTest` |

### Display Names

The original case name is preserved in the `@DisplayName` annotation for readable test reports:

```java
@Test
@DisplayName("adds two numbers")
public void testAddsTwoNumbers() { ... }
```

---

## Assertions for Complex Objects

For expected dict values, the emitter generates individual field assertions:

```java
// Expected: {"tier": "enterprise", "monthlyUsd": null, "requiresReview": true}
assertEquals("enterprise", result.getTier());
assertEquals(null, result.getMonthlyUsd());
assertEquals(true, result.getRequiresReview());
```

This assumes your result object has appropriate getter methods (`getTier()`, `getMonthlyUsd()`, etc.).

For flat values, a single assertion is used:

```java
assertEquals(42, result);
```

---

## Running Tests

### With Maven

```bash
mvn test
```

### With Gradle

```bash
gradle test
```

### Single Test Class

```bash
mvn test -Dtest=CalculatorTest
```

### IDE Support

JUnit 5 tests run directly in:
- IntelliJ IDEA
- Eclipse
- VS Code (with Java extension)

---

## Maven Configuration

### pom.xml Dependencies

```xml
<dependencies>
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>5.10.0</version>
        <scope>test</scope>
    </dependency>
</dependencies>

<build>
    <plugins>
        <plugin>
            <groupId>org.apache.maven.plugins</groupId>
            <artifactId>maven-surefire-plugin</artifactId>
            <version>3.1.2</version>
        </plugin>
    </plugins>
</build>
```

---

## Gradle Configuration

### build.gradle

```groovy
dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.0'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

test {
    useJUnitPlatform()
}
```

---

## Assertions & Matchers

The Java emitter uses JUnit 5's `Assertions` class:

### assertEquals

```java
assertEquals(expected, actual);
assertEquals(expected, actual, "Optional message");
```

### Other Available Assertions

While the emitter uses `assertEquals()`, JUnit 5 provides:

```java
assertTrue(condition);
assertFalse(condition);
assertNull(value);
assertNotNull(value);
assertSame(expected, actual);     // identity equality
assertArrayEquals(expected, actual);
assertThrows(Exception.class, executable);
assertDoesNotThrow(executable);
assertTimeout(Duration.ofMillis(100), executable);
```

---

## Map Literals

The emitter uses `java.util.Map.of()` for dict inputs:

```java
// Simple map
var input = java.util.Map.of("key", "value");

// Nested map
var input = java.util.Map.of(
    "account", java.util.Map.of("plan", "team", "yearsActive", 1),
    "usage", java.util.Map.of("projects", 91, "seats", 42)
);
```

### Map.of() Limitations

`Map.of()` has a 10-entry limit. For larger maps, the emitter will use `java.util.HashMap`:

```java
var input = new java.util.HashMap<String, Object>();
input.put("key1", "value1");
// ... more puts
```

---

## Source Map Comments

When source path is provided, the emitter includes source location comments:

```java
// Source: billing.tdd:4
@Test
@DisplayName("flags enterprise usage before charging")
public void testFlagsEnterpriseUsageBeforeCharging() { ... }
```

---

## Limitations

1. **Getter Assumption**: For dict expected values, the emitter assumes your result object has getters matching the field names (e.g., `getTier()` for `"tier"` field).

2. **Map Input Only**: Dict inputs are always passed as `java.util.Map`, not as typed objects.

3. **Static Method Calls**: The emitter generates static method calls (`ClassName.method()`). For instance methods, you'll need adapter classes.

4. **No null-safe accessor**: The generated code doesn't handle potential null results before calling getters.

---

## Integration Example

Suppose you have a Java class `BillingPolicy.java`:

```java
package com.example;

import java.util.Map;

public class BillingPolicy {
    public static Subscription quoteSubscription(Map<String, Object> input) {
        // Implementation
        return new Subscription("enterprise", null, true, "seat_count");
    }

    public static class Subscription {
        private final String tier;
        private final Integer monthlyUsd;
        private final boolean requiresReview;
        private final String reason;

        public Subscription(String tier, Integer monthlyUsd, boolean requiresReview, String reason) {
            this.tier = tier;
            this.monthlyUsd = monthlyUsd;
            this.requiresReview = requiresReview;
            this.reason = reason;
        }

        public String getTier() { return tier; }
        public Integer getMonthlyUsd() { return monthlyUsd; }
        public boolean getRequiresReview() { return requiresReview; }
        public String getReason() { return reason; }
    }
}
```

And a contract `billing.tdd`:

```text
suite "Billing policy"
target java "com.example.BillingPolicy"

case "quotes enterprise tier":
  given input:
    {"account": {"plan": "team"}, "usage": {"seats": 42}}
  when call "quoteSubscription"
  then equals:
    {"tier": "enterprise", "monthlyUsd": null, "requiresReview": true}
```

Emit and place in your test directory:

```bash
PYTHONPATH=src python -m tdd_dsl emit --target java billing.tdd > src/test/java/com/example/BillingPolicyTest.java
mvn test -Dtest=BillingPolicyTest
```

---

## See Also

- [JUnit 5 User Guide](https://junit.org/junit5/docs/current/user-guide/)
- [JUnit 5 API Documentation](https://junit.org/junit5/docs/current/api/)
