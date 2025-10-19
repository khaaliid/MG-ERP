import { useState } from 'react'

export interface CategoryFormData {
  name: string
  description: string
  sizeType: 'CLOTHING' | 'NUMERIC' | 'SHOE'
}

interface CategoryFormProps {
  onSubmit: (data: CategoryFormData) => void
  onCancel: () => void
  isLoading?: boolean
}

const CategoryForm = ({ onSubmit, onCancel, isLoading = false }: CategoryFormProps) => {
  const [formData, setFormData] = useState<CategoryFormData>({
    name: '',
    description: '',
    sizeType: 'CLOTHING'
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  const handleInputChange = (field: keyof CategoryFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) newErrors.name = 'Category name is required'
    if (!formData.sizeType) newErrors.sizeType = 'Size type is required'

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validateForm()) {
      onSubmit(formData)
    }
  }

  return (
    <div className="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Add New Category</h2>
        <button
          onClick={onCancel}
          className="text-gray-500 hover:text-gray-700"
        >
          ✕
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Information */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.name ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="e.g., Formal Shirts, Casual Pants"
              disabled={isLoading}
            />
            {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter category description"
              disabled={isLoading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Size Type *
            </label>
            <select
              value={formData.sizeType}
              onChange={(e) => handleInputChange('sizeType', e.target.value as CategoryFormData['sizeType'])}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.sizeType ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={isLoading}
            >
              <option value="CLOTHING">Clothing (S, M, L, XL, XXL)</option>
              <option value="NUMERIC">Numeric (30, 32, 34, 36, etc.)</option>
              <option value="SHOE">Shoe (7, 8, 9, 10, 11, etc.)</option>
            </select>
            {errors.sizeType && <p className="text-red-500 text-sm mt-1">{errors.sizeType}</p>}
            <p className="text-sm text-gray-500 mt-1">
              This determines what size options will be available for products in this category
            </p>
          </div>
        </div>

        {/* Form Actions */}
        <div className="flex justify-end space-x-4 pt-6 border-t">
          <button
            type="button"
            onClick={onCancel}
            className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={isLoading}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            disabled={isLoading}
          >
            {isLoading ? 'Adding...' : 'Add Category'}
          </button>
        </div>
      </form>
    </div>
  )
}

export default CategoryForm