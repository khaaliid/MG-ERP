import axios, { InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8004/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses
api.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: string;
  username?: string;
  email: string;
  full_name: string;
  phone?: string;
  department?: string;
  position?: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export const authService = {
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await api.post<LoginResponse>('/auth/login', credentials);
    return response.data;
  },

  async getProfile(): Promise<User> {
    const response = await api.get<User>('/auth/profile');
    return response.data;
  },

  async getUsers(): Promise<User[]> {
    const response = await api.get<User[]>('/auth/users');
    return response.data;
  },

  async createUser(userData: any): Promise<User> {
    const response = await api.post<User>('/auth/users', userData);
    return response.data;
  },

  async updateUser(userId: string, userData: any): Promise<User> {
    const response = await api.put<User>(`/auth/users/${userId}`, userData);
    return response.data;
  },

  async deleteUser(userId: string): Promise<void> {
    await api.delete(`/auth/users/${userId}`);
  },

  async toggleUserStatus(userId: string, activate: boolean): Promise<User> {
    const endpoint = activate ? 'activate' : 'deactivate';
    const response = await api.put<User>(`/auth/users/${userId}/${endpoint}`);
    return response.data;
  },

  logout() {
    localStorage.removeItem('token');
  },
};

export default api;
