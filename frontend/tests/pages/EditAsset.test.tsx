import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import EditAsset from "@/pages/EditAsset";
import i18n from "@/i18n";
import { Locale } from "@/types/Deployment";

const { getStockMock, updateStockMock } = vi.hoisted(() => ({
  getStockMock: vi.fn(),
  updateStockMock: vi.fn(),
}));

vi.mock("@/services/stockServices", async () => {
  const actual = await vi.importActual<typeof import("@/services/stockServices")>(
    "@/services/stockServices",
  );
  return {
    ...actual,
    getStock: getStockMock,
    updateStock: updateStockMock,
  };
});

describe("EditAsset", () => {
  beforeEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(Locale.EN);
    getStockMock.mockReset();
    updateStockMock.mockReset();
    getStockMock.mockResolvedValue({
      id: "tea-1",
      name: "Alishan Oolong",
      genre: "Oolong",
      origin: "Taiwan",
      producer: "Wu",
      price: 1200,
      weight: 150,
      quantity: 3,
      score: 90,
    });
  });

  afterEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(Locale.EN);
  });

  function renderEdit() {
    return render(
      <MemoryRouter initialEntries={["/assets/tea-1/edit"]}>
        <Routes>
          <Route path="/assets/:id/edit" element={<EditAsset />} />
        </Routes>
      </MemoryRouter>,
    );
  }

  it("renders English form copy after the asset loads", async () => {
    renderEdit();

    expect(
      await screen.findByRole("heading", { name: "Edit Asset" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Update tea details")).toBeInTheDocument();
    expect(screen.getByText("Price per 斤")).toBeInTheDocument();
  });

  it("switches remaining copy to zh-TW", async () => {
    renderEdit();

    expect(
      await screen.findByRole("heading", { name: "Edit Asset" }),
    ).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "中文" }));

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "編輯資產" }),
      ).toBeInTheDocument();
    });
    expect(screen.getByText("更新茶品資料")).toBeInTheDocument();
    expect(screen.getByText("每斤價格")).toBeInTheDocument();
  });
});