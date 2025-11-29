import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { productService, Product } from '../services/productService'

const Dashboard = () => {
  const navigate = useNavigate()
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await productService.getProducts()
      setProducts(response.data || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data')
      console.error('Error loading dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  // Calculate statistics from products data
  const totalProducts = products.length
  const inStockProducts = products.filter(() => {
    // Assuming we need to check stock levels - this might need adjustment based on actual data structure
    return true // For now, assume all products are in stock
  }).length
  const lowStockProducts = 0 // Would need stock data to calculate
  const outOfStockProducts = 0 // Would need stock data to calculate

  const handleAddProduct = () => {
    navigate('/products?action=add')
  }

  const handleAddCategory = () => {
    navigate('/categories?action=add')
  }

  const handleAddBrand = () => {
    navigate('/brands?action=add')
  }

  const handleAddSupplier = () => {
    navigate('/suppliers?action=add')
  }

  const handleCreatePurchaseOrder = () => {
    navigate('/purchase-orders?action=create')
  }

  const handleViewReports = () => {
    navigate('/stock-movements')
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Inventory Dashboard</h1>
        <p className="text-gray-600">Welcome to the MG-ERP Inventory Management System</p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <span className="text-red-400 text-xl">⚠️</span>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading dashboard data</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
              <button 
                onClick={loadDashboardData}
                className="mt-2 text-sm text-red-800 underline hover:text-red-900"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-500 rounded-lg">
              <span className="text-white text-2xl">📦</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Products</p>
              <p className="text-2xl font-semibold text-gray-900">
                {loading ? "..." : totalProducts}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-500 rounded-lg">
              <span className="text-white text-2xl">✅</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">In Stock</p>
              <p className="text-2xl font-semibold text-gray-900">
                {loading ? "..." : inStockProducts}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-500 rounded-lg">
              <span className="text-white text-2xl">⚠️</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Low Stock</p>
              <p className="text-2xl font-semibold text-gray-900">
                {loading ? "..." : lowStockProducts}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-2 bg-red-500 rounded-lg">
              <span className="text-white text-2xl">❌</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Out of Stock</p>
              <p className="text-2xl font-semibold text-gray-900">
                {loading ? "..." : outOfStockProducts}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <button 
            onClick={handleAddProduct}
            className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left transition-colors"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">➕</span>
              <div>
                <h3 className="font-medium">Add Product</h3>
                <p className="text-sm text-gray-600">Create a new product entry</p>
              </div>
            </div>
          </button>
          
          <button 
            onClick={handleAddCategory}
            className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left transition-colors"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">🏷️</span>
              <div>
                <h3 className="font-medium">Add Category</h3>
                <p className="text-sm text-gray-600">Create a new product category</p>
              </div>
            </div>
          </button>
          
          <button 
            onClick={handleAddBrand}
            className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left transition-colors"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">🏪</span>
              <div>
                <h3 className="font-medium">Add Brand</h3>
                <p className="text-sm text-gray-600">Create a new product brand</p>
              </div>
            </div>
          </button>
          
          <button 
            onClick={handleAddSupplier}
            className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left transition-colors"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">🏢</span>
              <div>
                <h3 className="font-medium">Add Supplier</h3>
                <p className="text-sm text-gray-600">Create a new supplier entry</p>
              </div>
            </div>
          </button>
          
          <button 
            onClick={handleCreatePurchaseOrder}
            className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left transition-colors"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">📋</span>
              <div>
                <h3 className="font-medium">Create Purchase Order</h3>
                <p className="text-sm text-gray-600">Order from suppliers</p>
              </div>
            </div>
          </button>
          
          <button 
            onClick={handleViewReports}
            className="p-4 border border-gray-300 rounded-lg hover:bg-gray-50 text-left transition-colors"
          >
            <div className="flex items-center">
              <span className="text-2xl mr-3">📊</span>
              <div>
                <h3 className="font-medium">Stock Report</h3>
                <p className="text-sm text-gray-600">View inventory reports</p>
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  )
}

export default Dashboard