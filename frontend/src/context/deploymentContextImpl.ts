import { createContext } from "react";
import type { Deployment } from "../types/Deployment";

export type DeploymentContextType = {
  deployment: Deployment | null;
  loading: boolean;
};

export const DeploymentContext = createContext<DeploymentContextType | undefined>(
  undefined,
);
