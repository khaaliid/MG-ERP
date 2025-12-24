import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout';

interface TrialBalanceItem {
  account_id: number;
  account_name: string;
  account_code: string;
  account_type: string;
  debit_balance: number;
  credit_balance: number;
}

interface TrialBalanceTotals {
  total_debits: number;
  total_credits: number;
  difference: number;
  balanced: boolean;
}

interface TrialBalanceData {
  accounts: TrialBalanceItem[];
  totals: TrialBalanceTotals;
  as_of_date: string;
  report_type?: string;
  summary?: string;
}

const TrialBalancePage: React.FC = () => {
  const [data, setData] = useState<TrialBalanceData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const { token, logout } = useAuth();

  useEffect(() => {
    fetchTrialBalance();
  }, [token]);

  const fetchTrialBalance = async () => {
    try {
      setIsLoading(true);
      setError('');

      const response = await fetch('http://localhost:8000/api/v1/reports/trial-balance', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 401) {
          logout();
          return;
        }
        throw new Error('Failed to fetch trial balance');
      }

      const trialBalanceData: TrialBalanceData = await response.json();
      setData(trialBalanceData);
    } catch (err) {
      setError('Failed to load trial balance. Please try again.');
      console.error('Error fetching trial balance:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Layout currentPage="reports" currentReport="trial-balance">
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading trial balance...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout currentPage="reports" currentReport="trial-balance">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">📊 Trial Balance</h2>
          <p className="text-gray-600">
            Account balances verification - ensuring total debits equal total credits
          </p>
          {data && (
            <p className="text-sm text-gray-500 mt-2">
              As of: {new Date(data.as_of_date).toLocaleDateString()}
            </p>
          )}
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
            <button
              onClick={fetchTrialBalance}
              className="ml-4 text-red-600 hover:text-red-800 underline"
            >
              Retry
            </button>
          </div>
        )}

        {data && (
          <div className="bg-white rounded-lg shadow overflow-hidden">
            {/* Balance Status */}
            <div className={`px-6 py-4 border-b ${data.totals.balanced ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
              <div className="flex items-center">
                <div className={`h-3 w-3 rounded-full mr-3 ${data.totals.balanced ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className={`font-medium ${data.totals.balanced ? 'text-green-800' : 'text-red-800'}`}>
                  {data.totals.balanced ? '✅ Books are in balance' : '❌ Books are out of balance'}
                </span>
              </div>
            </div>

            {/* Table */}
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Account
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Code
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Debit Balance
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Credit Balance
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {data.accounts.map((account) => (
                    <tr key={account.account_id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{account.account_name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-500">{account.account_code}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                          {account.account_type}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                        {account.debit_balance > 0 ? `$${account.debit_balance.toFixed(2)}` : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                        {account.credit_balance > 0 ? `$${account.credit_balance.toFixed(2)}` : '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="bg-gray-50">
                  <tr className="font-bold">
                    <td colSpan={3} className="px-6 py-4 text-sm text-gray-900">
                      TOTALS
                    </td>
                    <td className="px-6 py-4 text-right text-sm text-gray-900">
                      ${data.totals.total_debits.toFixed(2)}
                    </td>
                    <td className="px-6 py-4 text-right text-sm text-gray-900">
                      ${data.totals.total_credits.toFixed(2)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>
        )}

        {!data && !isLoading && !error && (
          <div className="text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No data available</h3>
            <p className="mt-1 text-sm text-gray-500">No trial balance data found.</p>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default TrialBalancePage;