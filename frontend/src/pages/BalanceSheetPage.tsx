import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';

interface BalanceSheetData {
  report_type: string;
  as_of_date: string;
  assets: {
    current_assets: Array<{
      id: number;
      name: string;
      code: string;
      balance: number;
    }>;
    non_current_assets: Array<{
      id: number;
      name: string;
      code: string;
      balance: number;
    }>;
    total: number;
  };
  liabilities: {
    current_liabilities: Array<{
      id: number;
      name: string;
      code: string;
      balance: number;
    }>;
    non_current_liabilities: Array<{
      id: number;
      name: string;
      code: string;
      balance: number;
    }>;
    total: number;
  };
  equity: {
    equity_accounts: Array<{
      id: number;
      name: string;
      code: string;
      balance: number;
    }>;
    retained_earnings: number;
    total: number;
  };
  totals: {
    total_assets: number;
    total_liabilities_equity: number;
    balanced: boolean;
  };
}

const BalanceSheetPage: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<BalanceSheetData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0]);

  const fetchBalanceSheet = async (date?: string) => {
    if (!token) {
      setError('Authentication required. Please log in again.');
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const url = new URL('http://localhost:8000/api/v1/reports/balance-sheet');
      if (date) {
        url.searchParams.append('as_of_date', date);
      }

      const response = await fetch(url.toString(), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch balance sheet: ${response.statusText}`);
      }

      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchBalanceSheet();
    }
  }, [token]);

  const handleDateChange = (newDate: string) => {
    setAsOfDate(newDate);
    fetchBalanceSheet(newDate);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <Layout currentPage="reports" currentReport="balance-sheet">
        <div className="p-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading Balance Sheet...</p>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout currentPage="reports" currentReport="balance-sheet">
        <div className="p-8">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error Loading Balance Sheet</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
                <div className="mt-4">
                  <button
                    onClick={() => fetchBalanceSheet(asOfDate)}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout currentPage="reports" currentReport="balance-sheet">
      <div className="p-8">
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-3xl font-bold text-gray-900">📋 Balance Sheet</h1>
            <div className="flex items-center space-x-4">
              <label htmlFor="as-of-date" className="text-sm font-medium text-gray-700">
                As of Date:
              </label>
              <input
                type="date"
                id="as-of-date"
                value={asOfDate}
                onChange={(e) => handleDateChange(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          {data && (
            <p className="text-gray-600">
              As of {formatDate(data.as_of_date)}
            </p>
          )}
        </div>

        {data && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Assets */}
            <div className="bg-white shadow-md rounded-lg overflow-hidden">
              <div className="bg-blue-50 px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Assets</h2>
              </div>
              <div className="p-6">
                {/* Current Assets */}
                {data.assets.current_assets.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-800 mb-3">Current Assets</h3>
                    <div className="space-y-2">
                      {data.assets.current_assets.map((account) => (
                        <div key={account.id} className="flex justify-between">
                          <span className="text-gray-700">{account.name} ({account.code})</span>
                          <span className="font-medium">{formatCurrency(account.balance)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Non-Current Assets */}
                {data.assets.non_current_assets.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-800 mb-3">Non-Current Assets</h3>
                    <div className="space-y-2">
                      {data.assets.non_current_assets.map((account) => (
                        <div key={account.id} className="flex justify-between">
                          <span className="text-gray-700">{account.name} ({account.code})</span>
                          <span className="font-medium">{formatCurrency(account.balance)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="border-t pt-4 mt-4">
                  <div className="flex justify-between text-lg font-semibold">
                    <span>Total Assets</span>
                    <span className="text-blue-600">{formatCurrency(data.assets.total)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Liabilities & Equity */}
            <div className="bg-white shadow-md rounded-lg overflow-hidden">
              <div className="bg-green-50 px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">Liabilities & Equity</h2>
              </div>
              <div className="p-6">
                {/* Current Liabilities */}
                {data.liabilities.current_liabilities.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-800 mb-3">Current Liabilities</h3>
                    <div className="space-y-2">
                      {data.liabilities.current_liabilities.map((account) => (
                        <div key={account.id} className="flex justify-between">
                          <span className="text-gray-700">{account.name} ({account.code})</span>
                          <span className="font-medium">{formatCurrency(account.balance)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Non-Current Liabilities */}
                {data.liabilities.non_current_liabilities.length > 0 && (
                  <div className="mb-6">
                    <h3 className="text-lg font-medium text-gray-800 mb-3">Non-Current Liabilities</h3>
                    <div className="space-y-2">
                      {data.liabilities.non_current_liabilities.map((account) => (
                        <div key={account.id} className="flex justify-between">
                          <span className="text-gray-700">{account.name} ({account.code})</span>
                          <span className="font-medium">{formatCurrency(account.balance)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {data.liabilities.total > 0 && (
                  <div className="border-t pt-2 mb-6">
                    <div className="flex justify-between font-medium">
                      <span>Total Liabilities</span>
                      <span>{formatCurrency(data.liabilities.total)}</span>
                    </div>
                  </div>
                )}

                {/* Equity */}
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-800 mb-3">Equity</h3>
                  <div className="space-y-2">
                    {data.equity.equity_accounts.map((account) => (
                      <div key={account.id} className="flex justify-between">
                        <span className="text-gray-700">{account.name} ({account.code})</span>
                        <span className="font-medium">{formatCurrency(account.balance)}</span>
                      </div>
                    ))}
                    {data.equity.retained_earnings !== 0 && (
                      <div className="flex justify-between">
                        <span className="text-gray-700">Retained Earnings</span>
                        <span className="font-medium">{formatCurrency(data.equity.retained_earnings)}</span>
                      </div>
                    )}
                  </div>
                  <div className="border-t pt-2 mt-4">
                    <div className="flex justify-between font-medium">
                      <span>Total Equity</span>
                      <span>{formatCurrency(data.equity.total)}</span>
                    </div>
                  </div>
                </div>

                <div className="border-t pt-4 mt-4">
                  <div className="flex justify-between text-lg font-semibold">
                    <span>Total Liabilities & Equity</span>
                    <span className="text-green-600">{formatCurrency(data.totals.total_liabilities_equity)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Balance Check */}
        {data && (
          <div className="mt-8">
            <div className={`border rounded-lg p-4 ${
              data.totals.balanced 
                ? 'border-green-300 bg-green-50' 
                : 'border-red-300 bg-red-50'
            }`}>
              <div className="flex items-center">
                <div className={`flex-shrink-0 ${
                  data.totals.balanced ? 'text-green-400' : 'text-red-400'
                }`}>
                  {data.totals.balanced ? (
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <div className="ml-3">
                  <h3 className={`text-sm font-medium ${
                    data.totals.balanced ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {data.totals.balanced ? 'Balance Sheet is Balanced ✅' : 'Balance Sheet is NOT Balanced ❌'}
                  </h3>
                  <div className={`mt-1 text-sm ${
                    data.totals.balanced ? 'text-green-700' : 'text-red-700'
                  }`}>
                    Assets: {formatCurrency(data.totals.total_assets)} | 
                    Liabilities + Equity: {formatCurrency(data.totals.total_liabilities_equity)}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default BalanceSheetPage;