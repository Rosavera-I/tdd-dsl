package calculator

import "core:testing"

// Source: tests/fixtures/valid_minimal.tdd:12
@(test)
test_adds_two_numbers :: proc(t: ^testing.T) {
    // Input: {'a': 2, 'b': 3}
    input := {a = 2, b = 3}
    result := add(input)

    testing.expect_value(t, result, 5)
}
