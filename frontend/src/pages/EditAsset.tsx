import type { Asset } from "../types/Asset";
import type { ChangeEvent, SubmitEvent } from "react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { isAxiosError } from "axios";
import axios from "../lib/axios";
import {
  dateInputToHarvestInt,
  harvestIntToDateInput,
} from "../lib/harvestDate";
import { PACKAGE_WEIGHT_OPTIONS } from "../lib/teaPricing";

type EditForm = {
  name: string;
  origin: string;
  genre: string;
  producer: string;
  harvest_time: string;
  roast_level: string;
  weight: string;
  price: string;
  quantity: string;
  score: string;
  comment: string;
};

type FieldErrors = Partial<Record<keyof EditForm, string>>;

type ValidationDetail = {
  loc: (string | number)[];
  msg: string;
};

const FIELD_LABELS: Partial<Record<keyof EditForm, string>> = {
  name: "Name",
  genre: "Genre",
  price: "Price per 斤",
  weight: "Weight per package",
  quantity: "Number of packages",
  harvest_time: "Harvest time",
};

function nullableString(value: string): string | null {
  return value.trim() === "" ? null : value.trim();
}

function validateForm(form: EditForm): FieldErrors {
  const errors: FieldErrors = {};

  if (!(form.name ?? "").trim()) {
    errors.name = "Name is required";
  }
  if (!(form.genre ?? "").trim()) {
    errors.genre = "Genre is required";
  }
  if (form.price.trim() === "") {
    errors.price = "Price per 斤 is required";
  } else if (Number.isNaN(Number(form.price)) || Number(form.price) < 0) {
    errors.price = "Enter a valid price";
  }
  if (form.weight.trim() === "") {
    errors.weight = "Please select package weight";
  }
  if (form.quantity.trim() === "") {
    errors.quantity = "Number of packages is required";
  } else {
    const qty = Number(form.quantity);
    if (Number.isNaN(qty) || qty < 0) {
      errors.quantity = "Enter a valid number of packages";
    }
  }
  if (form.harvest_time.trim() !== "") {
    const harvest = Number(form.harvest_time);
    if (Number.isNaN(harvest) || harvest < 20100101 || harvest > 22001231) {
      errors.harvest_time = "Pick a valid harvest date";
    }
  }

  return errors;
}

function formatApiError(error: unknown): string {
  if (!isAxiosError(error)) {
    return "Failed to update tea. Please try again.";
  }

  const data = error.response?.data as {
    detail?: string | ValidationDetail[];
    error?: { message?: string };
  };

  if (Array.isArray(data?.detail)) {
    return data.detail
      .map((item) => {
        const fieldKey = String(item.loc[item.loc.length - 1] ?? "field");
        const label =
          FIELD_LABELS[fieldKey as keyof EditForm] ??
          fieldKey.replace(/_/g, " ");
        return `${label}: ${item.msg}`;
      })
      .join(" · ");
  }

  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (data?.error?.message) {
    return data.error.message;
  }

  return "Failed to update tea. Please try again.";
}

function buildPayload(form: EditForm) {
  return {
    name: form.name.trim(),
    genre: form.genre.trim(),
    price: Number(form.price),
    weight: Number(form.weight),
    quantity: Number(form.quantity),
    origin: nullableString(form.origin),
    producer: nullableString(form.producer),
    comment: nullableString(form.comment),
    harvest_time: form.harvest_time === "" ? null : Number(form.harvest_time),
    roast_level: form.roast_level === "" ? null : Number(form.roast_level),
    score: form.score === "" ? null : Number(form.score),
  };
}

const EditAsset = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [form, setForm] = useState<EditForm>({
    name: "",
    origin: "",
    genre: "",
    producer: "",
    harvest_time: "",
    roast_level: "",
    weight: "150",
    price: "",
    quantity: "",
    score: "",
    comment: "",
  });

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [errMsg, setErrMsg] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});

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
          producer: asset.producer ?? "",
          harvest_time: asset.harvest_time?.toString() ?? "",
          roast_level: asset.roast_level?.toString() ?? "",
          weight: asset.weight?.toString() ?? "150",
          price: asset.price?.toString() ?? "",
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
    e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
    setErrMsg("");
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleHarvestDateChange = (value: string) => {
    setFieldErrors((prev) => ({ ...prev, harvest_time: undefined }));
    setErrMsg("");
    setForm((prev) => ({
      ...prev,
      harvest_time: dateInputToHarvestInt(value),
    }));
  };

  const handleSubmit = async (e: SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!e.currentTarget.reportValidity()) {
      return;
    }

    if (!id) return;

    const errors = validateForm(form);
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setErrMsg("Please fix the highlighted fields.");
      return;
    }

    setIsSaving(true);
    setErrMsg("");
    setFieldErrors({});

    try {
      await axios.patch(`/tea/${id}`, buildPayload(form));
      navigate("/assets");
    } catch (error) {
      console.error("Failed to update tea:", error);
      setErrMsg(formatApiError(error));
    } finally {
      setIsSaving(false);
    }
  };

  const fieldErrorClass = "text-sm text-red-600 mt-1";

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

        <div className="grid md:grid-cols-2 gap-4">
          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">Name</span>
            <input
              name="name"
              value={form.name}
              onChange={handleChange}
              required
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
            {fieldErrors.name && (
              <p className={fieldErrorClass}>{fieldErrors.name}</p>
            )}
          </label>
          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">Producer</span>
            <input
              name="producer"
              value={form.producer}
              onChange={handleChange}
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
          </label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">
              Price per 斤
            </span>
            <input
              type="number"
              name="price"
              min={0}
              value={form.price}
              onChange={handleChange}
              required
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
            {fieldErrors.price && (
              <p className={fieldErrorClass}>{fieldErrors.price}</p>
            )}
          </label>
          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">
              Weight per Package (g)
            </span>
            <select
              name="weight"
              value={form.weight}
              onChange={handleChange}
              required
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            >
              {PACKAGE_WEIGHT_OPTIONS.map((grams) => (
                <option key={grams} value={grams}>
                  {grams} g
                </option>
              ))}
            </select>
            {fieldErrors.weight && (
              <p className={fieldErrorClass}>{fieldErrors.weight}</p>
            )}
          </label>
          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">
              Number of Packages
            </span>
            <input
              type="number"
              name="quantity"
              value={form.quantity}
              onChange={handleChange}
              required
              min={0}
              step={1}
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
            {fieldErrors.quantity && (
              <p className={fieldErrorClass}>{fieldErrors.quantity}</p>
            )}
          </label>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">Genre</span>
            <input
              name="genre"
              value={form.genre}
              onChange={handleChange}
              required
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
            {fieldErrors.genre && (
              <p className={fieldErrorClass}>{fieldErrors.genre}</p>
            )}
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
            <span className="text-sm font-medium text-gray-600">
              Harvest Time
            </span>
            <input
              type="date"
              name="harvest_time"
              value={harvestIntToDateInput(form.harvest_time)}
              onChange={(e) => handleHarvestDateChange(e.target.value)}
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
            {fieldErrors.harvest_time && (
              <p className={fieldErrorClass}>{fieldErrors.harvest_time}</p>
            )}
          </label>
          <label className="space-y-2">
            <span className="text-sm font-medium text-gray-600">Score</span>
            <input
              type="number"
              name="score"
              min={0}
              max={100}
              value={form.score}
              onChange={handleChange}
              className="w-full rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
            />
          </label>
        </div>

        <label className="space-y-2 block">
          <span className="text-sm font-medium text-gray-600">Roast Level</span>
          <input
            type="range"
            name="roast_level"
            min="0"
            max="100"
            value={form.roast_level}
            onChange={handleChange}
            className="w-full accent-[#78a043]"
          />
          <p className="text-right text-sm font-semibold text-[#9f655d]">
            {form.roast_level || "-"}
          </p>
        </label>

        <label className="space-y-2 block">
          <span className="text-sm font-medium text-gray-600">Comment</span>
          <textarea
            name="comment"
            value={form.comment}
            onChange={handleChange}
            rows={4}
            className="w-full resize-none rounded-lg border px-3 py-2 text-gray-800 bg-[#d3d4be80]"
          />
        </label>

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
