import type { Asset } from "../types/Asset";

/** 1 斤 = 600 克 */
export const GRAMS_PER_JIN = 600;

/** Admin-selectable grams per package (API field: `weight`) */
export const PACKAGE_WEIGHT_OPTIONS = [75, 150] as const;

export type PackageWeightGrams = (typeof PACKAGE_WEIGHT_OPTIONS)[number];

export function isPackageWeightGrams(value: number): value is PackageWeightGrams {
  return PACKAGE_WEIGHT_OPTIONS.includes(value as PackageWeightGrams);
}

/**
 * Price for one package.
 * Formula: (weight_g / 600) × price_per_jin
 * API: `price` = 每斤單價, `weight` = 每包克數
 */
export function pricePerPackage(
  pricePerJin: number | undefined,
  weightGrams: number | undefined,
): number | undefined {
  if (pricePerJin == null || weightGrams == null) return undefined;
  return Math.round((weightGrams / GRAMS_PER_JIN) * pricePerJin);
}

/**
 * Inventory line total: price per package × number of packages.
 * API: `quantity` = 包數 (Number of Packages)
 */
export function lineTotalValue(asset: Asset): number | undefined {
  const perPackage = pricePerPackage(asset.price, asset.weight);
  if (perPackage == null || asset.quantity == null) return undefined;
  return perPackage * asset.quantity;
}

export function sumLineTotalValues(assets: Asset[]): number {
  return assets.reduce((sum, asset) => sum + (lineTotalValue(asset) ?? 0), 0);
}

export function formatMoney(value: number | undefined): string {
  if (value == null) return "-";
  return value.toLocaleString();
}
