import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ProfitSummary from "@/components/ProfitSummary";

const { getProfitSummaryMock } = vi.hoisted(() => ({
  getProfitSummaryMock: vi.fn(),
}));

vi.mock("@/services/analyticsServices", () => ({
  getProfitSummary: getProfitSummaryMock,
}));

describe("ProfitSummary", () => {
  beforeEach(() => {
    getProfitSummaryMock.mockReset();
    getProfitSummaryMock.mockResolvedValue({
      total_retail_value: 300,
      total_cost_value: 200,
      unrealized_profit: 100,
      priced_assets: 1,
      costed_assets: 1,
      complete_assets: 1,
      uncosted_assets: 2,
      by_origin: { Alishan: 100 },
      by_genre: { Oolong: 100 },
      lines: [],
    });
  });

  it("shows retail, cost, and unrealized profit", async () => {
    render(<ProfitSummary />);

    expect(await screen.findByText("Profit")).toBeInTheDocument();
    expect(screen.getByText("300")).toBeInTheDocument();
    expect(screen.getByText("200")).toBeInTheDocument();
    expect(screen.getByText("100")).toBeInTheDocument();
    expect(screen.getByText("2 assets are missing cost")).toBeInTheDocument();
  });
});