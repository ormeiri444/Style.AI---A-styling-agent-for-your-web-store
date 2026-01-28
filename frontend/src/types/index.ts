export interface CatalogItem {
  id: string;
  name: string;
  category: string;
  subcategory: string;
  color: string;
  style: string[];
  image_path: string;
  description: string;
  gender: string;
  brand: string;
}

export interface TryOnRequest {
  human_image: string;
  garment_image: string;
  garment_description: string;
  category: string;
}

export interface TryOnResponse {
  result_image: string;
  outfit_state: {
    worn_items: Array<{
      category: string;
      description: string;
    }>;
  };
}

export interface RecommendationItem {
  id: string;
  name: string;
  image_url: string;
  category: string;
  reason: string;
}

export interface OutfitState {
  humanImage: string | null;
  currentOutfitImage: string | null;
  wornItems: Array<{
    category: string;
    description: string;
    name: string;
  }>;
}
