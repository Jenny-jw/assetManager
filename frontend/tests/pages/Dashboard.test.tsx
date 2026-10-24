import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import Dashboard from "@/pages/Dashboard";
import { AuthContext } from "@/context/authContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";
import type { User } from "@/types/User";

vi.mock("@/services/teaServices", () => ({
  DASHBOARD_RECENT_LIMIT: 3,
  getTeaSummary: vi.fn().mockResolvedValue({
    total_assets: 0,
    total_packages: 0,
    total_weight_grams: 0,
    total_value: 0,
    by_origin: {},
    by_genre: {},
  }),
  listTeas: vi.fn().mockResolvedValue({
    data: [],
    page: 1,
    limit: 3,
    total: 0,
  }),
}));

const baseAuth: Omit<AuthContextType, "user"> = {
  loading: false,
  refresh: async () => {},
  login: async () => {},
  logout: async () => {},
};

function renderDashboard(user: User | null) {
  return render(
    <AuthContext.Provider value={{ ...baseAuth, user }}>
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/assets" element={<div>Asset list page</div>} />
          <Route path="/login" element={<div>Login page</div>} />
        </Routes>
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe("Dashboard", () => {
  it("offers the asset list and login when nobody is logged in", async () => {
    renderDashboard(null);

    expect(await screen.findByRole("button", { name: "Asset List" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Log in" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Order" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Add Asset" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Log out" })).not.toBeInTheDocument();
  });

  it("offers ordering for a logged-in user", async () => {
    renderDashboard({
      id: "user-1",
      name: "User",
      email: "user@example.com",
      role: "user",
      created_at: "2026-01-01T00:00:00Z",
      is_active: true,
    });

    expect(await screen.findByRole("button", { name: "Order" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Log out" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Asset List" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Add Asset" })).not.toBeInTheDocument();
  });
});
