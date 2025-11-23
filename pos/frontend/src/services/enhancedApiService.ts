/**
 * Enhanced API Service with Loading States
 * Wraps the original API service to automatically manage loading states
 */

import { apiService } from './apiService';
import type { 
  LoginRequest, 
  LoginResponse, 
  ProductsResponse, 
  SaleRequest, 
  Sale,
  Product,
  Category,
  Brand 
} from './apiService';

// Type for loading context (will be injected)
interface LoadingContextType {
  showLoading: (message?: string) => void;
  hideLoading: () => void;
}

class EnhancedApiService {
  private loadingContext: LoadingContextType | null = null;

  // Set the loading context (will be called from App component)
  setLoadingContext(context: LoadingContextType) {
    this.loadingContext = context;
  }

  // Generic wrapper for API calls with loading states
  private async withLoading<T>(
    apiCall: () => Promise<T>,
    loadingMessage: string
  ): Promise<T> {
    try {
      this.loadingContext?.showLoading(loadingMessage);
      const result = await apiCall();
      return result;
    } finally {
      this.loadingContext?.hideLoading();
    }
  }

  // Authentication methods
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    return this.withLoading(
      () => apiService.login(credentials),
      'Signing in...'
    );
  }

  logout(): void {
    this.loadingContext?.showLoading('Signing out...');
    apiService.logout();
    this.loadingContext?.hideLoading();
  }

  async getCurrentUser() {
    return this.withLoading(
      () => apiService.getCurrentUser(),
      'Loading user information...'
    );
  }

  // Product methods
  async getProducts(
    page: number = 1,
    limit: number = 100,
    search?: string,
    categoryId?: string,
    brandId?: string
  ): Promise<ProductsResponse> {
    return this.withLoading(
      () => apiService.getProducts(page, limit, search, categoryId, brandId),
      'Loading products...'
    );
  }

  async getProduct(id: string): Promise<Product> {
    return this.withLoading(
      () => apiService.getProduct(id),
      'Loading product details...'
    );
  }

  async searchProducts(query: string, limit: number = 50): Promise<Product[]> {
    return this.withLoading(
      () => apiService.searchProducts(query, limit),
      'Searching products...'
    );
  }

  // Category methods
  async getCategories(): Promise<Category[]> {
    return this.withLoading(
      () => apiService.getCategories(),
      'Loading categories...'
    );
  }

  // Brand methods
  async getBrands(): Promise<Brand[]> {
    return this.withLoading(
      () => apiService.getBrands(),
      'Loading brands...'
    );
  }

  // Sales methods
  async createSale(saleData: SaleRequest): Promise<Sale> {
    return this.withLoading(
      () => apiService.createSale(saleData),
      'Processing sale...'
    );
  }

  async getSales(
    page: number = 1,
    limit: number = 50,
    startDate?: string,
    endDate?: string
  ): Promise<{ data: Sale[]; total: number; page: number; limit: number }> {
    return this.withLoading(
      () => apiService.getSales(page, limit, startDate, endDate),
      'Loading sales history...'
    );
  }

  async getSale(id: string): Promise<Sale> {
    return this.withLoading(
      () => apiService.getSale(id),
      'Loading sale details...'
    );
  }

  async voidSale(saleId: string, reason: string): Promise<any> {
    return this.withLoading(
      () => apiService.voidSale(saleId, reason),
      'Voiding sale...'
    );
  }

  async refundSale(saleId: string, refundAmount: number, reason: string): Promise<any> {
    return this.withLoading(
      () => apiService.refundSale(saleId, refundAmount, reason),
      'Processing refund...'
    );
  }

  // Pass-through methods that don't need loading states
  isAuthenticated = () => apiService.isAuthenticated();
  getCurrentUserFromStorage = () => apiService.getCurrentUserFromStorage();

  // Health check
  async checkHealth(): Promise<any> {
    return this.withLoading(
      () => apiService.healthCheck(),
      'Checking system status...'
    );
  }
}

// Create and export the enhanced API service instance
export const enhancedApiService = new EnhancedApiService();

// Export types
export type { 
  LoginRequest, 
  LoginResponse, 
  ProductsResponse, 
  SaleRequest, 
  Sale,
  Product,
  Category,
  Brand 
};