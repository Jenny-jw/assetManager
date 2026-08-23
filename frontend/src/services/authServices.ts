import api from "../lib/axios";
import axios from "axios";
import { getApiErrorMessage } from "../lib/apiError";
import type { Edition } from "../types/Deployment";
import type { User } from "../types/User";

export type SignupPayload = {
  slug: string;
  username: string;
  name: string;
  email?: string | null;
  password: string;
  edition: Edition;
};

export type LoginPayload = {
  slug: string;
  username: string;
  password: string;
};

export const normalizeSlug = (raw: string): string => raw.trim().toLowerCase();

export const signup = async (payload: SignupPayload): Promise<User> => {
  const email = payload.email?.trim() ? payload.email.trim() : null;
  const response = await api.post<User>("/auth/signup", {
    slug: normalizeSlug(payload.slug),
    username: payload.username.trim(),
    name: payload.name.trim(),
    email,
    password: payload.password,
    edition: payload.edition,
  });
  return response.data;
};

export const login = async (payload: LoginPayload) => {
  try {
    const response = await api.post(
      "/auth/login",
      {
        slug: normalizeSlug(payload.slug),
        username: payload.username.trim(),
        password: payload.password,
      },
      {
        withCredentials: true,
      },
    );
    return response.data;
  } catch (err) {
    if (axios.isAxiosError(err)) {
      throw err;
    }

    throw new Error("An unexpected error occurred during login.");
  }
};

export const logout = async () => {
  await api.post("/auth/logout", {}, { withCredentials: true });
};

export const getCurrentUser = async (): Promise<User> => {
  const response = await api.get<User>("/security/me", {
    withCredentials: true,
  });
  return response.data;
};

export const loginErrorMessage = (
  error: unknown,
  fallback: string,
): string => {
  if (axios.isAxiosError(error)) {
    return getApiErrorMessage(error, fallback);
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
};
