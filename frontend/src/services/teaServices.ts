import api from "../lib/axios";
import type { Asset } from "../types/Asset";
import type {
  TeaFacets,
  TeaListParams,
  TeaListResponse,
  TeaSummary,
} from "../types/TeaList";

export const DEFAULT_TEA_PAGE_SIZE = 20;
export const DASHBOARD_RECENT_LIMIT = 3;

export const listTeas = async (
  params: TeaListParams = {},
): Promise<TeaListResponse> => {
  const response = await api.get<TeaListResponse>("/tea", {
    params: {
      page: params.page ?? 1,
      limit: params.limit ?? DEFAULT_TEA_PAGE_SIZE,
      sort_by: params.sort_by ?? "score",
      sort_direction: params.sort_direction ?? "desc",
      ...(params.search ? { search: params.search } : {}),
      ...(params.genre ? { genre: params.genre } : {}),
      ...(params.origin ? { origin: params.origin } : {}),
    },
  });
  return response.data;
};

export const getTeaSummary = async (): Promise<TeaSummary> => {
  const response = await api.get<TeaSummary>("/tea/summary");
  return response.data;
};

export const extractTeaFacets = (teas: Asset[]): TeaFacets => {
  const genres = [
    ...new Set(teas.map((tea) => tea.genre).filter((value) => Boolean(value))),
  ].sort() as string[];
  const origins = [
    ...new Set(teas.map((tea) => tea.origin).filter((value) => Boolean(value))),
  ].sort() as string[];

  return { genres, origins };
};
