import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';

// Remove unused interface
interface CashFlowData {
  report_type: string;
  period: {
    start_date: string;
    end_date: string;
  };
  cash_flows: any[];
  summary: {
    total_inflows: number;
    total_outflows: number;
    net_cash_flow: number;
  };
}

const CashFlowPage: React.FC = () => {
  const { token } = useAuth();
  const [data, setData] = useState<CashFlowData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState(() => {
    const currentYear = new Date().getFullYear();
    return `${currentYear}-01-01`;
  });
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);

  const fetchCashFlow = async (start?: string, end?: string) => {
    if (!token) {
      setError('Authentication required. Please log in again.');
      setLoading(false);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const url = new URL('http://localhost:8000/api/v1/reports/cash-flow');
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
        throw new Error(`Failed to fetch cash flow statement: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('Cash Flow API Response:', result);
      
      // Check if the backend returned an error (e.g., no cash accounts)
      if (result.error) {
        setError(result.error);
        setLoading(false);
        return;
      }
      
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchCashFlow();
    }
  }, [token]);

  const handleDateRangeChange = () => {
    fetchCashFlow(startDate, endDate);
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
      const d = new Date(dateString);
      if (isNaN(d.getTime())) return 'Invalid Date';
      return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
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
              <p className="text-gray-600">Loading Cash Flow Statement...</p>
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
                <h3 className="text-sm font-medium text-red-800">Error Loading Cash Flow Statement</h3>
                <div className="mt-2 text-sm text-red-700">{error}</div>
                <div className="mt-4">
                  <button
                    onClick={() => fetchCashFlow(startDate, endDate)}
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

  if (!data || !data.summary) {
    return (
      <Layout currentPage="reports">
        <div className="p-8">
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Invalid Data</h3>
                <div className="mt-2 text-sm text-yellow-700">
                  The cash flow data is incomplete or malformed. 
                  {data ? 'Missing summary data.' : 'No data received.'}
                </div>
                <div className="mt-4">
                  <button
                    onClick={() => fetchCashFlow(startDate, endDate)}
                    className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                  >
                    Reload
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
            <h1 className="text-3xl font-bold text-gray-900">💵 Cash Flow Statement</h1>
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
              For the period from {formatDate(data.period.start_date)} to {formatDate(data.period.end_date)}
            </p>
          )}
        </div>

        {data && (
          <div className="bg-white shadow-md rounded-lg overflow-hidden">
            <div className="p-6">
              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="text-green-600">
                      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-green-800">Cash Inflows</p>
                      <p className="text-2xl font-bold text-green-900">
                        {formatCurrency(data.summary.total_inflows)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-center">
                    <div className="text-red-600">
                      <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-red-800">Cash Outflows</p>
                      <p className="text-2xl font-bold text-red-900">
                        {formatCurrency(data.summary.total_outflows)}
                      </p>
                    </div>
                  </div>
                </div>

                <div className={`border rounded-lg p-4 ${
                  data.summary.net_cash_flow >= 0 
                    ? 'bg-blue-50 border-blue-200' 
                    : 'bg-orange-50 border-orange-200'
                }`}>
                  <div className="flex items-center">
                    <div className={data.summary.net_cash_flow >= 0 ? 'text-blue-600' : 'text-orange-600'}>
                      {data.summary.net_cash_flow >= 0 ? (
                        <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                        </svg>
                      ) : (
                        <svg className="h-8 w-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                        </svg>
                      )}
                    </div>
                    <div className="ml-3">
                      <p className={`text-sm font-medium ${
                        data.summary.net_cash_flow >= 0 ? 'text-blue-800' : 'text-orange-800'
                      }`}>
                        Net Cash Flow
                      </p>
                      <p className={`text-2xl font-bold ${
                        data.summary.net_cash_flow >= 0 ? 'text-blue-900' : 'text-orange-900'
                      }`}>
                        {formatCurrency(data.summary.net_cash_flow)}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Detailed Cash Movements */}
              {data.cash_flows.length > 0 ? (
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Cash Movements</h2>
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
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Account
                          </th>
                          <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Type
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Inflow
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Outflow
                          </th>
                          <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Net
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {data.cash_flows.map((flow, idx) => {
                          const isInflow = flow.type === 'Inflow';
                          const inflowAmt = isInflow ? flow.amount : 0;
                          const outflowAmt = !isInflow ? flow.amount : 0;
                          const netAmt = isInflow ? flow.amount : -flow.amount;
                          return (
                            <tr key={`${flow.date}-${idx}`} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {formatDate(flow.date)}
                              </td>
                              <td className="px-6 py-4 text-sm text-gray-900">
                                {flow.description || '—'}
                              </td>
                              <td className="px-6 py-4 text-sm text-gray-700">
                                {flow.account}
                              </td>
                              <td className="px-6 py-4 text-center text-sm">
                                <span className={`px-2 py-1 rounded ${isInflow ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>{flow.type}</span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                                {inflowAmt ? (
                                  <span className="text-green-600 font-medium">{formatCurrency(inflowAmt)}</span>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                                {outflowAmt ? (
                                  <span className="text-red-600 font-medium">{formatCurrency(outflowAmt)}</span>
                                ) : (
                                  <span className="text-gray-400">-</span>
                                )}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                                <span className={`font-medium ${netAmt >= 0 ? 'text-blue-600' : 'text-orange-600'}`}>{formatCurrency(netAmt)}</span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                      <tfoot className="bg-gray-50">
                        <tr className="font-semibold">
                          <td className="px-6 py-4 text-sm text-gray-900" colSpan={4}>
                            Total
                          </td>
                          <td className="px-6 py-4 text-sm text-right text-green-600">
                            {formatCurrency(data.summary.total_inflows)}
                          </td>
                          <td className="px-6 py-4 text-sm text-right text-red-600">
                            {formatCurrency(data.summary.total_outflows)}
                          </td>
                          <td className={`px-6 py-4 text-sm text-right ${
                            data.summary.net_cash_flow >= 0 ? 'text-blue-600' : 'text-orange-600'
                          }`}>
                            {formatCurrency(data.summary.net_cash_flow)}
                          </td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-gray-500">
                    <div className="text-4xl mb-4">💧</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Cash Flow Data</h3>
                    <p>No cash movements found for the selected period.</p>
                  </div>
                </div>
              )}

              {/* Analysis Section */}
              <div className="mt-8 bg-gray-50 rounded-lg p-6">
                <h3 className="text-lg font-medium text-gray-900 mb-4">Cash Flow Analysis</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Period Summary</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Inflows:</span>
                        <span className="font-medium text-green-600">
                          +{formatCurrency(data.summary.total_inflows)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Outflows:</span>
                        <span className="font-medium text-red-600">
                          -{formatCurrency(data.summary.total_outflows)}
                        </span>
                      </div>
                      <div className="border-t pt-2">
                        <div className="flex justify-between font-semibold">
                          <span>Net Cash Flow:</span>
                          <span className={data.summary.net_cash_flow >= 0 ? 'text-blue-600' : 'text-orange-600'}>
                            {formatCurrency(data.summary.net_cash_flow)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Liquidity Assessment</h4>
                    <div className={`p-3 rounded-md ${
                      data.summary.net_cash_flow >= 0 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-orange-100 text-orange-800'
                    }`}>
                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          {data.summary.net_cash_flow >= 0 ? (
                            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          ) : (
                            <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                            </svg>
                          )}
                        </div>
                        <div className="ml-2">
                          <div className="text-sm font-medium">
                            {data.summary.net_cash_flow >= 0 
                              ? 'Positive Cash Flow 📈' 
                              : 'Negative Cash Flow 📉'
                            }
                          </div>
                          <div className="text-xs">
                            {data.summary.net_cash_flow >= 0 
                              ? 'Cash position improved during this period' 
                              : 'Cash position declined during this period'
                            }
                          </div>
                        </div>
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

export default CashFlowPage;