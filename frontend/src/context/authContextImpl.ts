import { createContext } from "react";
import type { LoginPayload } from "../services/authServices";
import type { User } from "../types/User";

export type AuthContextType = {
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined,
);
