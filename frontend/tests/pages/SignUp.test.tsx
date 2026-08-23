import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import SignUp from "@/pages/SignUp";
import { AuthContext } from "@/context/authContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";
import { Edition } from "@/types/Deployment";

const { signupMock, loginMock } = vi.hoisted(() => ({
  signupMock: vi.fn(),
  loginMock: vi.fn(),
}));

vi.mock("@/services/authServices", async () => {
  const actual = await vi.importActual<typeof import("@/services/authServices")>(
    "@/services/authServices",
  );
  return {
    ...actual,
    signup: signupMock,
    login: loginMock,
  };
});

const refreshMock = vi.fn();

const baseAuth: AuthContextType = {
  user: null,
  loading: false,
  refresh: refreshMock,
  login: async () => {},
  logout: async () => {},
};

function renderSignUp() {
  return render(
    <AuthContext.Provider value={baseAuth}>
      <MemoryRouter>
        <SignUp />
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe("SignUp", () => {
  beforeEach(() => {
    signupMock.mockReset();
    loginMock.mockReset();
    refreshMock.mockReset();
    signupMock.mockResolvedValue({ id: "u1" });
    loginMock.mockResolvedValue({ message: "Login successful" });
    refreshMock.mockResolvedValue(undefined);
  });

  it("collects slug, username, and edition", () => {
    renderSignUp();

    expect(screen.getByPlaceholderText("Shop ID")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Username")).toBeInTheDocument();
    expect(screen.getByText("Professional")).toBeInTheDocument();
    expect(screen.getByDisplayValue("personal")).toBeChecked();
  });

  it("signs up then logs in with the chosen edition", async () => {
    renderSignUp();

    fireEvent.change(screen.getByPlaceholderText("Shop ID"), {
      target: { value: "my-shop" },
    });
    fireEvent.change(screen.getByPlaceholderText("Username"), {
      target: { value: "owner1" },
    });
    fireEvent.change(screen.getByPlaceholderText("Display name"), {
      target: { value: "Owner" },
    });
    fireEvent.change(screen.getByPlaceholderText("Password"), {
      target: { value: "secretpass" },
    });
    fireEvent.click(screen.getByDisplayValue("professional"));
    fireEvent.click(screen.getByRole("button", { name: "Sign Up" }));

    await waitFor(() => {
      expect(signupMock).toHaveBeenCalledWith({
        slug: "my-shop",
        username: "owner1",
        name: "Owner",
        email: "",
        password: "secretpass",
        edition: Edition.PROFESSIONAL,
      });
    });
    expect(loginMock).toHaveBeenCalledWith({
      slug: "my-shop",
      username: "owner1",
      password: "secretpass",
    });
    expect(refreshMock).toHaveBeenCalled();
  });
});
