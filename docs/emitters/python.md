# Python Emitter (pytest)

Generates idiomatic **pytest** test files from TDD DSL contracts.

---

## Framework Overview

| Attribute | Value |
|-----------|-------|
| **Framework** | [pytest](https://pytest.org/) |
| **Minimum Version** | 6.0+ recommended |
| **Test Discovery** | `pytest` or `python -m pytest` |
| **Assertion Style** | Python `assert` (pytest magic for rich diffs) |

---

## Target Declaration

```text
target python "module_name"
```

The module name is used for imports:
- Simple name: `calculator` → `import calculator`
- Dotted: `my_pkg.calculator` → `import my_pkg.calculator`

---

## Generated Test Structure

### Minimal Example

**Input (.tdd):**
```text
suite "Calculator"
target python "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5
```

**Output (.py):**
```python
import calculator


def test_adds_two_numbers():
    result = calculator.add(a=2, b=3)
    assert result == 5

```

### Complex Example

**Input (.tdd):**
```text
suite "Billing policy"
target python "billing_policy"

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
      "requires_review": true,
      "reason": "seat_count"
    }
```

**Output (.py):**
```python
import billing_policy


def test_calculates_enterprise_tier():
    input = {
        'account': {'plan': 'team', 'yearsActive': 1},
        'usage': {'projects': 91, 'seats': 42}
    }
    result = billing_policy.quote_subscription(input)
    assert result == {
        'tier': 'enterprise',
        'monthly_usd': None,
        'requires_review': True,
        'reason': 'seat_count'
    }

```

---

## Naming Conventions

### Function Names

Case names are converted to Python function names:

| Case Name | Function Name |
|-----------|---------------|
| `adds two numbers` | `test_adds_two_numbers` |
| `"handles" special chars!` | `test_handles_special_chars` |
| `Edge Case` | `test_edge_case` |
| `123 numeric start` | `test_123_numeric_start` |
| `class` (keyword) | `test_class_case` |

If duplicate names would be generated, a numeric suffix is added:
- `test_case` → `test_case_2` → `test_case_3`

---

## Running Tests

### Basic

```bash
pytest test_calculator.py
```

### With Verbose Output

```bash
pytest -v test_calculator.py
```

### Match Specific Test

```bash
pytest -k "test_adds" test_calculator.py
```

### Using the Runner

```bash
PYTHONPATH=src python -m tdd_dsl run --target python calculator.tdd
```

The runner:
1. Generates a temporary test file
2. Prepends your working directory to `PYTHONPATH`
3. Runs pytest
4. Maps failures back to the original `.tdd` source line

---

## Configuration Options

### Environment Variables

| Variable | Description |
|----------|-------------|
| `TDD_DSL_UPDATE_GOLDENS=1` | Refresh expected output fixtures |

### No pytest.ini Required

The generated tests use vanilla `assert` statements and don't require additional pytest configuration. However, you can add a `pytest.ini` or `pyproject.toml` for your project:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
```

---

## Assertions & Matchers

The Python emitter uses Python's built-in `assert` statement. pytest provides rich diffs on failure:

### Equality Assertion

```python
assert result == expected
```

### Output on Failure

```
E       AssertionError: assert {'a': 1} == {'a': 2}
E
E       Differing items:
E       {'a': 1} != {'a': 2}
E
E       Full diff:
E       - {'a': 2}
E       ?       ^
E       + {'a': 1}
E       ?       ^
```

### Source Map Comments

When using the runner, generated files include comments mapping back to the source:

```python
# tdd-dsl: source=calculator.tdd line=5 case='adds two numbers'
def test_adds_two_numbers():
    ...
```

---

## Limitations

1. **Dict input as kwargs**: If the `given input` is a dict with all string keys that are valid Python identifiers, the emitter uses keyword argument syntax (`fn(a=1, b=2)`). Otherwise, it passes the dict as a single argument.

2. **Single assertion per case**: Each case generates one `assert` statement. For complex assertions (exceptions, custom matchers), you'll need to manually edit the generated code or use multiple cases.

3. **Return value assertion only**: The current emitter only supports checking return values, not side effects or exceptions.

---

## Integration Example

Suppose you have a Python module `calculator.py`:

```python
def add(a: int, b: int) -> int:
    return a + b
```

And a contract `calculator.tdd`:

```text
suite "Calculator"
target python "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5

case "handles zero":
  given input:
    {"a": 0, "b": 5}
  when call "add"
  then equals:
    5
```

Emit and run:

```bash
PYTHONPATH=src python -m tdd_dsl emit --target python calculator.tdd > test_calculator.py
pytest test_calculator.py
```

Or use the runner directly:

```bash
PYTHONPATH=src python -m tdd_dsl run --target python calculator.tdd
```

---

## See Also

- [pytest documentation](https://docs.pytest.org/)
- [Python style guide for tests](https://docs.pytest.org/en/latest/explanation/goodpractices.html)
