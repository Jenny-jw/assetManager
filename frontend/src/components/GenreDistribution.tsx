import { useTranslation } from "react-i18next";

type Props = {
  counts: Record<string, number>;
};

const GenreDistribution = ({ counts }: Props) => {
  const { t } = useTranslation();
  const entries = Object.entries(counts).sort(([a], [b]) => a.localeCompare(b));

  return (
    <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
      <h2 className="font-semibold mb-3">{t("widgets.assetsByGenre")}</h2>
      <ul>
        {entries.map(([genre, count]) => (
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
