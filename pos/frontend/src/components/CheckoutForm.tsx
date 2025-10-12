import React, { useState } from 'react';

interface Product {
  id: string;
  name: string;
  price: number;
  stock_quantity: number;
  barcode?: string;
  category: string;
}

interface CartItem {
  product: Product;
  quantity: number;
}

interface CheckoutFormProps {
  cartItems: CartItem[];
  total: number;
  onSaleComplete: () => void;
  onCancel: () => void;
}

const CheckoutForm: React.FC<CheckoutFormProps> = ({
  cartItems,
  total,
  onSaleComplete,
  onCancel,
}) => {
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [amountReceived, setAmountReceived] = useState<number>(total);
  const [loading, setLoading] = useState(false);

  const change = amountReceived - total;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (paymentMethod === 'cash' && amountReceived < total) {
      alert('Amount received cannot be less than total');
      return;
    }

    setLoading(true);

    try {
      const saleData = {
        items: cartItems.map(item => ({
          product_id: item.product.id,
          quantity: item.quantity,
          unit_price: item.product.price
        })),
        payment_method: paymentMethod,
        amount_received: paymentMethod === 'cash' ? amountReceived : total,
        total_amount: total
      };

      const response = await fetch('http://localhost:8001/sales/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(saleData),
      });

      if (response.ok) {
        const result = await response.json();
        alert(`Sale completed successfully! Sale ID: ${result.id}`);
        onSaleComplete();
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail || 'Failed to complete sale'}`);
      }
    } catch (error) {
      console.error('Error completing sale:', error);
      alert('Error completing sale. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-semibold mb-4">Checkout</h3>
      
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Payment Method
          </label>
          <select
            value={paymentMethod}
            onChange={(e) => setPaymentMethod(e.target.value)}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="cash">Cash</option>
            <option value="card">Card</option>
            <option value="mobile">Mobile Payment</option>
          </select>
        </div>

        {paymentMethod === 'cash' && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Amount Received
            </label>
            <input
              type="number"
              step="0.01"
              min={total}
              value={amountReceived}
              onChange={(e) => setAmountReceived(parseFloat(e.target.value) || 0)}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              required
            />
            {change >= 0 && (
              <p className="text-sm text-green-600 mt-1">
                Change: ${change.toFixed(2)}
              </p>
            )}
            {change < 0 && (
              <p className="text-sm text-red-600 mt-1">
                Insufficient amount
              </p>
            )}
          </div>
        )}

        <div className="mb-4 p-3 bg-gray-50 rounded-md">
          <h4 className="font-medium mb-2">Order Summary</h4>
          <div className="space-y-1 text-sm">
            {cartItems.map((item) => (
              <div key={item.product.id} className="flex justify-between">
                <span>{item.product.name} x {item.quantity}</span>
                <span>${(item.product.price * item.quantity).toFixed(2)}</span>
              </div>
            ))}
          </div>
          <div className="border-t mt-2 pt-2 font-medium">
            <div className="flex justify-between">
              <span>Total:</span>
              <span>${total.toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className="flex space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={loading || (paymentMethod === 'cash' && change < 0)}
            className="flex-1 bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Processing...' : 'Complete Sale'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CheckoutForm;