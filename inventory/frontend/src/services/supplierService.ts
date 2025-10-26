import { baseApiService } from "./baseApiService";

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
  private basePath = "/suppliers";

  async getSuppliers(): Promise<Supplier[]> {
    return baseApiService.get<Supplier[]>(`${this.basePath}/`);
  }

  async getSupplier(id: string): Promise<Supplier> {
    return baseApiService.get<Supplier>(`${this.basePath}/${id}`);
  }

  async createSupplier(supplier: CreateSupplierRequest): Promise<Supplier> {
    return baseApiService.post<Supplier>(`${this.basePath}/`, supplier);
  }

  async updateSupplier(id: string, supplier: UpdateSupplierRequest): Promise<Supplier> {
    return baseApiService.put<Supplier>(`${this.basePath}/${id}`, supplier);
  }

  async deleteSupplier(id: string): Promise<void> {
    return baseApiService.delete(`${this.basePath}/${id}`);
  }
}

export const supplierService = new SupplierService()