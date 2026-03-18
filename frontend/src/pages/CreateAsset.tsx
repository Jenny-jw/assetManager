import React, { useState, FormEvent } from "react";
import { Link } from "react-router-dom";
import type { CreateAsset } from "../types/Asset";
import axios from "axios";

const CreateAsset = () => {
  const [form, setForm] = useState<CreateAsset>({
    name: "",
    origin: "",
    genre: "",
    roastLevel: 30,
    harvestTime: undefined,
    weight: 150,
    quantity: 1,
  });
  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value === "" ? undefined : value }));
  };
  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
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
            className="w-full border rounded-lg p-2"
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
              className="w-full border rounded-lg p-2"
            />
          </div>
          {/* Genre dropdown */}
          <div>
            <label className="block font-medium mb-1">Genre *</label>
            <select
              name="genre"
              value={form.genre || ""}
              onChange={handleChange}
              className="w-full border rounded-lg p-2"
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
        <div>
          <label className="block font-medium mb-2">
            Roast Level: {form.roastLevel}
          </label>
          <input
            type="range"
            name="roastLevel"
            min="0"
            max="100"
            value={form.roastLevel ?? 0}
            onChange={handleChange}
            className="w-full"
          />
          <div className="flex justify-between text-sm text-gray-500">
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
              className="w-full border rounded-lg p-2"
            />
          </div>
          <div>
            <label className="block font-medium mb-1">Quantity</label>
            <input
              type="number"
              name="quantity"
              value={form.quantity ?? ""}
              onChange={handleChange}
              className="w-full border rounded-lg p-2"
            />
          </div>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium mb-1">Harvest Time</label>
            <input
              type="month"
              name="harvestTime"
              onChange={(e) => {
                const value = e.target.value;
                if (!value) return;

                const formatted = value.replace("-", "");
                setForm((prev) => ({
                  ...prev,
                  harvestTime: Number(formatted),
                }));
              }}
              className="w-full border rounded-lg p-2"
            />
          </div>
          <button
            type="submit"
            className="bg-lime-500 text-white px-6 py-2 rounded-lg"
          >
            Create Asset
          </button>
        </div>
        <div className="pt-2">
          <Link
            to="/"
            className="text-lime-700 hover:underline hover:text-lime-800 transition"
          >
            ← Go back to Dashboard
          </Link>
        </div>
      </form>
    </div>
  );
};

export default CreateAsset;
