import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Login from "@/pages/Login";
import { AuthContext } from "@/context/authContextImpl";
import type { AuthContextType } from "@/context/authContextImpl";

const { loginMock } = vi.hoisted(() => ({
  loginMock: vi.fn(),
}));

vi.mock("@/services/authServices", async () => {
  const actual = await vi.importActual<typeof import("@/services/authServices")>(
    "@/services/authServices",
  );
  return {
    ...actual,
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

function renderLogin() {
  return render(
    <AuthContext.Provider value={baseAuth}>
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    </AuthContext.Provider>,
  );
}

describe("Login", () => {
  beforeEach(() => {
    loginMock.mockReset();
    refreshMock.mockReset();
    loginMock.mockResolvedValue({ message: "Login successful" });
    refreshMock.mockResolvedValue(undefined);
  });

  it("collects slug and username instead of email", () => {
    renderLogin();

    expect(screen.getByPlaceholderText("Shop ID")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Username")).toBeInTheDocument();
    expect(screen.queryByPlaceholderText("Email")).not.toBeInTheDocument();
    expect(
      screen.queryByText("View Dashboard as Guest →"),
    ).not.toBeInTheDocument();
  });

  it("submits slug, username, and password", async () => {
    renderLogin();

    fireEvent.change(screen.getByPlaceholderText("Shop ID"), {
      target: { value: "my-shop" },
    });
    fireEvent.change(screen.getByPlaceholderText("Username"), {
      target: { value: "owner1" },
    });
    fireEvent.change(screen.getByPlaceholderText("Password"), {
      target: { value: "secretpass" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Log In" }));

    await waitFor(() => {
      expect(loginMock).toHaveBeenCalledWith({
        slug: "my-shop",
        username: "owner1",
        password: "secretpass",
      });
    });
    expect(refreshMock).toHaveBeenCalled();
  });
});
