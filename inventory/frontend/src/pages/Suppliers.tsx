import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { supplierService, Supplier, CreateSupplierRequest, UpdateSupplierRequest } from '../services/supplierService'
import { SupplierForm } from '../components/SupplierForm'

const Suppliers: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams()
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null)
  const [formLoading, setFormLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')

  const loadSuppliers = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await supplierService.getSuppliers()
      setSuppliers(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load suppliers')
      console.error('Error loading suppliers:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSuppliers()
    
    // Check if we should open the add form from URL params
    const action = searchParams.get('action')
    if (action === 'add') {
      setShowForm(true)
      setSearchParams({}) // Clear the action parameter
    }
  }, [searchParams, setSearchParams])

  const handleCreateSupplier = async (data: CreateSupplierRequest) => {
    try {
      setFormLoading(true)
      setError(null)
      await supplierService.createSupplier(data)
      await loadSuppliers()
      setShowForm(false)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create supplier')
      console.error('Error creating supplier:', err)
    } finally {
      setFormLoading(false)
    }
  }

  const handleUpdateSupplier = async (data: UpdateSupplierRequest) => {
    if (!editingSupplier) return
    
    try {
      setFormLoading(true)
      setError(null)
      await supplierService.updateSupplier(editingSupplier.id, data)
      await loadSuppliers()
      setEditingSupplier(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update supplier')
      console.error('Error updating supplier:', err)
    } finally {
      setFormLoading(false)
    }
  }

  const handleDeleteSupplier = async (supplier: Supplier) => {
    if (!window.confirm(`Are you sure you want to delete "${supplier.name}"? This action cannot be undone.`)) {
      return
    }

    try {
      setError(null)
      await supplierService.deleteSupplier(supplier.id)
      await loadSuppliers()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete supplier')
      console.error('Error deleting supplier:', err)
    }
  }

  const handleCloseForm = () => {
    setShowForm(false)
    setEditingSupplier(null)
  }

  const filteredSuppliers = suppliers.filter(supplier =>
    supplier.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (supplier.contactPerson && supplier.contactPerson.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (supplier.email && supplier.email.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Suppliers</h1>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Add Supplier
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <div className="flex-1">
              <input
                type="text"
                placeholder="Search suppliers..."
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <button
              onClick={loadSuppliers}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            >
              Refresh
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Contact Person
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Phone
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Lead Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredSuppliers.map((supplier) => (
                <tr key={supplier.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{supplier.name}</div>
                    {supplier.address && (
                      <div className="text-sm text-gray-500 truncate max-w-xs">{supplier.address}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{supplier.contactPerson || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{supplier.email || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{supplier.phone || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{supplier.leadTimeDays} days</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium space-x-2">
                    <button
                      onClick={() => setEditingSupplier(supplier)}
                      className="text-indigo-600 hover:text-indigo-900"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteSupplier(supplier)}
                      className="text-red-600 hover:text-red-900"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
              {filteredSuppliers.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    {searchTerm ? 'No suppliers match your search.' : 'No suppliers found. Create your first supplier!'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {showForm && (
        <SupplierForm
          onSubmit={handleCreateSupplier}
          onCancel={handleCloseForm}
          isLoading={formLoading}
        />
      )}

      {editingSupplier && (
        <SupplierForm
          initialData={editingSupplier}
          onSubmit={handleUpdateSupplier}
          onCancel={handleCloseForm}
          isLoading={formLoading}
        />
      )}
    </div>
  )
}

export default Suppliers