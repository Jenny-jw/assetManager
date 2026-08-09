import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import i18n from "@/i18n";
import { Locale } from "@/types/Deployment";
import { AuthContext } from "@/context/authContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";
import { DeploymentProvider } from "@/context/DeploymentContext";
import Dashboard from "@/pages/Dashboard";

const { getDeploymentMock, getTeaSummaryMock, listTeasMock } = vi.hoisted(() => ({
  getDeploymentMock: vi.fn(),
  getTeaSummaryMock: vi.fn(),
  listTeasMock: vi.fn(),
}));

vi.mock("@/services/deploymentServices", () => ({
  getDeployment: getDeploymentMock,
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

const baseAuth: Omit<AuthContextType, "user"> = {
  loading: false,
  refresh: async () => {},
  login: async () => {},
  logout: async () => {},
};

const zhTWDeployment = {
  edition: "personal",
  locale: Locale.ZH_TW,
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

describe("tenant locale i18n", () => {
  beforeEach(async () => {
    getDeploymentMock.mockReset();
    getTeaSummaryMock.mockReset();
    listTeasMock.mockReset();
    await i18n.changeLanguage(Locale.EN);
    getTeaSummaryMock.mockResolvedValue({
      total_assets: 0,
      total_packages: 0,
      total_weight_grams: 0,
      total_value: 0,
      by_origin: {},
      by_genre: {},
    });
    listTeasMock.mockResolvedValue({ data: [] });
  });

  it("renders dashboard labels in zh-TW after deployment loads", async () => {
    getDeploymentMock.mockResolvedValue(zhTWDeployment);

    render(
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
        <DeploymentProvider>
          <MemoryRouter>
            <Dashboard />
          </MemoryRouter>
        </DeploymentProvider>
      </AuthContext.Provider>,
    );

    await waitFor(() => {
      expect(screen.getByText("茶葉管家儀表板")).toBeInTheDocument();
    });

    expect(screen.getByText("登出")).toBeInTheDocument();
    expect(screen.getByText("新增資產")).toBeInTheDocument();
  });
});
