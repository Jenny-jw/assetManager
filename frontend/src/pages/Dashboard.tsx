import { useCallback, useEffect, useState } from "react";
import Summary from "../components/Summary";
import OriginDistribution from "../components/OriginDistribution";
import GenreDistribution from "../components/GenreDistribution";
import PendingOrdersInbox from "../components/PendingOrdersInbox";
import RecentAssets from "../components/RecentAssets";
import { listTeas } from "../services/teaServices";
import type { Asset } from "../types/Asset";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

const Dashboard = () => {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "admin";
  const [assets, setAssets] = useState<Asset[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [pendingCount, setPendingCount] = useState(0);
  const [ordersRefresh, setOrdersRefresh] = useState(0);
  const navigate = useNavigate();

  const refreshAssets = useCallback(() => {
    listTeas({ limit: 100, sort_by: "created_at", sort_direction: "desc" })
      .then((response) => {
        setAssets(response.data);
        setTotalCount(response.total);
      })
      .catch((error) => {
        console.error("Failed to load dashboard assets:", error);
        setAssets([]);
        setTotalCount(0);
      });
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  useEffect(() => {
    refreshAssets();
  }, [refreshAssets]);

  const handleInventoryChange = useCallback(() => {
    refreshAssets();
    setOrdersRefresh((token) => token + 1);
  }, [refreshAssets]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between gap-4 px-2">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold">Tea Keeper Dashboard</h1>
          {isAdmin && pendingCount > 0 && (
            <span className="inline-flex items-center justify-center min-w-6 h-6 px-2 text-xs font-semibold rounded-full bg-[#894f45] text-white">
              {pendingCount}
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={handleLogout}
          className="px-4 py-2 text-sm rounded-lg bg-[#64794d] text-white hover:bg-lime-900 transition"
        >
          Log out
        </button>
      </div>
      <Summary assets={assets} totalCount={totalCount} showTotalValue={isAdmin} />
      <div
        className={
          isAdmin
            ? "grid grid-cols-1 lg:grid-cols-3 gap-6"
            : "grid grid-cols-1 lg:grid-cols-2 gap-6"
        }
      >
        <OriginDistribution assets={assets} />
        <GenreDistribution assets={assets} />
        {isAdmin && (
          <PendingOrdersInbox
            refreshToken={ordersRefresh}
            onPendingCountChange={setPendingCount}
            onInventoryChange={handleInventoryChange}
          />
        )}
      </div>
      <div className="grid md:grid-cols-6 gap-6">
        <RecentAssets assets={assets} className="md:col-span-4" />
        <div className="md:col-span-2 flex flex-col gap-4">
          {isAdmin && (
            <>
              <button
                className="flex-1 rounded-xl bg-[#78a043] hover:border-lime-200 text-white"
                onClick={() => navigate("/assets/new")}
              >
                Add Asset
              </button>
              <button
                className="flex-1 rounded-xl bg-[#b8cb75] hover:border-lime-100 text-white"
                onClick={() => navigate("/assets")}
              >
                Manage Inventory
              </button>
            </>
          )}
          {user?.role === "user" && (
            <button
              className="flex-1 rounded-xl bg-bg-[#78a043] hover:border-lime-100 text-white"
              onClick={() => navigate("/assets")}
            >
              Order
            </button>
          )}
          {user?.role === "guest" && (
            <button
              className="flex-1 rounded-xl bg-[#b8cb75] hover:border-lime-100 text-white"
              onClick={() => navigate("/assets")}
            >
              Asset List
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
