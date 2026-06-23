import XCTest
@testable import calculator

final class CalculatorTests: XCTestCase {

    // Source: tests/fixtures/valid_minimal.tdd:12
    func testAddsTwoNumbers() throws {
        // Input: {'a': 2, 'b': 3}
        let input = Add(a: 2, b: 3)
        let result = add(input: input)
        XCTAssertEqual(result, 5)
    }

}
