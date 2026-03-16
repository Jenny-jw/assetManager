import { useEffect, useState } from "react";
import Summary from "../components/Summary";
import OriginDistribution from "../components/OriginDistribution";
import GenreDistribution from "../components/GenreDistribution";
import RecentAssets from "../components/RecentAssets";
import axios from "axios";
import type { Asset } from "../types/Asset";
import { useNavigate } from "react-router-dom";

const Dashboard = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get("/api/tea").then((res) => {
      setAssets(res.data);
    });
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Asset Manager Dashboard</h1>
      <Summary assets={assets} />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <OriginDistribution assets={assets} />
        <GenreDistribution assets={assets} />
      </div>
      <div className="grid md:grid-cols-6 gap-6">
        <RecentAssets assets={assets} className="md:col-span-4" />
        <div className="md:col-span-2 flex flex-col gap-4">
          <button
            className="flex-1 rounded-xl bg-lime-700 text-white"
            onClick={() => navigate("/assets/new")}
          >
            Add Asset
          </button>
          <button className="flex-1 rounded-xl bg-lime-500 text-white">
            Manage Inventory
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
