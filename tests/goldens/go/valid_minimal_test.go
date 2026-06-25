package calculator

import (
    "reflect"
    "testing"
)

// Source: tests/fixtures/valid_minimal.tdd:12
func TestAddsTwoNumbers(t *testing.T) {
    input := map[string]interface{}{"a": 2, "b": 3}
    result := add(input)

    expected := 5
    if !reflect.DeepEqual(result, expected) {
        t.Errorf("expected %v, got %v", expected, result)
    }
}
