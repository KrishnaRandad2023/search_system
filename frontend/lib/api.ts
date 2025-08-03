/**
 * API Client for Flipkart Search System
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types for API responses
export interface AutosuggestItem {
  text: string;
  score: number;
  suggestion_type: string;
  metadata?: {
    category?: string;
    title?: string;
    brand?: string;
  };
}

export interface AutosuggestResponse {
  query: string;
  suggestions: AutosuggestItem[];
  total_count?: number;
  response_time_ms?: number;
}

export interface ProductResult {
  id: string;
  title: string;
  description: string;
  category: string;
  subcategory: string;
  brand: string;
  current_price: number;
  original_price?: number;
  discount_percent?: number;
  rating: number;
  num_ratings: number;
  availability: string;
  image_url?: string;
  features?: string[];
  specifications?: string;
  // Scoring metrics
  relevance_score: number;
  popularity_score: number;
  business_score: number;
  final_score: number;
}

export interface SearchFilters {
  category?: string;
  subcategory?: string;
  brand?: string;
  min_price?: number;
  max_price?: number;
  min_rating?: number;
  availability?: string;
}

export interface SearchResponse {
  products: ProductResult[];
  total_results: number;
  page: number;
  per_page: number;
  total_pages: number;
  filters_applied: SearchFilters;
  search_metadata: {
    query: string;
    search_type: string;
    response_time_ms: number;
    has_typo_correction: boolean;
    corrected_query?: string;
    semantic_similarity?: number;
  };
  aggregations: {
    categories: Array<{ name: string; count: number }>;
    brands: Array<{ name: string; count: number }>;
    price_ranges: Array<{ name: string; count: number }>;
    ratings: Array<{ name: string; count: number }>;
  };
}

export interface ClickTrackingPayload {
  query: string;
  product_id: string;
  position: number;
  timestamp?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          ...defaultHeaders,
          ...options.headers,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  /**
   * Get autosuggest recommendations
   */
  async getAutosuggest(
    query: string,
    limit: number = 10
  ): Promise<AutosuggestResponse> {
    const params = new URLSearchParams({
      q: query,
      limit: limit.toString(),
    });

    const response = await this.makeRequest<AutosuggestResponse>(
      `/api/v1/metadata/autosuggest?${params}`
    );
    
    return response;
  }

  /**
   * Perform search with filters and pagination
   */
  async search(
    query: string,
    filters: SearchFilters = {},
    page: number = 1,
    perPage: number = 20,
    sortBy: string = 'relevance'
  ): Promise<SearchResponse> {
    const params = new URLSearchParams({
      q: query,
      page: page.toString(),
      per_page: perPage.toString(),
      sort_by: sortBy,
    });

    // Disable hybrid search only for shoe-related queries where it's problematic
    const shoeKeywords = ['shoe', 'shoes', 'sneaker', 'sneakers', 'loafer', 'loafers', 'boot', 'boots', 'sandal', 'sandals'];
    const queryLower = query.toLowerCase();
    const isShoeQuery = shoeKeywords.some(keyword => queryLower.includes(keyword));
    
    if (isShoeQuery) {
      params.append('use_hybrid', 'false');
    }

    // Add filters to params
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params.append(key, value.toString());
      }
    });

    return this.makeRequest<SearchResponse>(
      `/api/v2/search?${params}`
    );
  }

  /**
   * Track product click for analytics and ranking improvement
   */
  async trackClick(payload: ClickTrackingPayload): Promise<void> {
    const clickData = {
      ...payload,
      timestamp: payload.timestamp || new Date().toISOString(),
    };

    await this.makeRequest('/api/v1/track-click', {
      method: 'POST',
      body: JSON.stringify(clickData),
    });
  }

  /**
   * Get popular search queries
   */
  async getPopularQueries(limit: number = 10): Promise<string[]> {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });

    const response = await this.makeRequest<{ queries: Array<{ query: string; count: number }> }>(
      `/api/v1/metadata/popular-queries?${params}`
    );
    
    // Extract just the query strings from the response
    return response.queries.map(item => item.query);
  }

  /**
   * Get trending categories
   */
  async getTrendingCategories(limit: number = 10): Promise<Array<{ category: string; trend_score: number }>> {
    const params = new URLSearchParams({
      limit: limit.toString(),
    });

    const response = await this.makeRequest<{ categories: Array<{ category: string; count: number }> }>(
      `/api/v1/metadata/trending-categories?${params}`
    );
    
    // Convert count to trend_score for frontend compatibility
    return response.categories.map(item => ({
      category: item.category,
      trend_score: Math.min(1.0, item.count / 200) // Normalize to 0-1 range
    }));
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.makeRequest<{ status: string; timestamp: string }>('/');
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export API client class for custom instances
export { ApiClient };

// Utility functions for handling API responses
export const handleApiError = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

export const formatPrice = (price: number | undefined): string => {
  if (price === undefined || price === null || isNaN(price)) {
    return '₹0';
  }
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(price);
};

export const formatRating = (rating: number | undefined): string => {
  if (rating === undefined || rating === null || isNaN(rating)) {
    return '0.0';
  }
  return rating.toFixed(1);
};

export const getCategoryIcon = (category: string): string => {
  const icons: Record<string, string> = {
    'Electronics': '📱',
    'Clothing': '👕',
    'Home': '🏠',
    'Books': '📚',
    'Sports': '⚽',
    'Beauty': '💄',
    'Automotive': '🚗',
    'Grocery': '🛒',
  };
  return icons[category] || '🛍️';
};
