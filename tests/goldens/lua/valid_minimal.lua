local subject = require("calculator")

describe("Calculator", function()
  -- Source: tests/fixtures/valid_minimal.tdd:12
  it("adds two numbers", function()
    local result = subject.add({ a = 2, b = 3 })
    assert.are.same(5, result)
  end)
end)
