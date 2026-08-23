import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { login, loginErrorMessage } from "../services/authServices";
import { getApiErrorCode } from "../lib/apiError";
import { useAuth } from "../context/useAuth";

const Login = () => {
  const { t } = useTranslation();
  const { refresh } = useAuth();
  const [errMsg, setErrMsg] = useState<string>("");
  const navigate = useNavigate();

  const handleLogin = async (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    setErrMsg("");
    const formData = new FormData(event.currentTarget);
    const slug = formData.get("slug") as string;
    const username = formData.get("username") as string;
    const password = formData.get("password") as string;

    try {
      await login({ slug, username, password });
      await refresh();
      navigate("/dashboard");
    } catch (err) {
      const code = getApiErrorCode(err);
      if (code === "invalid_credentials") {
        setErrMsg(t("auth.invalidCredentials"));
      } else if (code === "trial_expired") {
        setErrMsg(t("auth.trialExpired"));
      } else if (code === "tenant_suspended") {
        setErrMsg(t("auth.tenantSuspended"));
      } else {
        setErrMsg(loginErrorMessage(err, t("auth.loginUnexpectedError")));
      }
    }
  };
  return (
    <div className="min-h-screen grid grid-cols-1 md:grid-cols-2">
      <div className="hidden md:flex flex-col justify-center p-12">
        <h1 className="text-4xl font-bold mb-4 text-left">{t("auth.brandTitle")}</h1>
        <p className="text-[#d6d1c5] mb-8 text-left">{t("auth.brandSubtitle")}</p>
      </div>

      <div className="flex items-center justify-center p-6">
        <form onSubmit={handleLogin} className="w-full max-w-md space-y-6">
          <h2 className="text-2xl font-bold text-center">{t("auth.login")}</h2>

          <input
            type="text"
            name="slug"
            autoComplete="organization"
            placeholder={t("auth.slug")}
            required
            minLength={2}
            className="w-full border p-3 rounded bg-[#d3d4be80] text-[#ffffffE6]"
          />
          <input
            type="text"
            name="username"
            autoComplete="username"
            placeholder={t("auth.username")}
            required
            className="w-full border p-3 rounded bg-[#d3d4be80] text-[#ffffffE6]"
          />
          <input
            type="password"
            name="password"
            autoComplete="current-password"
            placeholder={t("auth.password")}
            required
            className="w-full border p-3 rounded bg-[#d3d4be80] text-[#ffffffE6]"
          />
          {errMsg && (
            <p className="text-red-300 text-sm text-center">{errMsg}</p>
          )}
          <button
            type="submit"
            className="w-full bg-[#bdcd68] text-white py-3 rounded"
          >
            {t("auth.login")}
          </button>

          <p className="text-center text-sm">
            {t("auth.noAccount")}{" "}
            <Link to="/signup" className="text-[#ccd989] hover:text-[#b8cb75]">
              {t("auth.signup")}
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Login;
