import api from "../lib/axios";

export const signup = async (name: string, email: string, password: string) => {
  const response = await api.post("/api/auth/signup", {
    name,
    email,
    password,
  });
  return response.data;
};

export const login = async (email: string, password: string) => {
  const response = await api.post("/auth/login", { email, password });
  return response.data;
};

export const logout = async () => {
  await api.post("/auth/logout");
};

export const getCurrentUser = async () => {
  const response = await api.get("/auth/me");
  return response.data;
};
