const API_BASE_URL = 'http://localhost:8002/api/v1'

export interface Category {
  id: string
  name: string
  description?: string
  sizeType: 'CLOTHING' | 'NUMERIC' | 'SHOE'
  createdAt: string
  updatedAt: string
}

export interface CreateCategoryRequest {
  name: string
  description?: string
  sizeType: 'CLOTHING' | 'NUMERIC' | 'SHOE'
}

export interface ApiResponse<T> {
  data: T
  message?: string
}

class CategoryService {
  async getCategories(): Promise<ApiResponse<Category[]>> {
    const response = await fetch(`${API_BASE_URL}/categories/`)
    
    if (!response.ok) {
      throw new Error(`Failed to fetch categories: ${response.statusText}`)
    }
    
    const data = await response.json()
    return { data }
  }

  async getCategory(id: string): Promise<ApiResponse<Category>> {
    const response = await fetch(`${API_BASE_URL}/categories/${id}`)
    
    if (!response.ok) {
      throw new Error(`Failed to fetch category: ${response.statusText}`)
    }
    
    const data = await response.json()
    return { data }
  }

  async createCategory(categoryData: CreateCategoryRequest): Promise<ApiResponse<Category>> {
    const response = await fetch(`${API_BASE_URL}/categories/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        name: categoryData.name,
        description: categoryData.description || '',
        size_type: categoryData.sizeType  // Convert to snake_case for backend
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `Failed to create category: ${response.statusText}`)
    }
    
    const data = await response.json()
    return { data, message: 'Category created successfully!' }
  }

  async updateCategory(id: string, categoryData: Partial<CreateCategoryRequest>): Promise<ApiResponse<Category>> {
    const response = await fetch(`${API_BASE_URL}/categories/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...categoryData,
        size_type: categoryData.sizeType  // Convert to snake_case for backend
      })
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `Failed to update category: ${response.statusText}`)
    }
    
    const data = await response.json()
    return { data, message: 'Category updated successfully!' }
  }

  async deleteCategory(id: string): Promise<ApiResponse<void>> {
    const response = await fetch(`${API_BASE_URL}/categories/${id}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
      throw new Error(errorData.detail || `Failed to delete category: ${response.statusText}`)
    }
    
    return { data: undefined, message: 'Category deleted successfully!' }
  }
}

export const categoryService = new CategoryService()