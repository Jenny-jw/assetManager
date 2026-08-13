import {
  Capability,
  DashboardWidget,
  Edition,
  Locale,
  type Deployment,
} from "@/types/Deployment";

export const professionalDeployment: Deployment = {
  edition: Edition.PROFESSIONAL,
  locale: Locale.ZH_TW,
  modules: {
    inventory: true,
    dashboard_summary: true,
    dashboard_origin_chart: true,
    dashboard_genre_chart: true,
    dashboard_recent_assets: true,
    orders: true,
    order_notifications: true,
    pricing_visibility: true,
    profit_analytics: true,
  },
  dashboard_layout: [
    DashboardWidget.SUMMARY,
    DashboardWidget.ORIGIN,
    DashboardWidget.GENRE,
    DashboardWidget.PENDING_ORDERS,
    DashboardWidget.RECENT_ASSETS,
  ],
  capabilities: [
    Capability.APPROVE_ORDERS,
    Capability.MANAGE_INVENTORY,
    Capability.VIEW_CATALOG,
    Capability.VIEW_PRICING,
    Capability.VIEW_PROFIT,
  ],
};