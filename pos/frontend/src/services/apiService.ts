/**
 * API Service for POS System with Authentication
 * Handles communication with the POS backend and manages JWT tokens
 */

const API_BASE_URL = 'http://localhost:8001/api/v1';
const AUTH_BASE_URL = 'http://localhost:8004/api/v1/auth';

export interface Product {
  id: string;
  name: string;
  price: number;
  sku: string;
  description?: string;
  category?: {
    id: string;
    name: string;
  };
  brand?: {
    id: string;
    name: string;
  };
  stock_quantity?: number;
  sizes?: (string | { size: string; quantity?: number; reorder_level?: number; max_stock_level?: number; })[];
  is_active?: boolean;
}

export interface Category {
  id: string;
  name: string;
  description?: string;
}

export interface Brand {
  id: string;
  name: string;
  description?: string;
}

export interface ProductsResponse {
  data: Product[];
  total: number;
  page: number;
  limit: number;
}

export interface SaleItem {
  product_id: string;
  quantity: number;
  unit_price: number;
  size?: string;
}

export interface SaleRequest {
  items: SaleItem[];
  customer_name?: string;
  payment_method: 'cash' | 'card' | 'wallet';
  tendered_amount?: number;
  discount_amount?: number;
  tax_rate?: number;
  notes?: string;
}

export interface Sale {
  id: string;
  sale_number: string;
  items: SaleItem[];
  subtotal: number;
  tax_amount: number;
  discount_amount: number;
  total_amount: number;
  payment_method: string;
  tendered_amount?: number;
  change_amount?: number;
  customer_name?: string;
  notes?: string;
  cashier?: string;
  created_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    username: string;
    full_name: string;
    role: string;
    is_active: boolean;
  };
}

export interface User {
  id: string;
  username: string;
  full_name: string;
  role: string;
  is_active: boolean;
}

class APIService {
  private baseURL: string;
  private authURL: string;
  private token: string | null = null;

  constructor(baseURL: string = API_BASE_URL, authURL: string = AUTH_BASE_URL) {
    this.baseURL = baseURL;
    this.authURL = authURL;
    this.loadTokenFromStorage();
  }

  private loadTokenFromStorage(): void {
    this.token = localStorage.getItem('pos_auth_token');
  }

  // Public method to reload token from storage (e.g., after login)
  reloadToken(): void {
    this.loadTokenFromStorage();
  }

  private saveTokenToStorage(token: string): void {
    this.token = token;
    localStorage.setItem('pos_auth_token', token);
  }

  private clearTokenFromStorage(): void {
    this.token = null;
    localStorage.removeItem('pos_auth_token');
    localStorage.removeItem('pos_current_user');
  }

  private getAuthHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  }

  private async fetchWithErrorHandling<T>(url: string, options?: RequestInit): Promise<T> {
    try {
      // Attempt to reload token if not in memory but present in storage
      if (!this.token) {
        this.reloadToken();
      }
      const response = await fetch(url, {
        ...options,
        headers: {
          ...this.getAuthHeaders(),
          ...options?.headers,
        },
      });

      if (response.status === 401) {
        // Only clear token if the failure is from auth endpoints (profile/refresh/login scope)
        const isAuthEndpoint = /\/auth\//.test(url);
        if (isAuthEndpoint) {
          this.clearTokenFromStorage();
        }
        const errorBody = await response.text().catch(() => '');
        // Force a full page reload to trigger fresh auth flow / route guards
        // Delay to ensure caller's error handling still runs
        setTimeout(() => {
          try {
            // Prefer redirect to login explicitly
            window.location.href = '/login';
          } catch {
            window.location.reload();
          }
        }, 50);
        throw new Error('Authentication required (401). ' + (errorBody || '')); 
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('Network error occurred');
    }
  }

  // Authentication APIs
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    // Convert username to email format if needed (for compatibility with auth service)
    const email = credentials.username.includes('@') ? credentials.username : `${credentials.username}@mg-erp.com`;
    
    const loginData = {
      email: email,
      password: credentials.password
    };

    try {
      const response = await fetch(`${this.authURL}/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
        throw new Error(errorData.detail || 'Invalid credentials');
      }

      const loginResponse = await response.json();
      this.saveTokenToStorage(loginResponse.access_token);
      
      // Save user info to localStorage for easy access
      localStorage.setItem('pos_current_user', JSON.stringify(loginResponse.user));
      
      return loginResponse;
    } catch (error) {
      throw error;
    }
  }

  async logout(): Promise<void> {
    this.clearTokenFromStorage();
  }

  async getCurrentUser(): Promise<User | null> {
    if (!this.token) {
      return null;
    }

    try {
      return await this.fetchWithErrorHandling<User>(`${this.authURL}/profile`);
    } catch (error) {
      // If profile fetch fails, clear auth state
      this.clearTokenFromStorage();
      return null;
    }
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  getCurrentUserFromStorage(): User | null {
    const userStr = localStorage.getItem('pos_current_user');
    if (userStr) {
      try {
        return JSON.parse(userStr);
      } catch {
        return null;
      }
    }
    return null;
  }

  // Product APIs
  async getProducts(
    page: number = 1,
    limit: number = 100,
    search?: string,
    categoryId?: string,
    brandId?: string
  ): Promise<ProductsResponse> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });

    if (search) params.append('search', search);
    if (categoryId) params.append('category_id', categoryId);
    if (brandId) params.append('brand_id', brandId);

    const url = `${this.baseURL}/products/?${params.toString()}`;
    const result = await this.fetchWithErrorHandling<any>(url);
    // If backend returned a raw array of products, wrap it to expected shape
    if (Array.isArray(result)) {
      return {
        data: result,
        total: result.length,
        page,
        limit
      };
    }
    // If result lacks data but has items list under another key, attempt to adapt
    if (result && !result.data) {
      const possible = result.products || result.items;
      if (Array.isArray(possible)) {
        return {
          data: possible,
          total: possible.length,
          page,
          limit
        };
      }
    }
    return result as ProductsResponse;
  }

  async searchProducts(query: string, limit: number = 50): Promise<Product[]> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
    });

    const url = `${this.baseURL}/products/search?${params.toString()}`;
    return this.fetchWithErrorHandling<Product[]>(url);
  }

  async getProduct(productId: string): Promise<Product> {
    const url = `${this.baseURL}/products/${productId}`;
    return this.fetchWithErrorHandling<Product>(url);
  }

  async getCategories(): Promise<Category[]> {
    const url = `${this.baseURL}/products/categories/`;
    return this.fetchWithErrorHandling<Category[]>(url);
  }

  async getBrands(): Promise<Brand[]> {
    const url = `${this.baseURL}/products/brands/`;
    return this.fetchWithErrorHandling<Brand[]>(url);
  }

  // Sales APIs
  async createSale(saleData: SaleRequest): Promise<Sale> {
    const url = `${this.baseURL}/sales/`;
    return this.fetchWithErrorHandling<Sale>(url, {
      method: 'POST',
      body: JSON.stringify(saleData),
    });
  }

  async getSales(
    page: number = 1,
    limit: number = 50,
    startDate?: string,
    endDate?: string
  ): Promise<{ data: Sale[]; total: number; page: number; limit: number }> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });

    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const url = `${this.baseURL}/sales/?${params.toString()}`;
    return this.fetchWithErrorHandling(url);
  }

  async getSale(saleId: string): Promise<Sale> {
    const url = `${this.baseURL}/sales/${saleId}`;
    return this.fetchWithErrorHandling<Sale>(url);
  }

  async voidSale(saleId: string, reason: string): Promise<any> {
    const params = new URLSearchParams({ reason });
    const url = `${this.baseURL}/sales/${saleId}/void?${params.toString()}`;
    return this.fetchWithErrorHandling(url, { method: 'POST' });
  }

  async refundSale(saleId: string, refundAmount: number, reason: string): Promise<any> {
    const params = new URLSearchParams({
      refund_amount: refundAmount.toString(),
      reason
    });
    const url = `${this.baseURL}/sales/${saleId}/refund?${params.toString()}`;
    return this.fetchWithErrorHandling(url, { method: 'POST' });
  }

  // Health check
  async healthCheck(): Promise<{ status: string; message: string; auth_service?: string }> {
    const url = `${this.baseURL.replace('/api/v1', '')}/health`;
    return this.fetchWithErrorHandling(url);
  }
}

// Export singleton instance
export const apiService = new APIService();
export default apiService;