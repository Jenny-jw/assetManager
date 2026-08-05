import { describe, expect, it } from "vitest";
import { personalDeployment } from "../fixtures/personalDeployment";
import { professionalDeployment } from "../fixtures/professionalDeployment";
import { isModuleEnabled } from "@/lib/moduleAccess";

describe("isModuleEnabled", () => {
  it("returns true when module flag is enabled", () => {
    expect(isModuleEnabled(professionalDeployment, "orders")).toBe(true);
  });

  it("returns false when module flag is disabled", () => {
    expect(isModuleEnabled(personalDeployment, "orders")).toBe(false);
  });

  it("returns false when deployment is missing", () => {
    expect(isModuleEnabled(null, "inventory")).toBe(false);
  });
});
