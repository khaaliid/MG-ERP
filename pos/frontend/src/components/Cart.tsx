import React, { useState, useMemo } from 'react';

interface Product {
  id: string;
  name: string;
  price: number;
  stock_quantity: number;
  barcode?: string;
  category: string;
  taxRate?: number;
  discount?: number;
}

interface CartItem {
  product: Product;
  quantity: number;
  discount?: number;
  note?: string;
}

interface CartProps {
  items: CartItem[];
  onUpdateQuantity: (productId: string, quantity: number) => void;
  onRemoveItem: (productId: string) => void;
  onAddDiscount?: (productId: string, discount: number) => void;
  onAddNote?: (productId: string, note: string) => void;
  onClearCart?: () => void;
  onCheckout: () => void;
  total?: number;
  customerDiscount?: number;
  loyaltyPoints?: number;
  isProcessing?: boolean;
}

const Cart: React.FC<CartProps> = ({ 
  items, 
  onUpdateQuantity, 
  onRemoveItem, 
  onAddDiscount,
  onAddNote,
  onClearCart,
  onCheckout,
  customerDiscount = 0,
  loyaltyPoints = 0,
  isProcessing = false
}) => {
  const [showDiscountModal, setShowDiscountModal] = useState<string | null>(null);
  const [showNoteModal, setShowNoteModal] = useState<string | null>(null);
  const [tempDiscount, setTempDiscount] = useState('');
  const [tempNote, setTempNote] = useState('');

  // Calculate totals
  const calculations = useMemo(() => {
    const subtotal = items.reduce((sum, item) => {
      const itemPrice = item.product.price * item.quantity;
      const itemDiscount = (item.discount || 0) * itemPrice / 100;
      return sum + itemPrice - itemDiscount;
    }, 0);

    const totalTax = items.reduce((sum, item) => {
      const itemPrice = item.product.price * item.quantity;
      const itemDiscount = (item.discount || 0) * itemPrice / 100;
      const taxableAmount = itemPrice - itemDiscount;
      return sum + (taxableAmount * (item.product.taxRate || 0));
    }, 0);

    const customerDiscountAmount = subtotal * customerDiscount / 100;
    const total = subtotal + totalTax - customerDiscountAmount;
    const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);

    return {
      subtotal,
      totalTax,
      customerDiscountAmount,
      total: Math.max(0, total),
      itemCount
    };
  }, [items, customerDiscount]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  const handleApplyDiscount = (productId: string) => {
    const discount = parseFloat(tempDiscount);
    if (!isNaN(discount) && discount >= 0 && discount <= 100 && onAddDiscount) {
      onAddDiscount(productId, discount);
    }
    setShowDiscountModal(null);
    setTempDiscount('');
  };

  const handleApplyNote = (productId: string) => {
    if (onAddNote) {
      onAddNote(productId, tempNote);
    }
    setShowNoteModal(null);
    setTempNote('');
  };

  return (
    <div className="card h-full flex flex-col">
      {/* Cart Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2.5 8H4a1 1 0 01-1-1V5a1 1 0 011-1h1m0 0h1m0 0l.9 3M7 13v8a2 2 0 002 2h8a2 2 0 002-2v-8" />
            </svg>
          </div>
          <div>
            <h3 className="heading-5">Shopping Cart</h3>
            <p className="text-caption">
              {calculations.itemCount} {calculations.itemCount === 1 ? 'item' : 'items'}
            </p>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          {items.length > 0 && (
            <span className="badge badge-primary">
              {items.length}
            </span>
          )}
          
          {loyaltyPoints > 0 && (
            <div className="flex items-center space-x-1 text-caption text-orange-600">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
              <span>{loyaltyPoints} pts</span>
            </div>
          )}
          
          {items.length > 0 && onClearCart && (
            <button
              onClick={onClearCart}
              className="btn btn-ghost btn-sm text-red-600 hover:bg-red-50"
              title="Clear cart"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          )}
        </div>
      </div>
      
      {/* Cart Content */}
      <div className="flex-1 overflow-hidden">
        {items.length === 0 ? (
          <div className="flex items-center justify-center h-full p-8">
            <div className="text-center">
              <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2.5 8H4a1 1 0 01-1-1V5a1 1 0 011-1h1m0 0h1m0 0l.9 3M7 13v8a2 2 0 002 2h8a2 2 0 002-2v-8" />
                </svg>
              </div>
              <h4 className="heading-6 mb-2">Your cart is empty</h4>
              <p className="text-body text-gray-600">Add some products to get started</p>
            </div>
          </div>
        ) : (
          <>
            {/* Cart Items */}
            <div className="p-4 space-y-3 overflow-y-auto flex-1">
              {items.map((item) => (
                <div
                  key={item.product.id}
                  className="card-nested group hover:shadow-md transition-all duration-200"
                >
                  <div className="flex items-start space-x-3">
                    {/* Product Image Placeholder */}
                    <div className="w-12 h-12 bg-gray-100 rounded-lg flex-shrink-0 flex items-center justify-center">
                      <svg className="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                      </svg>
                    </div>

                    {/* Product Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h4 className="text-body-sm font-semibold text-gray-900 truncate">
                            {item.product.name}
                          </h4>
                          <div className="flex items-center space-x-2 mt-1">
                            <span className="text-caption text-gray-500 bg-gray-100 px-2 py-1 rounded">
                              {item.product.category}
                            </span>
                            <span className="text-caption text-gray-600">
                              {formatPrice(item.product.price)} each
                            </span>
                          </div>
                          
                          {/* Item Note */}
                          {item.note && (
                            <div className="mt-2 text-caption text-blue-600 bg-blue-50 px-2 py-1 rounded">
                              📝 {item.note}
                            </div>
                          )}
                          
                          {/* Item Discount */}
                          {item.discount && item.discount > 0 && (
                            <div className="mt-1 text-caption text-green-600">
                              💰 {item.discount}% discount applied
                            </div>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center space-x-1 ml-2">
                          {/* Add Note */}
                          {onAddNote && (
                            <button
                              onClick={() => {
                                setShowNoteModal(item.product.id);
                                setTempNote(item.note || '');
                              }}
                              className="btn btn-ghost btn-xs"
                              title="Add note"
                            >
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </button>
                          )}
                          
                          {/* Add Discount */}
                          {onAddDiscount && (
                            <button
                              onClick={() => {
                                setShowDiscountModal(item.product.id);
                                setTempDiscount(item.discount?.toString() || '');
                              }}
                              className="btn btn-ghost btn-xs"
                              title="Add discount"
                            >
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                              </svg>
                            </button>
                          )}
                          
                          {/* Remove Item */}
                          <button
                            onClick={() => onRemoveItem(item.product.id)}
                            className="btn btn-ghost btn-xs text-red-600 hover:bg-red-50"
                            title="Remove item"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </div>

                      {/* Quantity Controls and Subtotal */}
                      <div className="flex items-center justify-between mt-3">
                        {/* Quantity Controls */}
                        <div className="flex items-center space-x-1 bg-gray-50 rounded-lg p-1">
                          <button
                            onClick={() => onUpdateQuantity(item.product.id, item.quantity - 1)}
                            className="btn btn-ghost btn-xs w-8 h-8"
                            disabled={item.quantity <= 1}
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                            </svg>
                          </button>
                          
                          <span className="text-body-sm font-semibold text-gray-900 w-8 text-center">
                            {item.quantity}
                          </span>
                          
                          <button
                            onClick={() => onUpdateQuantity(item.product.id, item.quantity + 1)}
                            disabled={item.quantity >= item.product.stock_quantity}
                            className="btn btn-ghost btn-xs w-8 h-8"
                          >
                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                            </svg>
                          </button>
                        </div>

                        {/* Item Subtotal */}
                        <div className="text-right">
                          <div className="text-body-sm font-bold text-gray-900">
                            {formatPrice(item.product.price * item.quantity * (1 - (item.discount || 0) / 100))}
                          </div>
                          {item.discount && item.discount > 0 && (
                            <div className="text-caption text-gray-500 line-through">
                              {formatPrice(item.product.price * item.quantity)}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Cart Summary and Checkout */}
      {items.length > 0 && (
        <div className="border-t border-gray-200 p-4 bg-gray-50">
          {/* Totals Breakdown */}
          <div className="space-y-2 mb-4">
            <div className="flex justify-between text-body">
              <span>Subtotal:</span>
              <span>{formatPrice(calculations.subtotal)}</span>
            </div>
            
            {calculations.totalTax > 0 && (
              <div className="flex justify-between text-body">
                <span>Tax:</span>
                <span>{formatPrice(calculations.totalTax)}</span>
              </div>
            )}
            
            {customerDiscount > 0 && (
              <div className="flex justify-between text-body text-green-600">
                <span>Customer Discount ({customerDiscount}%):</span>
                <span>-{formatPrice(calculations.customerDiscountAmount)}</span>
              </div>
            )}
            
            <div className="border-t border-gray-300 pt-2">
              <div className="flex justify-between items-center">
                <span className="text-heading-6 font-bold">Total:</span>
                <span className="text-heading-5 font-bold text-blue-600">
                  {formatPrice(calculations.total)}
                </span>
              </div>
            </div>
          </div>

          {/* Checkout Button */}
          <button
            onClick={onCheckout}
            disabled={isProcessing || items.length === 0}
            className="btn btn-primary w-full animate-pulse-on-hover"
          >
            {isProcessing ? (
              <div className="flex items-center space-x-2">
                <div className="loading-spinner"></div>
                <span>Processing...</span>
              </div>
            ) : (
              <div className="flex items-center justify-center space-x-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
                <span>Proceed to Checkout</span>
                <span className="text-sm opacity-90">
                  ({calculations.itemCount} {calculations.itemCount === 1 ? 'item' : 'items'})
                </span>
              </div>
            )}
          </button>
        </div>
      )}

      {/* Discount Modal */}
      {showDiscountModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card w-96">
            <h3 className="heading-6 mb-4">Add Discount</h3>
            <div className="space-y-4">
              <div>
                <label className="label">Discount Percentage</label>
                <input
                  type="number"
                  value={tempDiscount}
                  onChange={(e) => setTempDiscount(e.target.value)}
                  className="input w-full"
                  placeholder="Enter discount %"
                  min="0"
                  max="100"
                  autoFocus
                />
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleApplyDiscount(showDiscountModal)}
                  className="btn btn-primary flex-1"
                >
                  Apply
                </button>
                <button
                  onClick={() => {
                    setShowDiscountModal(null);
                    setTempDiscount('');
                  }}
                  className="btn btn-ghost flex-1"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Note Modal */}
      {showNoteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="card w-96">
            <h3 className="heading-6 mb-4">Add Note</h3>
            <div className="space-y-4">
              <div>
                <label className="label">Item Note</label>
                <textarea
                  value={tempNote}
                  onChange={(e) => setTempNote(e.target.value)}
                  className="input w-full"
                  placeholder="Enter note for this item..."
                  rows={3}
                  autoFocus
                />
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => handleApplyNote(showNoteModal)}
                  className="btn btn-primary flex-1"
                >
                  Save
                </button>
                <button
                  onClick={() => {
                    setShowNoteModal(null);
                    setTempNote('');
                  }}
                  className="btn btn-ghost flex-1"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Cart;