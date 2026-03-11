import client from './client';
import type { Category, CategoryCreate, CategoryTree } from '../types/category';

export async function listCategories(): Promise<Category[]> {
  const response = await client.get<Category[]>('/taxonomy/categories');
  return response.data;
}

export async function getCategoryTree(): Promise<CategoryTree[]> {
  const response = await client.get<CategoryTree[]>('/taxonomy/categories/tree');
  return response.data;
}

export async function getCategory(id: string): Promise<Category> {
  const response = await client.get<Category>(`/taxonomy/categories/${id}`);
  return response.data;
}

export async function createCategory(data: CategoryCreate): Promise<Category> {
  const response = await client.post<Category>('/taxonomy/categories', data);
  return response.data;
}

export async function deleteCategory(id: string): Promise<void> {
  await client.delete(`/taxonomy/categories/${id}`);
}
