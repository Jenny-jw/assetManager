import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
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
    expect(DASHBOARD_WIDGET_IDS).toHaveLength(5);

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
