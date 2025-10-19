const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002/api/v1'

export interface Supplier {
  id: string
  name: string
  contactPerson?: string
  email?: string
  phone?: string
  address?: string
  leadTimeDays: number
  createdAt: string
  updatedAt: string
}

export interface CreateSupplierRequest {
  name: string
  contactPerson?: string
  email?: string
  phone?: string
  address?: string
  leadTimeDays: number
}

export interface UpdateSupplierRequest {
  name?: string
  contactPerson?: string
  email?: string
  phone?: string
  address?: string
  leadTimeDays?: number
}

class SupplierService {
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    const response = await fetch(url, config)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }

    return response.json()
  }

  async getSuppliers(): Promise<Supplier[]> {
    return this.request<Supplier[]>('/suppliers/')
  }

  async getSupplier(id: string): Promise<Supplier> {
    return this.request<Supplier>(`/suppliers/${id}`)
  }

  async createSupplier(supplier: CreateSupplierRequest): Promise<Supplier> {
    return this.request<Supplier>('/suppliers/', {
      method: 'POST',
      body: JSON.stringify(supplier),
    })
  }

  async updateSupplier(id: string, supplier: UpdateSupplierRequest): Promise<Supplier> {
    return this.request<Supplier>(`/suppliers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(supplier),
    })
  }

  async deleteSupplier(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/suppliers/${id}`, {
      method: 'DELETE',
    })
  }
}

export const supplierService = new SupplierService()