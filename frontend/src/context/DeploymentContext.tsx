import { useEffect, useState } from "react";
import { getDeployment } from "../services/deploymentServices";
import type { Deployment } from "../types/Deployment";
import { useAuth } from "./useAuth";
import { DeploymentContext } from "./deploymentContextImpl";

export const DeploymentProvider = ({ children }: { children: React.ReactNode }) => {
  const { user, loading: authLoading } = useAuth();
  const [deployment, setDeployment] = useState<Deployment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) {
      return;
    }
    if (!user) {
      setDeployment(null);
      setLoading(false);
      return;
    }
    let mounted = true;
    setLoading(true);
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
  }, [user, authLoading]);

  return (
    <DeploymentContext.Provider value={{ deployment, loading }}>
      {children}
    </DeploymentContext.Provider>
  );
};
