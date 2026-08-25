import { beforeEach, describe, expect, it } from "vitest";
import i18n, { applyDeploymentLocale, FALLBACK_LOCALE } from "@/i18n";
import { LOCALE_STORAGE_KEY } from "@/i18n/localeStorage";
import { Locale } from "@/types/Deployment";

describe("applyDeploymentLocale", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("switches to zh-TW and persists it", async () => {
    applyDeploymentLocale(Locale.ZH_TW);
    await i18n.changeLanguage(Locale.ZH_TW);
    expect(i18n.language).toBe(Locale.ZH_TW);
    expect(i18n.t("dashboard.title")).toBe("茶葉管家儀表板");
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.ZH_TW);
  });

  it("switches to en and persists it", async () => {
    applyDeploymentLocale(Locale.EN);
    await i18n.changeLanguage(Locale.EN);
    expect(i18n.language).toBe(Locale.EN);
    expect(i18n.t("dashboard.title")).toBe("Tea Keeper Dashboard");
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.EN);
  });

  it("falls back to en for unknown locale without writing storage", async () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, Locale.ZH_TW);
    applyDeploymentLocale(null);
    await i18n.changeLanguage(FALLBACK_LOCALE);
    expect(i18n.language).toBe(FALLBACK_LOCALE);
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.ZH_TW);
  });
});
