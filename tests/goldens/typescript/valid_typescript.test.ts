import { describe, expect, test } from "vitest";
import { add } from "calculator";

describe("Calculator", () => {
  test("adds two numbers", () => {
    const result = add({
      a: 2,
      b: 3
    });
    expect(result).toEqual(5);
  });
});
