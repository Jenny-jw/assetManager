import { useEffect, useState } from "react";
import Summary from "../components/Summary";
import OriginDistribution from "../components/OriginDistribution";
import GenreDistribution from "../components/GenreDistribution";
import RecentAssets from "../components/RecentAssets";
import axios from "../lib/axios";
import type { Asset } from "../types/Asset";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";

const Dashboard = () => {
  const { user, loading, logout } = useAuth();
  const [assets, setAssets] = useState<Asset[]>([]);
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  useEffect(() => {
    axios.get("/tea").then((res) => {
      setAssets(res.data.data);
    });
  }, []);

  useEffect(() => {
    // if (!loading &&)
    console.log("Current user: ", user?.role);
  }, [loading, user]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between gap-4 px-2">
        <h1 className="text-3xl font-bold">Tea Keeper Dashboard</h1>

        <button
          type="button"
          onClick={handleLogout}
          className="px-4 py-2 text-sm rounded-lg bg-[#64794d] text-white hover:bg-lime-900 transition"
        >
          Log out
        </button>
      </div>
      <Summary assets={assets} showTotalValue={user?.role === "admin"} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <OriginDistribution assets={assets} />
        <GenreDistribution assets={assets} />
      </div>
      <div className="grid md:grid-cols-6 gap-6">
        <RecentAssets assets={assets} className="md:col-span-4" />
        <div className="md:col-span-2 flex flex-col gap-4">
          {user?.role === "admin" && (
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