import {
  Capability,
  DashboardWidget,
  Edition,
  Locale,
  type Deployment,
} from "@/types/Deployment";

export const personalDeployment: Deployment = {
  edition: Edition.PERSONAL,
  locale: Locale.ZH_TW,
  modules: {
    inventory: true,
    dashboard_summary: true,
    dashboard_origin_chart: true,
    dashboard_genre_chart: true,
    dashboard_recent_assets: true,
    orders: false,
    order_notifications: false,
    pricing_visibility: true,
    profit_analytics: false,
  },
  dashboard_layout: [
    DashboardWidget.SUMMARY,
    DashboardWidget.ORIGIN,
    DashboardWidget.GENRE,
    DashboardWidget.RECENT_ASSETS,
  ],
  capabilities: [
    Capability.MANAGE_INVENTORY,
    Capability.VIEW_CATALOG,
    Capability.VIEW_PRICING,
  ],
};