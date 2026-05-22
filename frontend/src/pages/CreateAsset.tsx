import React, { useState } from "react";
import { Link } from "react-router-dom";
import type { CreateAssetType } from "../types/Asset";
import axios from "axios";

const CreateAsset = () => {
  const [form, setForm] = useState<CreateAssetType>({
    name: "",
    origin: "",
    genre: "",
    roast_level: 30,
    harvest_time: undefined,
    weight: 150,
    quantity: 1,
    score: 80,
    comment: "",
    producer: {
      name: "",
      factory: "",
      location: "",
    },
  });
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value === "" ? undefined : value }));
  };
  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      await axios.post("/api/tea", form);
      console.log("Tea added! 🌿");
    } catch (err) {
      console.log(err);
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Create Asset</h1>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block font-medium mb-1">Name *</label>
          <input
            name="name"
            value={form.name}
            onChange={handleChange}
            required
            className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
          />
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          {/* Origin */}
          <div>
            <label className="block font-medium mb-1">Origin</label>
            <input
              name="origin"
              value={form.origin || ""}
              onChange={handleChange}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
            />
          </div>
          {/* Genre dropdown */}
          <div>
            <label className="block font-medium mb-1">Genre *</label>
            <select
              name="genre"
              value={form.genre || ""}
              onChange={handleChange}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
              required
            >
              <option value="">Select genre</option>
              <option value="Green">Green</option>
              <option value="Oolong">Oolong</option>
              <option value="Black">Black</option>
              <option value="White">White</option>
              <option value="Dark">Dark</option>
            </select>
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          {/* Score */}
          <div>
            <label className="block font-medium mb-1">Score</label>
            <input
              name="score"
              value={form.score || ""}
              onChange={handleChange}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
            />
          </div>
          {/* Producer */}
          <div>
            <label className="block font-medium mb-1">Producer</label>
            <input
              name="producer.name"
              value={form.producer?.name || ""}
              onChange={handleChange}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
            />
          </div>
        </div>
        <div>
          <label className="block font-medium mb-1">Comment</label>
          <input
            name="comment"
            value={form.comment}
            onChange={handleChange}
            className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
          />
        </div>
        <div>
          <label className="block font-medium mb-2">
            Roast Level: {form.roast_level}
          </label>
          <input
            type="range"
            name="roast_level"
            min="0"
            max="100"
            value={form.roast_level ?? 0}
            onChange={handleChange}
            className="w-full accent-[#b8cb75]"
          />
          <div className="flex justify-between text-sm text-[#ccd989]">
            <span>Light</span>
            <span>Medium</span>
            <span>Dark</span>
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium mb-1">Weight (g)</label>
            <input
              type="number"
              name="weight"
              value={form.weight ?? ""}
              onChange={handleChange}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
            />
          </div>
          <div>
            <label className="block font-medium mb-1">Quantity</label>
            <input
              type="number"
              name="quantity"
              value={form.quantity ?? ""}
              onChange={handleChange}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
            />
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium mb-1">Harvest Time</label>
            <input
              type="month"
              name="harvest_time"
              onChange={(e) => {
                const value = e.target.value;
                if (!value) return;

                const formatted = value.replace("-", "");
                setForm((prev) => ({
                  ...prev,
                  harvest_time: Number(formatted),
                }));
              }}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
            />
          </div>
          <button
            type="submit"
            className="bg-[#78a043] text-white px-6 py-2 rounded-lg"
          >
            Create Asset
          </button>
        </div>
        <div className="pt-2">
          <Link
            to="/dashboard"
            className="text-[#ccd989] hover:text-[#b8cb75] hover:underline transition"
          >
            ← Go back to Dashboard
          </Link>
        </div>
      </form>
    </div>
  );
};

export default CreateAsset;
