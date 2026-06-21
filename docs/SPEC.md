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
suite "Calculator"
target python "calculator"

case "adds two numbers":
  given input:
    {"a": 2, "b": 3}
  when call "add"
  then equals:
    5
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
