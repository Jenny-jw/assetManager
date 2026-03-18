import type { Asset } from "../types/Asset";

type Props = {
  assets: Asset[];
  className?: string;
};

const RecentAssets = ({ assets, className }: Props) => {
  const recent = assets.slice(-3);

  return (
    <div
      className={`col-start-1 col-end-4 bg-white p-4 shadow rounded-xl text-gray-500 ${className ?? ""}`}
    >
      <h2 className="font-semibold mb-3">Recent Assets</h2>

      <ul>
        {recent.map((a) => (
          <li key={a.id} className="flex justify-between border-b py-1">
            <span>{a.name}</span>
            <span>{a.origin}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default RecentAssets;
