import { useCallback, useEffect, useState } from "react";
import {
  DASHBOARD_RECENT_LIMIT,
  getStockSummary,
  listStocks,
} from "../services/stockServices";
import type { Asset } from "../types/Asset";
import type { TeaSummary } from "../types/TeaList";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/useAuth";
import { useDeployment } from "../context/useDeployment";
import {
  DashboardWidget,
  type DashboardWidgetId,
} from "../types/Deployment";
import { isModuleEnabled } from "../lib/moduleAccess";
import {
  isDashboardWidgetId,
  renderDashboardWidget,
} from "../lib/dashboardWidgetRegistry";

const EMPTY_SUMMARY: TeaSummary = {
  total_assets: 0,
  total_packages: 0,
  total_weight_grams: 0,
  total_value: 0,
  by_origin: {},
  by_genre: {},
};

const Dashboard = () => {
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  const { deployment } = useDeployment();
  const isOwner = user?.role === "owner";
  const [summary, setSummary] = useState<TeaSummary>(EMPTY_SUMMARY);
  const [recentAssets, setRecentAssets] = useState<Asset[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [ordersRefresh, setOrdersRefresh] = useState(0);
  const navigate = useNavigate();

  const refreshDashboard = useCallback(() => {
    Promise.all([
      getStockSummary(),
      listStocks({
        limit: DASHBOARD_RECENT_LIMIT,
        sort_by: "created_at",
        sort_direction: "desc",
      }),
    ])
      .then(([summaryData, recentResponse]) => {
        setSummary(summaryData);
        setRecentAssets(recentResponse.data);
      })
      .catch((error) => {
        console.error("Failed to load dashboard data:", error);
        setSummary(EMPTY_SUMMARY);
        setRecentAssets([]);
      });
  }, []);

  const handleLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (error) {
      console.error("Logout failed:", error);
    }
  };

  useEffect(() => {
    refreshDashboard();
  }, [refreshDashboard]);

  const handleInventoryChange = useCallback(() => {
    refreshDashboard();
    setOrdersRefresh((token) => token + 1);
  }, [refreshDashboard]);
  const enabledWidgetIds: DashboardWidgetId[] = (deployment?.dashboard_layout ?? [])
    .filter(isDashboardWidgetId);
  const includesPendingOrders = enabledWidgetIds.includes(
    DashboardWidget.PENDING_ORDERS,
  );
  const showTotalValue = deployment?.modules.pricing_visibility ?? false;
  const inventoryEnabled = isModuleEnabled(deployment, "inventory");
  const dashboardContext = {
    summary,
    recentAssets,
    showTotalValue,
    ordersRefresh,
    onPendingCountChange: setPendingCount,
    onInventoryChange: handleInventoryChange,
  };
  const summaryWidget = enabledWidgetIds.filter(
    (widgetId) => widgetId === DashboardWidget.SUMMARY,
  );
  const middleWidgets = enabledWidgetIds.filter(
    (widgetId) =>
      widgetId === DashboardWidget.ORIGIN ||
      widgetId === DashboardWidget.GENRE ||
      widgetId === DashboardWidget.PENDING_ORDERS ||
      widgetId === DashboardWidget.PROFIT,
  );
  const footerWidgets = enabledWidgetIds.filter(
    (widgetId) => widgetId === DashboardWidget.RECENT_ASSETS,
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between gap-4 px-2">
        <div className="flex items-center gap-3">
          <h1 className="text-3xl font-bold">{t("dashboard.title")}</h1>
          {includesPendingOrders && pendingCount > 0 && (
            <span className="inline-flex items-center justify-center min-w-6 h-6 px-2 text-xs font-semibold rounded-full bg-[#894f45] text-white">
              {pendingCount}
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={handleLogout}
          className="px-4 py-2 text-sm rounded-lg bg-[#64794d] text-white hover:bg-lime-900 transition"
        >
          {t("auth.logout")}
        </button>
      </div>
      {summaryWidget.map((widgetId, index) => (
        <div key={`${widgetId}-${index}`}>
          {renderDashboardWidget(widgetId, dashboardContext)}
        </div>
      ))}
      {middleWidgets.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {middleWidgets.map((widgetId, index) => (
            <div key={`${widgetId}-${index}`}>
              {renderDashboardWidget(widgetId, dashboardContext)}
            </div>
          ))}
        </div>
      )}
      <div className="grid md:grid-cols-6 gap-6">
        {footerWidgets.map((widgetId, index) => (
          <div key={`${widgetId}-${index}`}>
            {renderDashboardWidget(widgetId, dashboardContext)}
          </div>
        ))}
        <div className="md:col-span-2 flex flex-col gap-4">
          {isOwner && inventoryEnabled && (
            <>
              <button
                className="flex-1 rounded-xl bg-[#78a043] hover:border-lime-200 text-white"
                onClick={() => navigate("/assets/new")}
              >
                {t("dashboard.addAsset")}
              </button>
              <button
                className="flex-1 rounded-xl bg-[#b8cb75] hover:border-lime-100 text-white"
                onClick={() => navigate("/assets")}
              >
                {t("dashboard.manageInventory")}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;