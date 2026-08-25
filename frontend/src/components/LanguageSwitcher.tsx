import { useTranslation } from "react-i18next";

import { applyDeploymentLocale } from "../i18n";
import { isSupportedLocale } from "../i18n/localeStorage";
import { Locale } from "../types/Deployment";

const LANGUAGE_OPTIONS = [
  { locale: Locale.EN, label: "EN" },
  { locale: Locale.ZH_TW, label: "中文" },
] as const;

const LanguageSwitcher = () => {
  const { t, i18n } = useTranslation();
  const current = isSupportedLocale(i18n.resolvedLanguage)
    ? i18n.resolvedLanguage
    : isSupportedLocale(i18n.language)
      ? i18n.language
      : Locale.EN;

  return (
    <div
      role="group"
      aria-label={t("language.label")}
      className="inline-flex overflow-hidden rounded-lg border border-[#9e9d87]"
    >
      {LANGUAGE_OPTIONS.map(({ locale, label }) => {
        const selected = current === locale;
        return (
          <button
            key={locale}
            type="button"
            aria-pressed={selected}
            onClick={() => applyDeploymentLocale(locale)}
            className={
              selected
                ? "px-3 py-1.5 text-sm bg-[#bdcd68] text-[#425b2a]"
                : "px-3 py-1.5 text-sm bg-transparent text-[#ece2ba] hover:bg-[#64794d]"
            }
          >
            {label}
          </button>
        );
      })}
    </div>
  );
};

export default LanguageSwitcher;