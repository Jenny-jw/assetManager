import { useTranslation } from "react-i18next";
import type { TeaSummary } from "../types/TeaList";

type Props = {
  summary: TeaSummary;
  showTotalValue?: boolean;
};

const Summary = ({ summary, showTotalValue = false }: Props) => {
  const { t } = useTranslation();
  const gridClass = showTotalValue
    ? "grid grid-cols-2 lg:grid-cols-4 gap-4"
    : "grid grid-cols-3 gap-4";

  return (
    <div className={gridClass}>
      <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
        <p className="text-sm">{t("widgets.totalAssets")}</p>
        <p className="text-2xl font-bold">{summary.total_assets}</p>
      </div>
      <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
        <p className="text-sm">{t("widgets.totalPackages")}</p>
        <p className="text-2xl font-bold">{summary.total_packages}</p>
      </div>
      <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
        <p className="text-sm">{t("widgets.totalWeight")}</p>
        <p className="text-2xl font-bold">{summary.total_weight_grams}</p>
        <p className="text-xs text-gray-400 mt-1">{t("widgets.totalWeightHint")}</p>
      </div>
      {showTotalValue && (
        <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
          <p className="text-sm">{t("widgets.totalValue")}</p>
          <p className="text-2xl font-bold">
            {summary.total_value.toLocaleString()}
          </p>
          <p className="text-xs text-gray-400 mt-1">{t("widgets.totalValueHint")}</p>
        </div>
      )}
    </div>
  );
};

export default Summary;
