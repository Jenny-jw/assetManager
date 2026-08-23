import { beforeEach, describe, expect, it, vi } from "vitest";

const { postMock } = vi.hoisted(() => ({
  postMock: vi.fn(),
}));

vi.mock("@/lib/axios", () => ({
  default: {
    post: postMock,
    get: vi.fn(),
  },
}));

import { login, normalizeSlug, signup } from "@/services/authServices";
import { Edition } from "@/types/Deployment";

describe("authServices", () => {
  beforeEach(() => {
    postMock.mockReset();
  });

  it("normalizeSlug lowercases and trims", () => {
    expect(normalizeSlug("  My-Shop ")).toBe("my-shop");
  });

  it("signup sends slug, username, and edition", async () => {
    postMock.mockResolvedValue({
      data: {
        id: "u1",
        tenant_id: "t1",
        username: "owner1",
        name: "Owner",
        email: null,
        role: "owner",
      },
    });

    await signup({
      slug: "My-Shop",
      username: "owner1",
      name: "Owner",
      email: "",
      password: "secretpass",
      edition: Edition.PROFESSIONAL,
    });

    expect(postMock).toHaveBeenCalledWith("/auth/signup", {
      slug: "my-shop",
      username: "owner1",
      name: "Owner",
      email: null,
      password: "secretpass",
      edition: "professional",
    });
  });

  it("login sends slug and username", async () => {
    postMock.mockResolvedValue({ data: { message: "Login successful" } });

    await login({
      slug: "My-Shop",
      username: "owner1",
      password: "secretpass",
    });

    expect(postMock).toHaveBeenCalledWith(
      "/auth/login",
      {
        slug: "my-shop",
        username: "owner1",
        password: "secretpass",
      },
      { withCredentials: true },
    );
  });
});
