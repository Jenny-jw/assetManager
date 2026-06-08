import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AssetList from "@/pages/AssetList";
import { AuthContext } from "@/context/authContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";
import type { Asset } from "@/types/Asset";

const { listTeasMock } = vi.hoisted(() => ({
  listTeasMock: vi.fn(),
}));

vi.mock("@/services/teaServices", async () => {
  const actual = await vi.importActual<typeof import("@/services/teaServices")>(
    "@/services/teaServices",
  );
  return {
    ...actual,
    listTeas: listTeasMock,
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

function renderAssetList(role: "admin" | "user" = "user") {
  return render(
    <AuthContext.Provider
      value={{
        ...baseAuth,
        user: {
          id: "user-1",
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
    </AuthContext.Provider>,
  );
}

describe("AssetList", () => {
  beforeEach(() => {
    listTeasMock.mockReset();
    listTeasMock.mockResolvedValue({
      data: sampleAssets,
      page: 1,
      limit: 20,
      total: 2,
    });
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
    expect(listTeasMock).toHaveBeenCalled();
  });

  it("requests filtered results when genre changes", async () => {
    renderAssetList();

    await waitFor(() => {
      expect(screen.getAllByText("Alishan Oolong").length).toBeGreaterThan(0);
    });

    const genreSelect = screen.getAllByRole("combobox")[0];
    fireEvent.change(genreSelect, { target: { value: "Oolong" } });

    await waitFor(() => {
      expect(listTeasMock).toHaveBeenCalledWith(
        expect.objectContaining({
          genre: "Oolong",
          page: 1,
        }),
      );
    });
  });

  it("loads page two when Next is clicked", async () => {
    listTeasMock.mockImplementation(async (params) => {
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
      expect(listTeasMock).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 }),
      );
      expect(screen.getByText("Showing 21-32 of 32")).toBeInTheDocument();
      expect(screen.getAllByText("Page Two Tea").length).toBeGreaterThan(0);
    });
  });
});
