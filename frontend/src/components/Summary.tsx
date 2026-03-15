import type { Asset } from "../types/Asset";

type Props = {
  assets: Asset[];
};

const Summary = ({ assets }: Props) => {
  const totalAssets = assets.length;
  const totalQuantity = assets.reduce((sum, a) => sum + (a.quantity ?? 0), 0);
  const totalWeight = assets.reduce((sum, a) => sum + (a.weight ?? 0), 0);

  return (
    <div className="grid grid-cols-3 gap-4">
      <div className="bg-white p-4 shadow rounded-xl text-gray-500">
        <p className="text-sm">Total Assets</p>
        <p className="text-2xl font-bold">{totalAssets}</p>
      </div>
      <div className="bg-white p-4 shadow rounded-xl text-gray-500">
        <p className="text-sm">Total Quantity</p>
        <p className="text-2xl font-bold">{totalQuantity}</p>
      </div>
      <div className="bg-white p-4 shadow rounded-xl text-gray-500">
        <p className="text-sm">Total Weight (g)</p>
        <p className="text-2xl font-bold">{totalWeight}</p>
      </div>
    </div>
  );
};

export default Summary;
