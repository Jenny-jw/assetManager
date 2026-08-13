import { describe, expect, it } from "vitest";
import { getApiErrorCode, getApiErrorMessage } from "@/lib/apiError";

const axiosError = (data: unknown) =>
  ({
    isAxiosError: true,
    response: { data },
  }) as const;

describe("apiError", () => {
  it("reads structured error code and message from the envelope", () => {
    const error = axiosError({
      detail: "module_disabled",
      error: {
        code: "module_disabled",
        message: "This module is not enabled for the current tenant.",
      },
    });

    expect(getApiErrorCode(error)).toBe("module_disabled");
    expect(getApiErrorMessage(error, "fallback")).toBe(
      "This module is not enabled for the current tenant.",
    );
  });

  it("falls back to detail when the envelope is missing", () => {
    const error = axiosError({ detail: "invalid_credentials" });

    expect(getApiErrorCode(error)).toBe("invalid_credentials");
    expect(getApiErrorMessage(error, "fallback")).toBe("invalid_credentials");
  });

  it("formats validation details from error.details", () => {
    const error = axiosError({
      detail: "validation_error",
      error: {
        code: "validation_error",
        message: "Request validation failed",
        details: [{ loc: ["body", "name"], msg: "Field required" }],
      },
    });

    expect(getApiErrorMessage(error, "fallback")).toBe("name: Field required");
  });
});
