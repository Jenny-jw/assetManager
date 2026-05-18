type Producer = {
  name: string;
  factory?: string;
  location?: string;
};

export type AssetBase = {
  name: string;
  origin?: string;
  genre?: string;
  roast_level?: number;
  harvest_time?: number;
  weight?: number;
  quantity?: number;
  score?: number;
  comment?: string;
  producer?: Producer;
};

export type Asset = AssetBase & {
  id: string;
};

export type CreateAssetType = AssetBase;

export type UpdateAssetType = Partial<AssetBase>;
