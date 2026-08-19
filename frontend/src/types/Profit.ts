export type ProfitLine = {
  stock_id: string;
  name: string;
  quantity: number;
  retail_value: number;
  cost_value: number;
  profit: number | null;
  priced: boolean;
  costed: boolean;
};

export type ProfitSummary = {
  total_retail_value: number;
  total_cost_value: number;
  unrealized_profit: number;
  priced_assets: number;
  costed_assets: number;
  complete_assets: number;
  uncosted_assets: number;
  by_origin: Record<string, number>;
  by_genre: Record<string, number>;
  lines: ProfitLine[];
};