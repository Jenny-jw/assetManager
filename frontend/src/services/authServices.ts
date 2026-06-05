import api from "../lib/axios";
import axios from "axios";

export const signup = async (name: string, email: string, password: string) => {
  const response = await api.post("/auth/signup", {
    name,
    email,
    password,
  });
  return response.data;
};

export const login = async (email: string, password: string) => {
  try {
    const response = await api.post(
      "/auth/login",
      { email, password },
      {
        withCredentials: true,
      },
    );
    return response.data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      const detail = err.response?.data?.detail;

      if (typeof detail === "string") {
        throw new Error(detail);
      }
    }

    throw new Error("An unexpected error occurred during login.");
  }
};

export const logout = async () => {
  await api.post("/auth/logout", {}, { withCredentials: true });
};

export const getCurrentUser = async () => {
  const response = await api.get("/security/me", { withCredentials: true });
  return response.data;
};