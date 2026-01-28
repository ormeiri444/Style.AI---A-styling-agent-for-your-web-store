import axios from 'axios';
import { CatalogItem, TryOnRequest, TryOnResponse, RecommendationItem } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export async function performTryOn(request: TryOnRequest): Promise<TryOnResponse> {
  const response = await api.post<TryOnResponse>('/api/tryon', request);
  return response.data;
}

export async function addItemToOutfit(
  currentOutfitImage: string,
  newItemImage: string,
  itemDescription: string
): Promise<TryOnResponse> {
  const response = await api.post<TryOnResponse>('/api/tryon/add-item', {
    current_outfit_image: currentOutfitImage,
    new_item_image: newItemImage,
    item_description: itemDescription,
  });
  return response.data;
}

export async function getRecommendations(
  outfitImage: string,
  wornItems: Array<{ category: string; name: string; color?: string }>
): Promise<RecommendationItem[]> {
  const response = await api.post<{ recommendations: RecommendationItem[] }>('/api/recommend', {
    current_outfit_image: outfitImage,
    worn_items: wornItems,
  });
  return response.data.recommendations;
}

export async function getCatalog(category?: string): Promise<CatalogItem[]> {
  const params = category ? { category } : {};
  const response = await api.get<{ items: CatalogItem[] }>('/api/catalog', { params });
  return response.data.items;
}

export async function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => {
      const result = reader.result as string;
      // Remove data URL prefix (e.g., "data:image/png;base64,")
      const base64 = result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = (error) => reject(error);
  });
}

export async function urlToBase64(url: string): Promise<string> {
  const response = await fetch(url);
  const blob = await response.blob();
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(blob);
    reader.onload = () => {
      const result = reader.result as string;
      const base64 = result.split(',')[1];
      resolve(base64);
    };
    reader.onerror = (error) => reject(error);
  });
}
