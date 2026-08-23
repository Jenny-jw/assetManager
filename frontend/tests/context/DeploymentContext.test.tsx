import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Edition } from "@/types/Deployment";
import { AuthContext } from "@/context/authContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";

const { getDeploymentMock } = vi.hoisted(() => ({
  getDeploymentMock: vi.fn(),
}));

vi.mock("@/services/deploymentServices", () => ({
  getDeployment: getDeploymentMock,
}));

import { DeploymentProvider } from "@/context/DeploymentContext";
import { useDeployment } from "@/context/useDeployment";

const personalDeployment = {
  edition: "personal",
  locale: "zh-TW",
  modules: {
    inventory: true,
    dashboard_summary: true,
    dashboard_origin_chart: true,
    dashboard_genre_chart: true,
    dashboard_recent_assets: true,
    orders: false,
    order_notifications: false,
    pricing_visibility: true,
    profit_analytics: false,
  },
  dashboard_layout: ["summary", "origin", "genre", "recent_assets"],
} as const;

const baseAuth: Omit<AuthContextType, "user"> = {
  loading: false,
  refresh: async () => {},
  login: async () => {},
  logout: async () => {},
};

function DeploymentProbe() {
  const { deployment, loading } = useDeployment();
  if (loading) {
    return <div>loading</div>;
  }
  if (!deployment) {
    return <div>no deployment</div>;
  }
  return <div>edition:{deployment.edition}</div>;
}

function renderWithAuth(user: AuthContextType["user"], authLoading = false) {
  return render(
    <AuthContext.Provider value={{ ...baseAuth, user, loading: authLoading }}>
      <DeploymentProvider>
        <DeploymentProbe />
      </DeploymentProvider>
    </AuthContext.Provider>,
  );
}

describe("DeploymentProvider", () => {
  beforeEach(() => {
    getDeploymentMock.mockReset();
  });

  it("loads deployment when authenticated user is present", async () => {
    getDeploymentMock.mockResolvedValue(personalDeployment);

    renderWithAuth({
      id: "owner-1",
      tenant_id: "a1111111-b222-c333-d444-e55555555555",
      username: "owner1",
      name: "Owner",
      email: "owner@example.com",
      role: "owner",
      is_active: true,
      created_at: "2026-01-01T00:00:00Z",
    });

    expect(screen.getByText("loading")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(`edition:${Edition.PERSONAL}`)).toBeInTheDocument();
    });

    expect(getDeploymentMock).toHaveBeenCalledTimes(1);
  });

  it("skips deployment fetch when user is not authenticated", async () => {
    renderWithAuth(null);

    await waitFor(() => {
      expect(screen.getByText("no deployment")).toBeInTheDocument();
    });

    expect(getDeploymentMock).not.toHaveBeenCalled();
  });

  it("sets deployment to null when fetch fails", async () => {
    getDeploymentMock.mockRejectedValue(new Error("network error"));

    renderWithAuth({
      id: "owner-1",
      tenant_id: "a1111111-b222-c333-d444-e55555555555",
      username: "owner1",
      name: "Owner",
      email: "owner@example.com",
      role: "owner",
      is_active: true,
      created_at: "2026-01-01T00:00:00Z",
    });

    await waitFor(() => {
      expect(screen.getByText("no deployment")).toBeInTheDocument();
    });
  });

  it("useDeployment throws outside provider", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => render(<DeploymentProbe />)).toThrow(
      "useDeployment must be used within a DeploymentProvider",
    );

    consoleError.mockRestore();
  });
});
