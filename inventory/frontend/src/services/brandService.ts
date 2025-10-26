import { baseApiService } from "./baseApiService";

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
  private basePath = "/brands";

  async getBrands(): Promise<ApiResponse<Brand[]>> {
    const data = await baseApiService.get<Brand[]>(`${this.basePath}/`);
    return { data, message: 'Brands loaded successfully!' };
  }

  async getBrand(id: string): Promise<ApiResponse<Brand>> {
    const data = await baseApiService.get<Brand>(`${this.basePath}/${id}`);
    return { data, message: 'Brand loaded successfully!' };
  }

  async createBrand(brandData: CreateBrandRequest): Promise<ApiResponse<Brand>> {
    const requestData = {
      name: brandData.name,
      description: brandData.description || '',
      contact_info: brandData.contactInfo || ''
    };
    
    const data = await baseApiService.post<Brand>(`${this.basePath}/`, requestData);
    return { data, message: 'Brand created successfully!' };
  }

  async updateBrand(id: string, brandData: Partial<CreateBrandRequest>): Promise<ApiResponse<Brand>> {
    const updateData: any = {};
    if (brandData.name !== undefined) updateData.name = brandData.name;
    if (brandData.description !== undefined) updateData.description = brandData.description;
    if (brandData.contactInfo !== undefined) updateData.contact_info = brandData.contactInfo;

    const data = await baseApiService.put<Brand>(`${this.basePath}/${id}`, updateData);
    return { data, message: 'Brand updated successfully!' };
  }

  async deleteBrand(id: string): Promise<void> {
    await baseApiService.delete(`${this.basePath}/${id}`);
  }
}

export const brandService = new BrandService()