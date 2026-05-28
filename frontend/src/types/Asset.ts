export type AssetBase = {
  name: string;
  origin?: string;
  genre?: string;
  roast_level?: number;
  harvest_time?: number;
  roast_time?: number;
  weight?: number;
  quantity?: number;
  score?: number;
  comment?: string;
  producer?: string;
};

export type Asset = AssetBase & {
  id: string;
};

export type CreateAssetType = AssetBase;

export type UpdateAssetType = Partial<AssetBase>;
