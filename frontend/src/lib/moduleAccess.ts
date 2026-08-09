import type { Deployment, DeploymentModules } from "../types/Deployment";

export type ModuleKey = keyof DeploymentModules;

export const isModuleEnabled = (
  deployment: Deployment | null | undefined,
  moduleKey: ModuleKey,
): boolean => {
  return deployment?.modules[moduleKey] === true;
};
