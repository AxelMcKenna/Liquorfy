import { useState, useCallback, useEffect, useRef } from 'react';
import axios from 'axios';
import api from '@/lib/api';
import { ProductDetail } from '@/types';

interface FetchOptions {
  lat?: number;
  lon?: number;
  radius_km?: number;
}

export const useProductDetail = () => {
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activeRequest = useRef<AbortController | null>(null);

  const fetchProduct = useCallback(async (productId: string, options?: FetchOptions) => {
    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;

    setLoading(true);
    setError(null);

    try {
      const params: Record<string, number> = {};
      if (options?.lat != null && options?.lon != null && options?.radius_km != null) {
        params.lat = options.lat;
        params.lon = options.lon;
        params.radius_km = options.radius_km;
      }
      const { data } = await api.get<ProductDetail>(`/products/${productId}`, {
        params,
        signal: controller.signal,
      });
      setProduct(data);
    } catch (err) {
      if (axios.isCancel(err)) return;
      setError('Product not found');
      setProduct(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    return () => {
      activeRequest.current?.abort();
    };
  }, []);

  return { product, loading, error, fetchProduct };
};
