import type { Asset } from "../types/Asset";
import { sumLineTotalValues } from "../lib/teaPricing";

type Props = {
  assets: Asset[];
  showTotalValue?: boolean;
};

const Summary = ({ assets, showTotalValue = false }: Props) => {
  const totalAssets = assets.length;
  const totalPackages = assets.reduce((sum, a) => sum + (a.quantity ?? 0), 0);
  const totalWeightGrams = assets.reduce(
    (sum, a) => sum + (a.weight ?? 0) * (a.quantity ?? 0),
    0,
  );
  const totalValue = sumLineTotalValues(assets);

  const gridClass = showTotalValue
    ? "grid grid-cols-2 lg:grid-cols-4 gap-4"
    : "grid grid-cols-3 gap-4";

  return (
    <div className={gridClass}>
      <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
        <p className="text-sm">Total Assets</p>
        <p className="text-2xl font-bold">{totalAssets}</p>
      </div>
      <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
        <p className="text-sm">Total Packages</p>
        <p className="text-2xl font-bold">{totalPackages}</p>
      </div>
      <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
        <p className="text-sm">Total Weight (g)</p>
        <p className="text-2xl font-bold">{totalWeightGrams}</p>
        <p className="text-xs text-gray-400 mt-1">Σ (g per package × packages)</p>
      </div>
      {showTotalValue && (
        <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
          <p className="text-sm">Total Value</p>
          <p className="text-2xl font-bold">{totalValue.toLocaleString()}</p>
          <p className="text-xs text-gray-400 mt-1">
            Σ (price per package × packages)
          </p>
        </div>
      )}
    </div>
  );
};

export default Summary;