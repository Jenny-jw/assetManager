import type { Asset } from "./Asset";

export type TeaSortField =
  | "created_at"
  | "name"
  | "genre"
  | "origin"
  | "quantity"
  | "score"
  | "price"
  | "harvest_time";

export type TeaListParams = {
  page?: number;
  limit?: number;
  search?: string;
  genre?: string;
  origin?: string;
  sort_by?: TeaSortField;
  sort_direction?: "asc" | "desc";
};

export type TeaListResponse = {
  data: Asset[];
  page: number;
  limit: number;
  total: number;
};

export type TeaFacets = {
  genres: string[];
  origins: string[];
};
