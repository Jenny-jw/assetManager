import type { Asset } from "../types/Asset";
import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "../lib/axios";

type EditForm = {
  name: string;
  origin: string;
  genre: string;
  roast_level: string;
  weight: string;
  quantity: string;
  score: string;
  comment: string;
};

const EditAsset = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [form, setForm] = useState<EditForm>({
    name: "",
    origin: "",
    genre: "",
    roast_level: "",
    weight: "",
    quantity: "",
    score: "",
    comment: "",
  });

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errMsg, setErrMsg] = useState("");

  useEffect(() => {
    const fetchAsset = async () => {
      if (!id) {
        setErrMsg("Invalid tea id.");
        setIsLoading(false);
        return;
      }

      try {
        const res = await axios.get<Asset>(`/tea/${id}`);
        const asset = res.data;

        setForm({
          name: asset.name ?? "",
          origin: asset.origin ?? "",
          genre: asset.genre ?? "",
          roast_level: asset.roast_level ?? "",
          weight: asset.weight?.toString() ?? "",
          quantity: asset.quantity?.toString() ?? "",
          score: asset.score?.toString() ?? "",
          comment: asset.comment ?? "",
        });
      } catch (error) {
        console.error("Failed to load tea:", error);
        setErrMsg("Failed to load tea.");
      } finally {
        setIsLoading(false);
      }
    };

    fetchAsset();
  }, [id]);

  const handleChange = (
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    const { name, value } = e.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!id) return;

    setIsSaving(true);
    setErrMsg("");

    const payload = {
      name: form.name,
      origin: form.origin || undefined,
      genre: form.genre,
      roast_level: form.roast_level || undefined,
      weight: form.weight === "" ? undefined : Number(form.weight),
      quantity: form.quantity === "" ? undefined : Number(form.quantity),
      score: form.score === "" ? undefined : Number(form.score),
      comment: form.comment || undefined,
    };

    try {
      await axios.patch(`/tea/${id}`, payload);
      navigate("/assets");
    } catch (error) {
      console.error("Failed to update tea:", error);
      setErrMsg("Failed to update tea. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-4 md:p-6">
        <p className="text-[#ece2ba]">Loading...</p>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-6 space-y-6">
      <div className="flex items-start justify-between gap-4 px-2">
        <div className="text-left">
          <h1 className="text-3xl font-bold">Edit Asset</h1>
          <p className="text-sm text-[#d6d1c5]">Update tea details</p>
        </div>

        <button
          type="button"
          onClick={() => navigate("/assets")}
          className="px-4 py-2 text-sm rounded-lg bg-[#64794d] text-white hover:bg-lime-900 transition"
        >
          Back
        </button>
      </div>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-2xl shadow-sm border p-5 md:p-6 space-y-5 text-left"
      >
        {errMsg && (
          <p className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {errMsg}
          </p>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">Name</span>
            <input
              name="name"
              value={form.name}
              onChange={handleChange}
              required
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
          </label>

          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">Origin</span>
            <input
              name="origin"
              value={form.origin}
              onChange={handleChange}
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
          </label>

          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">Genre</span>
            <input
              name="genre"
              value={form.genre}
              onChange={handleChange}
              required
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
          </label>

          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">Roast</span>
            <input
              name="roast_level"
              value={form.roast_level}
              onChange={handleChange}
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
          </label>

          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">Weight</span>
            <input
              type="number"
              name="weight"
              value={form.weight}
              onChange={handleChange}
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
          </label>

          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">Quantity</span>
            <input
              type="number"
              name="quantity"
              value={form.quantity}
              onChange={handleChange}
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
          </label>

          <label className="space-y-2 md:col-span-2">
            <span className="text-sm font-medium text-gray-600">Score</span>
            <input
              type="range"
              name="score"
              min="0"
              max="100"
              value={form.score}
              onChange={handleChange}
              className="w-full accent-[#78a043]"
            />
            <p className="text-right text-sm font-semibold text-[#9f655d]">
              {form.score || "-"}
            </p>
          </label>

          <label className="space-y-2 md:col-span-2">
            <span className="text-sm font-medium text-gray-600">Comment</span>
            <textarea
              name="comment"
              value={form.comment}
              onChange={handleChange}
              rows={4}
              className="w-full resize-none rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
          </label>
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button
            type="button"
            onClick={() => navigate("/assets")}
            className="px-4 py-2 rounded-lg bg-gray-200 text-gray-700 hover:bg-gray-300 transition"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={isSaving}
            className="px-4 py-2 rounded-lg bg-[#78a043] text-white hover:bg-lime-900 transition disabled:opacity-60"
          >
            {isSaving ? "Saving..." : "Save"}
          </button>
        </div>
      </form>
    </div>
  );
};

export default EditAsset;
