import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.assertEquals;

import Calculator;

public class CalculatorTest {

    // Source: tests/fixtures/valid_minimal.tdd:6
    @Test
    @DisplayName("adds two numbers")
    public void testAddsTwoNumbers() {
        // Input: {'a': 2, 'b': 3}
        var input = java.util.Map.of("a", 2, "b", 3);
        var result = Calculator.add(input);
        assertEquals(5, result);
    }

}