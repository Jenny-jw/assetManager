import type { Asset } from "../types/Asset";

type Props = {
  assets: Asset[];
};

const GenreDistribution = ({ assets }: Props) => {
  const map: Record<string, number> = {};

  assets.forEach((asset) => {
    const genre = asset.genre ?? "Unknown";
    map[genre] = (map[genre] ?? 0) + 1;
  });

  return (
    <div className="bg-white p-4 shadow rounded-xl text-gray-500">
      <h2 className="font-semibold mb-3">Assets by Genre</h2>

      <ul>
        {Object.entries(map).map(([genre, count]) => (
          <li key={genre} className="flex justify-between border-b py-1">
            <span>{genre}</span>
            <span>{count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default GenreDistribution;
