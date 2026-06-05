import type { Asset } from "../types/Asset";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import axios from "../lib/axios";
import { createOrder } from "../services/orderServices";
import { useAuth } from "../context/useAuth";
import { useNavigate } from "react-router-dom";
import { isAxiosError } from "axios";
import {
  formatMoney,
  lineTotalValue,
  pricePerPackage,
} from "../lib/teaPricing";

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
  const isAdmin = user?.role === "admin";
  const [assets, setAssets] = useState<Asset[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [detailsMode, setDetailsMode] = useState<"details" | "full">("full");
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [orderingAssetId, setOrderingAssetId] = useState<string | null>(null);
  const isOrdering = orderingAssetId !== null;
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

  const refreshAssets = async () => {
    const res = await axios.get("/tea");
    setAssets(res.data.data);
  };

  const handleOrder = async (asset: Asset) => {
    if (isOrdering) return;

    const qtyInput = window.prompt(
      `How many packages of "${asset.name}" would you like to order?`,
      "1",
    );
    if (qtyInput === null) return;

    const quantity = Number(qtyInput);
    if (!Number.isInteger(quantity) || quantity < 1) {
      alert("Please enter a valid number of packages (1 or more).");
      return;
    }

    setOrderingAssetId(asset.id);

    try {
      const order = await createOrder({
        items: [{ tea_id: asset.id, quantity }],
      });
      await refreshAssets();
      setSelectedAsset((prev) => (prev?.id === asset.id ? null : prev));
      alert(
        `Order placed successfully. Price: ${order.total_amount.toLocaleString()}`,
      );
    } catch (error) {
      const message = isAxiosError(error)
        ? ((error.response?.data as { detail?: string })?.detail ??
          "Failed to place order.")
        : "Failed to place order.";
      alert(message);
    } finally {
      setOrderingAssetId(null);
    }
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
            void handleOrder(asset);
          }}
          disabled={isOrdering}
          className="px-3 py-1 text-sm rounded-lg bg-lime-700 text-white hover:bg-lime-900 transition disabled:opacity-60 disabled:cursor-not-allowed min-w-[5.5rem]"
        >
          {orderingAssetId === asset.id ? "Ordering…" : "Order"}
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
                <th className="px-4 py-3">WEIGHT/ PKG (G)</th>
                <SortableHeader
                  label="PACKAGES"
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
                  label="PRICE PER 斤"
                  sortKey="price"
                  currentSortKey={sortKey}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                />
                <th className="px-4 py-3">PRICE/ PKG</th>
                {isAdmin && <th className="px-4 py-3">TOTAL VALUE</th>}
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
                  <td className="px-4 py-3">{asset.weight ?? "-"}</td>
                  <td className="px-4 py-3">{asset.quantity ?? "-"}</td>
                  <td className="px-4 py-3">{asset.score ?? "-"}</td>
                  <td className="px-4 py-3">{formatMoney(asset.price)}</td>
                  <td className="px-4 py-3">
                    {formatMoney(pricePerPackage(asset.price, asset.weight))}
                  </td>
                  {isAdmin && (
                    <td className="px-4 py-3 font-medium">
                      {formatMoney(lineTotalValue(asset))}
                    </td>
                  )}
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
                label="Packages"
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
                  <DetailRow label="Genre" value={selectedAsset.genre} />
                  <DetailRow label="Origin" value={selectedAsset.origin} />
                  <DetailRow label="Producer" value={selectedAsset.producer} />
                  <DetailRow
                    label="Harvest Time"
                    value={selectedAsset.harvest_time}
                  />
                  <DetailRow
                    label="Roast Level"
                    value={selectedAsset.roast_level}
                  />
                  <DetailRow label="Score" value={selectedAsset.score} />
                  <DetailRow label="Comment" value={selectedAsset.comment} />
                </>
              )}
              <DetailRow
                label="Weight per package (g)"
                value={selectedAsset.weight}
              />
              <DetailRow
                label="Number of packages"
                value={selectedAsset.quantity}
              />
              <DetailRow
                label="Price per 斤"
                value={formatMoney(selectedAsset.price)}
              />
              <DetailRow
                label="Price per package"
                value={formatMoney(
                  pricePerPackage(selectedAsset.price, selectedAsset.weight),
                )}
              />
              {isAdmin && (
                <DetailRow
                  label="Total value"
                  value={formatMoney(lineTotalValue(selectedAsset))}
                />
              )}
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
                    void handleOrder(selectedAsset);
                  }}
                  disabled={isOrdering}
                  className="px-4 py-2 bg-lime-700 text-white rounded-lg transition disabled:opacity-60 disabled:cursor-not-allowed min-w-[7rem]"
                >
                  {orderingAssetId === selectedAsset.id
                    ? "Placing order…"
                    : "Order"}
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