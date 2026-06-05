import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import ProtectedRoute from "@/routes/ProtectedRoute";
import { AuthContext } from "@/context/authContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";
import type { User } from "@/types/User";

const baseAuth: Omit<AuthContextType, "user"> = {
  loading: false,
  refresh: async () => {},
  login: async () => {},
  logout: async () => {},
};

function renderProtectedRoute(user: User | null) {
  return render(
    <AuthContext.Provider value={{ ...baseAuth, user }}>
      <MemoryRouter initialEntries={["/protected"]}>
        <Routes>
          <Route
            path="/protected"
            element={
              <ProtectedRoute allowedRoles={["admin"]}>
                <div>Admin only content</div>
              </ProtectedRoute>
            }
          />
          <Route path="/login" element={<div>Login page</div>} />
          <Route path="/dashboard" element={<div>Dashboard page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe("ProtectedRoute", () => {
  it("redirects unauthenticated users to login", () => {
    renderProtectedRoute(null);
    expect(screen.getByText("Login page")).toBeInTheDocument();
    expect(screen.queryByText("Admin only content")).not.toBeInTheDocument();
  });

  it("redirects non-admin users to dashboard", () => {
    renderProtectedRoute({
      id: "1",
      name: "Regular User",
      email: "user@example.com",
      role: "user",
      created_at: "2026-01-01T00:00:00Z",
      is_active: true,
    });
    expect(screen.getByText("Dashboard page")).toBeInTheDocument();
    expect(screen.queryByText("Admin only content")).not.toBeInTheDocument();
  });

  it("renders children for admin users", () => {
    renderProtectedRoute({
      id: "2",
      name: "Admin User",
      email: "admin@example.com",
      role: "admin",
      created_at: "2026-01-01T00:00:00Z",
      is_active: true,
    });
    expect(screen.getByText("Admin only content")).toBeInTheDocument();
  });
});