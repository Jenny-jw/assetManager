import { useState } from "react";
import { Link } from "react-router-dom";
import { isAxiosError } from "axios";
import type { CreateAssetType } from "../types/Asset";
import axios from "../lib/axios";
import { PACKAGE_WEIGHT_OPTIONS } from "../lib/teaPricing";

const INITIAL_FORM: CreateAssetType = {
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
};

type FieldErrors = Partial<Record<keyof CreateAssetType, string>>;

type ValidationDetail = {
  loc: (string | number)[];
  msg: string;
};

function validateForm(form: CreateAssetType): FieldErrors {
  const errors: FieldErrors = {};

  if (!(form.name ?? "").trim()) {
    errors.name = "Name is required.";
  }
  if (!form.genre) {
    errors.genre = "Please select a genre";
  }
  if (form.price == null || Number.isNaN(form.price) || form.price < 0) {
    errors.price = "Price per 斤 is required";
  }
  if (
    form.weight == null ||
    !PACKAGE_WEIGHT_OPTIONS.includes(
      form.weight as (typeof PACKAGE_WEIGHT_OPTIONS)[number],
    )
  ) {
    errors.weight = "Please select package weight (75g or 150g).";
  }
  if (
    form.quantity == null ||
    Number.isNaN(form.quantity) ||
    form.quantity < 0
  ) {
    errors.quantity = "Number of packages is required";
  }

  return errors;
}

function formatApiError(error: unknown): string {
  if (!isAxiosError(error)) {
    return "Failed to create asset. Please try again.";
  }

  const data = error.response?.data as {
    detail?: string | ValidationDetail[];
    error?: { message?: string };
  };

  if (Array.isArray(data?.detail)) {
    return data.detail
      .map((item) => {
        const field = String(item.loc[item.loc.length - 1] ?? "field");
        return `${field}: ${item.msg}`;
      })
      .join(" · ");
  }

  if (typeof data?.detail === "string") {
    return data.detail;
  }

  if (data?.error?.message) {
    return data.error.message;
  }

  return "Failed to create asset. Please try again.";
}

const CreateAsset = () => {
  const [form, setForm] = useState<CreateAssetType>(INITIAL_FORM);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    setFieldErrors((prev) => ({ ...prev, [name]: undefined }));
    setFormError("");
    setSuccessMessage("");

    if (name === "weight") {
      setForm((prev) => ({
        ...prev,
        weight: value === "" ? undefined : Number(value),
      }));
      return;
    }
    if (name === "name" || name === "genre") {
      setForm((prev) => ({ ...prev, [name]: value }));
      return;
    }
    if (
      name === "price" ||
      name === "quantity" ||
      name === "score" ||
      name === "roast_level"
    ) {
      setForm((prev) => ({
        ...prev,
        [name]: value === "" ? undefined : Number(value),
      }));
      return;
    }
    setForm((prev) => ({ ...prev, [name]: value === "" ? undefined : value }));
  };

  const handleDateChange = (field: "harvest_time", value: string) => {
    setFormError("");
    setSuccessMessage("");
    setForm((prev) => ({
      ...prev,
      [field]: value ? Number(value.replace("-", "")) : undefined,
    }));
  };

  const resetForm = () => {
    setForm({ ...INITIAL_FORM });
    setFieldErrors({});
    setFormError("");
  };

  const handleSubmit = async (e: React.SubmitEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (isSubmitting) return;

    const errors = validateForm(form);
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      setFormError("Please complete all required fields before submitting.");
      return;
    }

    setIsSubmitting(true);
    setFormError("");
    setSuccessMessage("");

    try {
      await axios.post("/tea", form);
      setSuccessMessage("Added successfully! You can now add the next asset.");
      resetForm();
    } catch (error) {
      setFormError(formatApiError(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  const fieldErrorClass = "text-sm text-red-300 mt-1";

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <h1 className="text-3xl font-bold">Create Asset</h1>
      <form onSubmit={handleSubmit} className="space-y-6" noValidate>
        {successMessage && (
          <p className="rounded-lg bg-green-50 border border-green-200 px-4 py-3 text-sm text-green-800">
            {successMessage}
          </p>
        )}
        {formError && (
          <p className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
            {formError}
          </p>
        )}

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium mb-1">Name *</label>
            <input
              name="name"
              value={form.name ?? ""}
              onChange={handleChange}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            />
            {fieldErrors.name && (
              <p className={fieldErrorClass}>{fieldErrors.name}</p>
            )}
          </div>
          <div>
            <label className="block font-medium mb-1">Producer</label>
            <input
              name="producer"
              value={form.producer || ""}
              onChange={handleChange}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            />
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block font-medium mb-1">Price per 斤 *</label>
            <input
              type="number"
              name="price"
              min={0}
              value={form.price ?? ""}
              onChange={handleChange}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            />
            {fieldErrors.price && (
              <p className={fieldErrorClass}>{fieldErrors.price}</p>
            )}
          </div>
          <div>
            <label className="block font-medium mb-1">
              Weight per Package (g) *
            </label>
            <select
              name="weight"
              value={form.weight ?? ""}
              onChange={handleChange}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            >
              <option value="">Select weight</option>
              {PACKAGE_WEIGHT_OPTIONS.map((grams) => (
                <option key={grams} value={grams}>
                  {grams} g
                </option>
              ))}
            </select>
            {fieldErrors.weight && (
              <p className={fieldErrorClass}>{fieldErrors.weight}</p>
            )}
          </div>
          <div>
            <label className="block font-medium mb-1">
              Number of Packages *
            </label>
            <input
              type="number"
              name="quantity"
              min={0}
              value={form.quantity ?? ""}
              onChange={handleChange}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            />
            {fieldErrors.quantity && (
              <p className={fieldErrorClass}>{fieldErrors.quantity}</p>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium mb-1">Harvest Time</label>
            <input
              type="date"
              name="harvest_time"
              onChange={(e) => handleDateChange("harvest_time", e.target.value)}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
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
              disabled={isSubmitting}
              className="w-full accent-[#b8cb75] disabled:opacity-60"
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
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            />
          </div>
          <div>
            <label className="block font-medium mb-1">Genre *</label>
            <select
              name="genre"
              value={form.genre || ""}
              onChange={handleChange}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            >
              <option value="">Select genre</option>
              <option value="Green">Green</option>
              <option value="Oolong">Oolong</option>
              <option value="Black">Black</option>
              <option value="White">White</option>
            </select>
            {fieldErrors.genre && (
              <p className={fieldErrorClass}>{fieldErrors.genre}</p>
            )}
          </div>

          <div>
            <label className="block font-medium mb-1">Score</label>
            <input
              name="score"
              value={form.score ?? ""}
              onChange={handleChange}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            />
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium mb-1">Comment</label>
            <input
              name="comment"
              value={form.comment ?? ""}
              onChange={handleChange}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="bg-[#78a043] text-white px-6 py-2 rounded-lg transition disabled:opacity-60 disabled:cursor-not-allowed min-w-36"
          >
            {isSubmitting ? "Creating…" : "Create Asset"}
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
