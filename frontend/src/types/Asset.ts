/**
 * Tea inventory fields (API names kept for compatibility).
 *
 * | API field   | UI label              | Meaning                          |
 * |-------------|-----------------------|----------------------------------|
 * | `price`     | Price per 斤          | TWD (or unit) per 600g (1 斤)    |
 * | `weight`    | Weight per package    | Grams per package: 75 or 150 only |
 * | `quantity`  | Number of packages    | Count of packages in stock       |
 */
export type AssetBase = {
  name: string;
  origin?: string;
  genre?: string;
  roast_level?: number;
  harvest_time?: number;
  /** Price per 斤 */
  price?: number;
  /** Grams per package (75 or 150) */
  weight?: number;
  /** Number of packages in stock */
  quantity?: number;
  score?: number;
  comment?: string;
  producer?: string;
};

export type Asset = AssetBase & {
  id: string;
};

export type CreateAssetType = AssetBase;

/**
 * PATCH body. Omitted keys stay unchanged; `null` clears a nullable field
 * (same contract as backend `StockUpdate`). Do not use `Partial<AssetBase>`:
 * that only allows `undefined`, not `null`.
 */
export type UpdateAssetType = {
  [K in keyof AssetBase]?: Exclude<AssetBase[K], undefined> | null;
};