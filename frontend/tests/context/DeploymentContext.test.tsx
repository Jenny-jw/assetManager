import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Edition } from "@/types/Deployment";

const { getDeploymentMock } = vi.hoisted(() => ({
  getDeploymentMock: vi.fn(),
}));

vi.mock("@/services/deploymentServices", () => ({
  getDeployment: getDeploymentMock,
}));

import { DeploymentProvider } from "@/context/DeploymentContext";
import { useDeployment } from "@/context/useDeployment";

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
} as const;

function DeploymentProbe() {
  const { deployment, loading } = useDeployment();
  if (loading) {
    return <div>loading</div>;
  }
  if (!deployment) {
    return <div>no deployment</div>;
  }
  return <div>edition:{deployment.edition}</div>;
}

describe("DeploymentProvider", () => {
  beforeEach(() => {
    getDeploymentMock.mockReset();
  });

  it("loads deployment once on mount", async () => {
    getDeploymentMock.mockResolvedValue(personalDeployment);

    render(
      <DeploymentProvider>
        <DeploymentProbe />
      </DeploymentProvider>,
    );

    expect(screen.getByText("loading")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(`edition:${Edition.PERSONAL}`)).toBeInTheDocument();
    });

    expect(getDeploymentMock).toHaveBeenCalledTimes(1);
  });

  it("sets deployment to null when fetch fails", async () => {
    getDeploymentMock.mockRejectedValue(new Error("network error"));

    render(
      <DeploymentProvider>
        <DeploymentProbe />
      </DeploymentProvider>,
    );

    await waitFor(() => {
      expect(screen.getByText("no deployment")).toBeInTheDocument();
    });
  });

  it("useDeployment throws outside provider", () => {
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});

    expect(() => render(<DeploymentProbe />)).toThrow(
      "useDeployment must be used within a DeploymentProvider",
    );

    consoleError.mockRestore();
  });
});
