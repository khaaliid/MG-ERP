/**
 * POS (Point of Sale) Page Component
 * Main sales interface with product selection and cart functionality
 */

import { useEffect, useState, useMemo } from "react";
import { useNavigate } from 'react-router-dom';
import { enhancedApiService, Product, Category } from "../services/enhancedApiService";
import { useAuth } from "../contexts/AuthContext";

function formatCurrency(v: number, currencyCode: string) {
  const value = typeof v === 'number' && !isNaN(v) ? v : 0;
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: currencyCode || 'USD' }).format(value);
  } catch {
    return `${value.toFixed(2)} ${currencyCode || 'USD'}`;
  }
}

interface ProductTileProps {
  product: Product;
  onAdd: (product: Product) => void;
  currencyCode: string;
}

function ProductTile({ product, onAdd, currencyCode }: ProductTileProps) {
  // Add defensive checks
  if (!product) {
    return <div className="bg-red-100 p-4 rounded-lg">Invalid product data</div>;
  }

  // Ensure required fields exist
  const name = product.name || 'Unknown Product';
  const price = typeof product.price === 'number' ? product.price : 0;
  const sku = product.sku || 'N/A';

  return (
    <div className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow cursor-pointer p-4" onClick={() => onAdd(product)}>
      <div className="font-medium text-gray-900 mb-2">{name}</div>
      <div className="flex justify-between items-center mb-2">
        <div className="text-lg font-bold text-blue-600">{formatCurrency(price, currencyCode)}</div>
        <div className="text-sm text-gray-500">{sku}</div>
      </div>
      {product.sizes && Array.isArray(product.sizes) && product.sizes.length > 0 && (
        <div className="text-sm text-gray-600 mb-1">
          <strong>Sizes:</strong> {
            product.sizes.map(sizeItem => {
              if (typeof sizeItem === 'string') {
                return sizeItem;
              } else if (typeof sizeItem === 'object' && sizeItem !== null && 'size' in sizeItem) {
                return (sizeItem as any).size;
              }
              return 'Unknown';
            }).join(", ")
          }
        </div>
      )}
      {product.sizes && typeof product.sizes === 'object' && !Array.isArray(product.sizes) && (
        <div className="text-sm text-gray-600 mb-1">
          <strong>Sizes:</strong> Available
        </div>
      )}
      {typeof product.stock_quantity === 'number' && (
        <div className="text-sm text-gray-600">Stock: {product.stock_quantity}</div>
      )}
      {product.category && product.category.name && (
        <div className="text-xs text-gray-500 mt-1">{product.category.name}</div>
      )}
    </div>
  );
}

interface CartItem {
  id: string;
  name: string;
  price: number;
  qty: number;
  size?: string | null;
}

interface CartItemProps {
  item: CartItem;
  onInc: (id: string) => void;
  onDec: (id: string) => void;
  onRemove: (id: string) => void;
  currencyCode: string;
}

function CartItem({ item, onInc, onDec, onRemove, currencyCode }: CartItemProps) {
  return (
    <div className="flex items-center justify-between p-3 bg-white rounded-lg shadow-sm border">
      <div className="flex-1">
        <div className="font-medium text-gray-900">{item.name}</div>
        {item.size && <div className="text-sm text-gray-600">Size: {item.size}</div>}
        <div className="text-sm text-gray-600">{formatCurrency(item.price, currencyCode)} each</div>
      </div>
      <div className="flex items-center space-x-2">
        <button 
          onClick={() => onDec(item.id)} 
          className="w-8 h-8 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center text-gray-700"
        >
          -
        </button>
        <span className="w-8 text-center font-medium">{item.qty}</span>
        <button 
          onClick={() => onInc(item.id)} 
          className="w-8 h-8 rounded-full bg-blue-600 hover:bg-blue-700 flex items-center justify-center text-white"
        >
          +
        </button>
        <button 
          onClick={() => onRemove(item.id)} 
          className="w-8 h-8 rounded-full bg-red-600 hover:bg-red-700 flex items-center justify-center text-white ml-2"
        >
          ×
        </button>
      </div>
      <div className="text-right ml-4">
        <div className="font-medium text-gray-900">{formatCurrency(item.qty * item.price, currencyCode)}</div>
      </div>
    </div>
  );
}

export default function POS() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [category, setCategory] = useState("All");
  const [cart, setCart] = useState<CartItem[]>([]);
  const [discount, setDiscount] = useState(0); // currency-dependent
  const [taxPct, setTaxPct] = useState(14); // VAT %, loaded from settings
  const [currencyCode, setCurrencyCode] = useState('USD');
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState("Cash");
  const [tendered, setTendered] = useState("");
  const [isSyncingProducts, setIsSyncingProducts] = useState(false);
  const [isSyncingCategories, setIsSyncingCategories] = useState(false);
  const [productSyncMessage, setProductSyncMessage] = useState<string | null>(null);
  const [categorySyncMessage, setCategorySyncMessage] = useState<string | null>(null);

  // Load only settings on initial load (skip products/categories for instant load)
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        
        const apiBase = (import.meta as any).env?.VITE_API_BASE_URL || '';
        const token = localStorage.getItem('pos_auth_token') || '';
        
        // Load only settings
        const settingsResponse = await fetch(`${apiBase}/settings/`, {
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Accept': 'application/json'
          }
        }).catch(() => null);

        // Load POS settings
        if (settingsResponse?.ok) {
          const s = await settingsResponse.json();
          if (typeof s.tax_rate === 'number') {
            setTaxPct(Math.round(s.tax_rate * 100));
          }
          if (typeof s.currency_code === 'string') {
            setCurrencyCode(s.currency_code);
          }
        }
        
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to load data';
        setError(message);
        if (message.toLowerCase().includes('authentication required') || message.toLowerCase().includes('invalid or expired token')) {
          navigate('/login', { replace: true });
        }
      } finally {
        setLoading(false);
      }
    }
    
    loadData();
  }, []);

  async function handleSyncProducts() {
    if (isSyncingProducts) return;
    const authToken = localStorage.getItem('pos_auth_token');
    if (!authToken) {
      navigate('/login', { replace: true });
      return;
    }

    try {
      setIsSyncingProducts(true);
      setProductSyncMessage(null);
      const base = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8001/api/v1';
      
      const productsResp = await fetch(`${base}/products/sync`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!productsResp.ok) throw new Error('Product sync failed');
      
      const productsResult = await productsResp.json();
      const productsSynced = productsResult?.synced ?? 0;
      
      setProductSyncMessage(`✓ ${productsSynced} products synced`);
      
      // Reload products from backend cache
      try {
        const refreshed = await enhancedApiService.getProducts(1, 100);
        const refreshedProducts = Array.isArray(refreshed?.data) ? refreshed.data : Array.isArray(refreshed) ? (refreshed as any) : [];
        setProducts(refreshedProducts);
      } catch {}
    } catch (e) {
      setProductSyncMessage('✗ Product sync failed');
    } finally {
      setIsSyncingProducts(false);
      setTimeout(() => setProductSyncMessage(null), 5000);
    }
  }

  async function handleSyncCategories() {
    if (isSyncingCategories) return;
    const authToken = localStorage.getItem('pos_auth_token');
    if (!authToken) {
      navigate('/login', { replace: true });
      return;
    }

    try {
      setIsSyncingCategories(true);
      setCategorySyncMessage(null);
      const base = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8001/api/v1';
      
      const categoriesResp = await fetch(`${base}/products/categories/sync`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!categoriesResp.ok) throw new Error('Category sync failed');
      
      const categoriesResult = await categoriesResp.json();
      const categoriesSynced = categoriesResult?.synced ?? 0;
      
      setCategorySyncMessage(`✓ ${categoriesSynced} categories synced`);
      
      // Reload categories from backend cache
      try {
        const refreshedCategories = await enhancedApiService.getCategories();
        setCategories(Array.isArray(refreshedCategories) ? refreshedCategories : []);
      } catch {}
    } catch (e) {
      setCategorySyncMessage('✗ Category sync failed');
    } finally {
      setIsSyncingCategories(false);
      setTimeout(() => setCategorySyncMessage(null), 5000);
    }
  }

  function addToCart(product: Product) {
    
    // Handle sizes safely - could be array of strings, array of objects, or undefined
    let size: string | null = null;
    if (product.sizes && Array.isArray(product.sizes) && product.sizes.length > 0) {
      const firstSize = product.sizes[0];
      if (typeof firstSize === 'string') {
        // Array of strings
        size = firstSize;
      } else if (typeof firstSize === 'object' && firstSize !== null && 'size' in firstSize) {
        // Array of objects with size property
        size = (firstSize as any).size;
      }
    }
    
    setCart((c) => {
      const idx = c.findIndex((i) => i.id === product.id && i.size === size);
      if (idx >= 0) {
        const copy = [...c];
        copy[idx].qty += 1;
        return copy;
      }
      return [...c, { id: product.id, name: product.name, price: product.price, qty: 1, size }];
    });
  }

  async function addByBarcodeOrName(text: string) {
    if (!text) return;
    
    try {
      // Search products using the API
      const searchResults = await enhancedApiService.searchProducts(text);
      
      if (searchResults.length > 0) {
        // Add the first matching product
        addToCart(searchResults[0]);
      } else {
        alert("Product not found");
      }
    } catch (err) {
      console.error('Error searching products:', err);
      alert("Error searching for product");
    }
  }

  function inc(id: string) {
    setCart((c) => c.map((i) => (i.id === id ? { ...i, qty: i.qty + 1 } : i)));
  }
  function dec(id: string) {
    setCart((c) => {
      const idx = c.findIndex((i) => i.id === id);
      if (idx < 0) return c;
      const copy = [...c];
      copy[idx].qty -= 1;
      if (copy[idx].qty <= 0) copy.splice(idx, 1);
      return copy;
    });
  }
  function removeItem(id: string) {
    setCart((c) => c.filter((i) => i.id !== id));
  }

  function calcSubtotal() {
    return cart.reduce((s, i) => s + i.qty * i.price, 0);
  }
  function calcTax(sub: number) {
    return (sub - discount) * (taxPct / 100.0);
  }
  function calcTotal() {
    const sub = calcSubtotal();
    const t = Math.max(0, sub - discount);
    return t + calcTax(sub);
  }

  function handleCheckout() {
    if (cart.length === 0) return alert("Cart is empty");
    setPaymentOpen(true);
  }

  async function confirmPayment() {
    const total = calcTotal();
    if (paymentMethod === "Cash") {
      const tender = parseFloat(tendered || "0");
      if (isNaN(tender) || tender < total) {
        return alert("Insufficient cash tendered");
      }
    }
    
    try {
      // Create sale via API
      const saleData = {
        items: cart.map(item => ({
          product_id: item.id,
          quantity: item.qty,
          unit_price: item.price,
          size: item.size || undefined
        })),
        payment_method: paymentMethod.toLowerCase() as 'cash' | 'card' | 'wallet',
        tendered_amount: paymentMethod === "Cash" ? parseFloat(tendered) : undefined,
        discount_amount: discount,
        tax_rate: taxPct / 100,
        notes: ""
      };
      
      const sale = await enhancedApiService.createSale(saleData);
      
      alert(`Payment success!\nSale #: ${sale.sale_number}\nMethod: ${paymentMethod}\nTotal: ${formatCurrency(total, currencyCode)}`);
      
      // reset cart
      setCart([]);
      setDiscount(0);
      setTendered("");
      setPaymentOpen(false);
      
    } catch (err) {
      console.error('Error processing sale:', err);
      const message = err instanceof Error ? err.message : 'Unknown error';
      if (message.toLowerCase().includes('authentication required') || message.toLowerCase().includes('invalid or expired token')) {
        navigate('/login', { replace: true });
        return;
      }
      alert(`Payment failed: ${message}`);
    }
  }

  function holdSale() {
    // simple simulated hold: store in localStorage with timestamp
    if (cart.length === 0) return alert("No items to hold");
    const held = JSON.parse(localStorage.getItem("heldSales") || "[]");
    held.push({ 
      id: Date.now(), 
      cart, 
      discount, 
      createdAt: new Date().toISOString(),
      cashier: user?.username || 'unknown'
    });
    localStorage.setItem("heldSales", JSON.stringify(held));
    setCart([]);
    setDiscount(0);
    alert("Sale held");
  }

  function openDrawer() {
    // real hardware: trigger cash drawer via printer or API
    alert("Open drawer (simulated)");
  }

  // Build categories list including "All"
  const categoryOptions = useMemo(() => 
    ["All", ...categories.map(cat => cat.name)], 
    [categories]
  );

  const filtered = useMemo(() => 
    products.filter((p) => {
      if (!p || typeof p !== 'object') return false;
      
      if (category !== "All") {
        const productCategory = p.category?.name;
        if (productCategory !== category) return false;
      }
      if (!filter) return true;
      
      const searchLower = filter.toLowerCase();
      const name = p.name || '';
      const sku = p.sku || '';
      const description = p.description || '';
      
      return (
        name.toLowerCase().includes(searchLower) || 
        sku.toLowerCase().includes(searchLower) ||
        description.toLowerCase().includes(searchLower)
      );
    }),
    [products, category, filter]
  );

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
        <div className="text-center">
          <p className="text-red-600 mb-4">Error: {error}</p>
          <button 
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700" 
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Quick Search Bar */}
      <div className="bg-white border-b p-4">
        <div className="max-w-7xl mx-auto">
          <input
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Search product or scan barcode (press Enter)"
            onKeyDown={(e) => {
              if (e.key === "Enter") addByBarcodeOrName((e.target as HTMLInputElement).value.trim());
            }}
          />
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Products Panel */}
        <main className="flex-1 p-6 overflow-y-auto">
          <div className="max-w-7xl mx-auto">
            {/* Filters */}
            <div className="flex items-center space-x-4 mb-6">
              <input
                placeholder="Filter products..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <select 
                value={category} 
                onChange={(e) => setCategory(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {categoryOptions.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <button
                onClick={handleSyncProducts}
                disabled={isSyncingProducts}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  isSyncingProducts ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
                title="Sync products from inventory"
              >
                <svg className={`w-4 h-4 ${isSyncingProducts ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>{isSyncingProducts ? 'Syncing...' : 'Sync Products'}</span>
              </button>
              <button
                onClick={handleSyncCategories}
                disabled={isSyncingCategories}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  isSyncingCategories ? 'bg-gray-200 text-gray-500 cursor-not-allowed' : 'bg-green-600 text-white hover:bg-green-700'
                }`}
                title="Sync categories from inventory"
              >
                <svg className={`w-4 h-4 ${isSyncingCategories ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                <span>{isSyncingCategories ? 'Syncing...' : 'Sync Categories'}</span>
              </button>
              <div className="text-sm text-gray-600">
                {filtered.length} products
              </div>
              {productSyncMessage && (
                <div className={`px-3 py-1 rounded-lg text-sm font-medium ${productSyncMessage.startsWith('✓') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  {productSyncMessage}
                </div>
              )}
              {categorySyncMessage && (
                <div className={`px-3 py-1 rounded-lg text-sm font-medium ${categorySyncMessage.startsWith('✓') ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  {categorySyncMessage}
                </div>
              )}
            </div>

            {/* Products Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
              {filtered.map((p) => (
                <ProductTile key={p.id} product={p} onAdd={addToCart} currencyCode={currencyCode} />
              ))}
              {filtered.length === 0 && (
                <div className="col-span-full text-center text-gray-500 py-8">
                  No products match the filter.
                </div>
              )}
            </div>
          </div>
        </main>

        {/* Cart Panel */}
        <aside className="w-96 bg-gray-50 border-l flex flex-col">
          <div className="p-4 border-b bg-white">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-900">Current Sale</h3>
              <div className="text-sm text-gray-600">{cart.length} items</div>
            </div>
          </div>

          <div className="flex-1 p-4 overflow-y-auto space-y-3">
            {cart.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                Cart is empty. Select products to add.
              </div>
            )}
            {cart.map((it) => (
              <CartItem key={`${it.id}-${typeof it.size === 'string' ? it.size : 'no-size'}`} item={it} onInc={inc} onDec={dec} onRemove={removeItem} currencyCode={currencyCode} />
            ))}
          </div>

          {/* Totals */}
          <div className="p-4 border-t bg-white space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">Subtotal</span>
              <strong className="text-gray-900">{formatCurrency(calcSubtotal(), currencyCode)}</strong>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Discount</span>
              <input
                type="number"
                min="0"
                value={discount}
                onChange={(e) => setDiscount(parseFloat(e.target.value || "0"))}
                className="w-24 px-2 py-1 text-right border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Tax ({taxPct}%)</span>
              <strong className="text-gray-900">{formatCurrency(calcTax(calcSubtotal()), currencyCode)}</strong>
            </div>
            <div className="flex justify-between text-lg">
              <span className="font-semibold text-gray-900">Total</span>
              <strong className="text-blue-600">{formatCurrency(calcTotal(), currencyCode)}</strong>
            </div>
          </div>

          {/* Actions */}
          <div className="p-4 border-t bg-white space-y-2">
            <div className="grid grid-cols-2 gap-2">
              <button 
                onClick={holdSale} 
                className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
              >
                Hold Sale
              </button>
              <button 
                onClick={() => { setCart([]); setDiscount(0); }} 
                className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
              >
                Void
              </button>
              <button 
                onClick={() => alert("Refund flow (simulate)")} 
                className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                disabled={!user || (user.role !== 'manager' && user.role !== 'admin')}
              >
                Refund
              </button>
              <button 
                onClick={openDrawer} 
                className="px-4 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
              >
                Open Drawer
              </button>
            </div>
            <button 
              onClick={handleCheckout} 
              className="w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              disabled={cart.length === 0}
            >
              Checkout
            </button>
          </div>
        </aside>
      </div>

      {/* Payment Modal */}
      {paymentOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="p-6">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Payment</h3>
              
              {/* Payment Methods */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">Payment Method</label>
                <div className="grid grid-cols-3 gap-2">
                  {["Cash", "Card", "Wallet"].map((m) => (
                    <label key={m} className={`border rounded-lg p-3 text-center cursor-pointer transition-colors ${
                      paymentMethod === m 
                        ? 'bg-blue-600 text-white border-blue-600' 
                        : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                    }`}>
                      <input
                        type="radio"
                        name="pm"
                        value={m}
                        checked={paymentMethod === m}
                        onChange={() => setPaymentMethod(m)}
                        className="sr-only"
                      />
                      {m}
                    </label>
                  ))}
                </div>
              </div>

              {/* Payment Summary */}
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex justify-between text-lg font-semibold">
                  <span>Amount due:</span>
                  <span className="text-blue-600">{formatCurrency(calcTotal(), currencyCode)}</span>
                </div>
                
                {paymentMethod === "Cash" && (
                  <div className="mt-4">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Cash tendered:</label>
                    <input
                      type="number"
                      value={tendered}
                      onChange={(e) => setTendered(e.target.value)}
                      placeholder="0.00"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <div className="mt-2 text-sm text-gray-600">
                      Change: {tendered ? formatCurrency(Math.max(0, parseFloat(tendered) - calcTotal()), currencyCode) : `0.00 ${currencyCode}`}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="flex space-x-3 p-6 pt-0">
              <button 
                onClick={() => setPaymentOpen(false)} 
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={confirmPayment} 
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Confirm Payment
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}