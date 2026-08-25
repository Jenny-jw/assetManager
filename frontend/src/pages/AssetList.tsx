import type { Asset } from "../types/Asset";
import type { TeaSortField } from "../types/TeaList";
import type { ReactNode } from "react";
import { useEffect, useRef, useState } from "react";
import {
  DEFAULT_STOCK_PAGE_SIZE,
  deleteStock,
  extractStockFacets,
  listStocks,
} from "../services/stockServices";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { useAuth } from "../context/useAuth";
import { useDeployment } from "../context/useDeployment";
import { isModuleEnabled } from "../lib/moduleAccess";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  formatMoney,
  lineTotalValue,
  pricePerPackage,
} from "../lib/teaPricing";

type SortDirection = "asc" | "desc";

const SEARCH_DEBOUNCE_MS = 300;

function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}

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
  sortKey: TeaSortField;
  currentSortKey: TeaSortField;
  sortDirection: SortDirection;
  onSort: (key: TeaSortField) => void;
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
  const { t } = useTranslation();
  const { user } = useAuth();
  const { deployment } = useDeployment();
  const isOwner = user?.role === "owner";
  const canManageInventory = isOwner;
  const showTotalValue = isModuleEnabled(deployment, "pricing_visibility");
  const navigate = useNavigate();

  const [assets, setAssets] = useState<Asset[]>([]);
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null);
  const [detailsMode, setDetailsMode] = useState<"details" | "full">("full");
  const [sortKey, setSortKey] = useState<TeaSortField>("score");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [searchInput, setSearchInput] = useState("");
  const [genreFilter, setGenreFilter] = useState("");
  const [originFilter, setOriginFilter] = useState("");
  const [genreOptions, setGenreOptions] = useState<string[]>([]);
  const [originOptions, setOriginOptions] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const debouncedSearch = useDebouncedValue(searchInput, SEARCH_DEBOUNCE_MS);
  const previousSearch = useRef(debouncedSearch);

  useEffect(() => {
    listStocks({ limit: 100, sort_by: "name", sort_direction: "asc" })
      .then((response) => {
        const facets = extractStockFacets(response.data);
        setGenreOptions(facets.genres);
        setOriginOptions(facets.origins);
      })
      .catch(() => {
        setGenreOptions([]);
        setOriginOptions([]);
      });
  }, []);

  useEffect(() => {
    if (previousSearch.current !== debouncedSearch) {
      previousSearch.current = debouncedSearch;
      setPage(1);
    }
  }, [debouncedSearch]);

  useEffect(() => {
    let cancelled = false;

    const loadAssets = async () => {
      setIsLoading(true);
      setLoadError("");

      try {
        const response = await listStocks({
          page,
          limit: DEFAULT_STOCK_PAGE_SIZE,
          search: debouncedSearch.trim() || undefined,
          genre: genreFilter || undefined,
          origin: originFilter || undefined,
          sort_by: sortKey,
          sort_direction: sortDirection,
        });

        if (cancelled) return;

        const totalPages = Math.max(
          1,
          Math.ceil(response.total / response.limit),
        );

        if (page > totalPages) {
          setPage(totalPages);
          return;
        }

        setAssets(response.data);
        setTotal(response.total);
      } catch (error) {
        if (cancelled) return;
        console.error("Failed to load assets:", error);
        setLoadError(t("inventory.loadFailed"));
        setAssets([]);
        setTotal(0);
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void loadAssets();

    return () => {
      cancelled = true;
    };
  }, [page, debouncedSearch, genreFilter, originFilter, sortKey, sortDirection, t]);

  const totalPages = Math.max(1, Math.ceil(total / DEFAULT_STOCK_PAGE_SIZE));
  const rangeStart = total === 0 ? 0 : (page - 1) * DEFAULT_STOCK_PAGE_SIZE + 1;
  const rangeEnd = Math.min(page * DEFAULT_STOCK_PAGE_SIZE, total);
  const hasActiveFilters =
    searchInput.trim() !== "" || genreFilter !== "" || originFilter !== "";

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
    const response = await listStocks({
      page,
      limit: DEFAULT_STOCK_PAGE_SIZE,
      search: debouncedSearch.trim() || undefined,
      genre: genreFilter || undefined,
      origin: originFilter || undefined,
      sort_by: sortKey,
      sort_direction: sortDirection,
    });
    setAssets(response.data);
    setTotal(response.total);
  };

  const handleDelete = async (assetId: string) => {
    const confirmed = window.confirm(t("inventory.deleteConfirm"));

    if (!confirmed) return;

    try {
      await deleteStock(assetId);

      setSelectedAsset((prevAsset) =>
        prevAsset?.id === assetId ? null : prevAsset,
      );

      if (assets.length === 1 && page > 1) {
        setPage(page - 1);
        return;
      }

      await refreshAssets();
    } catch (error) {
      console.error("Delete failed:", error);
      alert(t("inventory.deleteFailed"));
    }
  };

  const renderActions = (asset: Asset) => {
    if (canManageInventory) {
      return (
        <div className="flex gap-2 justify-end">
          <button
            onClick={(e) => {
              e.stopPropagation();
              openDesktopDetails(asset);
            }}
            className="px-3 py-1 text-sm rounded-lg bg-[#bfc099] text-white hover:bg-[#bbbb82] transition"
          >
            {t("inventory.details")}
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              handleEdit(asset.id);
            }}
            className="px-3 py-1 text-sm rounded-lg bg-[#78a043] text-white hover:bg-lime-900 transition"
          >
            {t("inventory.edit")}
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              handleDelete(asset.id);
            }}
            className="px-3 py-1 text-sm rounded-lg bg-[#894f45] text-white hover:bg-red-700 transition"
          >
            {t("inventory.delete")}
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
          {t("inventory.details")}
        </button>
      </div>
    );
  };

  const genreLabel = (genre: string | undefined) =>
    genre ? t(`inventory.genres.${genre}`, { defaultValue: genre }) : "-";

  const handleSort = (key: TeaSortField) => {
    if (sortKey === key) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("desc");
    }
  };

  const handleGenreFilterChange = (value: string) => {
    setGenreFilter(value);
    setPage(1);
  };

  const handleOriginFilterChange = (value: string) => {
    setOriginFilter(value);
    setPage(1);
  };

  const clearFilters = () => {
    setSearchInput("");
    setGenreFilter("");
    setOriginFilter("");
    setPage(1);
  };

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex items-center justify-between gap-4 px-2">
        <div className="text-left">
          <h1 className="text-3xl font-bold">{t("inventory.title")}</h1>
          <p className="text-sm text-[#d6d1c5]">
            {t("inventory.subtitle")}
          </p>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <LanguageSwitcher />
          <button
            type="button"
            onClick={() => navigate("/dashboard")}
            className="px-4 py-2 text-sm rounded-lg bg-[#64794d] text-white hover:bg-lime-900 transition"
          >
            {t("inventory.backToDashboard")}
          </button>
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border p-4 md:p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
          <label className="space-y-1 text-left xl:col-span-2">
            <span className="text-sm font-medium text-gray-600">
              {t("inventory.search")}
            </span>
            <input
              type="search"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder={t("inventory.searchPlaceholder")}
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
          </label>

          <label className="space-y-1 text-left">
            <span className="text-sm font-medium text-gray-600">
              {t("inventory.fields.genre")}
            </span>
            <select
              value={genreFilter}
              onChange={(e) => handleGenreFilterChange(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            >
              <option value="">{t("inventory.allGenres")}</option>
              {genreOptions.map((genre) => (
                <option key={genre} value={genre}>
                  {genreLabel(genre)}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-1 text-left">
            <span className="text-sm font-medium text-gray-600">
              {t("inventory.fields.origin")}
            </span>
            <select
              value={originFilter}
              onChange={(e) => handleOriginFilterChange(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            >
              <option value="">{t("inventory.allOrigins")}</option>
              {originOptions.map((origin) => (
                <option key={origin} value={origin}>
                  {origin}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-gray-600 text-left">
            {isLoading
              ? t("inventory.loadingAssets")
              : total === 0
                ? t("inventory.noAssetsFound")
                : t("inventory.showingRange", {
                    start: rangeStart,
                    end: rangeEnd,
                    total,
                  })}
          </p>

          <div className="flex items-center gap-2 justify-end">
            {hasActiveFilters && (
              <button
                type="button"
                onClick={clearFilters}
                className="px-3 py-2 text-sm rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 transition"
              >
                {t("inventory.clearFilters")}
              </button>
            )}
            <button
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={isLoading || page <= 1}
              className="px-3 py-2 text-sm rounded-lg bg-[#64794d] text-white hover:bg-lime-900 transition disabled:opacity-50"
            >
              {t("inventory.previous")}
            </button>
            <span className="text-sm text-gray-700 min-w-[6rem] text-center">
              {t("inventory.pageOf", { page, totalPages })}
            </span>
            <button
              type="button"
              onClick={() =>
                setPage((current) => Math.min(totalPages, current + 1))
              }
              disabled={isLoading || page >= totalPages}
              className="px-3 py-2 text-sm rounded-lg bg-[#64794d] text-white hover:bg-lime-900 transition disabled:opacity-50"
            >
              {t("inventory.next")}
            </button>
          </div>
        </div>
      </div>

      {loadError && (
        <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          {loadError}
        </p>
      )}

      {/* Desktop */}
      <div className="hidden lg:block bg-white rounded-2xl shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-[#dee8ae] text-[#64794d] text-xs uppercase">
              <tr>
                <th className="px-4 py-3">{t("inventory.fields.name")}</th>
                <SortableHeader
                  label={t("inventory.fields.genre")}
                  sortKey="genre"
                  currentSortKey={sortKey}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                />
                <SortableHeader
                  label={t("inventory.fields.origin")}
                  sortKey="origin"
                  currentSortKey={sortKey}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                />
                <th className="px-4 py-3">
                  {t("inventory.fields.weightPerPkgShort")}
                </th>
                <SortableHeader
                  label={t("inventory.fields.packagesShort")}
                  sortKey="quantity"
                  currentSortKey={sortKey}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                />
                <SortableHeader
                  label={t("inventory.fields.score")}
                  sortKey="score"
                  currentSortKey={sortKey}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                />
                <SortableHeader
                  label={t("inventory.fields.pricePerJin")}
                  sortKey="price"
                  currentSortKey={sortKey}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                />
                <th className="px-4 py-3">
                  {t("inventory.fields.pricePerPkgShort")}
                </th>
                {showTotalValue && (
                  <th className="px-4 py-3">
                    {t("inventory.fields.totalValue")}
                  </th>
                )}
                <SortableHeader
                  label={t("inventory.fields.harvestTime")}
                  sortKey="harvest_time"
                  currentSortKey={sortKey}
                  sortDirection={sortDirection}
                  onSort={handleSort}
                />
                <th className="px-4 py-3">{t("inventory.fields.actions")}</th>
              </tr>
            </thead>

            <tbody className="divide-y text-gray-700">
              {!isLoading && assets.length === 0 && (
                <tr>
                  <td
                    colSpan={showTotalValue ? 11 : 10}
                    className="px-4 py-8 text-center text-gray-500"
                  >
                    {t("inventory.noMatches")}
                  </td>
                </tr>
              )}
              {assets.map((asset) => (
                <tr key={asset.id} className="hover:bg-[#fcf6de] transition">
                  <td className="px-4 py-3 font-medium">{asset.name}</td>
                  <td className="px-4 py-3">{genreLabel(asset.genre)}</td>
                  <td className="px-4 py-3">{asset.origin ?? "-"}</td>
                  <td className="px-4 py-3">{asset.weight ?? "-"}</td>
                  <td className="px-4 py-3">{asset.quantity ?? "-"}</td>
                  <td className="px-4 py-3">{asset.score ?? "-"}</td>
                  <td className="px-4 py-3">{formatMoney(asset.price)}</td>
                  <td className="px-4 py-3">
                    {formatMoney(pricePerPackage(asset.price, asset.weight))}
                  </td>
                  {showTotalValue && (
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
              <th className="px-4 py-3">{t("inventory.fields.name")}</th>
              <SortableHeader
                label={t("inventory.fields.genre")}
                sortKey="genre"
                currentSortKey={sortKey}
                sortDirection={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                label={t("inventory.fields.origin")}
                sortKey="origin"
                currentSortKey={sortKey}
                sortDirection={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                label={t("inventory.fields.packagesShort")}
                sortKey="quantity"
                currentSortKey={sortKey}
                sortDirection={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                label={t("inventory.fields.score")}
                sortKey="score"
                currentSortKey={sortKey}
                sortDirection={sortDirection}
                onSort={handleSort}
              />
            </tr>
          </thead>

          <tbody className="divide-y text-gray-700">
            {!isLoading && assets.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                  {t("inventory.noMatches")}
                </td>
              </tr>
            )}
            {assets.map((asset) => (
              <tr
                key={asset.id}
                onClick={() => openFullDetails(asset)}
                className="cursor-pointer hover:bg-gray-50 transition"
              >
                <td className="px-4 py-3 font-medium">{asset.name}</td>
                <td className="px-4 py-3">{genreLabel(asset.genre)}</td>
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
        {!isLoading && assets.length === 0 && (
          <div className="bg-white rounded-2xl border shadow-sm p-6 text-center text-gray-500">
            {t("inventory.noMatches")}
          </div>
        )}
        {assets.map((asset) => (
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
                  {genreLabel(asset.genre)} / {asset.origin ?? "-"}
                </p>
              </div>

              <div className="shrink-0 text-right">
                <p className="text-xs text-gray-400">
                  {t("inventory.fields.score")}
                </p>
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
                <p className="text-gray-500 text-left">
                  {t("inventory.moreDetails")}
                </p>
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
                  <DetailRow
                    label={t("inventory.fields.genre")}
                    value={genreLabel(selectedAsset.genre)}
                  />
                  <DetailRow
                    label={t("inventory.fields.origin")}
                    value={selectedAsset.origin}
                  />
                  <DetailRow
                    label={t("inventory.fields.producer")}
                    value={selectedAsset.producer}
                  />
                  <DetailRow
                    label={t("inventory.fields.harvestTime")}
                    value={selectedAsset.harvest_time}
                  />
                  <DetailRow
                    label={t("inventory.fields.roastLevel")}
                    value={selectedAsset.roast_level}
                  />
                  <DetailRow
                    label={t("inventory.fields.score")}
                    value={selectedAsset.score}
                  />
                  <DetailRow
                    label={t("inventory.fields.comment")}
                    value={selectedAsset.comment}
                  />
                </>
              )}
              <DetailRow
                label={t("inventory.fields.weightPerPackage")}
                value={selectedAsset.weight}
              />
              <DetailRow
                label={t("inventory.fields.packages")}
                value={selectedAsset.quantity}
              />
              <DetailRow
                label={t("inventory.fields.pricePerJin")}
                value={formatMoney(selectedAsset.price)}
              />
              <DetailRow
                label={t("inventory.fields.pricePerPackage")}
                value={formatMoney(
                  pricePerPackage(selectedAsset.price, selectedAsset.weight),
                )}
              />
              {showTotalValue && (
                <DetailRow
                  label={t("inventory.fields.totalValue")}
                  value={formatMoney(lineTotalValue(selectedAsset))}
                />
              )}
            </div>

            <div className="mt-6 flex justify-end">
              {canManageInventory ? (
                <>
                  <button
                    onClick={() => {
                      handleEdit(selectedAsset.id);
                      setSelectedAsset(null);
                    }}
                    className="px-4 py-2 bg-[#78a043] text-white rounded-lg mr-2 hover:bg-lime-900 transition"
                  >
                    {t("inventory.edit")}
                  </button>
                  <button
                    onClick={() => {
                      handleDelete(selectedAsset.id);
                      setSelectedAsset(null);
                    }}
                    className="px-4 py-2 bg-[#894f45] text-white rounded-lg hover:bg-red-700 transition"
                  >
                    {t("inventory.delete")}
                  </button>
                </>
              ) : null}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AssetList;
