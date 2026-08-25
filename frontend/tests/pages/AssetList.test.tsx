import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import AssetList from "@/pages/AssetList";
import i18n from "@/i18n";
import { AuthContext } from "@/context/authContextImpl";
import { DeploymentContext } from "@/context/deploymentContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";
import type { Asset } from "@/types/Asset";
import { Locale, type Deployment } from "@/types/Deployment";
import type { UserRole } from "@/types/User";
import { personalDeployment } from "../fixtures/personalDeployment";

const { listStocksMock } = vi.hoisted(() => ({
  listStocksMock: vi.fn(),
}));

vi.mock("@/services/stockServices", async () => {
  const actual = await vi.importActual<typeof import("@/services/stockServices")>(
    "@/services/stockServices",
  );
  return {
    ...actual,
    listStocks: listStocksMock,
  };
});

const baseAuth: Omit<AuthContextType, "user"> = {
  loading: false,
  refresh: async () => {},
  login: async () => {},
  logout: async () => {},
};

const sampleAssets: Asset[] = [
  {
    id: "tea-1",
    name: "Alishan Oolong",
    genre: "Oolong",
    origin: "Taiwan",
    quantity: 3,
    score: 90,
    price: 1200,
    weight: 150,
  },
  {
    id: "tea-2",
    name: "Sencha",
    genre: "Green",
    origin: "Japan",
    quantity: 5,
    score: 85,
    price: 900,
    weight: 75,
  },
];

function renderAssetList(
  role: UserRole = "user",
  deployment: Deployment = personalDeployment,
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
            id: "user-1",
            tenant_id: "a1111111-b222-c333-d444-e55555555555",
            username: "user1",
            email: "user@example.com",
            name: "User",
            role,
            is_active: true,
            created_at: "2026-01-01T00:00:00Z",
          },
        }}
      >
        <MemoryRouter>
          <AssetList />
        </MemoryRouter>
      </AuthContext.Provider>
    </DeploymentContext.Provider>,
  );
}

describe("AssetList", () => {
  beforeEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(Locale.EN);
    listStocksMock.mockReset();
    listStocksMock.mockResolvedValue({
      data: sampleAssets,
      page: 1,
      limit: 20,
      total: 2,
    });
  });

  afterEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(Locale.EN);
  });

  it("loads teas and renders search and filter controls", async () => {
    renderAssetList();

    expect(
      await screen.findByPlaceholderText("Search name, producer, or comment"),
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getAllByText("Alishan Oolong").length).toBeGreaterThan(0);
    });

    expect(screen.getByText("Showing 1-2 of 2")).toBeInTheDocument();
    expect(listStocksMock).toHaveBeenCalled();
    expect(screen.getByRole("group", { name: "Language" })).toBeInTheDocument();
  });

  it("switches remaining list copy to zh-TW", async () => {
    renderAssetList();

    expect(
      await screen.findByPlaceholderText("Search name, producer, or comment"),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "中文" }));

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText("搜尋名稱、製茶師或備註"),
      ).toBeInTheDocument();
    });
    expect(screen.getByText("顯示 1-2／共 2")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "下一頁" })).toBeInTheDocument();
  });

  it("requests filtered results when genre changes", async () => {
    renderAssetList();

    await waitFor(() => {
      expect(screen.getAllByText("Alishan Oolong").length).toBeGreaterThan(0);
    });

    const genreSelect = screen.getAllByRole("combobox")[0];
    fireEvent.change(genreSelect, { target: { value: "Oolong" } });

    await waitFor(() => {
      expect(listStocksMock).toHaveBeenCalledWith(
        expect.objectContaining({
          genre: "Oolong",
          page: 1,
        }),
      );
    });
  });

  it("loads page two when Next is clicked", async () => {
    listStocksMock.mockImplementation(async (params) => {
      if (params.page === 2) {
        return {
          data: [
            {
              id: "tea-3",
              name: "Page Two Tea",
              genre: "Oolong",
              quantity: 1,
              score: 10,
              price: 500,
              weight: 150,
            },
          ],
          page: 2,
          limit: 20,
          total: 32,
        };
      }

      return {
        data: sampleAssets,
        page: 1,
        limit: 20,
        total: 32,
      };
    });

    renderAssetList();

    await waitFor(() => {
      expect(screen.getByText("Showing 1-20 of 32")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "Next" }));

    await waitFor(() => {
      expect(listStocksMock).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 }),
      );
      expect(screen.getByText("Showing 21-32 of 32")).toBeInTheDocument();
      expect(screen.getAllByText("Page Two Tea").length).toBeGreaterThan(0);
    });
  });

  it("shows inventory actions for owner on personal deployment", async () => {
    renderAssetList("owner", personalDeployment);

    await waitFor(() => {
      expect(screen.getAllByText("Alishan Oolong").length).toBeGreaterThan(0);
    });

    expect(screen.getAllByRole("button", { name: "Edit" }).length).toBeGreaterThan(0);
    expect(screen.queryByRole("button", { name: "Order" })).not.toBeInTheDocument();
  });
});
