import { createContext } from "react";

export type User = {
  id: string;
  name: string;
  email: string;
  role: "admin" | "user" | "guest";
};

export type AuthContextType = {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
};

export const AuthContext = createContext<AuthContextType | undefined>(
  undefined,
);
