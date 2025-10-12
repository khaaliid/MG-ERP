import React, { useState, useEffect } from 'react';
import ProductList from '../components/ProductList';
import Cart from '../components/Cart';
import CheckoutForm from '../components/CheckoutForm';

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

const POSMain: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [showCheckout, setShowCheckout] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await fetch('http://localhost:8001/products/');
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      }
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (product: Product, quantity: number = 1) => {
    setCart(prevCart => {
      const existingItem = prevCart.find(item => item.product.id === product.id);
      if (existingItem) {
        return prevCart.map(item =>
          item.product.id === product.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      }
      return [...prevCart, { product, quantity }];
    });
  };

  const updateCartQuantity = (productId: string, quantity: number) => {
    if (quantity <= 0) {
      removeFromCart(productId);
      return;
    }
    setCart(prevCart =>
      prevCart.map(item =>
        item.product.id === productId
          ? { ...item, quantity }
          : item
      )
    );
  };

  const removeFromCart = (productId: string) => {
    setCart(prevCart => prevCart.filter(item => item.product.id !== productId));
  };

  const clearCart = () => {
    setCart([]);
    setShowCheckout(false);
  };

  const getTotalAmount = () => {
    return cart.reduce((total, item) => total + (item.product.price * item.quantity), 0);
  };

  const handleCheckout = () => {
    setShowCheckout(true);
  };

  const handleSaleComplete = () => {
    clearCart();
    fetchProducts(); // Refresh products to update stock
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lg">Loading products...</div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Products Section */}
      <div className="lg:col-span-2">
        <h2 className="text-2xl font-bold mb-4">Products</h2>
        <ProductList 
          products={products} 
          onAddToCart={addToCart} 
        />
      </div>

      {/* Cart Section */}
      <div className="lg:col-span-1">
        <h2 className="text-2xl font-bold mb-4">Cart</h2>
        <Cart
          items={cart}
          onUpdateQuantity={updateCartQuantity}
          onRemoveItem={removeFromCart}
          onCheckout={handleCheckout}
          total={getTotalAmount()}
        />
        
        {showCheckout && (
          <div className="mt-6">
            <CheckoutForm
              cartItems={cart}
              total={getTotalAmount()}
              onSaleComplete={handleSaleComplete}
              onCancel={() => setShowCheckout(false)}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default POSMain;