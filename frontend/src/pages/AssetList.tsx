import type { Asset } from "../types/Asset";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import axios from "../lib/axios";
import { useAuth } from "../context/useAuth";
import { useNavigate } from "react-router-dom";

type SortKey = "score" | "price" | "quantity" | "harvest_time" | "genre";
type SortDirection = "asc" | "desc";

const DetailRow = ({ label, value }: { label: string; value: ReactNode }) => (
  <div className="flex justify-between gap-4 border-b pb-2">
    <span className="font-medium text-gray-600">{label}</span>
    <span className="text-gray-800 text-right wrap-break-words">
      {value ?? "-"}
    </span>
  </div>
);

const SortableHeader = ({
  label,
  sortKey,
  currentSortKey,
  sortDirection,
  onSort,
}: {
  label: string;
  sortKey: SortKey;
  currentSortKey: SortKey;
  sortDirection: SortDirection;
  onSort: (key: SortKey) => void;
}) => (
  <th
    className="px-4 py-3 cursor-pointer select-none hover:bg-[#d4df9d] transition"
    onClick={() => onSort(sortKey)}
  >
    <span className="inline-flex items-center gap-1">
      {label}
      {currentSortKey === sortKey && (
        <span>{sortDirection === "asc" ? "↑" : "↓"}</span>
      )}
    </span>
  </th>
);

const AssetList = () => {
  const { user } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [detailsMode, setDetailsMode] = useState<"details" | "full">("full");
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const navigate = useNavigate();

  useEffect(() => {
    axios.get("/tea").then((res) => {
      setAssets(res.data.data);
    });
  }, []);

  const openDesktopDetails = (asset: Asset) => {
    setDetailsMode("details");
    setSelectedAsset(asset);
  };

  const openFullDetails = (asset: Asset) => {
    setDetailsMode("full");
    setSelectedAsset(asset);
  };

  const handleEdit = (assetId: string) => {
    navigate(`/assets/${assetId}/edit`);
  };

  const handleDelete = async (assetId: string) => {
    const confirmed = window.confirm(
      "Are you sure you want to delete this tea?",
    );

    if (!confirmed) return;

    try {
      await axios.delete(`/tea/${assetId}`);

      setAssets((prevAssets) =>
        prevAssets.filter((asset) => asset.id !== assetId),
      );

      setSelectedAsset((prevAsset) =>
        prevAsset?.id === assetId ? null : prevAsset,
      );
    } catch (error) {
      console.error("Delete failed:", error);
      alert("Failed to delete tea. Please try again.");
    }
  };

  const renderActions = (asset: Asset) => {
    if (user?.role === "admin") {
      return (
        <div className="flex gap-2 justify-end">
          <button
            onClick={(e) => {
              e.stopPropagation();
              openDesktopDetails(asset);
            }}
            className="px-3 py-1 text-sm rounded-lg bg-[#bfc099] text-white hover:bg-[#bbbb82] transition"
          >
            Details
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              handleEdit(asset.id);
            }}
            className="px-3 py-1 text-sm rounded-lg bg-[#78a043] text-white hover:bg-lime-900 transition"
          >
            Edit
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDelete(asset.id);
            }}
            className="px-3 py-1 text-sm rounded-lg bg-[#894f45] text-white hover:bg-red-700 transition"
          >
            Delete
          </button>
        </div>
      );
    }

    return (
      <div className="flex gap-2 justify-end">
        <button
          onClick={(e) => {
            e.stopPropagation();
            openDesktopDetails(asset);
          }}
          className="px-3 py-1 text-sm rounded-lg bg-[#bfc099] text-white hover:bg-[#bbbb82] transition"
        >
          Details
        </button>

        <button
          onClick={(e) => {
            e.stopPropagation();
            handleEdit(asset.id);
          }}
          className="px-3 py-1 text-sm rounded-lg bg-lime-700 text-white hover:bg-lime-900 transition"
        >
          Order
        </button>
      </div>
    );
  };

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("desc");
    }
  };

  const sortedAssets = [...assets].sort((a, b) => {
    const aValue = a[sortKey];
    const bValue = b[sortKey];

    if (aValue == null && bValue == null) return 0;
    if (aValue == null) return 1;
    if (bValue == null) return -1;

    if (typeof aValue === "number" && typeof bValue === "number") {
      return sortDirection === "asc" ? aValue - bValue : bValue - aValue;
    }

    return sortDirection === "asc"
      ? String(aValue).localeCompare(String(bValue))
      : String(bValue).localeCompare(String(aValue));
  });

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex items-center justify-between gap-4 px-2">
        <div className="text-left">
          <h1 className="text-3xl font-bold">Asset List</h1>
          <p className="text-sm text-[#d6d1c5]">
            Sort the rows by clicking on the column headers
          </p>
        </div>

        <button
          type="button"
          onClick={() => navigate("/dashboard")}
          className="px-4 py-2 text-sm rounded-lg bg-[#64794d] text-white hover:bg-lime-900 transition"
        >
          Back to Dashboard
        </button>
      </div>

      {/* Desktop */}
      <div className="hidden lg:block bg-white rounded-2xl shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-[#dee8ae] text-[#64794d] text-xs">
              <tr>
                <th className="px-4 py-3">NAME</th>
                <SortableHeader
                  label="GENRE"
                  sortKey="genre"
                  currentSortKey={sortKey}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                />
                <th className="px-4 py-3">ORIGIN</th>
                <SortableHeader
                  label="QUANTITY"
                  sortKey="quantity"
                  currentSortKey={sortKey}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="SCORE"
                  sortKey="score"
                  currentSortKey={sortKey}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="PRICE per 斤"
                  sortKey="price"
                  currentSortKey={sortKey}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                />
                <SortableHeader
                  label="HARVEST TIME"
                  sortKey="harvest_time"
                  currentSortKey={sortKey}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                />
                <th className="px-4 py-3">ACTIONS</th>
              </tr>
            </thead>

            <tbody className="divide-y text-gray-700">
              {sortedAssets.map((asset) => (
                <tr key={asset.id} className="hover:bg-[#fcf6de] transition">
                  <td className="px-4 py-3 font-medium">{asset.name}</td>
                  <td className="px-4 py-3">{asset.genre ?? "-"}</td>
                  <td className="px-4 py-3">{asset.origin ?? "-"}</td>
                  <td className="px-4 py-3">{asset.quantity ?? "-"}</td>
                  <td className="px-4 py-3">{asset.score ?? "-"}</td>
                  <td className="px-4 py-3">{asset.price ?? "-"}</td>
                  <td className="px-4 py-3">{asset.harvest_time ?? "-"}</td>
                  <td className="px-4 py-3">{renderActions(asset)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Tablet */}
      <div className="hidden md:block lg:hidden bg-white rounded-2xl shadow-sm border overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-[#dee8ae] text-[#64794d] uppercase text-xs">
            <tr>
              <th className="px-4 py-3">Name</th>
              <SortableHeader
                label="Genre"
                sortKey="genre"
                currentSortKey={sortKey}
                sortDirection={sortDirection}
                onSort={handleSort}
              />
              <th className="px-4 py-3">Origin</th>
              <SortableHeader
                label="Quantity"
                sortKey="quantity"
                currentSortKey={sortKey}
                sortDirection={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                label="Score"
                sortKey="score"
                currentSortKey={sortKey}
                sortDirection={sortDirection}
                onSort={handleSort}
              />
            </tr>
          </thead>

          <tbody className="divide-y text-gray-700">
            {sortedAssets.map((asset) => (
              <tr
                key={asset.id}
                onClick={() => openFullDetails(asset)}
                className="cursor-pointer hover:bg-gray-50 transition"
              >
                <td className="px-4 py-3 font-medium">{asset.name}</td>
                <td className="px-4 py-3">{asset.genre ?? "-"}</td>
                <td className="px-4 py-3">{asset.origin ?? "-"}</td>
                <td className="px-4 py-3">{asset.quantity ?? "-"}</td>
                <td className="px-4 py-3">{asset.score ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile */}
      <div className="md:hidden space-y-3">
        {sortedAssets.map((asset) => (
          <div
            key={asset.id}
            onClick={() => openFullDetails(asset)}
            className="bg-white rounded-2xl border shadow-sm p-4 cursor-pointer active:scale-[0.99] transition"
          >
            <div className="flex justify-between items-start gap-4">
              <div className="min-w-0 text-left">
                <h2 className="text-[#9f655d] font-semibold text-lg wrap-break-word">
                  {asset.name}
                </h2>
                <p className="text-sm text-gray-500 wrap-break-word">
                  {asset.genre ?? "-"} / {asset.origin ?? "-"}
                </p>
              </div>

              <div className="shrink-0 text-right">
                <p className="text-xs text-gray-400">Score</p>
                <p className="font-bold text-lg text-[#9f655d]">
                  {asset.score ?? "-"}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Modal */}
      {selectedAsset && (
        <div
          className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
          onClick={() => setSelectedAsset(null)}
        >
          <div
            className="bg-white w-full max-w-lg rounded-2xl shadow-xl p-6 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex justify-between items-start mb-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-500">
                  {selectedAsset.name}
                </h2>
                <p className="text-gray-500 text-left">More details</p>
              </div>

              <button
                onClick={() => setSelectedAsset(null)}
                className="text-gray-400 hover:text-gray-600 text-l"
              >
                ×
              </button>
            </div>

            <div className="space-y-3">
              {detailsMode === "full" && (
                <>
                  <DetailRow label="Name" value={selectedAsset.name} />
                  <DetailRow label="Genre" value={selectedAsset.genre} />
                  <DetailRow label="Origin" value={selectedAsset.origin} />
                  <DetailRow label="Producer" value={selectedAsset.producer} />
                  <DetailRow label="Weight" value={selectedAsset.weight} />
                  <DetailRow label="Quantity" value={selectedAsset.quantity} />
                  <DetailRow label="Score" value={selectedAsset.score} />
                  <DetailRow label="Price" value={selectedAsset.price} />
                  <DetailRow
                    label="Harvest Time"
                    value={selectedAsset.harvest_time}
                  />
                  <DetailRow
                    label="Roast Level"
                    value={selectedAsset.roast_level}
                  />
                </>
              )}
              <DetailRow
                label="Weight per package (g)"
                value={selectedAsset.weight}
              />
              <DetailRow
                label="Price per package"
                value={(selectedAsset.weight / 600) * selectedAsset.price}
              />
              <DetailRow
                label="Total value"
                value={
                  selectedAsset.quantity *
                  (selectedAsset.weight / 600) *
                  selectedAsset.price
                }
              />
              <DetailRow label="Producer" value={selectedAsset.producer} />
              <DetailRow
                label="Roast Level"
                value={selectedAsset.roast_level}
              />
              <DetailRow label="Comment" value={selectedAsset.comment} />
            </div>

            <div className="mt-6 flex justify-end">
              {user?.role === "admin" ? (
                <>
                  <button
                    onClick={() => {
                      handleEdit(selectedAsset.id);
                      setSelectedAsset(null);
                    }}
                    className="px-4 py-2 bg-[#78a043] text-white rounded-lg mr-2 hover:bg-lime-900 transition"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => {
                      handleDelete(selectedAsset.id);
                      setSelectedAsset(null);
                    }}
                    className="px-4 py-2 bg-[#894f45] text-white rounded-lg hover:bg-red-700 transition"
                  >
                    Delete
                  </button>
                </>
              ) : (
                <button
                  onClick={() => {
                    handleEdit(selectedAsset.id);
                    setSelectedAsset(null);
                  }}
                  className="px-4 py-2 bg-lime-700 text-white rounded"
                >
                  Order
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssetList;
