import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import CategoryForm, { CategoryFormData } from '../components/CategoryForm'
import { categoryService, Category, CreateCategoryRequest } from '../services/categoryService'

const Categories = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [showForm, setShowForm] = useState(searchParams.get('action') === 'add')
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Check if action=add is in URL params
    if (searchParams.get('action') === 'add') {
      setShowForm(true)
    }
  }, [searchParams])

  useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await categoryService.getCategories()
      setCategories(response.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load categories')
      console.error('Error loading categories:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAddCategory = async (data: CategoryFormData) => {
    setSubmitting(true)
    setError(null)
    
    try {
      const categoryData: CreateCategoryRequest = {
        name: data.name,
        description: data.description,
        sizeType: data.sizeType
      }

      await categoryService.createCategory(categoryData)
      setShowForm(false)
      // Clear the action parameter from URL
      searchParams.delete('action')
      setSearchParams(searchParams)
      await loadCategories() // Refresh the category list
      
      // Show success message (you could add a toast notification here)
      alert('Category added successfully!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add category')
      console.error('Error adding category:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancelAdd = () => {
    setShowForm(false)
    setError(null)
    // Clear the action parameter from URL
    searchParams.delete('action')
    setSearchParams(searchParams)
  }

  const getSizeTypeLabel = (sizeType: string) => {
    switch (sizeType) {
      case 'CLOTHING': return 'Clothing (S, M, L, XL)'
      case 'NUMERIC': return 'Numeric (30, 32, 34)'
      case 'SHOE': return 'Shoe (7, 8, 9, 10)'
      default: return sizeType
    }
  }

  if (showForm) {
    return (
      <div className="space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <p className="text-red-800">{error}</p>
          </div>
        )}
        <CategoryForm
          onSubmit={handleAddCategory}
          onCancel={handleCancelAdd}
          isLoading={submitting}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Categories</h1>
          <p className="text-gray-600 mt-1">Manage product categories and their size types</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Add Category
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-2 text-gray-600">Loading categories...</span>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {categories.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-6xl mb-4">🏷️</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No categories yet</h3>
              <p className="text-gray-600 mb-4">Create your first category to start organizing products</p>
              <button
                onClick={() => setShowForm(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Add First Category
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Description
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Size Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {categories.map((category) => (
                    <tr key={category.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">{category.name}</div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-600">
                          {category.description || 'No description'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {getSizeTypeLabel(category.sizeType)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(category.createdAt).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button className="text-blue-600 hover:text-blue-900 mr-4">
                          Edit
                        </button>
                        <button className="text-red-600 hover:text-red-900">
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
      )}
    </div>
  )
}

export default Categories