import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import CreateAsset from "@/pages/CreateAsset";
import i18n from "@/i18n";
import { Locale } from "@/types/Deployment";

const { createStockMock } = vi.hoisted(() => ({
  createStockMock: vi.fn(),
}));

vi.mock("@/services/stockServices", async () => {
  const actual = await vi.importActual<typeof import("@/services/stockServices")>(
    "@/services/stockServices",
  );
  return {
    ...actual,
    createStock: createStockMock,
  };
});

describe("CreateAsset", () => {
  beforeEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(Locale.EN);
    createStockMock.mockReset();
  });

  afterEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(Locale.EN);
  });

  it("renders English form copy by default", () => {
    render(
      <MemoryRouter>
        <CreateAsset />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { name: "Create Asset" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Name *")).toBeInTheDocument();
    expect(screen.getByText("Price per 斤 *")).toBeInTheDocument();
  });

  it("switches remaining copy to zh-TW", async () => {
    render(
      <MemoryRouter>
        <CreateAsset />
      </MemoryRouter>,
    );

    fireEvent.click(screen.getByRole("button", { name: "中文" }));

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: "新增資產" }),
      ).toBeInTheDocument();
    });
    expect(screen.getByText("名稱 *")).toBeInTheDocument();
    expect(screen.getByText("每斤價格 *")).toBeInTheDocument();
    expect(createStockMock).not.toHaveBeenCalled();
  });
});