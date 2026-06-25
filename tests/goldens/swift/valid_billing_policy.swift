import XCTest
@testable import BillingPolicy

final class BillingPolicyContractTests: XCTestCase {

    // Source: tests/fixtures/valid_billing_policy.tdd:11
    func testGrandfathersLoyalCustomersOntoTheProCap() throws {
        // Input: {'account': {'plan': 'legacy', 'yearsActive': 7}, 'usage'...
        let input = Quotesubscription(account: ["plan": "legacy", "yearsActive": 7], usage: ["projects": 18, "seats": 4])
        let result = quotesubscription(input: input)
        // Expected: {'tier': 'pro', 'monthlyUsd': 49, 'requiresReview': False}
        XCTAssertEqual(result.tier, "pro")
        XCTAssertEqual(result.monthlyusd, 49)
        XCTAssertEqual(result.requiresreview, false)
    }

    // Source: tests/fixtures/valid_billing_policy.tdd:25
    func testFlagsEnterpriseUsageBeforeCharging() throws {
        // Input: {'account': {'plan': 'team', 'yearsActive': 1}, 'usage': ...
        let input = Quotesubscription(account: ["plan": "team", "yearsActive": 1], usage: ["projects": 91, "seats": 42])
        let result = quotesubscription(input: input)
        // Expected: {'tier': 'enterprise', 'monthlyUsd': None, 'requiresRevie...
        XCTAssertEqual(result.tier, "enterprise")
        XCTAssertEqual(result.monthlyusd, nil)
        XCTAssertEqual(result.requiresreview, true)
        XCTAssertEqual(result.reason, "seat_count")
    }

}
