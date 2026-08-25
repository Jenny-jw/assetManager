import { Locale, type Locale as UiLocale } from "../types/Deployment";

export const LOCALE_STORAGE_KEY = "assetManager.locale";

export const isSupportedLocale = (value: unknown): value is UiLocale =>
  value === Locale.EN || value === Locale.ZH_TW;

export const readStoredLocale = (): UiLocale | null => {
  try {
    const raw = window.localStorage.getItem(LOCALE_STORAGE_KEY);
    return isSupportedLocale(raw) ? raw : null;
  } catch {
    return null;
  }
};

export const writeStoredLocale = (locale: UiLocale): void => {
  try {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch {
    // Ignore quota / private-mode failures; UI can still switch in-memory.
  }
};

export const resolveInitialLocale = (fallback: UiLocale): UiLocale =>
  readStoredLocale() ?? fallback;
