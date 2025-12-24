import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';

interface GeneralLedgerEntry {
  transaction_id: number;
  date: string;
  description: string;
  reference?: string;
  type: 'debit' | 'credit';
  amount: number;
  running_balance: number;
}

interface GeneralLedgerAccount {
  account_id: number;
  account_name: string;
  account_code: string;
  transactions: GeneralLedgerEntry[];
  running_balance: number;
  transaction_count: number;
}

interface GeneralLedgerData {
  report_type: string;
  period: {
    start_date: string;
    end_date: string;
  };
  account_filter?: number;
  accounts: GeneralLedgerAccount[];
  summary: string;
}

const GeneralLedgerPage: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<GeneralLedgerData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [accountId, setAccountId] = useState('');
  const [availableAccounts, setAvailableAccounts] = useState<Array<{id: number, name: string, code: string}>>([]);

  const fetchAccounts = async () => {
    if (!token) return;
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/accounts/', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const accounts = await response.json();
        setAvailableAccounts(accounts);
      }
    } catch (err) {
      console.error('Failed to fetch accounts:', err);
    }
  };

  const fetchGeneralLedger = async () => {
    if (!token) {
      setError('Authentication required. Please log in again.');
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const url = new URL('http://localhost:8000/api/v1/reports/general-ledger');
      
      if (accountId) {
        url.searchParams.append('account_id', accountId);
      }
      if (startDate) {
        url.searchParams.append('start_date', startDate);
      }
      if (endDate) {
        url.searchParams.append('end_date', endDate);
      }

      const response = await fetch(url.toString(), {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch general ledger: ${response.statusText}`);
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
      fetchAccounts();
      fetchGeneralLedger();
    }
  }, [token]);

  const handleFilterChange = () => {
    fetchGeneralLedger();
  };

  const formatCurrency = (amount: number | null | undefined) => {
    const validAmount = typeof amount === 'number' && !isNaN(amount) ? amount : 0;
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(validAmount);
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      if (isNaN(date.getTime())) return 'Invalid Date';
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return 'Invalid Date';
    }
  };

  if (loading) {
    return (
      <Layout currentPage="reports">
        <div className="p-8">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading General Ledger...</p>
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
                <h3 className="text-sm font-medium text-red-800">Error Loading General Ledger</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
                <div className="mt-4">
                  <button
                    onClick={fetchGeneralLedger}
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
          <h1 className="text-3xl font-bold text-gray-900 mb-4">📚 General Ledger</h1>
          
          {/* Filters */}
          <div className="bg-white shadow-md rounded-lg p-6 mb-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">Filters</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label htmlFor="account-select" className="block text-sm font-medium text-gray-700 mb-2">
                  Account (Optional)
                </label>
                <select
                  id="account-select"
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">All Accounts</option>
                  {availableAccounts.map((account) => (
                    <option key={account.id} value={account.id}>
                      {account.code} - {account.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="start-date" className="block text-sm font-medium text-gray-700 mb-2">
                  Start Date (Optional)
                </label>
                <input
                  type="date"
                  id="start-date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label htmlFor="end-date" className="block text-sm font-medium text-gray-700 mb-2">
                  End Date (Optional)
                </label>
                <input
                  type="date"
                  id="end-date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleFilterChange}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                >
                  Apply Filters
                </button>
              </div>
            </div>
          </div>

          {data && (
            <div className="text-sm text-gray-600 mb-4">
              {data.period?.start_date && data.period?.end_date && (
                <span>Period: {formatDate(data.period.start_date)} to {formatDate(data.period.end_date)} | </span>
              )}
              {data.account_filter && (
                <span>Account Filter: {availableAccounts.find(acc => acc.id === data.account_filter)?.name || 'Unknown'} | </span>
              )}
              Showing {data.accounts.length} account(s)
            </div>
          )}
        </div>

        {data && (
          <div className="space-y-8">
            {data.accounts.length === 0 ? (
              <div className="bg-white shadow-md rounded-lg p-8">
                <div className="text-center text-gray-500">
                  <div className="text-4xl mb-4">📭</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Found</h3>
                  <p>No ledger entries found for the selected criteria. Try adjusting your filters.</p>
                </div>
              </div>
            ) : (
              data.accounts.map((account) => (
                <div key={account.account_id} className="bg-white shadow-md rounded-lg overflow-hidden">
                  <div className="bg-blue-50 px-6 py-4 border-b border-gray-200">
                    <div className="flex justify-between items-center">
                      <div>
                        <h2 className="text-xl font-semibold text-gray-900">
                          {account.account_name || 'Unknown Account'} ({account.account_code || 'N/A'})
                        </h2>
                        <p className="text-sm text-gray-600">
                          {account.transaction_count} transaction(s)
                        </p>
                      </div>
                      <div className="text-right">
                        <div className="text-sm text-gray-600">Ending Balance</div>
                        <div className="text-lg font-semibold">
                          {formatCurrency(account.running_balance || 0)}
                        </div>
                      </div>
                    </div>
                  </div>

                  {(!account.transactions || account.transactions.length === 0) ? (
                    <div className="p-6 text-center text-gray-500">
                      No transactions found for this account
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Date
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Description
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Debit
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Credit
                            </th>
                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Balance
                            </th>
                            <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                              Txn ID
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {account.transactions?.map((entry, index) => (
                            <tr key={`${entry.transaction_id}-${index}`} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {formatDate(entry.date || '')}
                              </td>
                              <td className="px-6 py-4 text-sm text-gray-900">
                                {entry.description || 'No description'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                                {entry.type === 'debit' ? (
                                  <span className="text-green-600 font-medium">
                                    {formatCurrency(entry.amount || 0)}
                                  </span>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                                {entry.type === 'credit' ? (
                                  <span className="text-red-600 font-medium">
                                    {formatCurrency(entry.amount || 0)}
                                  </span>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium">
                                {formatCurrency(entry.running_balance || 0)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-center text-gray-500">
                                #{entry.transaction_id || 'N/A'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700">
                        Ending Balance:
                      </span>
                      <span className="text-lg font-semibold">
                        {formatCurrency(account.running_balance || 0)}
                      </span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};

export default GeneralLedgerPage;