import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { login } from "../services/authServices";
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
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    try {
      await login(email, password);
      await refresh();
      navigate("/dashboard");
    } catch (err) {
      if (err instanceof Error && err.message) {
        setErrMsg(err.message);
      } else {
        console.error("Unexpected error during login:", err);
        setErrMsg(t("auth.loginUnexpectedError"));
      }
    }
  };
  return (
    <div className="min-h-screen grid grid-cols-1 md:grid-cols-2">
      <div className="hidden md:flex flex-col justify-center p-12">
        <h1 className="text-4xl font-bold mb-4 text-left">{t("auth.brandTitle")}</h1>
        <p className="text-[#d6d1c5] mb-8 text-left">{t("auth.brandSubtitle")}</p>
        <Link
          to="/dashboard"
          className="text-[#ccd989] hover:text-[#b8cb75] font-semibold text-left"
        >
          {t("auth.viewGuestDashboard")}
        </Link>
      </div>

      <div className="flex items-center justify-center p-6">
        <form onSubmit={handleLogin} className="w-full max-w-md space-y-6">
          <h2 className="text-2xl font-bold text-center">{t("auth.login")}</h2>

          <input
            type="email"
            name="email"
            placeholder={t("auth.email")}
            className="w-full border p-3 rounded bg-[#d3d4be80] text-[#ffffffE6]"
          />
          <input
            type="password"
            name="password"
            placeholder={t("auth.password")}
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
