import { describe, expect, it } from "vitest";
import i18n, { applyDeploymentLocale, FALLBACK_LOCALE } from "@/i18n";
import { Locale } from "@/types/Deployment";

describe("applyDeploymentLocale", () => {
  it("switches to zh-TW when tenant locale is zh-TW", async () => {
    applyDeploymentLocale(Locale.ZH_TW);
    await i18n.changeLanguage(Locale.ZH_TW);
    expect(i18n.language).toBe(Locale.ZH_TW);
    expect(i18n.t("dashboard.title")).toBe("茶葉管家儀表板");
  });

  it("switches to en when tenant locale is en", async () => {
    applyDeploymentLocale(Locale.EN);
    await i18n.changeLanguage(Locale.EN);
    expect(i18n.language).toBe(Locale.EN);
    expect(i18n.t("dashboard.title")).toBe("Tea Keeper Dashboard");
  });

  it("falls back to en for unknown locale", async () => {
    applyDeploymentLocale(null);
    await i18n.changeLanguage(FALLBACK_LOCALE);
    expect(i18n.language).toBe(FALLBACK_LOCALE);
  });
});
