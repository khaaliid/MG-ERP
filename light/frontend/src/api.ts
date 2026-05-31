import axios from 'axios';

const API_BASE_URL = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8005/api';

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid, redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (username: string, password: string) => 
    api.post('/auth/login', { username, password }),
  getCurrentUser: () => 
    api.get('/auth/me'),
  getUsers: () => 
    api.get('/auth/users'),
  createUser: (data: any) => 
    api.post('/auth/users', data),
  updateUser: (id: number, data: any) => 
    api.put(`/auth/users/${id}`, data),
  deleteUser: (id: number) => 
    api.delete(`/auth/users/${id}`),
};

// Inventory API
export const inventoryAPI = {
  getAll: (params?: { category?: string; search?: string }) => 
    api.get('/inventory', { params }),
  getById: (id: number) => 
    api.get(`/inventory/${id}`),
  create: (data: any) => 
    api.post('/inventory', data),
  update: (id: number, data: any) => 
    api.put(`/inventory/${id}`, data),
  delete: (id: number) => 
    api.delete(`/inventory/${id}`),
};

// POS API
export const posAPI = {
  getTransactions: (params?: {
    start_date?: string;
    end_date?: string;
    search?: string;
    payment_method?: string;
    skip?: number;
    limit?: number;
    paginated?: boolean;
  }) => 
    api.get('/pos/transactions', { params }),
  getTransaction: (id: number) => 
    api.get(`/pos/transactions/${id}`),
  createTransaction: (data: any) => 
    api.post('/pos/transactions', data),
  createClosure: (data: any) =>
    api.post('/pos/closures', data),
  refundTransaction: (transactionId: number, data: any) =>
    api.post(`/pos/transactions/${transactionId}/refund`, data),
  refundTransactionItem: (transactionId: number, data: any) =>
    api.post(`/pos/transactions/${transactionId}/refund-item`, data),
  sendReceiptWhatsApp: (transactionId: number, data: { phone_number: string }) =>
    api.post(`/pos/transactions/${transactionId}/receipt/whatsapp`, data),
};

// Ledger API
export const ledgerAPI = {
  getRecords: (params?: {
    transaction_type?: string;
    start_date?: string;
    end_date?: string;
    skip?: number;
    limit?: number;
    paginated?: boolean;
  }) => 
    api.get('/ledger', { params }),
  getRecord: (id: number) => 
    api.get(`/ledger/${id}`),
  create: (data: any) => 
    api.post('/ledger', data),
};

// Reports API
export const reportsAPI = {
  getSalesReport: (params?: { start_date?: string; end_date?: string }) => 
    api.get('/reports/sales', { params }),
  getInventoryReport: () => 
    api.get('/reports/inventory'),
  getLedgerReport: (params?: { start_date?: string; end_date?: string }) => 
    api.get('/reports/ledger', { params }),
  getBalanceSheetReport: (params?: { as_of_date?: string }) =>
    api.get('/reports/balance-sheet', { params }),
  getCashierClosureSummaryReport: (params?: { start_date?: string; end_date?: string; sales_user_id?: number }) =>
    api.get('/reports/cashier-closures', { params }),
};

// Expense API
export const expenseAPI = {
  getAll: (params?: { start_date?: string; end_date?: string; category?: string; skip?: number; limit?: number; paginated?: boolean }) => 
    api.get('/expenses', { params }),
  getById: (id: number) => 
    api.get(`/expenses/${id}`),
  create: (data: any) => 
    api.post('/expenses', data),
  update: (id: number, data: any) => 
    api.put(`/expenses/${id}`, data),
  delete: (id: number) => 
    api.delete(`/expenses/${id}`),
};

// Sales User API
export const salesUserAPI = {
  getAll: (params?: { active_only?: boolean }) => 
    api.get('/sales-users', { params }),
  getById: (id: number) => 
    api.get(`/sales-users/${id}`),
  create: (data: any) => 
    api.post('/sales-users', data),
  update: (id: number, data: any) => 
    api.put(`/sales-users/${id}`, data),
  delete: (id: number) => 
    api.delete(`/sales-users/${id}`),
};
