import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { login } from "../services/authServices";
import { useAuth } from "../context/useAuth";

const Login = () => {
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
        setErrMsg("An unexpected error occurred during login.");
      }
    }
  };
  return (
    <div className="min-h-screen grid grid-cols-1 md:grid-cols-2">
      {/* Intro on the left */}
      <div className="hidden md:flex flex-col justify-center p-12">
        <h1 className="text-4xl font-bold mb-4">Tea Keeper 🌿</h1>
        <p className="text-gray-400 mb-6">
          Manage and track your yummy tea collection.
        </p>
        <Link
          to="/dashboard"
          className="text-lime-500 hover:text-lime-700 font-semibold"
        >
          View Dashboard as Guest →
        </Link>
      </div>

      {/* Login on the right */}
      <div className="flex items-center justify-center p-6">
        <form onSubmit={handleLogin} className="w-full max-w-md space-y-6">
          <h2 className="text-2xl font-bold text-center">Log In</h2>

          <input
            type="email"
            name="email"
            placeholder="Email"
            className="w-full border p-3 rounded"
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            className="w-full border p-3 rounded"
          />
          {errMsg && (
            <p className="text-red-300 text-sm text-center">{errMsg}</p>
          )}
          <button
            type="submit"
            className="w-full bg-lime-600 text-white py-3 rounded"
          >
            Log In
          </button>

          <p className="text-center text-sm">
            Don’t have an account?{" "}
            <Link to="/signup" className="text-lime-600 hover:text-lime-800">
              Sign Up
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Login;
