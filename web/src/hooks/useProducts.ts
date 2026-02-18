import { useState, useCallback, useEffect, useRef } from 'react';
import axios from 'axios';
import { Product, ProductListResponse, ProductFilters } from '@/types';
import { buildProductQueryParams } from '@/lib/productParams';

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export const useProducts = () => {
  const [products, setProducts] = useState<ProductListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activeRequest = useRef<AbortController | null>(null);
  const latestRequestId = useRef(0);

  const fetchProducts = useCallback(async (filters: ProductFilters) => {
    latestRequestId.current += 1;
    const requestId = latestRequestId.current;

    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;

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

      const { data } = await axios.get<ProductListResponse>(`${API_BASE}/products`, {
        params,
        signal: controller.signal,
      });

      if (requestId !== latestRequestId.current) {
        return;
      }

      setProducts(data);
    } catch (err) {
      if (axios.isCancel(err)) {
        return;
      }
      if (requestId !== latestRequestId.current) {
        return;
      }
      setError("Failed to load products");
    } finally {
      if (requestId === latestRequestId.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    return () => {
      activeRequest.current?.abort();
    };
  }, []);

  return { products, loading, error, fetchProducts };
};
