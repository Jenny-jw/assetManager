import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { getProfitSummary } from "../services/analyticsServices";
import type { ProfitSummary as ProfitSummaryData } from "../types/Profit";

const EMPTY_PROFIT: ProfitSummaryData = {
  total_retail_value: 0,
  total_cost_value: 0,
  unrealized_profit: 0,
  priced_assets: 0,
  costed_assets: 0,
  complete_assets: 0,
  uncosted_assets: 0,
  by_origin: {},
  by_genre: {},
  lines: [],
};

const ProfitSummary = () => {
  const { t } = useTranslation();
  const [summary, setSummary] = useState<ProfitSummaryData>(EMPTY_PROFIT);

  useEffect(() => {
    let cancelled = false;
    getProfitSummary()
      .then((data) => {
        if (!cancelled) setSummary(data);
      })
      .catch((error) => {
        console.error("Failed to load profit summary:", error);
        if (!cancelled) setSummary(EMPTY_PROFIT);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500 h-full">
      <h2 className="font-semibold mb-3">{t("widgets.profit")}</h2>
      <p className="text-sm">{t("widgets.retailValue")}</p>
      <p className="text-2xl font-bold">
        {summary.total_retail_value.toLocaleString()}
      </p>
      <p className="text-sm mt-3">{t("widgets.costValue")}</p>
      <p className="text-xl font-semibold">
        {summary.total_cost_value.toLocaleString()}
      </p>
      <p className="text-sm mt-3">{t("widgets.unrealizedProfit")}</p>
      <p className="text-xl font-semibold">
        {summary.unrealized_profit.toLocaleString()}
      </p>
      {summary.uncosted_assets > 0 && (
        <p className="text-xs text-gray-400 mt-3">
          {t("widgets.uncostedHint", { missing: summary.uncosted_assets })}
        </p>
      )}
    </div>
  );
};

export default ProfitSummary;