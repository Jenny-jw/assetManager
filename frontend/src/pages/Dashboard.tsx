import { useEffect, useState } from "react";
import Summary from "../components/Summary";
import axios from "axios";
import type { Asset } from "../types/Asset";

const Dashboard = () => {
  const [assets, setAssets] = useState<Asset[]>([]);

  useEffect(() => {
    axios.get("/api/tea").then((res) => {
      setAssets(res.data);
    });
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Asset Manager Dashboard</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Summary assets={assets} />
      </div>
    </div>
  );
};

export default Dashboard;
