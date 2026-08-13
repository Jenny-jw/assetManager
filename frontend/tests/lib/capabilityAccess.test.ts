import { describe, expect, it } from "vitest";
import { personalDeployment } from "../fixtures/personalDeployment";
import { professionalDeployment } from "../fixtures/professionalDeployment";
import { hasCapability } from "@/lib/capabilityAccess";
import { Capability } from "@/types/Deployment";

describe("hasCapability", () => {
  it("returns true when the capability is granted", () => {
    expect(hasCapability(personalDeployment, Capability.MANAGE_INVENTORY)).toBe(
      true,
    );
    expect(hasCapability(professionalDeployment, Capability.APPROVE_ORDERS)).toBe(
      true,
    );
  });

  it("returns false when the capability is not granted", () => {
    expect(hasCapability(personalDeployment, Capability.APPROVE_ORDERS)).toBe(
      false,
    );
    expect(hasCapability(personalDeployment, Capability.VIEW_PROFIT)).toBe(false);
  });

  it("returns false when deployment is missing", () => {
    expect(hasCapability(null, Capability.MANAGE_INVENTORY)).toBe(false);
  });
});