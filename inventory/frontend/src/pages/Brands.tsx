import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import BrandForm, { BrandFormData } from '../components/BrandForm'
import { brandService, Brand, CreateBrandRequest } from '../services/brandService'

const Brands = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [showForm, setShowForm] = useState(searchParams.get('action') === 'add')
  const [brands, setBrands] = useState<Brand[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editingBrand, setEditingBrand] = useState<Brand | null>(null)

  useEffect(() => {
    // Check if action=add is in URL params
    if (searchParams.get('action') === 'add') {
      setShowForm(true)
    }
  }, [searchParams])

  useEffect(() => {
    loadBrands()
  }, [])

  const loadBrands = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await brandService.getBrands()
      setBrands(response.data || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load brands')
      console.error('Error loading brands:', err)
      setBrands([]) // Ensure brands is always an array
    } finally {
      setLoading(false)
    }
  }

  const handleAddBrand = async (data: BrandFormData) => {
    setSubmitting(true)
    setError(null)
    
    try {
      const brandData: CreateBrandRequest = {
        name: data.name,
        description: data.description,
        contactInfo: data.contactInfo
      }

      await brandService.createBrand(brandData)
      setShowForm(false)
      // Clear the action parameter from URL
      searchParams.delete('action')
      setSearchParams(searchParams)
      await loadBrands() // Refresh the brand list
      
      // Show success message (you could add a toast notification here)
      alert('Brand added successfully!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add brand')
      console.error('Error adding brand:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const handleEditBrand = async (data: BrandFormData) => {
    if (!editingBrand) return
    
    setSubmitting(true)
    setError(null)
    
    try {
      await brandService.updateBrand(editingBrand.id, {
        name: data.name,
        description: data.description,
        contactInfo: data.contactInfo
      })
      
      setEditingBrand(null)
      await loadBrands() // Refresh the brand list
      
      alert('Brand updated successfully!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update brand')
      console.error('Error updating brand:', err)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteBrand = async (brandId: string) => {
    if (!confirm('Are you sure you want to delete this brand?')) {
      return
    }

    try {
      await brandService.deleteBrand(brandId)
      await loadBrands() // Refresh the brand list
      alert('Brand deleted successfully!')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete brand')
      console.error('Error deleting brand:', err)
    }
  }

  const handleCancel = () => {
    setShowForm(false)
    setEditingBrand(null)
    // Clear the action parameter from URL
    searchParams.delete('action')
    setSearchParams(searchParams)
    setError(null)
  }

  const startEdit = (brand: Brand) => {
    setEditingBrand(brand)
    setShowForm(true)
  }

  if (showForm || editingBrand) {
    return (
      <div className="space-y-6">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}
        <BrandForm
          onSubmit={editingBrand ? handleEditBrand : handleAddBrand}
          onCancel={handleCancel}
          isLoading={submitting}
          initialData={editingBrand ? {
            name: editingBrand.name,
            description: editingBrand.description || '',
            contactInfo: editingBrand.contactInfo || ''
          } : undefined}
        />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Brands</h1>
          <button
            onClick={() => setShowForm(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center"
          >
            <span className="text-lg mr-2">+</span>
            Add Brand
          </button>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading brands...</p>
          </div>
        ) : (brands || []).length === 0 ? (
          <div className="text-center py-12">
            <span className="text-6xl">🏷️</span>
            <h3 className="text-lg font-medium text-gray-900 mt-4">No brands yet</h3>
            <p className="text-gray-600 mt-2">Get started by creating your first brand</p>
            <button
              onClick={() => setShowForm(true)}
              className="mt-4 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
            >
              Add Brand
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {brands.map((brand) => (
              <div key={brand.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-gray-900">{brand.name}</h3>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => startEdit(brand)}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                      title="Edit brand"
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => handleDeleteBrand(brand.id)}
                      className="text-red-600 hover:text-red-800 text-sm"
                      title="Delete brand"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
                
                {brand.description && (
                  <p className="text-gray-600 text-sm mb-2">{brand.description}</p>
                )}
                
                {brand.contactInfo && (
                  <div className="text-xs text-gray-500">
                    <strong>Contact:</strong> {brand.contactInfo}
                  </div>
                )}
                
                <div className="text-xs text-gray-400 mt-2">
                  Created: {new Date(brand.createdAt).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default Brands