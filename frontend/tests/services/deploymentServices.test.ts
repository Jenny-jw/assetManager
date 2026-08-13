import { beforeEach, describe, expect, it, vi } from "vitest";
import { Edition } from "@/types/Deployment";

const { getMock } = vi.hoisted(() => ({
  getMock: vi.fn(),
}));

vi.mock("@/lib/axios", () => ({
  default: {
    get: getMock,
  },
}));

import { getDeployment } from "@/services/deploymentServices";

const personalDeployment = {
  edition: "personal",
  locale: "zh-TW",
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
  dashboard_layout: ["summary", "origin", "genre", "recent_assets"],
  capabilities: ["manage_inventory", "view_catalog", "view_pricing"],
} as const;

describe("deploymentServices", () => {
  beforeEach(() => {
    getMock.mockReset();
  });

  it("getDeployment calls GET /deployment and returns config", async () => {
    getMock.mockResolvedValue({ data: personalDeployment });

    const deployment = await getDeployment();

    expect(getMock).toHaveBeenCalledWith("/deployment");
    expect(deployment.edition).toBe(Edition.PERSONAL);
    expect(deployment.modules.orders).toBe(false);
    expect(deployment.dashboard_layout).not.toContain("pending_orders");
    expect(deployment.capabilities).toEqual([
      "manage_inventory",
      "view_catalog",
      "view_pricing",
    ]);
  });
});