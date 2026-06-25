require "billing_policy"

RSpec.describe "Billing policy contract" do
  # Source: tests/fixtures/valid_billing_policy.tdd:11
  it "grandfathers loyal customers onto the pro cap" do
    result = quoteSubscription(account: { plan: "legacy", yearsActive: 7 }, usage: { projects: 18, seats: 4 })
    expect(result).to eq({ tier: "pro", monthlyUsd: 49, requiresReview: false })
  end
  # Source: tests/fixtures/valid_billing_policy.tdd:25
  it "flags enterprise usage before charging" do
    result = quoteSubscription(account: { plan: "team", yearsActive: 1 }, usage: { projects: 91, seats: 42 })
    expect(result).to eq({ tier: "enterprise", monthlyUsd: nil, requiresReview: true, reason: "seat_count" })
  end
end
