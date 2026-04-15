import { Link } from "react-router-dom";

const Login = () => {
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
        <div className="w-full max-w-md space-y-6">
          <h2 className="text-2xl font-bold text-center">Log In</h2>

          <input
            type="email"
            placeholder="Email"
            className="w-full border p-3 rounded"
          />
          <input
            type="password"
            placeholder="Password"
            className="w-full border p-3 rounded"
          />

          <button className="w-full bg-lime-600 text-white py-3 rounded">
            Log In
          </button>

          <p className="text-center text-sm">
            Don’t have an account?{" "}
            <Link to="/signup" className="text-lime-600 hover:text-lime-800">
              Sign Up
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
