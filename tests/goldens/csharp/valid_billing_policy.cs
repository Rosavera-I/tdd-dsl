using System.Collections.Generic;
using Xunit;

public class BillingpolicyTests
{

    // Source: tests/fixtures/valid_billing_policy.tdd:11
    [Fact]
    public void testGrandfathersLoyalCustomersOntoTheProCap()
    {
        // Input: {'account': {'plan': 'legacy', 'yearsActive': 7}, 'usage'...
        var input = new Dictionary<string, object> { { "account", new Dictionary<string, object> { { "plan", "legacy" }, { "yearsActive", 7 } } }, { "usage", new Dictionary<string, object> { { "projects", 18 }, { "seats", 4 } } } };
        var result = BillingPolicy.quoteSubscription(input);
        // Expected: {'tier': 'pro', 'monthlyUsd': 49, 'requiresReview': False}
        Assert.Equal("pro", result["tier"]);
        Assert.Equal(49, result["monthlyUsd"]);
        Assert.Equal(false, result["requiresReview"]);
    }

    // Source: tests/fixtures/valid_billing_policy.tdd:25
    [Fact]
    public void testFlagsEnterpriseUsageBeforeCharging()
    {
        // Input: {'account': {'plan': 'team', 'yearsActive': 1}, 'usage': ...
        var input = new Dictionary<string, object> { { "account", new Dictionary<string, object> { { "plan", "team" }, { "yearsActive", 1 } } }, { "usage", new Dictionary<string, object> { { "projects", 91 }, { "seats", 42 } } } };
        var result = BillingPolicy.quoteSubscription(input);
        // Expected: {'tier': 'enterprise', 'monthlyUsd': None, 'requiresRevie...
        Assert.Equal("enterprise", result["tier"]);
        Assert.Equal(null, result["monthlyUsd"]);
        Assert.Equal(true, result["requiresReview"]);
        Assert.Equal("seat_count", result["reason"]);
    }

}