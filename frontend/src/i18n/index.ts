import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en.json";
import zhTW from "./locales/zh-TW.json";
import { Locale, type Locale as TenantLocale } from "../types/Deployment";
import {
  isSupportedLocale,
  readStoredLocale,
  resolveInitialLocale,
  resolvePreferredLocale,
  writeStoredLocale,
} from "./localeStorage";

export const DEFAULT_LOCALE: TenantLocale = Locale.EN;
export const FALLBACK_LOCALE: TenantLocale = Locale.EN;

const resources = {
  [Locale.EN]: { common: en },
  [Locale.ZH_TW]: { common: zhTW },
} as const;

void i18n.use(initReactI18next).init({
  resources,
  lng: resolveInitialLocale(DEFAULT_LOCALE),
  fallbackLng: FALLBACK_LOCALE,
  defaultNS: "common",
  interpolation: {
    escapeValue: false,
  },
});

export const applyDeploymentLocale = (
  locale: TenantLocale | null | undefined,
): void => {
  if (isSupportedLocale(locale)) {
    writeStoredLocale(locale);
    void i18n.changeLanguage(locale);
    return;
  }
  void i18n.changeLanguage(FALLBACK_LOCALE);
};

export const applyPreferredLocale = (
  tenantLocale?: TenantLocale | null,
): void => {
  if (!readStoredLocale() && isSupportedLocale(tenantLocale)) {
    writeStoredLocale(tenantLocale);
  }
  void i18n.changeLanguage(
    resolvePreferredLocale(tenantLocale, FALLBACK_LOCALE),
  );
};

export default i18n;
