import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/services/analyticsServices", () => ({
  getProfitSummary: vi.fn().mockResolvedValue({
    total_retail_value: 0,
    total_cost_value: 0,
    unrealized_profit: 0,
    priced_assets: 0,
    costed_assets: 0,
    complete_assets: 0,
    uncosted_assets: 0,
    by_origin: {},
    by_genre: {},
    lines: [],
  }),
}));
import {
  DASHBOARD_WIDGET_IDS,
  dashboardWidgetRegistry,
  isDashboardWidgetId,
  renderDashboardWidget,
  type DashboardWidgetContext,
} from "@/lib/dashboardWidgetRegistry";
import { DashboardWidget } from "@/types/Deployment";

const emptyContext: DashboardWidgetContext = {
  summary: {
    total_assets: 2,
    total_packages: 3,
    total_weight_grams: 225,
    total_value: 900,
    by_origin: { Taiwan: 2 },
    by_genre: { Oolong: 2 },
  },
  recentAssets: [
    { id: "tea-1", name: "High Mountain", origin: "Taiwan", genre: "Oolong" },
  ],
  showTotalValue: true,
  ordersRefresh: 0,
  onPendingCountChange: () => {},
  onInventoryChange: () => {},
};

describe("dashboardWidgetRegistry", () => {
  it("maps every DashboardWidget id to a renderer", () => {
    expect(DASHBOARD_WIDGET_IDS).toHaveLength(6);

    for (const widgetId of DASHBOARD_WIDGET_IDS) {
      expect(dashboardWidgetRegistry[widgetId]).toBeTypeOf("function");
    }
  });

  it("isDashboardWidgetId accepts known ids and rejects unknown values", () => {
    expect(isDashboardWidgetId(DashboardWidget.SUMMARY)).toBe(true);
    expect(isDashboardWidgetId("pending_orders")).toBe(true);
    expect(isDashboardWidgetId("unknown")).toBe(false);
  });

  it("renderDashboardWidget renders the summary widget", () => {
    render(<>{renderDashboardWidget(DashboardWidget.SUMMARY, emptyContext)}</>);

    expect(screen.getByText("Total Assets")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("Total Value")).toBeInTheDocument();
  });

  it("renderDashboardWidget renders chart widgets from summary data", () => {
    render(<>{renderDashboardWidget(DashboardWidget.ORIGIN, emptyContext)}</>);
    expect(screen.getByText("Assets by Origin")).toBeInTheDocument();
    expect(screen.getByText("Taiwan")).toBeInTheDocument();

    render(<>{renderDashboardWidget(DashboardWidget.GENRE, emptyContext)}</>);
    expect(screen.getByText("Assets by Genre")).toBeInTheDocument();
    expect(screen.getByText("Oolong")).toBeInTheDocument();
  });
});
