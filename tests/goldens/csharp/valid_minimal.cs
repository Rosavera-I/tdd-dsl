using Xunit;

public class CalculatorTests
{

    // Source: tests/fixtures/valid_minimal.tdd:10
    [Fact]
    public void testAddsTwoNumbers()
    {
        // Input: {'a': 2, 'b': 3}
        var input = new Dictionary<string, object> { { "a", 2 }, { "b", 3 } };
        var result = Calculator.add(input);
        Assert.Equal(5, result);
    }

}