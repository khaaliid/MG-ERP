import React from 'react';

interface Product {
  id: string;
  name: string;
  price: number;
  stock_quantity: number;
  barcode?: string;
  category: string;
}

interface ProductListProps {
  products: Product[];
  onAddToCart: (product: Product, quantity?: number) => void;
}

const ProductList: React.FC<ProductListProps> = ({ products, onAddToCart }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {products.map((product) => (
        <div
          key={product.id}
          className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow"
        >
          <div className="mb-3">
            <h3 className="font-semibold text-lg mb-1">{product.name}</h3>
            <p className="text-sm text-gray-600 mb-1">Category: {product.category}</p>
            {product.barcode && (
              <p className="text-sm text-gray-500">Barcode: {product.barcode}</p>
            )}
          </div>
          
          <div className="mb-3">
            <p className="text-xl font-bold text-blue-600">
              ${product.price.toFixed(2)}
            </p>
            <p className={`text-sm ${product.stock_quantity > 10 ? 'text-green-600' : product.stock_quantity > 0 ? 'text-yellow-600' : 'text-red-600'}`}>
              Stock: {product.stock_quantity}
            </p>
          </div>
          
          <button
            onClick={() => onAddToCart(product, 1)}
            disabled={product.stock_quantity === 0}
            className={`w-full py-2 px-4 rounded-md font-medium transition-colors ${
              product.stock_quantity === 0
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {product.stock_quantity === 0 ? 'Out of Stock' : 'Add to Cart'}
          </button>
        </div>
      ))}
      
      {products.length === 0 && (
        <div className="col-span-full text-center py-8 text-gray-500">
          No products available
        </div>
      )}
    </div>
  );
};

export default ProductList;