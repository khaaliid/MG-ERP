import { useState, useEffect } from 'react'

interface ProductFormData {
  name: string
  description: string
  sku: string
  barcode: string
  categoryId: string
  brandId: string
  supplierId: string
  costPrice: number
  sellingPrice: number
  material: string
  color: string
  season: string
  sizes: Array<{
    size: string
    quantity: number
    reorderLevel: number
    maxStockLevel: number
    location: string
  }>
}

interface Category {
  id: string
  name: string
  description?: string
}

interface Brand {
  id: string
  name: string
  description?: string
}

interface Supplier {
  id: string
  name: string
  contactPerson?: string
}

interface ProductFormProps {
  initialData?: Partial<ProductFormData> & { id?: string }
  onSubmit: (data: ProductFormData) => void
  onCancel: () => void
  isLoading?: boolean
}

const ProductForm = ({ initialData, onSubmit, onCancel, isLoading = false }: ProductFormProps) => {
  const [categories, setCategories] = useState<Category[]>([])
  const [brands, setBrands] = useState<Brand[]>([])
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [loadingData, setLoadingData] = useState(true)
  
  const [formData, setFormData] = useState<ProductFormData>({
    name: initialData?.name || '',
    description: initialData?.description || '',
    sku: initialData?.sku || '',
    barcode: initialData?.barcode || '',
    categoryId: initialData?.categoryId || '',
    brandId: initialData?.brandId || '',
    supplierId: initialData?.supplierId || '',
    costPrice: initialData?.costPrice || 0,
    sellingPrice: initialData?.sellingPrice || 0,
    material: initialData?.material || '',
    color: initialData?.color || '',
    season: initialData?.season || '',
    sizes: initialData?.sizes || [{ size: '', quantity: 0, reorderLevel: 5, maxStockLevel: 100, location: '' }]
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  // Load dropdown data on component mount
  useEffect(() => {
    const loadFormData = async () => {
      try {
        setLoadingData(true)
        const baseUrl = 'http://localhost:8002/api/v1'
        
        // Load categories, brands, and suppliers in parallel
        const [categoriesRes, brandsRes, suppliersRes] = await Promise.all([
          fetch(`${baseUrl}/categories/`),
          fetch(`${baseUrl}/brands/`),
          fetch(`${baseUrl}/suppliers/`)
        ])
        
        if (categoriesRes.ok) {
          const categoriesData = await categoriesRes.json()
          setCategories(categoriesData)
        }
        
        if (brandsRes.ok) {
          const brandsData = await brandsRes.json()
          setBrands(brandsData)
        }
        
        if (suppliersRes.ok) {
          const suppliersData = await suppliersRes.json()
          setSuppliers(suppliersData)
        }
        
      } catch (error) {
        console.error('Failed to load form data:', error)
      } finally {
        setLoadingData(false)
      }
    }
    
    loadFormData()
  }, [])

  const handleInputChange = (field: keyof ProductFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }))
    }
  }

  const handleSizeChange = (index: number, field: string, value: any) => {
    const newSizes = [...formData.sizes]
    newSizes[index] = { ...newSizes[index], [field]: value }
    setFormData(prev => ({ ...prev, sizes: newSizes }))
  }

  const addSizeRow = () => {
    setFormData(prev => ({
      ...prev,
      sizes: [...prev.sizes, { size: '', quantity: 0, reorderLevel: 5, maxStockLevel: 100, location: '' }]
    }))
  }

  const removeSizeRow = (index: number) => {
    if (formData.sizes.length > 1) {
      setFormData(prev => ({
        ...prev,
        sizes: prev.sizes.filter((_, i) => i !== index)
      }))
    }
  }

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) newErrors.name = 'Product name is required'
    if (!formData.sku.trim()) newErrors.sku = 'SKU is required'
    if (!formData.categoryId.trim()) newErrors.categoryId = 'Category is required'
    if (formData.costPrice <= 0) newErrors.costPrice = 'Cost price must be greater than 0'
    if (formData.sellingPrice <= 0) newErrors.sellingPrice = 'Selling price must be greater than 0'
    if (formData.sellingPrice <= formData.costPrice) {
      newErrors.sellingPrice = 'Selling price must be greater than cost price'
    }

    // Validate sizes
    formData.sizes.forEach((size, index) => {
      if (!size.size.trim()) {
        newErrors[`size_${index}`] = 'Size is required'
      }
      if (size.quantity < 0) {
        newErrors[`quantity_${index}`] = 'Quantity cannot be negative'
      }
    })

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (validateForm()) {
      onSubmit(formData)
    }
  }

  const seasons = ['Spring/Summer', 'Fall/Winter', 'All Season']
  const commonSizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL', '28', '30', '32', '34', '36', '38', '40', '42']

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Basic Information */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Product Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.name ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter product name"
            />
            {errors.name && <p className="text-red-500 text-sm mt-1">{errors.name}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              SKU *
            </label>
            <input
              type="text"
              value={formData.sku}
              onChange={(e) => handleInputChange('sku', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.sku ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter SKU"
            />
            {errors.sku && <p className="text-red-500 text-sm mt-1">{errors.sku}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Barcode
            </label>
            <input
              type="text"
              value={formData.barcode}
              onChange={(e) => handleInputChange('barcode', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter barcode"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Category
            </label>
            <select
              value={formData.categoryId}
              onChange={(e) => handleInputChange('categoryId', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.categoryId ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={loadingData}
            >
              <option value="">{loadingData ? 'Loading categories...' : 'Select category'}</option>
              {categories.map(category => (
                <option key={category.id} value={category.id}>
                  {category.name}
                </option>
              ))}
            </select>
            {errors.categoryId && <p className="text-red-500 text-sm mt-1">{errors.categoryId}</p>}
          </div>
        </div>

        {/* Brand and Supplier Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Brand
            </label>
            <select
              value={formData.brandId}
              onChange={(e) => handleInputChange('brandId', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loadingData}
            >
              <option value="">{loadingData ? 'Loading brands...' : 'Select brand (optional)'}</option>
              {brands.map(brand => (
                <option key={brand.id} value={brand.id}>
                  {brand.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Supplier
            </label>
            <select
              value={formData.supplierId}
              onChange={(e) => handleInputChange('supplierId', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loadingData}
            >
              <option value="">{loadingData ? 'Loading suppliers...' : 'Select supplier (optional)'}</option>
              {suppliers.map(supplier => (
                <option key={supplier.id} value={supplier.id}>
                  {supplier.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <textarea
            value={formData.description}
            onChange={(e) => handleInputChange('description', e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter product description"
          />
        </div>
      </div>

      {/* Product Details */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Product Details</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Material
            </label>
            <input
              type="text"
              value={formData.material}
              onChange={(e) => handleInputChange('material', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Cotton, Wool, Polyester"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Color
            </label>
            <input
              type="text"
              value={formData.color}
              onChange={(e) => handleInputChange('color', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Blue, Black, Navy"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Season
            </label>
            <select
              value={formData.season}
              onChange={(e) => handleInputChange('season', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select season</option>
              {seasons.map(season => (
                <option key={season} value={season}>{season}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Pricing */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Pricing</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Cost Price *
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.costPrice}
              onChange={(e) => handleInputChange('costPrice', parseFloat(e.target.value) || 0)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.costPrice ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="0.00"
            />
            {errors.costPrice && <p className="text-red-500 text-sm mt-1">{errors.costPrice}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Selling Price *
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.sellingPrice}
              onChange={(e) => handleInputChange('sellingPrice', parseFloat(e.target.value) || 0)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.sellingPrice ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="0.00"
            />
            {errors.sellingPrice && <p className="text-red-500 text-sm mt-1">{errors.sellingPrice}</p>}
          </div>
        </div>
        
        {formData.costPrice > 0 && formData.sellingPrice > 0 && (
          <div className="mt-2 p-3 bg-blue-50 rounded-md">
            <p className="text-sm text-blue-700">
              Profit Margin: ${(formData.sellingPrice - formData.costPrice).toFixed(2)} 
              ({(((formData.sellingPrice - formData.costPrice) / formData.costPrice) * 100).toFixed(1)}%)
            </p>
          </div>
        )}
      </div>

      {/* Stock Information */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Stock Information</h3>
          <button
            type="button"
            onClick={addSizeRow}
            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
          >
            Add Size
          </button>
        </div>

        <div className="space-y-3">
          {formData.sizes.map((sizeItem, index) => (
            <div key={index} className="grid grid-cols-2 md:grid-cols-6 gap-2 items-start">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Size *</label>
                <select
                  value={sizeItem.size}
                  onChange={(e) => handleSizeChange(index, 'size', e.target.value)}
                  className={`w-full px-2 py-1 text-sm border rounded focus:outline-none focus:ring-1 focus:ring-blue-500 ${
                    errors[`size_${index}`] ? 'border-red-500' : 'border-gray-300'
                  }`}
                >
                  <option value="">Select</option>
                  {commonSizes.map(size => (
                    <option key={size} value={size}>{size}</option>
                  ))}
                </select>
                {errors[`size_${index}`] && (
                  <p className="text-red-500 text-xs mt-1">{errors[`size_${index}`]}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Quantity</label>
                <input
                  type="number"
                  min="0"
                  value={sizeItem.quantity}
                  onChange={(e) => handleSizeChange(index, 'quantity', parseInt(e.target.value) || 0)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Reorder Level</label>
                <input
                  type="number"
                  min="0"
                  value={sizeItem.reorderLevel}
                  onChange={(e) => handleSizeChange(index, 'reorderLevel', parseInt(e.target.value) || 0)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Max Stock</label>
                <input
                  type="number"
                  min="0"
                  value={sizeItem.maxStockLevel}
                  onChange={(e) => handleSizeChange(index, 'maxStockLevel', parseInt(e.target.value) || 0)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Location</label>
                <input
                  type="text"
                  value={sizeItem.location}
                  onChange={(e) => handleSizeChange(index, 'location', e.target.value)}
                  className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  placeholder="Shelf/Rack"
                />
              </div>

              <div className="flex items-end">
                {formData.sizes.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeSizeRow(index)}
                    className="text-red-600 hover:text-red-800 text-sm mt-5"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Form Actions */}
      <div className="flex justify-end space-x-3 pt-6 border-t">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
          disabled={isLoading}
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading 
            ? (initialData?.id ? 'Updating Product...' : 'Adding Product...')
            : (initialData?.id ? 'Update Product' : 'Add Product')
          }
        </button>
      </div>
    </form>
  )
}

export default ProductForm