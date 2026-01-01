import { useState, useCallback } from 'react';
import axios from 'axios';
import { Product, ProductListResponse, ProductFilters } from '@/types';
import { buildProductQueryParams } from '@/lib/productParams';

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const useProducts = () => {
  const [products, setProducts] = useState<ProductListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchProducts = useCallback(async (filters: ProductFilters) => {
    setLoading(true);
    setError(null);
    try {
      const params = buildProductQueryParams(filters);

      // Handle pagination if specified
      if (filters.limit !== undefined) params.append("page_size", filters.limit.toString());
      if (filters.offset !== undefined && filters.limit !== undefined) {
        const page = Math.floor(filters.offset / filters.limit) + 1;
        params.append("page", page.toString());
      } else if (filters.limit !== undefined) {
        params.append("page", "1");
      }

      const { data } = await axios.get<ProductListResponse>(`${API_BASE}/products`, { params });
      setProducts(data);
    } catch (err) {
      setError("Failed to load products");
    } finally {
      setLoading(false);
    }
  }, []);

  return { products, loading, error, fetchProducts };
};
