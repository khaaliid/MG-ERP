import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';

interface IncomeStatementData {
  report_type: string;
  start_date: string;
  end_date: string;
  income: {
    accounts: Array<{
      id: number;
      name: string;
      code: string;
      balance: number;
    }>;
    total: number;
  };
  expenses: {
    accounts: Array<{
      id: number;
      name: string;
      code: string;
      balance: number;
    }>;
    total: number;
  };
  net_income: number;
}

const IncomeStatementPage: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<IncomeStatementData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState(() => {
    const currentYear = new Date().getFullYear();
    return `${currentYear}-01-01`;
  });
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

  const fetchIncomeStatement = async (start?: string, end?: string) => {
    if (!token) {
      setError('Authentication required. Please log in again.');
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const url = new URL('http://localhost:8000/api/v1/reports/income-statement');
      url.searchParams.append('start_date', start || startDate);
      if (end) {
        url.searchParams.append('end_date', end);
      }

      const response = await fetch(url.toString(), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch income statement: ${response.statusText}`);
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
      fetchIncomeStatement();
    }
  }, [token]);

  const handleDateRangeChange = () => {
    fetchIncomeStatement(startDate, endDate);
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
      <Layout currentPage="reports" currentReport="income-statement">
        <div className="p-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading Income Statement...</p>
            </div>
          </div>
        </div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout currentPage="reports" currentReport="income-statement">
        <div className="p-8">
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">Error Loading Income Statement</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
                <div className="mt-4">
                  <button
                    onClick={() => fetchIncomeStatement(startDate, endDate)}
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
    <Layout currentPage="reports" currentReport="income-statement">
      <div className="p-8">
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-3xl font-bold text-gray-900">💰 Income Statement (P&L)</h1>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <label htmlFor="start-date" className="text-sm font-medium text-gray-700">
                  From:
                </label>
                <input
                  type="date"
                  id="start-date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center space-x-2">
                <label htmlFor="end-date" className="text-sm font-medium text-gray-700">
                  To:
                </label>
                <input
                  type="date"
                  id="end-date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                onClick={handleDateRangeChange}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Update
              </button>
            </div>
          </div>
          {data && (
            <p className="text-gray-600">
              For the period from {formatDate(data.start_date)} to {formatDate(data.end_date)}
            </p>
          )}
        </div>

        {data && (
          <div className="bg-white shadow-md rounded-lg overflow-hidden">
            <div className="p-6">
              {/* Income Section */}
              <div className="mb-8">
                <div className="bg-green-50 px-4 py-3 border-b border-gray-200 mb-4">
                  <h2 className="text-xl font-semibold text-gray-900">Revenue / Income</h2>
                </div>
                {data.income.accounts.length > 0 ? (
                  <div className="space-y-2 mb-4">
                    {data.income.accounts.map((account) => (
                      <div key={account.id} className="flex justify-between">
                        <span className="text-gray-700">{account.name} ({account.code})</span>
                        <span className="font-medium text-green-600">{formatCurrency(account.balance)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-gray-500 italic mb-4">No income accounts found</div>
                )}
                <div className="border-t pt-3">
                  <div className="flex justify-between text-lg font-semibold">
                    <span>Total Income</span>
                    <span className="text-green-600">{formatCurrency(data.income.total)}</span>
                  </div>
                </div>
              </div>

              {/* Expenses Section */}
              <div className="mb-8">
                <div className="bg-red-50 px-4 py-3 border-b border-gray-200 mb-4">
                  <h2 className="text-xl font-semibold text-gray-900">Expenses</h2>
                </div>
                {data.expenses.accounts.length > 0 ? (
                  <div className="space-y-2 mb-4">
                    {data.expenses.accounts.map((account) => (
                      <div key={account.id} className="flex justify-between">
                        <span className="text-gray-700">{account.name} ({account.code})</span>
                        <span className="font-medium text-red-600">{formatCurrency(account.balance)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-gray-500 italic mb-4">No expense accounts found</div>
                )}
                <div className="border-t pt-3">
                  <div className="flex justify-between text-lg font-semibold">
                    <span>Total Expenses</span>
                    <span className="text-red-600">{formatCurrency(data.expenses.total)}</span>
                  </div>
                </div>
              </div>

              {/* Net Income Section */}
              <div className="border-t-2 border-gray-300 pt-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-2xl font-bold text-gray-900">Net Income</h2>
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${
                      data.net_income >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatCurrency(data.net_income)}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">
                      {data.net_income >= 0 ? 'Profit' : 'Loss'}
                    </div>
                  </div>
                </div>
                
                {/* Calculation Summary */}
                <div className="mt-6 bg-gray-50 rounded-lg p-4">
                  <h3 className="text-lg font-medium text-gray-900 mb-3">Calculation Summary</h3>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-gray-700">Total Income</span>
                      <span className="font-medium text-green-600">+{formatCurrency(data.income.total)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-700">Total Expenses</span>
                      <span className="font-medium text-red-600">-{formatCurrency(data.expenses.total)}</span>
                    </div>
                    <div className="border-t pt-2">
                      <div className="flex justify-between text-lg font-semibold">
                        <span>Net Income</span>
                        <span className={data.net_income >= 0 ? 'text-green-600' : 'text-red-600'}>
                          {formatCurrency(data.net_income)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Performance Indicator */}
              <div className="mt-6">
                <div className={`border rounded-lg p-4 ${
                  data.net_income >= 0 
                    ? 'border-green-300 bg-green-50' 
                    : 'border-red-300 bg-red-50'
                }`}>
                  <div className="flex items-center">
                    <div className={`flex-shrink-0 ${
                      data.net_income >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {data.net_income >= 0 ? (
                        <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 2a8 8 0 100 16 8 8 0 000-16zm1 11a1 1 0 10-2 0v2a1 1 0 102 0v-2zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V5a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                    <div className="ml-3">
                      <h3 className={`text-sm font-medium ${
                        data.net_income >= 0 ? 'text-green-800' : 'text-red-800'
                      }`}>
                        {data.net_income >= 0 ? 'Profitable Period 📈' : 'Loss Period 📉'}
                      </h3>
                      <div className={`mt-1 text-sm ${
                        data.net_income >= 0 ? 'text-green-700' : 'text-red-700'
                      }`}>
                        {data.net_income >= 0 
                          ? 'Your business generated a profit during this period'
                          : 'Your business had a loss during this period'
                        }
                      </div>
                    </div>
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

export default IncomeStatementPage;