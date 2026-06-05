import React, { useState } from "react";
import { Link } from "react-router-dom";
import type { CreateAssetType } from "../types/Asset";
import axios from "../lib/axios";
import { PACKAGE_WEIGHT_OPTIONS } from "../lib/teaPricing";

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
    price: 2000,
    comment: "",
    producer: "",
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    if (name === "weight") {
      setForm((prev) => ({
        ...prev,
        weight: value === "" ? undefined : Number(value),
      }));
      return;
    }
    if (name === "price" || name === "quantity" || name === "score" || name === "roast_level") {
      setForm((prev) => ({
        ...prev,
        [name]: value === "" ? undefined : Number(value),
      }));
      return;
    }
    setForm((prev) => ({ ...prev, [name]: value === "" ? undefined : value }));
  };

  const handleDateChange = (field: "harvest_time", value: string) => {
    setForm((prev) => ({
      ...prev,
      [field]: value ? Number(value.replace("-", "")) : undefined,
    }));
  };

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    try {
      await axios.post("/tea", form);
      console.log("Tea added!");
    } catch (err) {
      console.log(err);
    }
  };

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Create Asset</h1>
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid md:grid-cols-2 gap-4">
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
          <div>
            <label className="block font-medium mb-1">Producer</label>
            <input
              name="producer"
              value={form.producer || ""}
              onChange={handleChange}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
            />
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block font-medium mb-1">Price per 斤 *</label>
            <input
              type="number"
              name="price"
              value={form.price ?? ""}
              onChange={handleChange}
              required
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
            />
          </div>
          <div>
            <label className="block font-medium mb-1">
              Weight per Package (g) *
            </label>
            <select
              name="weight"
              value={form.weight ?? ""}
              onChange={handleChange}
              required
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
            >
              <option value="">Select weight</option>
              {PACKAGE_WEIGHT_OPTIONS.map((grams) => (
                <option key={grams} value={grams}>
                  {grams} g
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block font-medium mb-1">
              Number of Packages *
            </label>
            <input
              type="number"
              name="quantity"
              value={form.quantity ?? ""}
              onChange={handleChange}
              required
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
            />
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium mb-1">Harvest Time</label>
            <input
              type="date"
              name="harvest_time"
              onChange={(e) => handleDateChange("harvest_time", e.target.value)}
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
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block font-medium mb-1">Origin</label>
            <input
              name="origin"
              value={form.origin || ""}
              onChange={handleChange}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
            />
          </div>
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
            </select>
          </div>

          <div>
            <label className="block font-medium mb-1">Score</label>
            <input
              name="score"
              value={form.score || ""}
              onChange={handleChange}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6]"
            />
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium mb-1">Comment</label>
            <input
              name="comment"
              value={form.comment}
              onChange={handleChange}
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