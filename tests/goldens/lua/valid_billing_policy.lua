local subject = require("billing_policy")

describe("Billing policy contract", function()
  -- Source: tests/fixtures/valid_billing_policy.tdd:11
  it("grandfathers loyal customers onto the pro cap", function()
    local result = subject.quoteSubscription({ account = { plan = "legacy", yearsActive = 7 }, usage = { projects = 18, seats = 4 } })
    assert.are.same("pro", result.tier)
    assert.are.same(49, result.monthlyUsd)
    assert.are.same(false, result.requiresReview)
  end)
  -- Source: tests/fixtures/valid_billing_policy.tdd:25
  it("flags enterprise usage before charging", function()
    local result = subject.quoteSubscription({ account = { plan = "team", yearsActive = 1 }, usage = { projects = 91, seats = 42 } })
    assert.are.same("enterprise", result.tier)
    assert.are.same(nil, result.monthlyUsd)
    assert.are.same(true, result.requiresReview)
    assert.are.same("seat_count", result.reason)
  end)
end)
