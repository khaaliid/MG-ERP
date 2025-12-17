import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';

export interface POSSettings {
  id?: number;
  tax_rate: number; // decimal (e.g., 0.14)
  tax_inclusive?: string; // 'true' | 'false'
  currency_code: string;
  currency_symbol: string;
  business_name?: string | null;
  business_address?: string | null;
  business_phone?: string | null;
  business_email?: string | null;
  business_tax_id?: string | null;
  receipt_header?: string | null;
  receipt_footer?: string | null;
  print_receipt?: string; // 'true' | 'false'
  require_customer_name?: string; // 'true' | 'false'
  allow_discounts?: string; // 'true' | 'false'
  low_stock_threshold?: number;
  updated_by?: string | null;
}

interface SettingsContextValue {
  settings: POSSettings | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

const SettingsContext = createContext<SettingsContextValue | undefined>(undefined);

export const SettingsProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<POSSettings | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8001/api/v1';
      const token = localStorage.getItem('pos_auth_token') || '';
      const resp = await fetch(`${apiBase}/settings/`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Accept': 'application/json'
        }
      });
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ detail: 'Failed to load settings' }));
        throw new Error(err.detail || 'Failed to load settings');
      }
      const data = (await resp.json()) as POSSettings;
      setSettings(data);
    } catch (e: any) {
      setError(e?.message || 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const value = useMemo<SettingsContextValue>(() => ({
    settings,
    loading,
    error,
    refresh: fetchSettings,
  }), [settings, loading, error]);

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = (): SettingsContextValue => {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useSettings must be used within SettingsProvider');
  return ctx;
};
