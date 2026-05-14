import * as authServices from "../services/authServices";
import { useState, useEffect } from "react";
import { AuthContext } from "./authContextImpl";
import type { User } from "./authContextImpl";

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    authServices
      .getCurrentUser()
      .then(setUser)
      .catch(() => setUser(null));
  }, []);

  const login = async (email: string, password: string) => {
    await authServices.login(email, password);
    const user = await authServices.getCurrentUser();
    setUser(user);
  };

  const logout = async () => {
    await authServices.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
