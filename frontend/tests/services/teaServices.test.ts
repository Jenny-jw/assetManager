import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Asset } from "@/types/Asset";

const { getMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
}));

vi.mock("@/lib/axios", () => ({
  default: {
    get: getMock,
  },
}));

import {
  DEFAULT_TEA_PAGE_SIZE,
  extractTeaFacets,
  listTeas,
} from "@/services/teaServices";

describe("teaServices", () => {
  beforeEach(() => {
    getMock.mockReset();
  });

  it("listTeas forwards pagination, search, filters, and sort params", async () => {
    getMock.mockResolvedValue({
      data: { data: [], page: 2, limit: 20, total: 0 },
    });

    await listTeas({
      page: 2,
      search: "oolong",
      genre: "Oolong",
      origin: "Japan",
      sort_by: "price",
      sort_direction: "asc",
    });

    expect(getMock).toHaveBeenCalledWith("/tea", {
      params: {
        page: 2,
        limit: DEFAULT_TEA_PAGE_SIZE,
        search: "oolong",
        genre: "Oolong",
        origin: "Japan",
        sort_by: "price",
        sort_direction: "asc",
      },
    });
  });

  it("extractTeaFacets returns sorted unique genres and origins", () => {
    const teas: Asset[] = [
      { id: "1", name: "A", genre: "Black", origin: "Japan" },
      { id: "2", name: "B", genre: "Oolong", origin: "Taiwan" },
      { id: "3", name: "C", genre: "Oolong" },
    ];

    expect(extractTeaFacets(teas)).toEqual({
      genres: ["Black", "Oolong"],
      origins: ["Japan", "Taiwan"],
    });
  });
});
