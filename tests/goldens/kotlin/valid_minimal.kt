import org.junit.jupiter.api.Test
import kotlin.test.assertEquals

class CalculatorTest {

    // Source: tests/fixtures/valid_minimal.tdd:12
    @Test
    fun `adds two numbers`() {
        // Input: {'a': 2, 'b': 3}
        val input = mapOf("a" to 2, "b" to 3)
        val result = Calculator.add(input)
        assertEquals(5, result)
    }

}