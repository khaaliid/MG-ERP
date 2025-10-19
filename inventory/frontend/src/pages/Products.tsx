import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import ProductForm from '../components/ProductForm'
import { productService, Product, CreateProductRequest } from '../services/productService'

const Products = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [showForm, setShowForm] = useState(searchParams.get('action') === 'add')
  const [products, setProducts] = useState<Product[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [formMode, setFormMode] = useState<'add' | 'edit'>('add')

  useEffect(() => {
    // Check if action=add is in URL params
    if (searchParams.get('action') === 'add') {
      setShowForm(true)
    }
  }, [searchParams])

  useEffect(() => {
    loadProducts()
  }, [])

  const loadProducts = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await productService.getProducts()
      setProducts(response.data || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load products')
      console.error('Error loading products:', err)
      setProducts([]) // Ensure products is always an array
    } finally {
      setLoading(false)
    }
  }

  const handleAddProduct = async (data: any) => {
    setSubmitting(true)
    setError(null)
    try {
      const productData: CreateProductRequest = {
        name: data.name,
        description: data.description,
        sku: data.sku,
        barcode: data.barcode,
        costPrice: data.costPrice,
        sellingPrice: data.sellingPrice,
        material: data.material,
        color: data.color,
        season: data.season,
        categoryId: data.categoryId,
        brandId: data.brandId,
        supplierId: data.supplierId,
        sizes: data.sizes
      }

      await productService.createProduct(productData)
      setShowForm(false)
      // Clear the action parameter from URL
      searchParams.delete('action')
      setSearchParams(searchParams)
      await loadProducts() // Refresh the product list
      
      // Show success message (you could add a toast notification here)
      alert('Product added successfully!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add product')
      console.error('Error adding product:', err)
    } finally {
      setSubmitting(false)
    }
  }



  const handleEditProduct = (product: Product) => {
    setEditingProduct(product)
    setFormMode('edit')
    setShowForm(true)
  }

  const handleUpdateProduct = async (data: any) => {
    if (!editingProduct) return
    
    setSubmitting(true)
    setError(null)
    try {
      const productData = {
        name: data.name,
        description: data.description,
        sku: data.sku,
        barcode: data.barcode,
        costPrice: data.costPrice,
        sellingPrice: data.sellingPrice,
        material: data.material,
        color: data.color,
        season: data.season,
        categoryId: data.categoryId || null,
        brandId: data.brandId || null,
        supplierId: data.supplierId || null,
        sizes: data.sizes || []
      }
      
      await productService.updateProduct(editingProduct.id, productData)
      await loadProducts()
      handleCloseForm()
      alert('Product updated successfully!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update product')
      console.error('Error updating product:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteProduct = async (product: Product) => {
    if (!window.confirm(`Are you sure you want to delete "${product.name}"? This action cannot be undone.`)) {
      return
    }

    try {
      setError(null)
      await productService.deleteProduct(product.id)
      await loadProducts()
      alert('Product deleted successfully!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete product')
      console.error('Error deleting product:', err)
    }
  }

  const handleCloseForm = () => {
    setShowForm(false)
    setEditingProduct(null)
    setFormMode('add')
    setError(null)
    // Clear the action parameter from URL when closing form
    if (searchParams.get('action')) {
      searchParams.delete('action')
      setSearchParams(searchParams, { replace: true })
    }
  }

  if (showForm) {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center mb-6">
            <button
              onClick={handleCloseForm}
              className="mr-4 text-gray-600 hover:text-gray-800"
            >
              ← Back to Products
            </button>
            <h1 className="text-2xl font-bold text-gray-900">
              {formMode === 'edit' ? 'Edit Product' : 'Add New Product'}
            </h1>
          </div>
          
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
              <p className="text-red-600">{error}</p>
            </div>
          )}
          
          <ProductForm
            initialData={editingProduct ? {
              name: editingProduct.name,
              description: editingProduct.description || '',
              sku: editingProduct.sku,
              barcode: editingProduct.barcode || '',
              costPrice: editingProduct.costPrice,
              sellingPrice: editingProduct.sellingPrice,
              material: editingProduct.material || '',
              color: editingProduct.color || '',
              season: editingProduct.season || '',
              categoryId: editingProduct.categoryId || '',
              brandId: editingProduct.brandId || '',
              supplierId: editingProduct.supplierId || '',
              sizes: []
            } : undefined}
            onSubmit={formMode === 'edit' ? handleUpdateProduct : handleAddProduct}
            onCancel={handleCloseForm}
            isLoading={submitting}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Products</h1>
          <button
            onClick={() => {
              setFormMode('add')
              setEditingProduct(null)
              setShowForm(true)
            }}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2"
          >
            <span>➕</span>
            <span>Add Product</span>
          </button>
        </div>
        
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-600">{error}</p>
            <button
              onClick={loadProducts}
              className="mt-2 text-blue-600 hover:text-blue-800 underline"
            >
              Try again
            </button>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading products...</p>
          </div>
        ) : (products || []).length === 0 ? (
          <div className="text-center py-12">
            <span className="text-6xl">📦</span>
            <h3 className="text-lg font-medium text-gray-900 mt-4">No products yet</h3>
            <p className="text-gray-600 mt-2">Get started by creating your first product</p>
            <button
              onClick={() => setShowForm(true)}
              className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
            >
              Add Your First Product
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Product
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    SKU
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Stock
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {products.map((product) => (
                  <tr key={product.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{product.name || 'Unnamed Product'}</div>
                        <div className="text-sm text-gray-500">{product.description || 'No description'}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {product.sku || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${(product.sellingPrice || 0).toFixed(2)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                        In Stock
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button 
                        onClick={() => handleEditProduct(product)}
                        className="text-blue-600 hover:text-blue-900 mr-3"
                      >
                        Edit
                      </button>
                      <button 
                        onClick={() => handleDeleteProduct(product)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

export default Products