import { afterEach, beforeEach, describe, expect, it } from "vitest";
import i18n, {
  applyDeploymentLocale,
  applyPreferredLocale,
  FALLBACK_LOCALE,
} from "@/i18n";
import { LOCALE_STORAGE_KEY } from "@/i18n/localeStorage";
import { Locale } from "@/types/Deployment";

describe("applyDeploymentLocale", () => {
  beforeEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(FALLBACK_LOCALE);
  });

  afterEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(FALLBACK_LOCALE);
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

  it("does not let a later tenant locale override the persisted user choice", async () => {
    applyDeploymentLocale(Locale.EN);
    await i18n.changeLanguage(Locale.EN);
    applyPreferredLocale(Locale.ZH_TW);
    await i18n.changeLanguage(Locale.EN);
    expect(i18n.language).toBe(Locale.EN);
    expect(i18n.t("dashboard.title")).toBe("Tea Keeper Dashboard");
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.EN);
  });
});

describe("applyPreferredLocale", () => {
  beforeEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(FALLBACK_LOCALE);
  });

  afterEach(async () => {
    window.localStorage.clear();
    await i18n.changeLanguage(FALLBACK_LOCALE);
  });

  it("keeps a saved locale and does not overwrite it with tenant locale", async () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, Locale.EN);
    applyPreferredLocale(Locale.ZH_TW);
    await i18n.changeLanguage(Locale.EN);
    expect(i18n.language).toBe(Locale.EN);
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.EN);
  });

  it("seeds storage from tenant locale when nothing is saved", async () => {
    applyPreferredLocale(Locale.ZH_TW);
    await i18n.changeLanguage(Locale.ZH_TW);
    expect(i18n.language).toBe(Locale.ZH_TW);
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.ZH_TW);
  });

  it("falls back to en without writing storage when nothing is saved", async () => {
    applyPreferredLocale();
    await i18n.changeLanguage(FALLBACK_LOCALE);
    expect(i18n.language).toBe(FALLBACK_LOCALE);
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBeNull();
  });

  it("keeps a saved locale when tenant locale is absent", async () => {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, Locale.ZH_TW);
    applyPreferredLocale();
    await i18n.changeLanguage(Locale.ZH_TW);
    expect(i18n.language).toBe(Locale.ZH_TW);
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.ZH_TW);
  });

  it("uses tenant locale only as fallback after applyDeploymentLocale", async () => {
    applyDeploymentLocale(Locale.ZH_TW);
    await i18n.changeLanguage(Locale.ZH_TW);
    applyPreferredLocale(Locale.EN);
    await i18n.changeLanguage(Locale.ZH_TW);
    expect(i18n.language).toBe(Locale.ZH_TW);
    expect(i18n.t("dashboard.title")).toBe("茶葉管家儀表板");
    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.ZH_TW);
  });
});
