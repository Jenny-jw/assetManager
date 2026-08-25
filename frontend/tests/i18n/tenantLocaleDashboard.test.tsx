import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import i18n, { applyDeploymentLocale } from "@/i18n";
import { LOCALE_STORAGE_KEY } from "@/i18n/localeStorage";
import { Locale } from "@/types/Deployment";
import { AuthContext } from "@/context/authContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";
import { DeploymentProvider } from "@/context/DeploymentContext";
import Dashboard from "@/pages/Dashboard";

const { getDeploymentMock, getStockSummaryMock, listStocksMock } = vi.hoisted(() => ({
  getDeploymentMock: vi.fn(),
  getStockSummaryMock: vi.fn(),
  listStocksMock: vi.fn(),
}));

vi.mock("@/services/deploymentServices", () => ({
  getDeployment: getDeploymentMock,
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

const enDeployment = {
  ...zhTWDeployment,
  locale: Locale.EN,
} as const;

const ownerUser = {
  id: "owner-1",
  tenant_id: "a1111111-b222-c333-d444-e55555555555",
  username: "owner1",
  name: "Owner",
  email: "owner@example.com",
  role: "owner" as const,
  is_active: true,
  created_at: "2026-01-01T00:00:00Z",
};

function renderOwnerDashboard() {
  return render(
    <AuthContext.Provider value={{ ...baseAuth, user: ownerUser }}>
      <DeploymentProvider>
        <MemoryRouter>
          <Dashboard />
        </MemoryRouter>
      </DeploymentProvider>
    </AuthContext.Provider>,
  );
}

describe("tenant locale i18n", () => {
  beforeEach(async () => {
    window.localStorage.clear();
    getDeploymentMock.mockReset();
    getStockSummaryMock.mockReset();
    listStocksMock.mockReset();
    await i18n.changeLanguage(Locale.EN);
    getStockSummaryMock.mockResolvedValue({
      total_assets: 0,
      total_packages: 0,
      total_weight_grams: 0,
      total_value: 0,
      by_origin: {},
      by_genre: {},
    });
    listStocksMock.mockResolvedValue({ data: [] });
  });

  afterEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(Locale.EN);
  });

  it("uses tenant locale as first-visit fallback and persists it", async () => {
    getDeploymentMock.mockResolvedValue(zhTWDeployment);

    renderOwnerDashboard();

    await waitFor(() => {
      expect(screen.getByText("茶葉管家儀表板")).toBeInTheDocument();
    });

    expect(screen.getByText("登出")).toBeInTheDocument();
    expect(screen.getByText("新增資產")).toBeInTheDocument();
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.ZH_TW);
  });

  it("keeps a saved English locale when tenant locale is zh-TW", async () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, Locale.EN);
    getDeploymentMock.mockResolvedValue(zhTWDeployment);

    renderOwnerDashboard();

    await waitFor(() => {
      expect(screen.getByText("Tea Keeper Dashboard")).toBeInTheDocument();
    });

    expect(screen.getByText("Log out")).toBeInTheDocument();
    expect(screen.getByText("Add Asset")).toBeInTheDocument();
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.EN);
  });

  it("does not let tenant locale override applyDeploymentLocale", async () => {
    applyDeploymentLocale(Locale.EN);
    await i18n.changeLanguage(Locale.EN);
    getDeploymentMock.mockResolvedValue(zhTWDeployment);

    renderOwnerDashboard();

    await waitFor(() => {
      expect(screen.getByText("Tea Keeper Dashboard")).toBeInTheDocument();
    });

    expect(screen.getByText("Log out")).toBeInTheDocument();
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.EN);
  });

  it("keeps a saved zh-TW locale when tenant locale is en", async () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, Locale.ZH_TW);
    await i18n.changeLanguage(Locale.ZH_TW);
    getDeploymentMock.mockResolvedValue(enDeployment);

    renderOwnerDashboard();

    await waitFor(() => {
      expect(screen.getByText("茶葉管家儀表板")).toBeInTheDocument();
    });

    expect(screen.getByText("登出")).toBeInTheDocument();
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.ZH_TW);
  });
});
