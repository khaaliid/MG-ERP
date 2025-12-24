import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';

interface DashboardData {
  report_type: string;
  as_of_date: string;
  key_metrics: {
    total_assets: number;
    total_liabilities: number;
    net_worth: number;
    ytd_net_income: number;
    books_balanced: boolean;
  };
  balance_sheet_summary: {
    assets: number;
    liabilities: number;
    equity: number;
  };
  income_summary: {
    total_income: number;
    total_expenses: number;
    net_income: number;
  };
  system_health: {
    trial_balance_balanced: boolean;
    balance_sheet_balanced: boolean;
    total_accounts: number;
  };
}

const DashboardPage: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = async () => {
    if (!token) {
      setError('Authentication required. Please log in again.');
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/reports/dashboard', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch dashboard: ${response.statusText}`);
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
      fetchDashboard();
    }
  }, [token]);

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
      <Layout currentPage="reports">
        <div className="p-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading Financial Dashboard...</p>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout currentPage="reports">
        <div className="p-8">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error Loading Dashboard</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
                <div className="mt-4">
                  <button
                    onClick={fetchDashboard}
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
    <Layout currentPage="reports">
      <div className="p-8">
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-3xl font-bold text-gray-900">🎯 Financial Dashboard</h1>
            <button
              onClick={fetchDashboard}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium flex items-center"
            >
              <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Refresh
            </button>
          </div>
          {data && (
            <p className="text-gray-600">
              As of {formatDate(data.as_of_date)}
            </p>
          )}
        </div>

        {data && (
          <div className="space-y-8">
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white shadow-md rounded-lg p-6 border-l-4 border-blue-500">
                <div className="flex items-center">
                  <div className="text-blue-600">
                    <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-600">Total Assets</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(data.key_metrics.total_assets)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white shadow-md rounded-lg p-6 border-l-4 border-red-500">
                <div className="flex items-center">
                  <div className="text-red-600">
                    <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-600">Total Liabilities</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(data.key_metrics.total_liabilities)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white shadow-md rounded-lg p-6 border-l-4 border-green-500">
                <div className="flex items-center">
                  <div className="text-green-600">
                    <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-600">Net Worth</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {formatCurrency(data.key_metrics.net_worth)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white shadow-md rounded-lg p-6 border-l-4 border-purple-500">
                <div className="flex items-center">
                  <div className="text-purple-600">
                    <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-600">YTD Net Income</p>
                    <p className={`text-2xl font-bold ${
                      data.key_metrics.ytd_net_income >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(data.key_metrics.ytd_net_income)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Financial Summary */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Balance Sheet Summary */}
              <div className="bg-white shadow-md rounded-lg overflow-hidden">
                <div className="bg-blue-50 px-6 py-4 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">Balance Sheet Summary</h2>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700 font-medium">Assets</span>
                      <span className="text-lg font-semibold text-blue-600">
                        {formatCurrency(data.balance_sheet_summary.assets)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700 font-medium">Liabilities</span>
                      <span className="text-lg font-semibold text-red-600">
                        {formatCurrency(data.balance_sheet_summary.liabilities)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700 font-medium">Equity</span>
                      <span className="text-lg font-semibold text-green-600">
                        {formatCurrency(data.balance_sheet_summary.equity)}
                      </span>
                    </div>
                    <div className="border-t pt-4">
                      <div className="flex justify-between items-center">
                        <span className="text-lg font-semibold text-gray-900">
                          Balance Check (Assets = Liabilities + Equity)
                        </span>
                        <span className={`text-lg font-bold ${
                          data.system_health.balance_sheet_balanced ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {data.system_health.balance_sheet_balanced ? '✅ Balanced' : '❌ Unbalanced'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Income Summary */}
              <div className="bg-white shadow-md rounded-lg overflow-hidden">
                <div className="bg-green-50 px-6 py-4 border-b border-gray-200">
                  <h2 className="text-xl font-semibold text-gray-900">Year-to-Date Income Summary</h2>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700 font-medium">Total Income</span>
                      <span className="text-lg font-semibold text-green-600">
                        {formatCurrency(data.income_summary.total_income)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700 font-medium">Total Expenses</span>
                      <span className="text-lg font-semibold text-red-600">
                        {formatCurrency(data.income_summary.total_expenses)}
                      </span>
                    </div>
                    <div className="border-t pt-4">
                      <div className="flex justify-between items-center">
                        <span className="text-lg font-semibold text-gray-900">Net Income</span>
                        <span className={`text-xl font-bold ${
                          data.income_summary.net_income >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatCurrency(data.income_summary.net_income)}
                        </span>
                      </div>
                      <div className="text-center mt-2">
                        <span className={`text-sm ${
                          data.income_summary.net_income >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {data.income_summary.net_income >= 0 ? '📈 Profitable Year' : '📉 Loss Year'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* System Health */}
            <div className="bg-white shadow-md rounded-lg overflow-hidden">
              <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">System Health</h2>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className={`p-4 rounded-lg border ${
                    data.system_health.trial_balance_balanced 
                      ? 'border-green-300 bg-green-50' 
                      : 'border-red-300 bg-red-50'
                  }`}>
                    <div className="flex items-center">
                      <div className={`flex-shrink-0 ${
                        data.system_health.trial_balance_balanced ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {data.system_health.trial_balance_balanced ? (
                          <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                      <div className="ml-3">
                        <h3 className={`text-sm font-medium ${
                          data.system_health.trial_balance_balanced ? 'text-green-800' : 'text-red-800'
                        }`}>
                          Trial Balance
                        </h3>
                        <div className={`text-xs ${
                          data.system_health.trial_balance_balanced ? 'text-green-700' : 'text-red-700'
                        }`}>
                          {data.system_health.trial_balance_balanced ? 'Balanced' : 'Unbalanced'}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className={`p-4 rounded-lg border ${
                    data.system_health.balance_sheet_balanced 
                      ? 'border-green-300 bg-green-50' 
                      : 'border-red-300 bg-red-50'
                  }`}>
                    <div className="flex items-center">
                      <div className={`flex-shrink-0 ${
                        data.system_health.balance_sheet_balanced ? 'text-green-400' : 'text-red-400'
                      }`}>
                        {data.system_health.balance_sheet_balanced ? (
                          <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                          </svg>
                        )}
                      </div>
                      <div className="ml-3">
                        <h3 className={`text-sm font-medium ${
                          data.system_health.balance_sheet_balanced ? 'text-green-800' : 'text-red-800'
                        }`}>
                          Balance Sheet
                        </h3>
                        <div className={`text-xs ${
                          data.system_health.balance_sheet_balanced ? 'text-green-700' : 'text-red-700'
                        }`}>
                          {data.system_health.balance_sheet_balanced ? 'Balanced' : 'Unbalanced'}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="p-4 rounded-lg border border-blue-300 bg-blue-50">
                    <div className="flex items-center">
                      <div className="text-blue-400 flex-shrink-0">
                        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <h3 className="text-sm font-medium text-blue-800">
                          Total Accounts
                        </h3>
                        <div className="text-lg font-bold text-blue-900">
                          {data.system_health.total_accounts}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Overall Health Indicator */}
            <div className={`rounded-lg p-6 ${
              data.key_metrics.books_balanced 
                ? 'bg-green-50 border border-green-200' 
                : 'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-center">
                <div className={`flex-shrink-0 ${
                  data.key_metrics.books_balanced ? 'text-green-400' : 'text-red-400'
                }`}>
                  {data.key_metrics.books_balanced ? (
                    <svg className="h-8 w-8" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <svg className="h-8 w-8" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                  )}
                </div>
                <div className="ml-4">
                  <h2 className={`text-xl font-bold ${
                    data.key_metrics.books_balanced ? 'text-green-800' : 'text-red-800'
                  }`}>
                    {data.key_metrics.books_balanced 
                      ? 'Books are Balanced! ✅' 
                      : 'Books Need Attention! ⚠️'
                    }
                  </h2>
                  <p className={`text-sm ${
                    data.key_metrics.books_balanced ? 'text-green-700' : 'text-red-700'
                  }`}>
                    {data.key_metrics.books_balanced 
                      ? 'Your accounting records are in good order and all accounts are balanced.'
                      : 'There are balancing issues that need to be reviewed and corrected.'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default DashboardPage;