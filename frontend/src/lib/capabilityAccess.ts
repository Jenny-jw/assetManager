import type { Capability, Deployment } from "../types/Deployment";

export const hasCapability = (
  deployment: Deployment | null | undefined,
  capability: Capability,
): boolean => {
  return deployment?.capabilities.includes(capability) === true;
};