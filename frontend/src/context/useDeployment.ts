import { useContext } from "react";
import { DeploymentContext } from "./deploymentContextImpl";

export const useDeployment = () => {
  const context = useContext(DeploymentContext);
  if (!context) {
    throw new Error("useDeployment must be used within a DeploymentProvider");
  }
  return context;
};
