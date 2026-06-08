type Props = {
  counts: Record<string, number>;
};

const OriginDistribution = ({ counts }: Props) => {
  const entries = Object.entries(counts).sort(([a], [b]) => a.localeCompare(b));

  return (
    <div className="bg-[#ffffffE6] p-4 shadow rounded-xl text-gray-500">
      <h2 className="font-semibold mb-3">Assets by Origin</h2>
      <ul>
        {entries.map(([origin, count]) => (
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