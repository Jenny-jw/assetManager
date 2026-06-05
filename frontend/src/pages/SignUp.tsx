import type React from "react";
import { signup } from "../services/authServices";
import { useState, type SubmitEventHandler } from "react";

declare module "react-router" {
  interface FetcherFormProps {
    onSubmit?: SubmitEventHandler<HTMLFormElement>;
  }
}

const SignUp = () => {
  const [errMsg, setErrMsg] = useState<string>("");
  const handleSubmit = async (event: React.SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);
    const name = formData.get("name") as string;
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    try {
      await signup(name, email, password);
      console.log("User signed up! 🎉");
    } catch (err) {
      if (err instanceof Error) {
        const msg = err.message;
        if (msg === "Email already registered") {
          setErrMsg("This email is already registered. Please log in instead.");
        } else {
          setErrMsg("An error occurred during sign up. Please try again.");
        }
      } else {
        console.error("Unexpected error during sign up:", err);
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="bg-lime-600/50 p-8 rounded shadow-md w-full max-w-md">
        <h2 className="text-2xl font-bold mb-6 text-center">Sign Up</h2>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label
              htmlFor="name"
              className="block text-sm font-medium text-gray-200"
            >
              Name
            </label>
            <input
              type="text"
              id="name"
              name="name"
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-200"
            >
              Email
            </label>
            <input
              type="email"
              id="email"
              name="email"
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-200"
            >
              Password
            </label>
            <input
              type="password"
              id="password"
              name="password"
              required
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            />
          </div>
          {errMsg && (
            <p className="text-red-300 text-sm text-center">{errMsg}</p>
          )}
          <button
            type="submit"
            className="w-full bg-lime-600 text-white py-2 rounded hover:bg-lime-700 hover:border-lime-500 transition"
          >
            Sign Up
          </button>
        </form>
        <p className="mt-4 text-center text-sm">
          Already have an account?{" "}
          <a href="/login" className="text-lime-300 hover:text-lime-500">
            Log In
          </a>
        </p>
      </div>
    </div>
  );
};

export default SignUp;