import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { login, signup } from "../services/authServices";
import { getApiErrorCode } from "../lib/apiError";
import { useAuth } from "../context/useAuth";
import { Edition } from "../types/Deployment";

const SignUp = () => {
  const { t } = useTranslation();
  const { refresh } = useAuth();
  const navigate = useNavigate();
  const [errMsg, setErrMsg] = useState<string>("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (isSubmitting) return;

    const formData = new FormData(event.currentTarget);
    const slug = String(formData.get("slug") ?? "");
    const username = String(formData.get("username") ?? "");
    const name = String(formData.get("name") ?? "");
    const email = String(formData.get("email") ?? "");
    const password = String(formData.get("password") ?? "");
    const editionRaw = String(formData.get("edition") ?? Edition.PERSONAL);
    const edition =
      editionRaw === Edition.PROFESSIONAL
        ? Edition.PROFESSIONAL
        : Edition.PERSONAL;

    setIsSubmitting(true);
    setErrMsg("");

    try {
      await signup({ slug, username, name, email, password, edition });
      await login({ slug, username, password });
      await refresh();
      navigate("/dashboard");
    } catch (err) {
      const code = getApiErrorCode(err);
      if (code === "slug_taken") {
        setErrMsg(t("auth.signupSlugTaken"));
      } else if (code === "duplicate_registration") {
        setErrMsg(t("auth.signupDuplicate"));
      } else {
        setErrMsg(t("auth.signupError"));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="relative min-h-screen grid grid-cols-1 md:grid-cols-2">
      <div className="absolute top-4 right-4 z-10">
        <LanguageSwitcher />
      </div>
      <div className="hidden md:flex flex-col justify-center p-12">
        <h1 className="text-4xl font-bold mb-4 text-left">{t("auth.brandTitle")}</h1>
        <p className="text-[#d6d1c5] mb-8 text-left">{t("auth.brandSubtitle")}</p>
      </div>

      <div className="flex items-center justify-center p-6">
        <form onSubmit={handleSubmit} className="w-full max-w-md space-y-4">
          <h2 className="text-2xl font-bold text-center">{t("auth.signup")}</h2>

          <div>
            <input
              type="text"
              name="slug"
              autoComplete="organization"
              placeholder={t("auth.slug")}
              required
              minLength={2}
              maxLength={100}
              pattern="[A-Za-z0-9]+(-[A-Za-z0-9]+)*"
              title={t("auth.slugHint")}
              className="w-full border p-3 rounded bg-[#d3d4be80] text-[#ffffffE6]"
            />
            <p className="mt-1 text-xs text-[#d6d1c5]">{t("auth.slugHint")}</p>
          </div>
          <input
            type="text"
            name="username"
            autoComplete="username"
            placeholder={t("auth.username")}
            required
            maxLength={50}
            className="w-full border p-3 rounded bg-[#d3d4be80] text-[#ffffffE6]"
          />
          <input
            type="text"
            name="name"
            autoComplete="name"
            placeholder={t("auth.name")}
            required
            maxLength={100}
            className="w-full border p-3 rounded bg-[#d3d4be80] text-[#ffffffE6]"
          />
          <input
            type="email"
            name="email"
            autoComplete="email"
            placeholder={t("auth.email")}
            className="w-full border p-3 rounded bg-[#d3d4be80] text-[#ffffffE6]"
          />
          <div>
            <input
              type="password"
              name="password"
              autoComplete="new-password"
              placeholder={t("auth.password")}
              required
              minLength={8}
              className="w-full border p-3 rounded bg-[#d3d4be80] text-[#ffffffE6]"
            />
            <p className="mt-1 text-xs text-[#d6d1c5]">{t("auth.passwordHint")}</p>
          </div>

          <fieldset className="space-y-2">
            <legend className="text-sm font-medium">{t("auth.edition")}</legend>
            <label className="flex items-start gap-2 text-sm">
              <input
                type="radio"
                name="edition"
                value={Edition.PERSONAL}
                defaultChecked
                className="mt-1"
              />
              <span>
                <span className="font-medium">{t("auth.editionPersonal")}</span>
                <span className="block text-[#d6d1c5]">
                  {t("auth.editionPersonalHint")}
                </span>
              </span>
            </label>
            <label className="flex items-start gap-2 text-sm">
              <input
                type="radio"
                name="edition"
                value={Edition.PROFESSIONAL}
                className="mt-1"
              />
              <span>
                <span className="font-medium">
                  {t("auth.editionProfessional")}
                </span>
                <span className="block text-[#d6d1c5]">
                  {t("auth.editionProfessionalHint")}
                </span>
              </span>
            </label>
          </fieldset>

          {errMsg && (
            <p className="text-red-300 text-sm text-center">{errMsg}</p>
          )}
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-[#bdcd68] text-white py-3 rounded disabled:opacity-70"
          >
            {t("auth.signup")}
          </button>

          <p className="text-center text-sm">
            {t("auth.hasAccount")}{" "}
            <Link to="/login" className="text-[#ccd989] hover:text-[#b8cb75]">
              {t("auth.login")}
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default SignUp;
