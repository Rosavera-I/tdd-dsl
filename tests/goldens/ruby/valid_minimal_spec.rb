require "calculator"

RSpec.describe "Calculator" do
  # Source: tests/fixtures/valid_minimal.tdd:12
  it "adds two numbers" do
    result = add(a: 2, b: 3)
    expect(result).to eq(5)
  end
end
