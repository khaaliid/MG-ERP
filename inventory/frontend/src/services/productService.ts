import { baseApiService } from "./baseApiService";

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
  private basePath = "/products";

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
    const endpoint = `${this.basePath}${query ? `?${query}` : ''}`
    
    return baseApiService.get<PaginatedResponse<Product>>(endpoint)
  }

  async getProduct(id: string): Promise<ApiResponse<Product>> {
    return baseApiService.get<ApiResponse<Product>>(`${this.basePath}/${id}`)
  }

  async createProduct(data: CreateProductRequest): Promise<ApiResponse<Product>> {
    return baseApiService.post<ApiResponse<Product>>(this.basePath, data)
  }

  async updateProduct(id: string, data: Partial<CreateProductRequest>): Promise<ApiResponse<Product>> {
    return baseApiService.put<ApiResponse<Product>>(`${this.basePath}/${id}`, data)
  }

  async deleteProduct(id: string): Promise<void> {
    return baseApiService.delete(`${this.basePath}/${id}`)
  }

  async getProductStock(productId: string): Promise<ApiResponse<StockItem[]>> {
    return baseApiService.get<ApiResponse<StockItem[]>>(`${this.basePath}/${productId}/stock`)
  }

  async updateStock(productId: string, size: string, quantity: number): Promise<ApiResponse<StockItem>> {
    return baseApiService.put<ApiResponse<StockItem>>(`${this.basePath}/${productId}/stock/${size}`, { quantity })
  }

  // Categories
  async getCategories(): Promise<ApiResponse<Array<{ id: string; name: string }>>> {
    return baseApiService.get<ApiResponse<Array<{ id: string; name: string }>>>('/categories')
  }

  // Brands
  async getBrands(): Promise<ApiResponse<Array<{ id: string; name: string }>>> {
    return baseApiService.get<ApiResponse<Array<{ id: string; name: string }>>>('/brands')
  }

  // Suppliers
  async getSuppliers(): Promise<ApiResponse<Array<{ id: string; name: string }>>> {
    return baseApiService.get<ApiResponse<Array<{ id: string; name: string }>>>('/suppliers')
  }
}

export const productService = new ProductService()
export default productService