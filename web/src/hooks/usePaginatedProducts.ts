import { useState, useCallback } from 'react';
import axios from 'axios';
import { Product, ProductListResponse, ProductFilters } from '@/types';
import { buildProductQueryParams } from '@/lib/productParams';

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const PAGE_SIZE = 24;

export const usePaginatedProducts = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const fetchProducts = useCallback(async (filters: ProductFilters, page: number = 1) => {
    setLoading(true);
    setError(null);
    setCurrentPage(page);

    try {
      const params = buildProductQueryParams(filters);
      params.append("page_size", PAGE_SIZE.toString());
      params.append("page", page.toString());

      const { data } = await axios.get<ProductListResponse>(`${API_BASE}/products`, { params });

      setProducts(data.items);
      setTotal(data.total);
    } catch (err) {
      setError("Failed to load products");
      setProducts([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, []);

  const goToPage = useCallback((page: number) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [totalPages]);

  return {
    products,
    total,
    loading,
    error,
    currentPage,
    totalPages,
    pageSize: PAGE_SIZE,
    fetchProducts,
    goToPage,
  };
};
