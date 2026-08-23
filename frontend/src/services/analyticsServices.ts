import api from "../lib/axios";
import type { ProfitSummary } from "../types/Profit";

export const getProfitSummary = async (): Promise<ProfitSummary> => {
  const response = await api.get<ProfitSummary>("/analytics/profit");
  return response.data;
};