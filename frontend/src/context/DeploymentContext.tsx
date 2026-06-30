import { useEffect, useState } from "react";
import { getDeployment } from "../services/deploymentServices";
import type { Deployment } from "../types/Deployment";
import { DeploymentContext } from "./deploymentContextImpl";

export const DeploymentProvider = ({ children }: { children: React.ReactNode }) => {
  const [deployment, setDeployment] = useState<Deployment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const config = await getDeployment();
        if (mounted) setDeployment(config);
      } catch {
        if (mounted) setDeployment(null);
      } finally {
        if (mounted) setLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <DeploymentContext.Provider value={{ deployment, loading }}>
      {children}
    </DeploymentContext.Provider>
  );
};
