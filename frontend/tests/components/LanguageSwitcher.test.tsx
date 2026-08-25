import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { useTranslation } from "react-i18next";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import i18n from "@/i18n";
import { LOCALE_STORAGE_KEY } from "@/i18n/localeStorage";
import { Locale } from "@/types/Deployment";

function Probe() {
  const { t } = useTranslation();
  return (
    <>
      <LanguageSwitcher />
      <p>{t("auth.login")}</p>
    </>
  );
}

describe("LanguageSwitcher", () => {
  beforeEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(Locale.EN);
  });

  afterEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(Locale.EN);
  });

  it("persists zh-TW and updates copy when 中文 is clicked", async () => {
    render(<Probe />);

    expect(screen.getByRole("group", { name: "Language" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "中文" }));

    await waitFor(() => {
      expect(i18n.language).toBe(Locale.ZH_TW);
      expect(screen.getByText("登入")).toBeInTheDocument();
    });
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.ZH_TW);
    expect(screen.getByRole("button", { name: "中文" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("persists en and restores English copy", async () => {
    await i18n.changeLanguage(Locale.ZH_TW);
    render(<Probe />);

    fireEvent.click(screen.getByRole("button", { name: "EN" }));

    await waitFor(() => {
      expect(i18n.language).toBe(Locale.EN);
      expect(screen.getByText("Log In")).toBeInTheDocument();
    });
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.EN);
  });
});