import { describe, expect, it } from "vitest";
import {
  GRAMS_PER_JIN,
  lineTotalValue,
  pricePerPackage,
  sumLineTotalValues,
} from "@/lib/teaPricing";
import type { Asset } from "@/types/Asset";

const baseAsset = (overrides: Partial<Asset> = {}): Asset => ({
  id: "1",
  name: "Test Tea",
  genre: "Oolong",
  ...overrides,
});

describe("teaPricing", () => {
  it("uses 600g per 斤", () => {
    expect(GRAMS_PER_JIN).toBe(600);
  });

  it("computes price per package from 斤 price and package weight", () => {
    // 150g package, 1200 per 斤 → (150/600)*1200 = 300
    expect(pricePerPackage(1200, 150)).toBe(300);
    expect(pricePerPackage(1200, 75)).toBe(150);
  });

  it("computes line total as price per package × packages", () => {
    const asset = baseAsset({
      price: 1200,
      weight: 150,
      quantity: 3,
    });
    expect(lineTotalValue(asset)).toBe(900);
  });

  it("sums line totals across assets", () => {
    const assets = [
      baseAsset({ price: 1200, weight: 150, quantity: 2 }),
      baseAsset({ id: "2", price: 600, weight: 75, quantity: 4 }),
    ];
    // 300*2 + 75*4 = 600 + 300 = 900
    expect(sumLineTotalValues(assets)).toBe(900);
  });
});
