import api from "../lib/axios";
import type { Asset, CreateAssetType, UpdateAssetType } from "../types/Asset";
import type {
  TeaFacets,
  TeaListParams,
  TeaListResponse,
  TeaSummary,
} from "../types/TeaList";

export const DEFAULT_STOCK_PAGE_SIZE = 20;
export const DASHBOARD_RECENT_LIMIT = 3;

type StockApiRow = {
  id: string;
  name: string;
  origin?: string | null;
  genre?: string | null;
  producer?: string | null;
  roast_level?: number | null;
  harvest_time?: number | null;
  weight_grams?: number | null;
  price_per_jin?: number | null;
  quantity?: number;
  score?: number | null;
  comment?: string | null;
};

type StockListApiResponse = {
  data: StockApiRow[];
  page: number;
  limit: number;
  total: number;
};

const toApiSort = (sortBy?: TeaListParams["sort_by"]): string | undefined => {
  if (sortBy === "price") {
    return "price_per_jin";
  }
  return sortBy;
};

export const fromStockRow = (row: StockApiRow): Asset => ({
  id: row.id,
  name: row.name,
  origin: row.origin ?? undefined,
  genre: row.genre ?? undefined,
  producer: row.producer ?? undefined,
  roast_level: row.roast_level ?? undefined,
  harvest_time: row.harvest_time ?? undefined,
  weight: row.weight_grams ?? undefined,
  price: row.price_per_jin ?? undefined,
  quantity: row.quantity,
  score: row.score ?? undefined,
  comment: row.comment ?? undefined,
});

export const toStockWrite = (payload: CreateAssetType | UpdateAssetType) => {
  const { weight, price, ...rest } = payload;
  return {
    ...rest,
    ...(weight !== undefined ? { weight_grams: weight } : {}),
    ...(price !== undefined ? { price_per_jin: price } : {}),
  };
};

export const listStocks = async (
  params: TeaListParams = {},
): Promise<TeaListResponse> => {
  const response = await api.get<StockListApiResponse>("/stock", {
    params: {
      page: params.page ?? 1,
      limit: params.limit ?? DEFAULT_STOCK_PAGE_SIZE,
      sort_by: toApiSort(params.sort_by) ?? "score",
      sort_direction: params.sort_direction ?? "desc",
      ...(params.search ? { search: params.search } : {}),
      ...(params.genre ? { genre: params.genre } : {}),
      ...(params.origin ? { origin: params.origin } : {}),
    },
  });
  return {
    ...response.data,
    data: response.data.data.map(fromStockRow),
  };
};

export const getStockSummary = async (): Promise<TeaSummary> => {
  const response = await api.get<TeaSummary>("/stock/summary");
  return response.data;
};

export const getStock = async (id: string): Promise<Asset> => {
  const response = await api.get<StockApiRow>(`/stock/${id}`);
  return fromStockRow(response.data);
};

export const createStock = async (payload: CreateAssetType): Promise<Asset> => {
  const response = await api.post<StockApiRow>("/stock", toStockWrite(payload));
  return fromStockRow(response.data);
};

export const updateStock = async (
  id: string,
  payload: UpdateAssetType,
): Promise<Asset> => {
  const response = await api.patch<StockApiRow>(
    `/stock/${id}`,
    toStockWrite(payload),
  );
  return fromStockRow(response.data);
};

export const deleteStock = async (id: string): Promise<void> => {
  await api.delete(`/stock/${id}`);
};

export const extractStockFacets = (stocks: Asset[]): TeaFacets => {
  const genres = [
    ...new Set(
      stocks.map((stock) => stock.genre).filter((value) => Boolean(value)),
    ),
  ].sort() as string[];
  const origins = [
    ...new Set(
      stocks.map((stock) => stock.origin).filter((value) => Boolean(value)),
    ),
  ].sort() as string[];

  return { genres, origins };
};
