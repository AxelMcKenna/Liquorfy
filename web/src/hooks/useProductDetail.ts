import { useState, useCallback, useEffect, useRef } from 'react';
import axios from 'axios';
import api from '@/lib/api';
import { ProductDetail } from '@/types';

export const useProductDetail = () => {
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const activeRequest = useRef<AbortController | null>(null);

  const fetchProduct = useCallback(async (productId: string) => {
    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;

    setLoading(true);
    setError(null);

    try {
      const { data } = await api.get<ProductDetail>(`/products/${productId}`, {
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
