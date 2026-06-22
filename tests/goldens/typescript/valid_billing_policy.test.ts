import { describe, expect, test } from "vitest";
import { quoteSubscription } from "billing-policy";

describe("Billing policy contract", () => {
  test("grandfathers loyal customers onto the pro cap", () => {
    const result = quoteSubscription({
      account: {
        plan: "legacy",
        yearsActive: 7
      },
      usage: {
        projects: 18,
        seats: 4
      }
    });
    expect(result).toEqual({
      tier: "pro",
      monthlyUsd: 49,
      requiresReview: false
    });
  });
  test("flags enterprise usage before charging", () => {
    const result = quoteSubscription({
      account: {
        plan: "team",
        yearsActive: 1
      },
      usage: {
        projects: 91,
        seats: 42
      }
    });
    expect(result).toEqual({
      tier: "enterprise",
      monthlyUsd: null,
      requiresReview: true,
      reason: "seat_count"
    });
  });
});
