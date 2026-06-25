package billingpolicy

import (
    "reflect"
    "testing"
)

// Source: tests/fixtures/valid_billing_policy.tdd:11
func TestGrandfathersLoyalCustomersOntoTheProCap(t *testing.T) {
    input := map[string]interface{}{"account": map[string]interface{}{"plan": "legacy", "yearsActive": 7}, "usage": map[string]interface{}{"projects": 18, "seats": 4}}
    result := quoteSubscription(input)

    expected := map[string]interface{}{"tier": "pro", "monthlyUsd": 49, "requiresReview": false}
    if !reflect.DeepEqual(result, expected) {
        t.Errorf("expected %v, got %v", expected, result)
    }
}

// Source: tests/fixtures/valid_billing_policy.tdd:25
func TestFlagsEnterpriseUsageBeforeCharging(t *testing.T) {
    input := map[string]interface{}{"account": map[string]interface{}{"plan": "team", "yearsActive": 1}, "usage": map[string]interface{}{"projects": 91, "seats": 42}}
    result := quoteSubscription(input)

    expected := map[string]interface{}{"tier": "enterprise", "monthlyUsd": nil, "requiresReview": true, "reason": "seat_count"}
    if !reflect.DeepEqual(result, expected) {
        t.Errorf("expected %v, got %v", expected, result)
    }
}
