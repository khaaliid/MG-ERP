const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8002/api/v1'

export interface Product {
  id: string
  name: string
  description?: string
  sku: string
  barcode?: string
  costPrice: number
  sellingPrice: number
  material?: string
  color?: string
  season?: string
  categoryId?: string
  brandId?: string
  supplierId?: string
  createdAt: string
  updatedAt: string
}

export interface StockItem {
  id: string
  productId: string
  size: string
  quantity: number
  reorderLevel: number
  maxStockLevel: number
  location?: string
}

export interface CreateProductRequest {
  name: string
  description?: string
  sku: string
  barcode?: string
  costPrice: number
  sellingPrice: number
  material?: string
  color?: string
  season?: string
  categoryId?: string
  brandId?: string
  supplierId?: string
  sizes: Array<{
    size: string
    quantity: number
    reorderLevel: number
    maxStockLevel: number
    location?: string
  }>
}

export interface ApiResponse<T> {
  data: T
  message?: string
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  limit: number
}

class ProductService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      let errorMessage = `HTTP error! status: ${response.status}`
      try {
        const errorData = await response.json()
        errorMessage = errorData.detail || errorData.message || errorMessage
      } catch {
        // If we can't parse the error response, use the default message
      }
      throw new Error(errorMessage)
    }

    return response.json()
  }

  async getProducts(params?: {
    page?: number
    limit?: number
    search?: string
    categoryId?: string
    brandId?: string
  }): Promise<PaginatedResponse<Product>> {
    const searchParams = new URLSearchParams()
    
    if (params?.page) searchParams.append('page', params.page.toString())
    if (params?.limit) searchParams.append('limit', params.limit.toString())
    if (params?.search) searchParams.append('search', params.search)
    if (params?.categoryId) searchParams.append('category_id', params.categoryId)
    if (params?.brandId) searchParams.append('brand_id', params.brandId)

    const query = searchParams.toString()
    const endpoint = `/products${query ? `?${query}` : ''}`
    
    return this.request<PaginatedResponse<Product>>(endpoint)
  }

  async getProduct(id: string): Promise<ApiResponse<Product>> {
    return this.request<ApiResponse<Product>>(`/products/${id}`)
  }

  async createProduct(data: CreateProductRequest): Promise<ApiResponse<Product>> {
    return this.request<ApiResponse<Product>>('/products', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async updateProduct(id: string, data: Partial<CreateProductRequest>): Promise<ApiResponse<Product>> {
    return this.request<ApiResponse<Product>>(`/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteProduct(id: string): Promise<ApiResponse<void>> {
    return this.request<ApiResponse<void>>(`/products/${id}`, {
      method: 'DELETE',
    })
  }

  async getProductStock(productId: string): Promise<ApiResponse<StockItem[]>> {
    return this.request<ApiResponse<StockItem[]>>(`/products/${productId}/stock`)
  }

  async updateStock(productId: string, size: string, quantity: number): Promise<ApiResponse<StockItem>> {
    return this.request<ApiResponse<StockItem>>(`/products/${productId}/stock/${size}`, {
      method: 'PUT',
      body: JSON.stringify({ quantity }),
    })
  }

  // Categories
  async getCategories(): Promise<ApiResponse<Array<{ id: string; name: string }>>> {
    return this.request<ApiResponse<Array<{ id: string; name: string }>>>('/categories')
  }

  // Brands
  async getBrands(): Promise<ApiResponse<Array<{ id: string; name: string }>>> {
    return this.request<ApiResponse<Array<{ id: string; name: string }>>>('/brands')
  }

  // Suppliers
  async getSuppliers(): Promise<ApiResponse<Array<{ id: string; name: string }>>> {
    return this.request<ApiResponse<Array<{ id: string; name: string }>>>('/suppliers')
  }
}

export const productService = new ProductService()
export default productService