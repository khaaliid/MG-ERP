import React, { useState, useEffect } from 'react';

interface Product {
  id: string;
  name: string;
  price: number;
  stock_quantity: number;
  barcode?: string;
  category: string;
  taxRate?: number;
}

interface CartItem {
  product: Product;
  quantity: number;
  discount?: number;
  note?: string;
}

interface Customer {
  id?: string;
  name: string;
  email?: string;
  phone?: string;
  loyaltyNumber?: string;
  discountPercent?: number;
}

interface CheckoutFormProps {
  cartItems: CartItem[];
  subtotal: number;
  totalTax: number;
  total: number;
  customer?: Customer;
  onSaleComplete: (saleData: any) => void;
  onCancel: () => void;
  onCustomerSelect?: (customer: Customer | null) => void;
}

const CheckoutForm: React.FC<CheckoutFormProps> = ({
  cartItems,
  subtotal,
  totalTax,
  total,
  customer,
  onSaleComplete,
  onCancel,
  onCustomerSelect
}) => {
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [amountReceived, setAmountReceived] = useState<number>(total);
  const [cardNumber, setCardNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [customerSearch, setCustomerSearch] = useState('');
  const [receiptEmail, setReceiptEmail] = useState('');
  const [notes, setNotes] = useState('');
  const [splitPayment, setSplitPayment] = useState(false);
  const [splitAmounts, setSplitAmounts] = useState({ cash: 0, card: 0 });

  const change = amountReceived - total;

  // Auto-set amount received when payment method changes
  useEffect(() => {
    if (paymentMethod !== 'cash' && !splitPayment) {
      setAmountReceived(total);
    }
  }, [paymentMethod, total, splitPayment]);

  // Quick cash amount buttons
  const quickAmounts = [
    Math.ceil(total),
    Math.ceil(total / 5) * 5,
    Math.ceil(total / 10) * 10,
    Math.ceil(total / 20) * 20
  ].filter((amount, index, arr) => arr.indexOf(amount) === index && amount >= total);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  const paymentMethods = [
    {
      value: 'cash',
      label: 'Cash Payment',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      description: 'Physical cash payment'
    },
    {
      value: 'card',
      label: 'Card Payment',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
      ),
      description: 'Credit/Debit card'
    },
    {
      value: 'mobile',
      label: 'Mobile Payment',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      ),
      description: 'Mobile wallet or app'
    },
    {
      value: 'split',
      label: 'Split Payment',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
      ),
      description: 'Multiple payment methods'
    }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (paymentMethod === 'cash' && amountReceived < total) {
      alert('Amount received cannot be less than total');
      return;
    }

    if (splitPayment && (splitAmounts.cash + splitAmounts.card !== total)) {
      alert('Split payment amounts must equal the total');
      return;
    }

    setLoading(true);

    try {
      const saleData = {
        items: cartItems.map(item => ({
          product_id: item.product.id,
          quantity: item.quantity,
          unit_price: item.product.price,
          discount: item.discount || 0,
          note: item.note || '',
          tax_rate: item.product.taxRate || 0
        })),
        payment_method: splitPayment ? 'split' : paymentMethod,
        payment_details: splitPayment ? splitAmounts : {
          amount_received: paymentMethod === 'cash' ? amountReceived : total,
          card_number: paymentMethod === 'card' ? cardNumber.slice(-4) : null
        },
        customer_id: customer?.id || null,
        subtotal: subtotal,
        total_tax: totalTax,
        total_amount: total,
        receipt_email: receiptEmail || customer?.email || null,
        notes: notes,
        transaction_timestamp: new Date().toISOString()
      };

      // Simulate API call with realistic delay
      await new Promise(resolve => setTimeout(resolve, 2000));

      const mockResponse = {
        id: 'TXN-' + Math.random().toString(36).substr(2, 9).toUpperCase(),
        receipt_number: 'RCP-' + Date.now(),
        timestamp: new Date().toISOString(),
        change: paymentMethod === 'cash' ? change : 0,
        ...saleData
      };

      onSaleComplete(mockResponse);
    } catch (error) {
      console.error('Error completing sale:', error);
      alert('Error completing sale. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card h-full flex flex-col">
      {/* Checkout Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-green-50 to-emerald-50">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <div>
            <h3 className="heading-5">Checkout</h3>
            <p className="text-caption">Complete your transaction</p>
          </div>
        </div>
        
        <div className="text-right">
          <div className="text-heading-6 font-bold text-green-600">
            {formatPrice(total)}
          </div>
          <div className="text-caption">
            {cartItems.reduce((sum, item) => sum + item.quantity, 0)} items
          </div>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Customer Section */}
          <div className="card-nested">
            <div className="flex items-center justify-between mb-4">
              <h4 className="heading-6">Customer</h4>
              {onCustomerSelect && (
                <button
                  type="button"
                  onClick={() => setShowCustomerModal(true)}
                  className="btn btn-ghost btn-sm"
                >
                  {customer ? 'Change' : 'Add Customer'}
                </button>
              )}
            </div>
            
            {customer ? (
              <div className="bg-blue-50 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-gray-900">{customer.name}</div>
                    {customer.email && (
                      <div className="text-caption text-gray-600">{customer.email}</div>
                    )}
                    {customer.loyaltyNumber && (
                      <div className="text-caption text-blue-600">
                        Loyalty: {customer.loyaltyNumber}
                      </div>
                    )}
                  </div>
                  {customer.discountPercent && customer.discountPercent > 0 && (
                    <div className="badge badge-success">
                      {customer.discountPercent}% Off
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                <svg className="w-8 h-8 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <p className="text-caption">No customer selected</p>
              </div>
            )}
          </div>

          {/* Payment Method */}
          <div>
            <label className="label mb-3">Payment Method</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {paymentMethods.map(method => (
                <button
                  key={method.value}
                  type="button"
                  onClick={() => {
                    setPaymentMethod(method.value);
                    setSplitPayment(method.value === 'split');
                  }}
                  className={`p-4 rounded-lg border-2 transition-all text-left ${
                    paymentMethod === method.value
                      ? 'border-green-500 bg-green-50 ring-2 ring-green-200'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className={`${paymentMethod === method.value ? 'text-green-600' : 'text-gray-400'}`}>
                      {method.icon}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-gray-800">{method.label}</div>
                      <div className="text-caption text-gray-500">{method.description}</div>
                    </div>
                    {paymentMethod === method.value && (
                      <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Cash Payment Details */}
          {paymentMethod === 'cash' && !splitPayment && (
            <div className="card-nested">
              <label className="label mb-3">Amount Received</label>
              
              {/* Quick Amount Buttons */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
                {quickAmounts.map(amount => (
                  <button
                    key={amount}
                    type="button"
                    onClick={() => setAmountReceived(amount)}
                    className="btn btn-outline btn-sm"
                  >
                    {formatPrice(amount)}
                  </button>
                ))}
              </div>

              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 font-semibold">$</span>
                <input
                  type="number"
                  step="0.01"
                  min={total}
                  value={amountReceived}
                  onChange={(e) => setAmountReceived(parseFloat(e.target.value) || 0)}
                  className="input w-full pl-8 text-heading-6 font-bold"
                  required
                />
              </div>
              
              <div className="mt-4 p-3 bg-gray-50 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="text-body">Change:</span>
                  <span className={`text-heading-6 font-bold ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {formatPrice(Math.abs(change))}
                    {change < 0 && ' (Insufficient)'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Card Payment Details */}
          {paymentMethod === 'card' && !splitPayment && (
            <div className="card-nested">
              <label className="label mb-3">Card Information</label>
              <input
                type="text"
                placeholder="Card number (last 4 digits for reference)"
                value={cardNumber}
                onChange={(e) => setCardNumber(e.target.value)}
                className="input w-full"
                maxLength={4}
              />
              <p className="text-caption text-gray-500 mt-2">
                Complete payment using card terminal or reader
              </p>
            </div>
          )}

          {/* Split Payment Details */}
          {splitPayment && (
            <div className="card-nested">
              <label className="label mb-3">Split Payment Amounts</label>
              <div className="space-y-3">
                <div>
                  <label className="label label-sm">Cash Amount</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max={total}
                      value={splitAmounts.cash}
                      onChange={(e) => {
                        const cashAmount = parseFloat(e.target.value) || 0;
                        setSplitAmounts({
                          cash: cashAmount,
                          card: total - cashAmount
                        });
                      }}
                      className="input w-full pl-8"
                    />
                  </div>
                </div>
                <div>
                  <label className="label label-sm">Card Amount</label>
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                    <input
                      type="number"
                      step="0.01"
                      min="0"
                      max={total}
                      value={splitAmounts.card}
                      onChange={(e) => {
                        const cardAmount = parseFloat(e.target.value) || 0;
                        setSplitAmounts({
                          card: cardAmount,
                          cash: total - cardAmount
                        });
                      }}
                      className="input w-full pl-8"
                    />
                  </div>
                </div>
                <div className="text-center text-caption">
                  Total: {formatPrice(splitAmounts.cash + splitAmounts.card)} / {formatPrice(total)}
                </div>
              </div>
            </div>
          )}

          {/* Additional Details */}
          <div className="card-nested">
            <label className="label mb-3">Additional Details</label>
            <div className="space-y-3">
              <div>
                <label className="label label-sm">Receipt Email (Optional)</label>
                <input
                  type="email"
                  placeholder="Enter email for receipt"
                  value={receiptEmail}
                  onChange={(e) => setReceiptEmail(e.target.value)}
                  className="input w-full"
                />
              </div>
              <div>
                <label className="label label-sm">Transaction Notes (Optional)</label>
                <textarea
                  placeholder="Add any notes about this transaction..."
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  className="input w-full"
                  rows={2}
                />
              </div>
            </div>
          </div>

          {/* Order Summary */}
          <div className="card-nested">
            <h4 className="heading-6 mb-3">Order Summary</h4>
            <div className="space-y-2 max-h-32 overflow-y-auto">
              {cartItems.map((item) => (
                <div key={item.product.id} className="flex justify-between items-center py-1">
                  <div className="flex-1 min-w-0">
                    <span className="text-body-sm font-medium truncate">{item.product.name}</span>
                    <span className="text-caption text-gray-500 ml-2">×{item.quantity}</span>
                  </div>
                  <span className="text-body-sm font-semibold">
                    {formatPrice(item.product.price * item.quantity)}
                  </span>
                </div>
              ))}
            </div>
            
            <div className="border-t border-gray-200 mt-3 pt-3 space-y-1">
              <div className="flex justify-between text-body">
                <span>Subtotal:</span>
                <span>{formatPrice(subtotal)}</span>
              </div>
              {totalTax > 0 && (
                <div className="flex justify-between text-body">
                  <span>Tax:</span>
                  <span>{formatPrice(totalTax)}</span>
                </div>
              )}
              <div className="flex justify-between items-center pt-2 border-t">
                <span className="text-heading-6 font-bold">Total:</span>
                <span className="text-heading-5 font-bold text-green-600">
                  {formatPrice(total)}
                </span>
              </div>
            </div>
          </div>
        </form>
      </div>

      {/* Action Buttons */}
      <div className="border-t border-gray-200 p-4 bg-gray-50">
        <div className="flex space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="btn btn-ghost flex-1"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span>Cancel</span>
          </button>
          <button
            type="submit"
            onClick={handleSubmit}
            disabled={loading || (paymentMethod === 'cash' && change < 0) || (splitPayment && splitAmounts.cash + splitAmounts.card !== total)}
            className="btn btn-success flex-1 animate-pulse-on-hover"
          >
            {loading ? (
              <div className="flex items-center space-x-2">
                <div className="loading-spinner"></div>
                <span>Processing...</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span>Complete Sale</span>
                <span className="text-sm opacity-90">
                  {formatPrice(total)}
                </span>
              </div>
            )}
          </button>
        </div>
      </div>

      {/* Customer Modal */}
      {showCustomerModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card w-96 max-h-96">
            <div className="flex items-center justify-between mb-4">
              <h3 className="heading-6">Select Customer</h3>
              <button
                onClick={() => setShowCustomerModal(false)}
                className="btn btn-ghost btn-sm"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Search customers..."
                value={customerSearch}
                onChange={(e) => setCustomerSearch(e.target.value)}
                className="input w-full"
                autoFocus
              />
              
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {/* Mock customer list */}
                {[
                  { id: '1', name: 'John Doe', email: 'john@example.com', loyaltyNumber: 'LOY001', discountPercent: 10 },
                  { id: '2', name: 'Jane Smith', email: 'jane@example.com', loyaltyNumber: 'LOY002', discountPercent: 5 },
                  { id: '3', name: 'Bob Johnson', email: 'bob@example.com' }
                ].filter(c => c.name.toLowerCase().includes(customerSearch.toLowerCase())).map(customer => (
                  <button
                    key={customer.id}
                    onClick={() => {
                      onCustomerSelect?.(customer);
                      setShowCustomerModal(false);
                      setReceiptEmail(customer.email || '');
                    }}
                    className="w-full text-left p-3 rounded-lg border border-gray-200 hover:bg-gray-50"
                  >
                    <div className="font-medium">{customer.name}</div>
                    {customer.email && (
                      <div className="text-caption text-gray-600">{customer.email}</div>
                    )}
                    {customer.loyaltyNumber && (
                      <div className="text-caption text-blue-600">
                        Loyalty: {customer.loyaltyNumber}
                        {customer.discountPercent && ` • ${customer.discountPercent}% Discount`}
                      </div>
                    )}
                  </button>
                ))}
              </div>
              
              <div className="flex space-x-2 pt-2 border-t">
                <button
                  onClick={() => {
                    onCustomerSelect?.(null);
                    setShowCustomerModal(false);
                    setReceiptEmail('');
                  }}
                  className="btn btn-ghost flex-1"
                >
                  No Customer
                </button>
                <button
                  onClick={() => setShowCustomerModal(false)}
                  className="btn btn-primary flex-1"
                >
                  Add New Customer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CheckoutForm;