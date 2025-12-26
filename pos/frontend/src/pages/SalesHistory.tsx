/**
 * Sales History Page Component
 * Displays sales transactions with authentication and role-based access
 */

import React, { useState, useEffect } from 'react';
import { enhancedApiService, Sale } from '../services/enhancedApiService';
import { useAuth } from '../contexts/AuthContext';
import { printReceipt } from '../utils/receiptPrinter';

function formatEGP(v: number) {
  return `${v.toFixed(2)} EGP`;
}

function formatCurrency(v: number, currencyCode: string) {
  const value = typeof v === 'number' && !isNaN(v) ? v : 0;
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: currencyCode || 'USD' }).format(value);
  } catch {
    return `${value.toFixed(2)} ${currencyCode || 'USD'}`;
  }
}

const SalesHistory: React.FC = () => {
  const { user } = useAuth();
  const [sales, setSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [selectedSale, setSelectedSale] = useState<Sale | null>(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  // POS Settings for receipt printing
  const [currencyCode, setCurrencyCode] = useState('USD');
  const [currencySymbol, setCurrencySymbol] = useState('$');
  const [receiptHeader, setReceiptHeader] = useState<string>('');
  const [receiptFooter, setReceiptFooter] = useState<string>('');
  const [businessName, setBusinessName] = useState<string>('');
  const [businessAddress, setBusinessAddress] = useState<string>('');
  const [businessPhone, setBusinessPhone] = useState<string>('');
  const [businessEmail, setBusinessEmail] = useState<string>('');

  useEffect(() => {
    fetchSales();
    fetchSettings();
  }, [page, startDate, endDate]);

  const fetchSettings = async () => {
    try {
      const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || '';
      const token = localStorage.getItem('pos_auth_token') || '';
      
      const settingsResponse = await fetch(`${apiBase}/settings/`, {
        headers: {
          'Authorization': token ? `Bearer ${token}` : '',
          'Accept': 'application/json'
        }
      }).catch(() => null);

      if (settingsResponse?.ok) {
        const s = await settingsResponse.json();
        if (typeof s.currency_code === 'string') {
          setCurrencyCode(s.currency_code);
        }
        if (typeof s.currency_symbol === 'string') {
          setCurrencySymbol(s.currency_symbol);
        }
        if (typeof s.receipt_header === 'string') {
          setReceiptHeader(s.receipt_header);
        }
        if (typeof s.receipt_footer === 'string') {
          setReceiptFooter(s.receipt_footer);
        }
        if (typeof s.business_name === 'string') {
          setBusinessName(s.business_name);
        }
        if (typeof s.business_address === 'string') {
          setBusinessAddress(s.business_address);
        }
        if (typeof s.business_phone === 'string') {
          setBusinessPhone(s.business_phone);
        }
        if (typeof s.business_email === 'string') {
          setBusinessEmail(s.business_email);
        }
      }
    } catch (err) {
      console.error('Failed to load settings for receipt:', err);
    }
  };

  const fetchSales = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await enhancedApiService.getSales(page, 20, startDate, endDate);
      setSales(response.data);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sales');
    } finally {
      setLoading(false);
    }
  };

  const handleViewSale = (sale: Sale) => {
    setSelectedSale(sale);
  };

  const handleVoidSale = async (saleId: string, reason: string) => {
    if (!user || (user.role !== 'manager' && user.role !== 'admin')) {
      alert('Only managers and admins can void sales');
      return;
    }

    try {
      await enhancedApiService.voidSale(saleId, reason);
      fetchSales(); // Refresh the list
      setSelectedSale(null);
      alert('Sale voided successfully');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to void sale');
    }
  };

  const handleRefundSale = async (saleId: string, refundAmount: number, reason: string) => {
    if (!user || (user.role !== 'manager' && user.role !== 'admin')) {
      alert('Only managers and admins can process refunds');
      return;
    }

    try {
      await enhancedApiService.refundSale(saleId, refundAmount, reason);
      fetchSales(); // Refresh the list
      setSelectedSale(null);
      alert('Refund processed successfully');
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to process refund');
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const formatPaymentMethod = (method: string | undefined | null) => {
    if (!method) return '💵 Cash';
    switch (method.toLowerCase()) {
      case 'cash':
        return '💵 Cash';
      case 'card':
        return '💳 Card';
      case 'wallet':
        return '📱 Wallet';
      default:
        return method;
    }
  };

  const handlePrintReceipt = (sale: Sale) => {
    const items = sale.items.map(item => ({
      name: item.product_id,
      qty: item.quantity,
      price: item.unit_price,
      size: item.size || null,
      total: item.quantity * item.unit_price
    }));

    printReceipt(
      {
        saleNumber: sale.sale_number,
        date: new Date(sale.created_at),
        cashier: sale.cashier,
        customerName: sale.customer_name,
        items,
        subtotal: sale.subtotal,
        discount: sale.discount_amount,
        tax: sale.tax_amount,
        total: sale.total_amount,
        paymentMethod: sale.payment_method || 'Cash',
        tenderedAmount: sale.tendered_amount,
        changeAmount: sale.change_amount
      },
      {
        currencyCode,
        currencySymbol,
        receiptHeader,
        receiptFooter,
        businessName,
        businessAddress,
        businessPhone,
        businessEmail
      }
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="bg-red-50 border border-red-200 rounded-md p-6 max-w-md w-full mx-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error Loading Sales</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
              <div className="mt-4">
                <button
                  onClick={fetchSales}
                  className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm transition-colors"
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="bg-white shadow rounded-lg">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Sales History</h1>
              <p className="mt-1 text-sm text-gray-500">
                View and manage sales transactions
              </p>
            </div>
            <div className="mt-4 sm:mt-0 flex space-x-3">
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Start Date"
              />
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="End Date"
              />
              <button
                onClick={() => {
                  setStartDate('');
                  setEndDate('');
                  setPage(1);
                }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm hover:bg-gray-200 transition-colors"
              >
                Clear
              </button>
            </div>
          </div>
        </div>

        {/* Sales List */}
        <div className="divide-y divide-gray-200">
          {sales.length === 0 ? (
            <div className="px-6 py-12 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No sales found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {startDate || endDate ? 'Try adjusting your date filters.' : 'No sales have been recorded yet.'}
              </p>
            </div>
          ) : (
            sales.map((sale) => (
              <div key={sale.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                        </div>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          Sale #{sale.sale_number}
                        </p>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span>{formatDate(sale.created_at)}</span>
                          <span>{formatPaymentMethod(sale.payment_method)}</span>
                          {sale.customer_name && (
                            <span>Customer: {sale.customer_name}</span>
                          )}
                          {sale.cashier && (
                            <span>Cashier: {sale.cashier}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="text-lg font-semibold text-gray-900">
                        {formatEGP(sale.total_amount)}
                      </p>
                      <p className="text-sm text-gray-500">
                        {sale.items.length} item{sale.items.length !== 1 ? 's' : ''}
                      </p>
                    </div>
                    <button
                      onClick={() => handleViewSale(sale)}
                      className="bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-1 rounded text-sm transition-colors"
                    >
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {total > 20 && (
          <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page * 20 >= total}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Showing <span className="font-medium">{(page - 1) * 20 + 1}</span> to{' '}
                  <span className="font-medium">{Math.min(page * 20, total)}</span> of{' '}
                  <span className="font-medium">{total}</span> results
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <button
                    onClick={() => setPage(page + 1)}
                    disabled={page * 20 >= total}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sale Detail Modal */}
      {selectedSale && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-2xl shadow-lg rounded-md bg-white">
            <div className="mt-3">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Sale Details - #{selectedSale.sale_number}
                </h3>
                <button
                  onClick={() => setSelectedSale(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-6">
                <div>
                  <p className="text-sm font-medium text-gray-500">Date & Time</p>
                  <p className="text-sm text-gray-900">{formatDate(selectedSale.created_at)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Payment Method</p>
                  <p className="text-sm text-gray-900">{formatPaymentMethod(selectedSale.payment_method)}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Customer</p>
                  <p className="text-sm text-gray-900">{selectedSale.customer_name || 'Walk-in'}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Cashier</p>
                  <p className="text-sm text-gray-900">{selectedSale.cashier || 'Unknown'}</p>
                </div>
              </div>

              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Items</h4>
                <div className="bg-gray-50 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Product
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Qty
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Price
                        </th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Total
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {selectedSale.items.map((item, index) => (
                        <tr key={index}>
                          <td className="px-4 py-2 text-sm text-gray-900">
                            {item.product_id}
                            {item.size && <span className="text-gray-500"> ({item.size})</span>}
                          </td>
                          <td className="px-4 py-2 text-sm text-gray-900">{item.quantity}</td>
                          <td className="px-4 py-2 text-sm text-gray-900">{formatEGP(item.unit_price)}</td>
                          <td className="px-4 py-2 text-sm text-gray-900">{formatEGP(item.quantity * item.unit_price)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="mb-6 bg-gray-50 p-4 rounded-lg">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Subtotal:</span>
                    <span className="text-gray-900">{formatEGP(selectedSale.subtotal)}</span>
                  </div>
                  {selectedSale.discount_amount > 0 && (
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Discount:</span>
                      <span className="text-red-600">-{formatEGP(selectedSale.discount_amount)}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-500">Tax:</span>
                    <span className="text-gray-900">{formatEGP(selectedSale.tax_amount)}</span>
                  </div>
                  <div className="flex justify-between text-lg font-semibold border-t border-gray-200 pt-2">
                    <span className="text-gray-900">Total:</span>
                    <span className="text-gray-900">{formatEGP(selectedSale.total_amount)}</span>
                  </div>
                  {selectedSale.tendered_amount && (
                    <>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Tendered:</span>
                        <span className="text-gray-900">{formatEGP(selectedSale.tendered_amount)}</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-500">Change:</span>
                        <span className="text-gray-900">{formatEGP(selectedSale.change_amount || 0)}</span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setSelectedSale(null)}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
                >
                  Close
                </button>
                <button
                  onClick={() => handlePrintReceipt(selectedSale)}
                  className="px-4 py-2 bg-green-100 text-green-700 rounded-md hover:bg-green-200 transition-colors flex items-center space-x-2"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                  </svg>
                  <span>Print Receipt</span>
                </button>
                {(user?.role === 'manager' || user?.role === 'admin') && (
                  <>
                    <button
                      onClick={() => {
                        const reason = prompt('Please enter a reason for the refund:');
                        if (reason) {
                          const amountStr = prompt('Enter refund amount:', selectedSale.total_amount.toString());
                          if (amountStr) {
                            const amount = parseFloat(amountStr);
                            if (amount > 0 && amount <= selectedSale.total_amount) {
                              handleRefundSale(selectedSale.id, amount, reason);
                            } else {
                              alert('Invalid refund amount');
                            }
                          }
                        }
                      }}
                      className="px-4 py-2 bg-yellow-100 text-yellow-700 rounded-md hover:bg-yellow-200 transition-colors"
                    >
                      Refund
                    </button>
                    <button
                      onClick={() => {
                        const reason = prompt('Please enter a reason for voiding this sale:');
                        if (reason) {
                          handleVoidSale(selectedSale.id, reason);
                        }
                      }}
                      className="px-4 py-2 bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
                    >
                      Void Sale
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SalesHistory;