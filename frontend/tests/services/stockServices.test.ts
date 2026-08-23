import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Asset } from "@/types/Asset";

const { getMock, postMock, patchMock, deleteMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
  postMock: vi.fn(),
  patchMock: vi.fn(),
  deleteMock: vi.fn(),
}));

vi.mock("@/lib/axios", () => ({
  default: {
    get: getMock,
    post: postMock,
    patch: patchMock,
    delete: deleteMock,
  },
}));

import {
  DEFAULT_STOCK_PAGE_SIZE,
  createStock,
  extractStockFacets,
  getStockSummary,
  listStocks,
  toStockWrite,
} from "@/services/stockServices";

describe("stockServices", () => {
  beforeEach(() => {
    getMock.mockReset();
    postMock.mockReset();
    patchMock.mockReset();
    deleteMock.mockReset();
  });

  it("listStocks calls /stock and maps price/weight fields", async () => {
    getMock.mockResolvedValue({
      data: {
        data: [
          {
            id: "1",
            name: "Alishan",
            genre: "Oolong",
            origin: "Taiwan",
            weight_grams: 75,
            price_per_jin: 1200,
            quantity: 2,
          },
        ],
        page: 2,
        limit: 20,
        total: 1,
      },
    });

    const result = await listStocks({
      page: 2,
      search: "oolong",
      genre: "Oolong",
      origin: "Japan",
      sort_by: "price",
      sort_direction: "asc",
    });

    expect(getMock).toHaveBeenCalledWith("/stock", {
      params: {
        page: 2,
        limit: DEFAULT_STOCK_PAGE_SIZE,
        search: "oolong",
        genre: "Oolong",
        origin: "Japan",
        sort_by: "price_per_jin",
        sort_direction: "asc",
      },
    });
    expect(result.data[0]).toMatchObject({
      id: "1",
      weight: 75,
      price: 1200,
    });
  });

  it("getStockSummary calls /stock/summary", async () => {
    getMock.mockResolvedValue({
      data: {
        total_assets: 32,
        total_packages: 40,
        total_weight_grams: 5000,
        total_value: 12000,
        by_origin: { Taiwan: 20 },
        by_genre: { Oolong: 32 },
      },
    });

    const summary = await getStockSummary();

    expect(getMock).toHaveBeenCalledWith("/stock/summary");
    expect(summary.total_assets).toBe(32);
    expect(summary.total_value).toBe(12000);
  });

  it("createStock posts mapped API fields", async () => {
    postMock.mockResolvedValue({
      data: {
        id: "new-1",
        name: "Alishan",
        weight_grams: 150,
        price_per_jin: 2000,
        quantity: 1,
      },
    });

    const created = await createStock({
      name: "Alishan",
      weight: 150,
      price: 2000,
      quantity: 1,
    });

    expect(postMock).toHaveBeenCalledWith("/stock", {
      name: "Alishan",
      quantity: 1,
      weight_grams: 150,
      price_per_jin: 2000,
    });
    expect(created.weight).toBe(150);
    expect(created.price).toBe(2000);
  });

  it("toStockWrite maps UI fields to API names", () => {
    expect(toStockWrite({ name: "Tea", weight: 75, price: 900 })).toEqual({
      name: "Tea",
      weight_grams: 75,
      price_per_jin: 900,
    });
  });

  it("extractStockFacets returns sorted unique genres and origins", () => {
    const stocks: Asset[] = [
      { id: "1", name: "A", genre: "Black", origin: "Japan" },
      { id: "2", name: "B", genre: "Oolong", origin: "Taiwan" },
      { id: "3", name: "C", genre: "Oolong" },
    ];

    expect(extractStockFacets(stocks)).toEqual({
      genres: ["Black", "Oolong"],
      origins: ["Japan", "Taiwan"],
    });
  });
});
