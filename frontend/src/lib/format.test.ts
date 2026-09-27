import { describe, expect, it } from "vitest";
import { discountLabel, formatINR, nutritionText } from "./format";

describe("format", () => {
  it("does not invent a price", () => {
    expect(formatINR(null)).toBe("Price pending");
  });
  it("formats rupees", () => {
    expect(formatINR("149.00")).toContain("149");
  });
  it("leaves nutrition blank", () => {
    expect(nutritionText(null, "g")).toBe("Pending");
  });
  it("hides discount without both prices", () => {
    expect(discountLabel(null, "199.00")).toBeNull();
  });
});
