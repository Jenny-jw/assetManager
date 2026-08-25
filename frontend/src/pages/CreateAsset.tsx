import { useState } from "react";
import { Link } from "react-router-dom";
import type { TFunction } from "i18next";
import { useTranslation } from "react-i18next";

import LanguageSwitcher from "../components/LanguageSwitcher";
import type { CreateAssetType } from "../types/Asset";
import { getApiErrorMessage } from "../lib/apiError";
import { PACKAGE_WEIGHT_OPTIONS } from "../lib/teaPricing";
import { createStock } from "../services/stockServices";

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

const GENRE_OPTIONS = ["Green", "Oolong", "Black", "White"] as const;

type FieldErrors = Partial<Record<keyof CreateAssetType, string>>;

function validateForm(form: CreateAssetType): FieldErrors {
  const errors: FieldErrors = {};

  if (!(form.name ?? "").trim()) {
    errors.name = "inventory.errors.nameRequired";
  }
  if (!form.genre) {
    errors.genre = "inventory.errors.genreSelect";
  }
  if (form.price == null || Number.isNaN(form.price) || form.price < 0) {
    errors.price = "inventory.errors.priceRequired";
  }
  if (
    form.weight == null ||
    !PACKAGE_WEIGHT_OPTIONS.includes(
      form.weight as (typeof PACKAGE_WEIGHT_OPTIONS)[number],
    )
  ) {
    errors.weight = "inventory.errors.weightRequired";
  }
  if (
    form.quantity == null ||
    Number.isNaN(form.quantity) ||
    form.quantity < 0
  ) {
    errors.quantity = "inventory.errors.quantityRequired";
  }

  return errors;
}

function formatApiError(error: unknown, t: TFunction): string {
  return getApiErrorMessage(error, t("inventory.create.failed"));
}

const CreateAsset = () => {
  const { t } = useTranslation();
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
      setFormError(t("inventory.create.incomplete"));
      return;
    }

    setIsSubmitting(true);
    setFormError("");
    setSuccessMessage("");

    try {
      await createStock(form);
      setSuccessMessage(t("inventory.create.success"));
      resetForm();
    } catch (error) {
      setFormError(formatApiError(error, t));
    } finally {
      setIsSubmitting(false);
    }
  };

  const fieldErrorClass = "text-sm text-red-300 mt-1";

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between gap-4">
        <h1 className="text-3xl font-bold">{t("inventory.create.title")}</h1>
        <LanguageSwitcher />
      </div>
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
            <label className="block font-medium mb-1">
              {t("inventory.fields.name")} *
            </label>
            <input
              name="name"
              value={form.name ?? ""}
              onChange={handleChange}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            />
            {fieldErrors.name && (
              <p className={fieldErrorClass}>{t(fieldErrors.name)}</p>
            )}
          </div>
          <div>
            <label className="block font-medium mb-1">
              {t("inventory.fields.producer")}
            </label>
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
            <label className="block font-medium mb-1">
              {t("inventory.fields.pricePerJin")} *
            </label>
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
              <p className={fieldErrorClass}>{t(fieldErrors.price)}</p>
            )}
          </div>
          <div>
            <label className="block font-medium mb-1">
              {t("inventory.fields.weightPerPackage")} *
            </label>
            <select
              name="weight"
              value={form.weight ?? ""}
              onChange={handleChange}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            >
              <option value="">{t("inventory.create.selectWeight")}</option>
              {PACKAGE_WEIGHT_OPTIONS.map((grams) => (
                <option key={grams} value={grams}>
                  {t("inventory.weightGrams", { grams })}
                </option>
              ))}
            </select>
            {fieldErrors.weight && (
              <p className={fieldErrorClass}>{t(fieldErrors.weight)}</p>
            )}
          </div>
          <div>
            <label className="block font-medium mb-1">
              {t("inventory.fields.packages")} *
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
              <p className={fieldErrorClass}>{t(fieldErrors.quantity)}</p>
            )}
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div>
            <label className="block font-medium mb-1">
              {t("inventory.fields.harvestTime")}
            </label>
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
              {t("inventory.fields.roastLevelWithValue", {
                level: form.roast_level,
              })}
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
              <span>{t("inventory.roast.light")}</span>
              <span>{t("inventory.roast.medium")}</span>
              <span>{t("inventory.roast.dark")}</span>
            </div>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          <div>
            <label className="block font-medium mb-1">
              {t("inventory.fields.origin")}
            </label>
            <input
              name="origin"
              value={form.origin || ""}
              onChange={handleChange}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            />
          </div>
          <div>
            <label className="block font-medium mb-1">
              {t("inventory.fields.genre")} *
            </label>
            <select
              name="genre"
              value={form.genre || ""}
              onChange={handleChange}
              disabled={isSubmitting}
              className="w-full border rounded-lg p-2 bg-[#d3d4be80] text-[#ffffffE6] disabled:opacity-60"
            >
              <option value="">{t("inventory.create.selectGenre")}</option>
              {GENRE_OPTIONS.map((genre) => (
                <option key={genre} value={genre}>
                  {t(`inventory.genres.${genre}`)}
                </option>
              ))}
            </select>
            {fieldErrors.genre && (
              <p className={fieldErrorClass}>{t(fieldErrors.genre)}</p>
            )}
          </div>

          <div>
            <label className="block font-medium mb-1">
              {t("inventory.fields.score")}
            </label>
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
            <label className="block font-medium mb-1">
              {t("inventory.fields.comment")}
            </label>
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
            {isSubmitting
              ? t("inventory.create.submitting")
              : t("inventory.create.submit")}
          </button>
        </div>

        <div className="pt-2">
          <Link
            to="/dashboard"
            className="text-[#ccd989] hover:text-[#b8cb75] hover:underline transition"
          >
            {t("inventory.create.backToDashboard")}
          </Link>
        </div>
      </form>
    </div>
  );
};

export default CreateAsset;