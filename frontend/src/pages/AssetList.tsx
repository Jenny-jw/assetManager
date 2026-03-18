import type { Asset } from "../types/Asset";
import { useEffect, useState } from "react";
import axios from "axios";

const AssetList = () => {
  const [assets, setAssets] = useState<Asset[]>([]);
  const handleEdit = (assetId) => {
    console.log(assetId);
  };
  const handleDelete = (assetId) => {
    console.log(assetId);
  };

  useEffect(() => {
    axios.get("/api/tea").then((res) => {
      console.log(res.data);
      setAssets(res.data);
    });
  }, []);

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">Asset list</h1>
      {/* Desktop Table */}
      <div className="hidden md:block bg-white rounded-xl shadow-sm border">
        <table className="min-w-full text-sm">
          {/* Header */}
          <thead className="text-gray-600 uppercase text-xs">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Origin</th>
              <th className="px-4 py-3">Genre</th>
              <th className="px-4 py-3">Roast</th>
              <th className="px-4 py-3">Weight</th>
              <th className="px-4 py-3">Quantity</th>
              <th className="px-4 py-3">Actions</th>
            </tr>
          </thead>
          {/* Body */}
          <tbody className="divide-y text-gray-500">
            {assets.map((asset) => (
              <tr key={asset.id} className="hover:bg-gray-50 transition">
                <td className="px-4 py-3 font-medium">{asset.name}</td>
                <td className="px-4 py-3">{asset.origin || "-"}</td>
                <td className="px-4 py-3">{asset.genre}</td>
                <td className="px-4 py-3">{asset.roastLevel}</td>
                <td className="px-4 py-3">{asset.weight ?? "-"}</td>
                <td className="px-4 py-3">{asset.quantity ?? "-"}</td>
                {/* Actions */}
                <td className="px-4 py-3">
                  <div className="flex justify-end gap-2">
                    <button
                      onClick={() => handleEdit(asset.id)}
                      className="px-3 py-1 text-sm rounded-lg bg-lime-700 text-white border 
                           border-gray-300 hover:bg-lime-900 hover:border-gray-500 transition"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(asset.id)}
                      className="px-3 py-1 text-sm rounded-lg 
                           bg-red-500 text-white 
                           hover:bg-red-700 hover:border-gray-500 transition"
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile Card */}
      {/* <div className="md:hidden"></div> */}
    </div>
  );
};

export default AssetList;
