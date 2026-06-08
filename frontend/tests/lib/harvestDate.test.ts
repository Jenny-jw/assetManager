import { describe, expect, it } from "vitest";
import {
  dateInputToHarvestInt,
  harvestIntToDateInput,
} from "@/lib/harvestDate";

describe("harvestDate", () => {
  it("converts stored YYYYMMDD to date input value", () => {
    expect(harvestIntToDateInput(20260517)).toBe("2026-05-17");
    expect(harvestIntToDateInput("20260517")).toBe("2026-05-17");
    expect(harvestIntToDateInput("")).toBe("");
  });

  it("converts date input value to stored YYYYMMDD", () => {
    expect(dateInputToHarvestInt("2026-05-17")).toBe("20260517");
    expect(dateInputToHarvestInt("")).toBe("");
  });
});
