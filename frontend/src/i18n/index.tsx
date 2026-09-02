import { createContext, useContext, type ReactNode } from "react";
import { en, type TranslationKeys } from "./en";

const locales = { en };
type LocaleCode = keyof typeof locales;

const I18nContext = createContext<TranslationKeys>(en);

export function I18nProvider({
  locale = "en",
  children,
}: {
  locale?: LocaleCode;
  children: ReactNode;
}) {
  return (
    <I18nContext.Provider value={locales[locale]}>
      {children}
    </I18nContext.Provider>
  );
}

export function useTranslations(): TranslationKeys {
  return useContext(I18nContext);
}
