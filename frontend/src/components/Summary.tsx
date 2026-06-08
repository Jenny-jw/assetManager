import type { TeaSummary } from "../types/TeaList";

type Props = {
  summary: TeaSummary | null;
  isLoading?: boolean;
  showTotalValue?: boolean;
};

const Summary = ({ summary, isLoading = false, showTotalValue = false }: Props) => {
  const display = (value: number | undefined) =>
    isLoading || summary == null ? "—" : value;

  const gridClass = showTotalValue
    ? "grid grid-cols-2 lg:grid-cols-4 gap-4"
    : "grid grid-cols-3 gap-4";

  return (
    <div className={gridClass}>
      <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
        <p className="text-sm">Total Assets</p>
        <p className="text-2xl font-bold">{display(summary?.total_assets)}</p>
      </div>
      <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
        <p className="text-sm">Total Packages</p>
        <p className="text-2xl font-bold">{display(summary?.total_packages)}</p>
      </div>
      <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
        <p className="text-sm">Total Weight (g)</p>
        <p className="text-2xl font-bold">{display(summary?.total_weight_grams)}</p>
        <p className="text-xs text-gray-400 mt-1">Σ (g per package × packages)</p>
      </div>
      {showTotalValue && (
        <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
          <p className="text-sm">Total Value</p>
          <p className="text-2xl font-bold">
            {isLoading || summary == null
              ? "—"
              : summary.total_value.toLocaleString()}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Σ (price per package × packages)
          </p>
        </div>
      )}
    </div>
  );
};

export default Summary;
