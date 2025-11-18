import { useEffect, useState } from "react";
import "./index.css";
import { apiService, Product, Category, Brand } from "./services/apiService";

function formatEGP(v: number) {
  return `${v.toFixed(2)} EGP`;
}

interface HeaderProps {
  cashier: string;
  onSearch: (value: string) => void;
  online: boolean;
}

function Header({ cashier, onSearch, online }: HeaderProps) {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return (
    <header className="pos-header">
      <div className="left">
        <div className="logo">MyStore</div>
        <div className="meta">
          <div className="cashier">Cashier: <strong>{cashier}</strong></div>
          <div className="status">{online ? "Online" : "Offline"}</div>
        </div>
      </div>

      <div className="center">
        <input
          className="search"
          placeholder="Search product or scan barcode (press Enter)"
          onKeyDown={(e) => {
            if (e.key === "Enter") onSearch((e.target as HTMLInputElement).value.trim());
          }}
        />
      </div>

      <div className="right">
        <div className="time">{now.toLocaleString()}</div>
      </div>
    </header>
  );
}

interface ProductTileProps {
  product: Product;
  onAdd: (product: Product) => void;
}

function ProductTile({ product, onAdd }: ProductTileProps) {
  return (
    <div className="product-tile" onClick={() => onAdd(product)}>
      <div className="img-placeholder" aria-hidden>
        <span>{product.name.split(" ")[0]}</span>
      </div>
      <div className="product-info">
        <div className="name">{product.name}</div>
        <div className="meta">
          <div className="price">{formatEGP(product.price)}</div>
          <div className="sizes">{product.sizes?.join(" / ") || "N/A"}</div>
        </div>
      </div>
    </div>
  );
}

interface CartItem {
  id: string;
  name: string;
  price: number;
  qty: number;
  size: string | null;
}

interface CartItemProps {
  item: CartItem;
  onInc: (id: string) => void;
  onDec: (id: string) => void;
  onRemove: (id: string) => void;
}

function CartItem({ item, onInc, onDec, onRemove }: CartItemProps) {
  return (
    <div className="cart-item">
      <div className="ci-left">
        <div className="ci-name">{item.name}</div>
        <div className="ci-meta">{item.size ? `Size: ${item.size}` : ""}</div>
      </div>
      <div className="ci-right">
        <div className="qty-controls">
          <button onClick={() => onDec(item.id)}>-</button>
          <span>{item.qty}</span>
          <button onClick={() => onInc(item.id)}>+</button>
        </div>
        <div className="ci-price">{formatEGP(item.price * item.qty)}</div>
        <button className="remove" onClick={() => onRemove(item.id)}>✕</button>
      </div>
    </div>
  );
}

export default function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [category, setCategory] = useState("All");
  const [cart, setCart] = useState<CartItem[]>([]);
  const [discount, setDiscount] = useState(0); // EGP
  const [taxPct] = useState(14); // example VAT %
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [paymentMethod, setPaymentMethod] = useState("Cash");
  const [tendered, setTendered] = useState("");
  const [online, setOnline] = useState(true);

  // Load products and categories from backend
  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        setError(null);
        
        // Check backend health
        await apiService.healthCheck();
        setOnline(true);
        
        // Load products and categories in parallel
        const [productsResponse, categoriesData] = await Promise.all([
          apiService.getProducts(1, 100),
          apiService.getCategories()
        ]);
        
        setProducts(productsResponse.data);
        setCategories(categoriesData);
        
      } catch (err) {
        console.error('Error loading data:', err);
        setError(err instanceof Error ? err.message : 'Failed to load data');
        setOnline(false);
      } finally {
        setLoading(false);
      }
    }
    
    loadData();
  }, []);

  function addToCart(product: Product) {
    // default size selection: first size
    const size = product.sizes && product.sizes.length ? product.sizes[0] : null;
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
      const searchResults = await apiService.searchProducts(text, 10);
      
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
      
      const sale = await apiService.createSale(saleData);
      
      alert(`Payment success!\nSale #: ${sale.sale_number}\nMethod: ${paymentMethod}\nTotal: ${formatEGP(total)}`);
      
      // reset cart
      setCart([]);
      setDiscount(0);
      setTendered("");
      setPaymentOpen(false);
      
    } catch (err) {
      console.error('Error processing sale:', err);
      alert(`Payment failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }

  function holdSale() {
    // simple simulated hold: store in localStorage with timestamp
    if (cart.length === 0) return alert("No items to hold");
    const held = JSON.parse(localStorage.getItem("heldSales") || "[]");
    held.push({ id: Date.now(), cart, discount, createdAt: new Date().toISOString() });
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
  const categoryOptions = ["All", ...categories.map(cat => cat.name)];

  const filtered = products.filter((p) => {
    if (category !== "All") {
      // Filter by selected category
      const productCategory = p.category?.name;
      if (productCategory !== category) return false;
    }
    if (!filter) return true;
    return (
      p.name.toLowerCase().includes(filter.toLowerCase()) || 
      p.sku.toLowerCase().includes(filter.toLowerCase()) ||
      (p.description && p.description.toLowerCase().includes(filter.toLowerCase()))
    );
  });

  if (loading) {
    return (
      <div className="pos-app">
        <Header cashier="Ahmed" onSearch={() => {}} online={false} />
        <div className="container">
          <div className="empty">Loading products...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pos-app">
        <Header cashier="Ahmed" onSearch={() => {}} online={false} />
        <div className="container">
          <div className="empty">
            <p>Error: {error}</p>
            <button 
              className="btn primary" 
              onClick={() => window.location.reload()}
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pos-app">
      <Header cashier="Ahmed" onSearch={(v) => addByBarcodeOrName(v)} online={online} />

      <div className="container">
        <main className="left-panel">
          <div className="panel-top">
            <div className="filters">
              <input
                placeholder="Filter products..."
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="filter-input"
              />
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {categoryOptions.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div className="summary">
              <div>Total SKUs: {filtered.length}</div>
            </div>
          </div>

          <div className="product-grid">
            {filtered.map((p) => (
              <ProductTile key={p.id} product={p} onAdd={addToCart} />
            ))}
            {filtered.length === 0 && <div className="empty">No products match the filter.</div>}
          </div>
        </main>

        <aside className="right-panel">
          <div className="cart-header">
            <h3>Current Sale</h3>
            <div className="cart-meta">{cart.length} items</div>
          </div>

          <div className="cart-list">
            {cart.length === 0 && <div className="empty">Cart is empty. Tap product to add.</div>}
            {cart.map((it) => (
              <CartItem key={it.id + it.size} item={it} onInc={inc} onDec={dec} onRemove={removeItem} />
            ))}
          </div>

          <div className="totals">
            <div className="tot-line">
              <span>Subtotal</span>
              <strong>{formatEGP(calcSubtotal())}</strong>
            </div>
            <div className="tot-line">
              <span>Discount</span>
              <input
                type="number"
                min="0"
                value={discount}
                onChange={(e) => setDiscount(parseFloat(e.target.value || "0"))}
                className="discount-input"
              />
            </div>
            <div className="tot-line">
              <span>Tax ({taxPct}%)</span>
              <strong>{formatEGP(calcTax(calcSubtotal()))}</strong>
            </div>
            <div className="tot-line total">
              <span>Total</span>
              <strong>{formatEGP(calcTotal())}</strong>
            </div>
          </div>

          <div className="actions">
            <button onClick={holdSale} className="btn secondary">Hold Sale</button>
            <button onClick={() => { setCart([]); setDiscount(0); }} className="btn secondary">Void</button>
            <button onClick={() => alert("Refund flow (simulate)")} className="btn secondary">Refund</button>
            <button onClick={openDrawer} className="btn secondary">Open Drawer</button>
            <button onClick={handleCheckout} className="btn primary">Checkout</button>
          </div>
        </aside>
      </div>

      {paymentOpen && (
        <div className="modal-backdrop" role="dialog" aria-modal>
          <div className="modal">
            <h3>Payment</h3>
            <div className="modal-body">
              <div className="payment-methods">
                {["Cash", "Card", "Wallet"].map((m) => (
                  <label key={m} className={`pm ${paymentMethod === m ? "active" : ""}`}>
                    <input
                      type="radio"
                      name="pm"
                      value={m}
                      checked={paymentMethod === m}
                      onChange={() => setPaymentMethod(m)}
                    />
                    {m}
                  </label>
                ))}
              </div>

              <div className="pay-summary">
                <div>Amount due: <strong>{formatEGP(calcTotal())}</strong></div>
                {paymentMethod === "Cash" && (
                  <div className="tender">
                    <label>Cash tendered:</label>
                    <input
                      type="number"
                      value={tendered}
                      onChange={(e) => setTendered(e.target.value)}
                      placeholder="0.00"
                    />
                    <div className="change">Change: {tendered ? formatEGP(Math.max(0, parseFloat(tendered) - calcTotal())) : "0.00 EGP"}</div>
                  </div>
                )}
              </div>
            </div>

            <div className="modal-actions">
              <button onClick={() => setPaymentOpen(false)} className="btn secondary">Cancel</button>
              <button onClick={confirmPayment} className="btn primary">Confirm Payment</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}