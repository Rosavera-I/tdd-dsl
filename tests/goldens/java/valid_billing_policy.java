import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.assertEquals;

import com.example.BillingPolicy;

public class BillingpolicyTest {

    // Source: tests/fixtures/valid_billing_policy.tdd:6
    @Test
    @DisplayName("grandfathers loyal customers onto the pro cap")
    public void testGrandfathersLoyalCustomersOntoTheProCap() {
        // Input: {'account': {'plan': 'legacy', 'yearsActive': 7}, 'usage'...
        var input = java.util.Map.of("account", java.util.Map.of("plan", "legacy", "yearsActive", 7), "usage", java.util.Map.of("projects", 18, "seats", 4));
        var result = BillingPolicy.quoteSubscription(input);
        // Expected: {'tier': 'pro', 'monthlyUsd': 49, 'requiresReview': False}
        assertEquals("pro", result.getTier());
        assertEquals(49, result.getMonthlyusd());
        assertEquals(false, result.getRequiresreview());
    }

    // Source: tests/fixtures/valid_billing_policy.tdd:20
    @Test
    @DisplayName("flags enterprise usage before charging")
    public void testFlagsEnterpriseUsageBeforeCharging() {
        // Input: {'account': {'plan': 'team', 'yearsActive': 1}, 'usage': ...
        var input = java.util.Map.of("account", java.util.Map.of("plan", "team", "yearsActive", 1), "usage", java.util.Map.of("projects", 91, "seats", 42));
        var result = BillingPolicy.quoteSubscription(input);
        // Expected: {'tier': 'enterprise', 'monthlyUsd': None, 'requiresRevie...
        assertEquals("enterprise", result.getTier());
        assertEquals(null, result.getMonthlyusd());
        assertEquals(true, result.getRequiresreview());
        assertEquals("seat_count", result.getReason());
    }

}