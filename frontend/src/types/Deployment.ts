export const Edition = {
  PERSONAL: "personal",
  PROFESSIONAL: "professional",
} as const;

export type Edition = (typeof Edition)[keyof typeof Edition];

export const Locale = {
  ZH_TW: "zh-TW",
  EN: "en",
} as const;

export type Locale = (typeof Locale)[keyof typeof Locale];

export const DashboardWidget = {
  SUMMARY: "summary",
  ORIGIN: "origin",
  GENRE: "genre",
  RECENT_ASSETS: "recent_assets",
  PENDING_ORDERS: "pending_orders",
} as const;

export type DashboardWidgetId =
  (typeof DashboardWidget)[keyof typeof DashboardWidget];

export const Capability = {
  MANAGE_INVENTORY: "manage_inventory",
  VIEW_PRICING: "view_pricing",
  VIEW_PROFIT: "view_profit",
  APPROVE_ORDERS: "approve_orders",
  VIEW_CATALOG: "view_catalog",
} as const;

export type Capability = (typeof Capability)[keyof typeof Capability];

export type DeploymentModules = {
  inventory: boolean;
  dashboard_summary: boolean;
  dashboard_origin_chart: boolean;
  dashboard_genre_chart: boolean;
  dashboard_recent_assets: boolean;
  orders: boolean;
  order_notifications: boolean;
  pricing_visibility: boolean;
  profit_analytics: boolean;
};

export type Deployment = {
  edition: Edition;
  locale: Locale;
  modules: DeploymentModules;
  dashboard_layout: DashboardWidgetId[];
  capabilities: Capability[];
};