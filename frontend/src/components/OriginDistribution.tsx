import type { Asset } from "../types/Asset";

type Props = {
  assets: Asset[];
};

const OriginDistribution = ({ assets }: Props) => {
  const map: Record<string, number> = {};

  assets.forEach((asset) => {
    const origin = asset.origin ?? "Unknown";
    map[origin] = (map[origin] ?? 0) + 1;
  });

  return (
    <div className="bg-white p-4 shadow rounded-xl text-gray-500">
      <h2 className="font-semibold mb-3">Assets by Origin</h2>
      <ul>
        {Object.entries(map).map(([origin, count]) => (
          <li key={origin} className="flex justify-between border-b py-1">
            <span>{origin}</span>
            <span>{count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default OriginDistribution;
