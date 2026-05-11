export type AssetBase = {
  name: string;
  origin?: string;
  genre?: string;
  roastLevel?: number;
  harvestTime?: number;
  weight?: number;
  quantity?: number;
};

export type Asset = AssetBase & {
  id: string;
};

export type CreateAssetType = AssetBase;

export type UpdateAssetType = Partial<AssetBase>;
