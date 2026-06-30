import { createElement, type ReactNode } from "react";
import GenreDistribution from "../components/GenreDistribution";
import OriginDistribution from "../components/OriginDistribution";
import PendingOrdersInbox from "../components/PendingOrdersInbox";
import RecentAssets from "../components/RecentAssets";
import Summary from "../components/Summary";
import type { Asset } from "../types/Asset";
import { DashboardWidget, type DashboardWidgetId } from "../types/Deployment";
import type { TeaSummary } from "../types/TeaList";

export type DashboardWidgetContext = {
  summary: TeaSummary;
  recentAssets: Asset[];
  showTotalValue: boolean;
  ordersRefresh: number;
  onPendingCountChange: (count: number) => void;
  onInventoryChange: () => void;
};

export type DashboardWidgetRenderer = (
  context: DashboardWidgetContext,
) => ReactNode;

export const DASHBOARD_WIDGET_IDS = Object.values(DashboardWidget);

export const dashboardWidgetRegistry: Record<
  DashboardWidgetId,
  DashboardWidgetRenderer
> = {
  [DashboardWidget.SUMMARY]: (context) =>
    createElement(Summary, {
      summary: context.summary,
      showTotalValue: context.showTotalValue,
    }),
  [DashboardWidget.ORIGIN]: (context) =>
    createElement(OriginDistribution, {
      counts: context.summary.by_origin,
    }),
  [DashboardWidget.GENRE]: (context) =>
    createElement(GenreDistribution, {
      counts: context.summary.by_genre,
    }),
  [DashboardWidget.PENDING_ORDERS]: (context) =>
    createElement(PendingOrdersInbox, {
      refreshToken: context.ordersRefresh,
      onPendingCountChange: context.onPendingCountChange,
      onInventoryChange: context.onInventoryChange,
    }),
  [DashboardWidget.RECENT_ASSETS]: (context) =>
    createElement(RecentAssets, {
      assets: context.recentAssets,
      className: "md:col-span-4",
    }),
};

export function isDashboardWidgetId(value: string): value is DashboardWidgetId {
  return (DASHBOARD_WIDGET_IDS as readonly string[]).includes(value);
}

export function renderDashboardWidget(
  widgetId: DashboardWidgetId,
  context: DashboardWidgetContext,
): ReactNode {
  return dashboardWidgetRegistry[widgetId](context);
}
