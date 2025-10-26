import { baseApiService } from "./baseApiService";

export interface Category {
  id: string;
  name: string;
  description?: string;
  size_type: "CLOTHING" | "NUMERIC" | "SHOE";
  created_at?: string;
  updated_at?: string;
}

export interface CategoryCreate {
  name: string;
  description?: string;
  size_type: "CLOTHING" | "NUMERIC" | "SHOE";
}

export interface CategoryUpdate {
  name?: string;
  description?: string;
  size_type?: "CLOTHING" | "NUMERIC" | "SHOE";
}

class CategoryService {
  private basePath = "/api/v1/categories";

  async getCategories(): Promise<Category[]> {
    return baseApiService.get<Category[]>(this.basePath);
  }

  async getCategory(id: string): Promise<Category> {
    return baseApiService.get<Category>(`${this.basePath}/${id}`);
  }

  async createCategory(category: CategoryCreate): Promise<Category> {
    return baseApiService.post<Category>(this.basePath, category);
  }

  async updateCategory(id: string, category: CategoryUpdate): Promise<Category> {
    return baseApiService.put<Category>(`${this.basePath}/${id}`, category);
  }

  async deleteCategory(id: string): Promise<void> {
    return baseApiService.delete(`${this.basePath}/${id}`);
  }
}

export const categoryService = new CategoryService();