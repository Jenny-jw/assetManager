import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Dashboard from "@/pages/Dashboard";
import { AuthContext } from "@/context/authContextImpl";
import { DeploymentContext } from "@/context/deploymentContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";
import { DashboardWidget, type DashboardWidgetId } from "@/types/Deployment";

const { getTeaSummaryMock, listTeasMock } = vi.hoisted(() => ({
  getTeaSummaryMock: vi.fn(),
  listTeasMock: vi.fn(),
}));

vi.mock("@/services/teaServices", async () => {
  const actual = await vi.importActual<typeof import("@/services/teaServices")>(
    "@/services/teaServices",
  );
  return {
    ...actual,
    getTeaSummary: getTeaSummaryMock,
    listTeas: listTeasMock,
  };
});

vi.mock("@/components/PendingOrdersInbox", () => ({
  default: () => <div>Pending Orders Widget</div>,
}));

const baseAuth: Omit<AuthContextType, "user"> = {
  loading: false,
  refresh: async () => {},
  login: async () => {},
  logout: async () => {},
};

function renderDashboard(layout: DashboardWidgetId[]) {
  return render(
    <DeploymentContext.Provider
      value={{
        loading: false,
        deployment: {
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
          dashboard_layout: layout,
        },
      }}
    >
      <AuthContext.Provider
        value={{
          ...baseAuth,
          user: {
            id: "owner-1",
            name: "Owner",
            email: "owner@example.com",
            role: "owner",
            is_active: true,
            created_at: "2026-01-01T00:00:00Z",
          },
        }}
      >
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      </AuthContext.Provider>
    </DeploymentContext.Provider>,
  );
}

describe("Dashboard", () => {
  beforeEach(() => {
    getTeaSummaryMock.mockReset();
    listTeasMock.mockReset();
    getTeaSummaryMock.mockResolvedValue({
      total_assets: 3,
      total_packages: 5,
      total_weight_grams: 600,
      total_value: 2000,
      by_origin: { Taiwan: 3 },
      by_genre: { Oolong: 3 },
    });
    listTeasMock.mockResolvedValue({
      data: [{ id: "tea-1", name: "Alishan", origin: "Taiwan", genre: "Oolong" }],
    });
  });

  it("does not render pending orders widget when layout excludes it", async () => {
    renderDashboard([
      DashboardWidget.SUMMARY,
      DashboardWidget.ORIGIN,
      DashboardWidget.GENRE,
      DashboardWidget.RECENT_ASSETS,
    ]);

    await waitFor(() => {
      expect(screen.getByText("Tea Keeper Dashboard")).toBeInTheDocument();
    });

    expect(screen.queryByText("Pending Orders Widget")).not.toBeInTheDocument();
  });

  it("renders pending orders widget when layout includes it", async () => {
    renderDashboard([
      DashboardWidget.SUMMARY,
      DashboardWidget.ORIGIN,
      DashboardWidget.GENRE,
      DashboardWidget.PENDING_ORDERS,
      DashboardWidget.RECENT_ASSETS,
    ]);

    await waitFor(() => {
      expect(screen.getByText("Pending Orders Widget")).toBeInTheDocument();
    });
  });
});
