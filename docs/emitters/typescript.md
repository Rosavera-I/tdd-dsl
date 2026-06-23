# TypeScript Emitter (Vitest)

Generates idiomatic **Vitest** test files from TDD DSL contracts.

---

## Framework Overview

| Attribute | Value |
|-----------|-------|
| **Framework** | [Vitest](https://vitest.dev/) |
| **Minimum Version** | 0.25+ recommended |
| **Test Discovery** | `npx vitest run` or `vitest run` |
| **Assertion Style** | `expect(value).toEqual(expected)` |

---

## Target Declaration

```text
target typescript "module-name"
```

The module name is used for imports:
- Simple name: `calculator` → `import { ... } from "calculator";`
- Scoped: `@my-org/calculator` → `import { ... } from "@my-org/calculator";`

Note: Vitest uses camelCase or kebab-case conventions for module names.

---

## Generated Test Structure

### Minimal Example

**Input (.tdd):**
```text
suite "Calculator"
target typescript "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5
```

**Output (.test.ts):**
```typescript
import { describe, expect, test } from "vitest";
import { add } from "calculator";

describe("Calculator", () => {
  test("adds two numbers", () => {
    const result = add({"a": 2, "b": 3});
    expect(result).toEqual(5);
  });
});
```

### Complex Example

**Input (.tdd):**
```text
suite "User service"
target typescript "user-service"

case "creates a new user":
  given input:
    {"name": "Alice", "email": "alice@example.com"}
  when call "createUser"
  then equals:
    {"id": 1, "name": "Alice", "email": "alice@example.com", "active": true}
```

**Output (.test.ts):**
```typescript
import { describe, expect, test } from "vitest";
import { createUser } from "user-service";

describe("User service", () => {
  test("creates a new user", () => {
    const result = createUser({"name": "Alice", "email": "alice@example.com"});
    expect(result).toEqual({
      "id": 1,
      "name": "Alice",
      "email": "alice@example.com",
      "active": true
    });
  });
});
```

### Multiple Cases

**Input (.tdd):**
```text
suite "Calculator"
target typescript "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5

case "subtracts numbers":
  given input:
    {"a": 5, "b": 3}
  when call "subtract"
  then equals:
    2
```

**Output (.test.ts):**
```typescript
import { describe, expect, test } from "vitest";
import { add, subtract } from "calculator";

describe("Calculator", () => {
  test("adds two numbers", () => {
    const result = add({"a": 2, "b": 3});
    expect(result).toEqual(5);
  });

  test("subtracts numbers", () => {
    const result = subtract({"a": 5, "b": 3});
    expect(result).toEqual(2);
  });
});
```

---

## Naming Conventions

### Import Names

Function names from `when call` are used directly as imports and must be valid TypeScript identifiers:

| Call Name | Import Name | Notes |
|-----------|-------------|-------|
| `add` | `add` | ✅ Valid |
| `createUser` | `createUser` | ✅ camelCase valid |
| `fetch-data` | Error | ❌ kebab-case not valid for imports |
| `class` | Error | ❌ Reserved keyword |

### String Literals

Vitest test names preserve the exact `.tdd` case name as a string literal.

---

## Import Deduplication

If multiple cases call the same function, the emitter deduplicates imports:

```typescript
// Multiple cases using "add" - imported once
import { add } from "calculator";

// Multiple cases using "add" and "subtract" - both imported
import { add, subtract } from "calculator";
```

---

## Running Tests

### With npx (recommended)

```bash
npx vitest run test-calculator.test.ts
```

### With installed Vitest

```bash
vitest run
```

### Watch Mode

```bash
npx vitest
```

### Using the Runner

```bash
PYTHONPATH=src python -m tdd_dsl run --target typescript --cwd ./my-project calculator.tdd
```

The runner:
1. Generates a temporary test file
2. Runs `npx vitest run` in the specified working directory
3. Returns the test output

---

## Configuration

### vitest.config.ts

Recommended configuration for TDD DSL generated tests:

```typescript
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['**/*.test.ts'],
  },
})
```

### TypeScript Configuration

Ensure your `tsconfig.json` allows importing from the module paths:

```json
{
  "compilerOptions": {
    "module": "ESNext",
    "moduleResolution": "bundler",
    "target": "ES2020"
  }
}
```

---

## Assertions & Matchers

The TypeScript emitter uses Vitest's `expect` API:

### .toEqual()

```typescript
expect(result).toEqual(expected);
```

Deep equality comparison for objects, arrays, and primitives.

### Output on Failure

```
AssertionError: expected { id: 2, …(2) } to deeply equal { id: 1, …(2) }

- Expected
+ Received

  Object {
-   "id": 1,
+   "id": 2,
    "name": "Alice",
  }
```

### Available Matchers

While the emitter only uses `.toEqual()`, Vitest provides many matchers you can add manually:

```typescript
expect(result).toBe(expected);           // Strict equality (same reference)
expect(result).toEqual(expected);        // Deep equality
expect(result).toBeNull();               // null check
expect(result).toBeDefined();            // not undefined
expect(result).toBeTruthy();             // truthy check
expect(result).toContain(item);          // array/string contains
expect(result).toMatch(pattern);         // regex match
expect(fn).toThrow();                    // exception assertion
```

---

## JSON Handling

The emitter converts JSON keys to valid JavaScript object shorthand when possible:

**Input:**
```json
{"userId": 123, "userName": "Alice"}
```

**Output:**
```typescript
{userId: 123, userName: "Alice"}
```

This produces cleaner TypeScript code while maintaining the same values.

---

## Limitations

1. **Single object input**: The entire `given input` is passed as a single argument, not destructured.

2. **Return value only**: Only supports checking return values, not side effects or thrown exceptions.

3. **No async/await**: Synchronous tests only. For async functions, manually wrap the generated code:
   ```typescript
   test("async case", async () => {
     const result = await fetchData({"id": 1});
     expect(result).toEqual({...});
   });
   ```

---

## Integration Example

Suppose you have a TypeScript module `calculator.ts`:

```typescript
export function add(input: { a: number; b: number }): number {
  return input.a + input.b;
}
```

And a contract `calculator.tdd`:

```text
suite "Calculator"
target typescript "./calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5
```

Emit and run:

```bash
PYTHONPATH=src python -m tdd_dsl emit --target typescript calculator.tdd > calculator.test.ts
npx vitest run calculator.test.ts
```

Or use the runner directly:

```bash
PYTHONPATH=src python -m tdd_dsl run --target typescript --cwd . calculator.tdd
```

---

## See Also

- [Vitest documentation](https://vitest.dev/guide/)
- [Vitest API reference](https://vitest.dev/api/)
