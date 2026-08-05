import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it } from "vitest";
import ModuleRoute from "@/routes/ModuleRoute";
import { AuthContext } from "@/context/authContextImpl";
import { DeploymentContext } from "@/context/deploymentContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";
import { personalDeployment } from "../fixtures/personalDeployment";
import { professionalDeployment } from "../fixtures/professionalDeployment";
import type { User } from "@/types/User";

const baseAuth: Omit<AuthContextType, "user"> = {
  loading: false,
  refresh: async () => {},
  login: async () => {},
  logout: async () => {},
};

const ownerUser: User = {
  id: "owner-1",
  name: "Owner",
  email: "owner@example.com",
  role: "owner",
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
};

function renderModuleRoute({
  user = ownerUser,
  deployment = personalDeployment,
  authLoading = false,
  deploymentLoading = false,
  requireModule,
}: {
  user?: User | null;
  deployment?: typeof personalDeployment | null;
  authLoading?: boolean;
  deploymentLoading?: boolean;
  requireModule?: "inventory" | "orders";
} = {}) {
  return render(
    <AuthContext.Provider value={{ ...baseAuth, user, loading: authLoading }}>
      <DeploymentContext.Provider
        value={{ deployment, loading: deploymentLoading }}
      >
        <MemoryRouter initialEntries={["/protected"]}>
          <Routes>
            <Route
              path="/protected"
              element={
                <ModuleRoute
                  allowedRoles={["owner"]}
                  requireModule={requireModule}
                >
                  <div>Protected content</div>
                </ModuleRoute>
              }
            />
            <Route path="/login" element={<div>Login page</div>} />
            <Route path="/dashboard" element={<div>Dashboard page</div>} />
          </Routes>
        </MemoryRouter>
      </DeploymentContext.Provider>
    </AuthContext.Provider>,
  );
}

describe("ModuleRoute", () => {
  it("redirects unauthenticated users to login", () => {
    renderModuleRoute({ user: null });
    expect(screen.getByText("Login page")).toBeInTheDocument();
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });

  it("renders children for owner when inventory module is enabled", () => {
    renderModuleRoute({ requireModule: "inventory" });
    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });

  it("redirects to dashboard when required module is disabled", () => {
    renderModuleRoute({ requireModule: "orders" });
    expect(screen.getByText("Dashboard page")).toBeInTheDocument();
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });

  it("allows routes gated by orders on professional deployment", () => {
    renderModuleRoute({
      deployment: professionalDeployment,
      requireModule: "orders",
    });
    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });
});
