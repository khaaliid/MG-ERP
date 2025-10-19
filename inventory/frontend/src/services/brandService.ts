const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002/api/v1'

export interface Brand {
  id: string
  name: string
  description?: string
  contactInfo?: string
  createdAt: string
  updatedAt: string
}

export interface CreateBrandRequest {
  name: string
  description?: string
  contactInfo?: string
}

export interface ApiResponse<T> {
  data: T
  message?: string
}

class BrandService {
  async getBrands(): Promise<ApiResponse<Brand[]>> {
    const response = await fetch(`${API_BASE_URL}/brands/`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `Failed to fetch brands: ${response.statusText}`)
    }
    
    const data = await response.json()
    return { data, message: 'Brands loaded successfully!' }
  }

  async getBrand(id: string): Promise<ApiResponse<Brand>> {
    const response = await fetch(`${API_BASE_URL}/brands/${id}`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `Failed to fetch brand: ${response.statusText}`)
    }
    
    const data = await response.json()
    return { data, message: 'Brand loaded successfully!' }
  }

  async createBrand(brandData: CreateBrandRequest): Promise<ApiResponse<Brand>> {
    const response = await fetch(`${API_BASE_URL}/brands/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: brandData.name,
        description: brandData.description || '',
        contact_info: brandData.contactInfo || ''
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `Failed to create brand: ${response.statusText}`)
    }
    
    const data = await response.json()
    return { data, message: 'Brand created successfully!' }
  }

  async updateBrand(id: string, brandData: Partial<CreateBrandRequest>): Promise<ApiResponse<Brand>> {
    const updateData: any = {}
    if (brandData.name !== undefined) updateData.name = brandData.name
    if (brandData.description !== undefined) updateData.description = brandData.description
    if (brandData.contactInfo !== undefined) updateData.contact_info = brandData.contactInfo

    const response = await fetch(`${API_BASE_URL}/brands/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updateData)
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `Failed to update brand: ${response.statusText}`)
    }
    
    const data = await response.json()
    return { data, message: 'Brand updated successfully!' }
  }

  async deleteBrand(id: string): Promise<ApiResponse<void>> {
    const response = await fetch(`${API_BASE_URL}/brands/${id}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `Failed to delete brand: ${response.statusText}`)
    }
    
    return { data: undefined, message: 'Brand deleted successfully!' }
  }
}

export const brandService = new BrandService()