import React from 'react';
import { useI18n } from '../i18n/I18nContext';

const LanguageSwitcher: React.FC = () => {
  const { lang, setLang, t } = useI18n();
  return (
    <div className="flex items-center gap-2 bg-white p-1 rounded">
      <span className="text-sm font-medium text-gray-700">{t('language')}:</span>
      <button
        className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
          lang === 'en' 
            ? 'bg-indigo-600 text-white shadow-sm' 
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
        onClick={() => setLang('en')}
      >
        {t('english')}
      </button>
      <button
        className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${
          lang === 'ar' 
            ? 'bg-indigo-600 text-white shadow-sm' 
            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
        }`}
        onClick={() => setLang('ar')}
      >
        {t('arabic')}
      </button>
    </div>
  );
};

export default LanguageSwitcher;