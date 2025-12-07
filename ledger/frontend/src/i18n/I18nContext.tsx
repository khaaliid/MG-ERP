import React, { createContext, useContext, useMemo, useState } from 'react';
import { translations, LangKey } from './translations';

type I18nContextType = {
  lang: LangKey;
  setLang: (l: LangKey) => void;
  t: (key: string) => string;
  dir: 'ltr' | 'rtl';
};

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export const useI18n = () => {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error('useI18n must be used within I18nProvider');
  return ctx;
};

export const I18nProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [lang, setLang] = useState<LangKey>(() => {
    const saved = localStorage.getItem('ledger_lang');
    return (saved === 'ar' || saved === 'en') ? (saved as LangKey) : 'en';
  });

  const t = useMemo(() => {
    const dict = translations[lang] || translations.en;
    return (key: string) => dict[key] ?? key;
  }, [lang]);

  const dir: 'ltr' | 'rtl' = lang === 'ar' ? 'rtl' : 'ltr';

  const value: I18nContextType = {
    lang,
    setLang: (l: LangKey) => {
      localStorage.setItem('ledger_lang', l);
      setLang(l);
    },
    t,
    dir,
  };

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
};