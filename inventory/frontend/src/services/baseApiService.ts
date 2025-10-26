// Base API service with authentication
export class BaseApiService {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://localhost:8002/api/v1') {
    this.baseUrl = baseUrl;
  }

  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('auth_token');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  protected async fetch(endpoint: string, options: RequestInit = {}): Promise<Response> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.getAuthHeaders(),
        ...options.headers,
      },
    };

    console.log(`🌐 API Call: ${config.method || 'GET'} ${url}`);
    
    try {
      const response = await fetch(url, config);
      
      if (response.status === 401) {
        // Token expired or invalid - redirect to login
        console.error('🚫 Authentication failed - redirecting to login');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
        window.location.reload();
        throw new Error('Authentication failed');
      }
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`❌ API Error: ${response.status} ${response.statusText}`, errorText);
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }
      
      console.log(`✅ API Success: ${response.status}`);
      return response;
    } catch (error) {
      console.error('💥 API Request failed:', error);
      throw error;
    }
  }

  public async get<T>(endpoint: string): Promise<T> {
    const response = await this.fetch(endpoint);
    return response.json();
  }

  public async post<T>(endpoint: string, data?: any): Promise<T> {
    const response = await this.fetch(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.json();
  }

  public async put<T>(endpoint: string, data?: any): Promise<T> {
    const response = await this.fetch(endpoint, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.json();
  }

  public async delete(endpoint: string): Promise<void> {
    await this.fetch(endpoint, {
      method: 'DELETE',
    });
  }
}

// Export a singleton instance
export const baseApiService = new BaseApiService();