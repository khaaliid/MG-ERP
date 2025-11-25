import React, { useState, useEffect, useMemo } from 'react';

interface Product {
  id: string;
  name: string;
  description?: string;
  price: number;
  category: string;
  stock_quantity: number;
  image?: string;
  barcode?: string;
  isActive?: boolean;
  tags?: string[];
  taxRate?: number;
}

interface ProductListProps {
  products?: Product[];
  onAddToCart: (product: Product, quantity?: number) => void;
  searchTerm?: string;
  selectedCategory?: string;
}

const ProductList: React.FC<ProductListProps> = ({ 
  products: propProducts = [],
  onAddToCart, 
  searchTerm = '',
  selectedCategory = 'all' 
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [sortBy, setSortBy] = useState<'name' | 'price' | 'category' | 'stock'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [priceRange, setPriceRange] = useState<{ min: number; max: number }>({ min: 0, max: 1000 });
  const [showFilters, setShowFilters] = useState(false);

  // Use prop products if provided, otherwise use mock data
  useEffect(() => {
    if (propProducts.length > 0) {
      setProducts(propProducts);
      setLoading(false);
    } else {
      // Mock data for standalone usage
      const mockProducts: Product[] = [
        {
          id: '1',
          name: 'Premium Coffee Beans',
          description: 'Freshly roasted arabica coffee beans from Colombia',
          price: 24.99,
          category: 'Beverages',
          stock_quantity: 45,
          image: '/api/placeholder/300/300',
          barcode: '1234567890123',
          isActive: true,
          tags: ['organic', 'fair-trade', 'premium'],
          taxRate: 0.08
        },
        {
          id: '2',
          name: 'Wireless Bluetooth Headphones',
          description: 'High-quality wireless headphones with noise cancellation',
          price: 199.99,
          category: 'Electronics',
          stock_quantity: 12,
          image: '/api/placeholder/300/300',
          barcode: '2345678901234',
          isActive: true,
          tags: ['wireless', 'bluetooth', 'noise-cancelling'],
          taxRate: 0.10
        },
        {
          id: '3',
          name: 'Organic Bananas',
          description: 'Fresh organic bananas, sold per bunch',
          price: 3.49,
          category: 'Produce',
          stock_quantity: 78,
          image: '/api/placeholder/300/300',
          barcode: '3456789012345',
          isActive: true,
          tags: ['organic', 'fresh', 'fruit'],
          taxRate: 0.00
        },
        {
          id: '4',
          name: 'Artisan Sourdough Bread',
          description: 'Freshly baked sourdough bread made with organic flour',
          price: 6.99,
          category: 'Bakery',
          stock_quantity: 23,
          image: '/api/placeholder/300/300',
          barcode: '4567890123456',
          isActive: true,
          tags: ['artisan', 'sourdough', 'organic'],
          taxRate: 0.05
        },
        {
          id: '5',
          name: 'Stainless Steel Water Bottle',
          description: 'Insulated stainless steel water bottle, 24oz capacity',
          price: 29.99,
          category: 'Home & Garden',
          stock_quantity: 34,
          image: '/api/placeholder/300/300',
          barcode: '5678901234567',
          isActive: true,
          tags: ['eco-friendly', 'insulated', 'stainless-steel'],
          taxRate: 0.08
        },
        {
          id: '6',
          name: 'Greek Yogurt',
          description: 'Creamy Greek yogurt with live cultures, 32oz container',
          price: 5.99,
          category: 'Dairy',
          stock_quantity: 56,
          image: '/api/placeholder/300/300',
          barcode: '6789012345678',
          isActive: true,
          tags: ['protein', 'probiotics', 'low-fat'],
          taxRate: 0.05
        }
      ];

      setTimeout(() => {
        setProducts(mockProducts);
        setLoading(false);
      }, 800);
    }
  }, [propProducts]);

  // Get unique categories
  const categories = useMemo(() => {
    const cats = ['all', ...new Set(products.map(p => p.category))];
    return cats;
  }, [products]);

  // Filter and sort products
  const filteredProducts = useMemo(() => {
    let filtered = products.filter(product => {
      const matchesSearch = searchTerm === '' || 
        product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        product.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        product.barcode?.includes(searchTerm) ||
        product.tags?.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));

      const matchesCategory = selectedCategory === 'all' || product.category === selectedCategory;
      const matchesPrice = product.price >= priceRange.min && product.price <= priceRange.max;
      const isActive = product.isActive !== false;

      return matchesSearch && matchesCategory && matchesPrice && isActive;
    });

    // Sort products
    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'price':
          comparison = a.price - b.price;
          break;
        case 'category':
          comparison = a.category.localeCompare(b.category);
          break;
        case 'stock':
          comparison = a.stock_quantity - b.stock_quantity;
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [products, searchTerm, selectedCategory, priceRange, sortBy, sortOrder]);

  // handleSort function removed - not currently used in UI

  const getStockStatus = (stock: number) => {
    if (stock === 0) return { status: 'out-of-stock', label: 'Out of Stock', color: 'bg-red-100 text-red-800' };
    if (stock <= 10) return { status: 'low-stock', label: 'Low Stock', color: 'bg-orange-100 text-orange-800' };
    return { status: 'in-stock', label: 'In Stock', color: 'bg-green-100 text-green-800' };
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  if (loading) {
    return (
      <div className="card">
        <div className="flex items-center justify-center py-16">
          <div className="flex items-center space-x-3">
            <div className="loading-spinner"></div>
            <span className="text-body text-gray-600">Loading products...</span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="card">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          {/* Results Info */}
          <div className="flex items-center space-x-4">
            <h2 className="heading-5">Products</h2>
            <span className="badge badge-neutral">
              {filteredProducts.length} of {products.length}
            </span>
          </div>

          {/* Controls */}
          <div className="flex items-center space-x-3">
            {/* Filters Toggle */}
            <button
              onClick={() => setShowFilters(!showFilters)}
              className={`btn btn-ghost btn-sm ${showFilters ? 'text-blue-600' : ''}`}
              aria-label="Toggle filters"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              <span>Filters</span>
            </button>

            {/* Sort Dropdown */}
            <select
              value={`${sortBy}-${sortOrder}`}
              onChange={(e) => {
                const [field, order] = e.target.value.split('-') as [typeof sortBy, typeof sortOrder];
                setSortBy(field);
                setSortOrder(order);
              }}
              className="input input-sm"
            >
              <option value="name-asc">Name A-Z</option>
              <option value="name-desc">Name Z-A</option>
              <option value="price-asc">Price Low-High</option>
              <option value="price-desc">Price High-Low</option>
              <option value="category-asc">Category A-Z</option>
              <option value="stock-asc">Stock Low-High</option>
              <option value="stock-desc">Stock High-Low</option>
            </select>

            {/* View Mode Toggle */}
            <div className="flex border rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode('grid')}
                className={`btn btn-sm border-0 rounded-none ${
                  viewMode === 'grid' ? 'btn-primary' : 'btn-ghost'
                }`}
                aria-label="Grid view"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
              </button>
              <button
                onClick={() => setViewMode('list')}
                className={`btn btn-sm border-0 rounded-none ${
                  viewMode === 'list' ? 'btn-primary' : 'btn-ghost'
                }`}
                aria-label="List view"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Filters Panel */}
        {showFilters && (
          <div className="mt-6 pt-6 border-t border-gray-200 animate-fade-in">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Category Filter */}
              <div>
                <label className="label">Category</label>
                <select
                  value={selectedCategory}
                  onChange={(e) => {
                    // Note: This would need proper implementation in parent component
                    console.log('Category changed:', e.target.value);
                  }}
                  className="input w-full"
                >
                  {categories.map(category => (
                    <option key={category} value={category}>
                      {category === 'all' ? 'All Categories' : category}
                    </option>
                  ))}
                </select>
              </div>

              {/* Price Range */}
              <div>
                <label className="label">Price Range</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={priceRange.min}
                    onChange={(e) => setPriceRange(prev => ({ ...prev, min: Number(e.target.value) }))}
                    className="input flex-1"
                    min="0"
                  />
                  <span className="text-gray-400">-</span>
                  <input
                    type="number"
                    placeholder="Max"
                    value={priceRange.max}
                    onChange={(e) => setPriceRange(prev => ({ ...prev, max: Number(e.target.value) }))}
                    className="input flex-1"
                    min="0"
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Products Display */}
      {filteredProducts.length === 0 ? (
        <div className="card">
          <div className="text-center py-16">
            <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
            <h3 className="heading-6 mb-2">No products found</h3>
            <p className="text-body text-gray-600 mb-4">
              Try adjusting your search criteria or filters
            </p>
            <button
              onClick={() => {
                setPriceRange({ min: 0, max: 1000 });
                setShowFilters(false);
              }}
              className="btn btn-ghost"
            >
              Clear Filters
            </button>
          </div>
        </div>
      ) : (
        <div className={`${
          viewMode === 'grid' 
            ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6' 
            : 'space-y-4'
        }`}>
          {filteredProducts.map((product) => {
            const stockInfo = getStockStatus(product.stock_quantity);
            
            // Grid view
            return (
              <div key={product.id} className="card group hover:shadow-xl hover:-translate-y-1 transition-all duration-300">
                {/* Product Image */}
                <div className="relative aspect-square bg-gray-100 rounded-t-lg overflow-hidden">
                  <div className="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center">
                    <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                    </svg>
                  </div>
                  
                  {/* Stock Badge */}
                  <div className="absolute top-3 left-3">
                    <span className={`badge badge-sm ${stockInfo.color}`}>
                      {stockInfo.label}
                    </span>
                  </div>
                </div>

                {/* Product Details */}
                <div className="p-4">
                  <div className="mb-3">
                    <h3 className="text-body-lg font-semibold text-gray-900 line-clamp-2 group-hover:text-blue-600 transition-colors">
                      {product.name}
                    </h3>
                    {product.description && (
                      <p className="text-body text-gray-600 line-clamp-2 mt-1">
                        {product.description}
                      </p>
                    )}
                  </div>

                  <div className="flex items-center justify-between mb-3">
                    <span className="text-caption text-gray-500 bg-gray-100 px-2 py-1 rounded">
                      {product.category}
                    </span>
                    <span className="text-caption text-gray-500">
                      Stock: {product.stock_quantity}
                    </span>
                  </div>

                  {/* Tags */}
                  {product.tags && product.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {product.tags.slice(0, 3).map(tag => (
                        <span key={tag} className="badge badge-outline badge-xs">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Price and Add Button */}
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-heading-6 font-bold text-gray-900">
                        {formatPrice(product.price)}
                      </div>
                      {product.taxRate && product.taxRate > 0 && (
                        <div className="text-caption text-gray-500">
                          +{(product.taxRate * 100).toFixed(1)}% tax
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => onAddToCart(product, 1)}
                      disabled={product.stock_quantity === 0}
                      className="btn btn-primary btn-sm group-hover:shadow-lg transition-shadow"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      <span>Add</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ProductList;