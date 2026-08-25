import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import i18n from "@/i18n";
import { LOCALE_STORAGE_KEY } from "@/i18n/localeStorage";
import { Edition, Locale } from "@/types/Deployment";
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

describe("DeploymentProvider", () => {
  beforeEach(async () => {
    window.localStorage.clear();
    getDeploymentMock.mockReset();
    await i18n.changeLanguage(Locale.EN);
  });

  it("loads deployment when authenticated user is present", async () => {
    getDeploymentMock.mockResolvedValue(personalDeployment);

    renderWithAuth(ownerUser);

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

    renderWithAuth(ownerUser);

    await waitFor(() => {
      expect(screen.getByText("no deployment")).toBeInTheDocument();
    });
  });

  it("does not overwrite a saved locale with tenant locale", async () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, Locale.EN);
    getDeploymentMock.mockResolvedValue(personalDeployment);

    renderWithAuth(ownerUser);

    await waitFor(() => {
      expect(screen.getByText(`edition:${Edition.PERSONAL}`)).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(i18n.language).toBe(Locale.EN);
    });
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.EN);
  });

  it("seeds storage from tenant locale when nothing is saved", async () => {
    getDeploymentMock.mockResolvedValue(personalDeployment);

    renderWithAuth(ownerUser);

    await waitFor(() => {
      expect(screen.getByText(`edition:${Edition.PERSONAL}`)).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(i18n.language).toBe(Locale.ZH_TW);
    });
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.ZH_TW);
  });

  it("keeps a saved locale after logout", async () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, Locale.ZH_TW);
    await i18n.changeLanguage(Locale.ZH_TW);

    renderWithAuth(null);

    await waitFor(() => {
      expect(screen.getByText("no deployment")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(i18n.language).toBe(Locale.ZH_TW);
    });
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.ZH_TW);
  });

  it("keeps a saved locale when deployment fetch fails", async () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, Locale.ZH_TW);
    await i18n.changeLanguage(Locale.ZH_TW);
    getDeploymentMock.mockRejectedValue(new Error("network error"));

    renderWithAuth(ownerUser);

    await waitFor(() => {
      expect(screen.getByText("no deployment")).toBeInTheDocument();
    });
    await waitFor(() => {
      expect(i18n.language).toBe(Locale.ZH_TW);
    });
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.ZH_TW);
  });

  it("useDeployment throws outside provider", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => render(<DeploymentProbe />)).toThrow(
      "useDeployment must be used within a DeploymentProvider",
    );

    consoleError.mockRestore();
  });
});
