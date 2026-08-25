import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Dashboard from "@/pages/Dashboard";
import i18n from "@/i18n";
import { AuthContext } from "@/context/authContextImpl";
import { DeploymentContext } from "@/context/deploymentContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";
import { personalDeployment } from "../fixtures/personalDeployment";
import {
  DashboardWidget,
  Locale,
  type Deployment,
} from "@/types/Deployment";
import type { UserRole } from "@/types/User";

const { getStockSummaryMock, listStocksMock } = vi.hoisted(() => ({
  getStockSummaryMock: vi.fn(),
  listStocksMock: vi.fn(),
}));

vi.mock("@/services/stockServices", async () => {
  const actual = await vi.importActual<typeof import("@/services/stockServices")>(
    "@/services/stockServices",
  );
  return {
    ...actual,
    getStockSummary: getStockSummaryMock,
    listStocks: listStocksMock,
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

function renderDashboard(
  deployment: Deployment = personalDeployment,
  role: UserRole = "owner",
) {
  return render(
    <DeploymentContext.Provider
      value={{
        loading: false,
        deployment,
      }}
    >
      <AuthContext.Provider
        value={{
          ...baseAuth,
          user: {
            id: "owner-1",
            tenant_id: "a1111111-b222-c333-d444-e55555555555",
            username: "owner1",
            name: "Owner",
            email: "owner@example.com",
            role,
            is_active: true,
            created_at: "2026-01-01T00:00:00Z",
          },
        }}
      >
        <MemoryRouter initialEntries={["/dashboard"]}>
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/assets" element={<div>Asset list page</div>} />
            <Route path="/assets/new" element={<div>Create asset page</div>} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    </DeploymentContext.Provider>,
  );
}

describe("Dashboard", () => {
  beforeEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(Locale.EN);
    getStockSummaryMock.mockReset();
    listStocksMock.mockReset();
    getStockSummaryMock.mockResolvedValue({
      total_assets: 3,
      total_packages: 5,
      total_weight_grams: 600,
      total_value: 2000,
      by_origin: { Taiwan: 3 },
      by_genre: { Oolong: 3 },
    });
    listStocksMock.mockResolvedValue({
      data: [{ id: "tea-1", name: "Alishan", origin: "Taiwan", genre: "Oolong" }],
    });
  });

  it("personal preset layout hides PendingOrdersInbox", async () => {
    renderDashboard(personalDeployment);

    await waitFor(() => {
      expect(screen.getByText("Tea Keeper Dashboard")).toBeInTheDocument();
    });

    expect(personalDeployment.modules.orders).toBe(false);
    expect(personalDeployment.dashboard_layout).not.toContain(
      DashboardWidget.PENDING_ORDERS,
    );
    expect(screen.queryByText("Pending Orders Widget")).not.toBeInTheDocument();
    expect(screen.getByRole("group", { name: "Language" })).toBeInTheDocument();
  });

  it("renders pending orders widget when layout includes it", async () => {
    renderDashboard({
      ...personalDeployment,
      edition: "professional",
      modules: {
        ...personalDeployment.modules,
        orders: true,
        order_notifications: true,
      },
      dashboard_layout: [
        DashboardWidget.SUMMARY,
        DashboardWidget.ORIGIN,
        DashboardWidget.GENRE,
        DashboardWidget.PENDING_ORDERS,
        DashboardWidget.RECENT_ASSETS,
      ],
    });

    await waitFor(() => {
      expect(screen.getByText("Pending Orders Widget")).toBeInTheDocument();
    });
  });

  it("shows owner actions and navigates to create/list pages", async () => {
    renderDashboard();

    await waitFor(() => {
      expect(screen.getByText("Add Asset")).toBeInTheDocument();
      expect(screen.getByText("Manage Inventory")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Add Asset"));
    expect(screen.getByText("Create asset page")).toBeInTheDocument();
  });

  it("hides owner actions for non-owner roles", async () => {
    renderDashboard(personalDeployment, "admin");

    await waitFor(() => {
      expect(screen.getByText("Tea Keeper Dashboard")).toBeInTheDocument();
    });

    expect(screen.queryByText("Add Asset")).not.toBeInTheDocument();
    expect(screen.queryByText("Manage Inventory")).not.toBeInTheDocument();
  });
});
