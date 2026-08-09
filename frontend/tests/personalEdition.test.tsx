import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Dashboard from "@/pages/Dashboard";
import ModuleRoute from "@/routes/ModuleRoute";
import { AuthContext } from "@/context/authContextImpl";
import { DeploymentContext } from "@/context/deploymentContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";
import { isModuleEnabled } from "@/lib/moduleAccess";
import {
  renderDashboardWidget,
  type DashboardWidgetContext,
} from "@/lib/dashboardWidgetRegistry";
import { personalDeployment } from "./fixtures/personalDeployment";
import {
  DashboardWidget,
  Edition,
  type DashboardWidgetId,
} from "@/types/Deployment";
import type { User } from "@/types/User";

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

const ownerUser: User = {
  id: "owner-1",
  name: "Owner",
  email: "owner@example.com",
  role: "owner",
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
};

const widgetContext: DashboardWidgetContext = {
  summary: {
    total_assets: 2,
    total_packages: 3,
    total_weight_grams: 225,
    total_value: 900,
    by_origin: { Taiwan: 2 },
    by_genre: { Oolong: 2 },
  },
  recentAssets: [
    { id: "tea-1", name: "Alishan", origin: "Taiwan", genre: "Oolong" },
  ],
  showTotalValue: true,
  ordersRefresh: 0,
  onPendingCountChange: () => {},
  onInventoryChange: () => {},
};

function renderPersonalDashboard() {
  return render(
    <DeploymentContext.Provider
      value={{ loading: false, deployment: personalDeployment }}
    >
      <AuthContext.Provider value={{ ...baseAuth, user: ownerUser }}>
        <MemoryRouter initialEntries={["/dashboard"]}>
          <Routes>
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </MemoryRouter>
      </AuthContext.Provider>
    </DeploymentContext.Provider>,
  );
}

function renderPersonalModuleRoute(requireModule?: "inventory" | "orders") {
  return render(
    <AuthContext.Provider value={{ ...baseAuth, user: ownerUser }}>
      <DeploymentContext.Provider
        value={{ loading: false, deployment: personalDeployment }}
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
            <Route path="/dashboard" element={<div>Dashboard page</div>} />
          </Routes>
        </MemoryRouter>
      </DeploymentContext.Provider>
    </AuthContext.Provider>,
  );
}

describe("Personal edition", () => {
  beforeEach(() => {
    getTeaSummaryMock.mockReset();
    listTeasMock.mockReset();
    getTeaSummaryMock.mockResolvedValue(widgetContext.summary);
    listTeasMock.mockResolvedValue({ data: widgetContext.recentAssets });
  });

  it("fixture matches personal preset modules and dashboard layout", () => {
    expect(personalDeployment.edition).toBe(Edition.PERSONAL);
    expect(personalDeployment.modules.orders).toBe(false);
    expect(personalDeployment.modules.order_notifications).toBe(false);
    expect(personalDeployment.modules.profit_analytics).toBe(false);
    expect(personalDeployment.modules.inventory).toBe(true);
    expect(personalDeployment.modules.pricing_visibility).toBe(true);
    expect(personalDeployment.dashboard_layout).toEqual([
      DashboardWidget.SUMMARY,
      DashboardWidget.ORIGIN,
      DashboardWidget.GENRE,
      DashboardWidget.RECENT_ASSETS,
    ]);
    expect(personalDeployment.dashboard_layout).not.toContain(
      DashboardWidget.PENDING_ORDERS,
    );
  });

  it("module flags reflect personal capabilities", () => {
    expect(isModuleEnabled(personalDeployment, "inventory")).toBe(true);
    expect(isModuleEnabled(personalDeployment, "pricing_visibility")).toBe(true);
    expect(isModuleEnabled(personalDeployment, "orders")).toBe(false);
    expect(isModuleEnabled(personalDeployment, "profit_analytics")).toBe(false);
  });

  it("renders each personal dashboard widget and hides pending orders", async () => {
    for (const widgetId of personalDeployment.dashboard_layout) {
      render(<>{renderDashboardWidget(widgetId as DashboardWidgetId, widgetContext)}</>);
    }

    expect(screen.getByText("Total Assets")).toBeInTheDocument();
    expect(screen.getByText("Assets by Origin")).toBeInTheDocument();
    expect(screen.getByText("Assets by Genre")).toBeInTheDocument();
    expect(screen.getByText("Recent Assets")).toBeInTheDocument();
    expect(screen.queryByText("Pending Orders Widget")).not.toBeInTheDocument();
  });

  it("dashboard uses personal layout without pending orders inbox", async () => {
    renderPersonalDashboard();

    await waitFor(() => {
      expect(screen.getByText("Tea Keeper Dashboard")).toBeInTheDocument();
    });

    expect(screen.getByText("Total Assets")).toBeInTheDocument();
    expect(screen.getByText("Recent Assets")).toBeInTheDocument();
    expect(screen.queryByText("Pending Orders Widget")).not.toBeInTheDocument();
  });

  it("allows inventory routes on personal deployment", () => {
    renderPersonalModuleRoute("inventory");
    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });

  it("redirects orders-gated routes to dashboard on personal deployment", () => {
    renderPersonalModuleRoute("orders");
    expect(screen.getByText("Dashboard page")).toBeInTheDocument();
    expect(screen.queryByText("Protected content")).not.toBeInTheDocument();
  });
});
