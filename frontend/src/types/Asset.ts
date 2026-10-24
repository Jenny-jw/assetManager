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
  genre: string;
  origin?: string;
  /** Roast scale: 0 light, 100 heavy */
  roast_level?: number;
  harvest_time?: number;
  /** Price per 斤 */
  price?: number;
  /** Grams per package (75 or 150) */
  weight: 75 | 150;
  /** Number of packages in stock */
  quantity: number;
  /** Quality score from 0 to 100 */
  score?: number;
  comment?: string;
  producer?: string;
};

export type Asset = AssetBase & {
  id: string;
  owner_id: string | null;
  created_at: string;
  updated_at: string | null;
};

export type CreateAssetType = AssetBase;

export type UpdateAssetType = Partial<AssetBase>;