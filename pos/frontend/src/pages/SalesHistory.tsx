import React, { useState, useEffect } from 'react';

interface Sale {
  id: string;
  total_amount: number;
  payment_method: string;
  amount_received: number;
  change_given: number;
  created_at: string;
  items: SaleItem[];
}

interface SaleItem {
  id: string;
  product_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

const SalesHistory: React.FC = () => {
  const [sales, setSales] = useState<Sale[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSale, setSelectedSale] = useState<Sale | null>(null);

  useEffect(() => {
    fetchSales();
  }, []);

  const fetchSales = async () => {
    try {
      const response = await fetch('http://localhost:8001/sales/');
      if (response.ok) {
        const data = await response.json();
        setSales(data);
      }
    } catch (error) {
      console.error('Error fetching sales:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getTodaysSales = () => {
    const today = new Date().toDateString();
    return sales.filter(sale => 
      new Date(sale.created_at).toDateString() === today
    );
  };

  const getTodaysTotal = () => {
    return getTodaysSales().reduce((total, sale) => total + sale.total_amount, 0);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading sales history...</div>
      </div>
    );
  }

  const todaysSales = getTodaysSales();
  const todaysTotal = getTodaysTotal();

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-4">Sales History</h2>
        
        {/* Today's Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-100 rounded-lg p-4">
            <h3 className="font-semibold text-blue-800">Today's Sales</h3>
            <p className="text-2xl font-bold text-blue-600">{todaysSales.length}</p>
          </div>
          <div className="bg-green-100 rounded-lg p-4">
            <h3 className="font-semibold text-green-800">Today's Revenue</h3>
            <p className="text-2xl font-bold text-green-600">${todaysTotal.toFixed(2)}</p>
          </div>
          <div className="bg-purple-100 rounded-lg p-4">
            <h3 className="font-semibold text-purple-800">Total Sales</h3>
            <p className="text-2xl font-bold text-purple-600">{sales.length}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-md overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sale ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date & Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total Amount
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Payment Method
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Items
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sales.map((sale) => (
                <tr key={sale.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    #{sale.id.slice(-8)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatDate(sale.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                    ${sale.total_amount.toFixed(2)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                      sale.payment_method === 'cash' 
                        ? 'bg-green-100 text-green-800'
                        : sale.payment_method === 'card'
                        ? 'bg-blue-100 text-blue-800'
                        : 'bg-purple-100 text-purple-800'
                    }`}>
                      {sale.payment_method.charAt(0).toUpperCase() + sale.payment_method.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {sale.items?.length || 0} items
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => setSelectedSale(sale)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {sales.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No sales found.
          </div>
        )}
      </div>

      {/* Sale Details Modal */}
      {selectedSale && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full max-h-96 overflow-y-auto m-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold">Sale Details</h3>
              <button
                onClick={() => setSelectedSale(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-sm text-gray-600">Sale ID</p>
                <p className="font-medium">#{selectedSale.id}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Date & Time</p>
                <p className="font-medium">{formatDate(selectedSale.created_at)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Payment Method</p>
                <p className="font-medium">{selectedSale.payment_method}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Amount Received</p>
                <p className="font-medium">${selectedSale.amount_received.toFixed(2)}</p>
              </div>
            </div>

            <div className="mb-4">
              <h4 className="font-semibold mb-2">Items</h4>
              <div className="space-y-2">
                {selectedSale.items?.map((item) => (
                  <div key={item.id} className="flex justify-between items-center bg-gray-50 p-2 rounded">
                    <div>
                      <p className="font-medium">{item.product_name}</p>
                      <p className="text-sm text-gray-600">
                        ${item.unit_price.toFixed(2)} × {item.quantity}
                      </p>
                    </div>
                    <p className="font-medium">${item.total_price.toFixed(2)}</p>
                  </div>
                )) || (
                  <p className="text-gray-500">No items found</p>
                )}
              </div>
            </div>

            <div className="border-t pt-4">
              <div className="flex justify-between items-center">
                <span className="text-lg font-semibold">Total:</span>
                <span className="text-xl font-bold text-green-600">
                  ${selectedSale.total_amount.toFixed(2)}
                </span>
              </div>
              {selectedSale.payment_method === 'cash' && selectedSale.change_given > 0 && (
                <div className="flex justify-between items-center mt-2">
                  <span className="text-sm text-gray-600">Change Given:</span>
                  <span className="text-sm font-medium">
                    ${selectedSale.change_given.toFixed(2)}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default SalesHistory;