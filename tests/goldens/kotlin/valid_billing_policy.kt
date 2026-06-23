package com.example

import org.junit.jupiter.api.Test
import kotlin.test.assertEquals

class BillingpolicyTest {

    // Source: tests/fixtures/valid_billing_policy.tdd:8
    @Test
    fun `grandfathers loyal customers onto the pro cap`() {
        // Input: {'account': {'plan': 'legacy', 'yearsActive': 7}, 'usage'...
        val input = mapOf("account" to mapOf("plan" to "legacy", "yearsActive" to 7), "usage" to mapOf("projects" to 18, "seats" to 4))
        val result = BillingPolicy.quoteSubscription(input)
        // Expected: {'tier': 'pro', 'monthlyUsd': 49, 'requiresReview': False}
        assertEquals("pro", result.tier)
        assertEquals(49, result.monthlyUsd)
        assertEquals(false, result.requiresReview)
    }

    // Source: tests/fixtures/valid_billing_policy.tdd:22
    @Test
    fun `flags enterprise usage before charging`() {
        // Input: {'account': {'plan': 'team', 'yearsActive': 1}, 'usage': ...
        val input = mapOf("account" to mapOf("plan" to "team", "yearsActive" to 1), "usage" to mapOf("projects" to 91, "seats" to 42))
        val result = BillingPolicy.quoteSubscription(input)
        // Expected: {'tier': 'enterprise', 'monthlyUsd': None, 'requiresRevie...
        assertEquals("enterprise", result.tier)
        assertEquals(null, result.monthlyUsd)
        assertEquals(true, result.requiresReview)
        assertEquals("seat_count", result.reason)
    }

}