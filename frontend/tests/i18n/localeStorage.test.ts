import { beforeEach, describe, expect, it } from "vitest";
import { Locale } from "@/types/Deployment";
import {
  LOCALE_STORAGE_KEY,
  readStoredLocale,
  resolveInitialLocale,
  writeStoredLocale,
} from "@/i18n/localeStorage";

describe("localeStorage", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("round-trips a supported locale", () => {
    writeStoredLocale(Locale.ZH_TW);

    expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe(Locale.ZH_TW);
    expect(readStoredLocale()).toBe(Locale.ZH_TW);
  });

  it("returns null for missing or unsupported values", () => {
    expect(readStoredLocale()).toBeNull();
    window.localStorage.setItem(LOCALE_STORAGE_KEY, "fr");
    expect(readStoredLocale()).toBeNull();
  });

  it("resolveInitialLocale uses storage before the fallback", () => {
    expect(resolveInitialLocale(Locale.EN)).toBe(Locale.EN);
    writeStoredLocale(Locale.ZH_TW);
    expect(resolveInitialLocale(Locale.EN)).toBe(Locale.ZH_TW);
  });
});
