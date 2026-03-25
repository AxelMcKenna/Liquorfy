import { useState, useEffect, useCallback } from 'react';
import { Product } from '@/types';

const STORAGE_KEY = 'liquorfy_recently_viewed';
const MAX_ITEMS = 10;

interface StoredProduct {
  product: Product;
  viewedAt: number;
}

export const useRecentlyViewed = () => {
  const [items, setItems] = useState<Product[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return [];
      const parsed: StoredProduct[] = JSON.parse(stored);
      return parsed.map((s) => s.product);
    } catch {
      return [];
    }
  });

  useEffect(() => {
    const stored: StoredProduct[] = items.map((product, i) => ({
      product,
      viewedAt: Date.now() - i,
    }));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
  }, [items]);

  const addProduct = useCallback((product: Product) => {
    setItems((prev) => {
      const filtered = prev.filter((p) => p.id !== product.id);
      return [product, ...filtered].slice(0, MAX_ITEMS);
    });
  }, []);

  return { recentlyViewed: items, addProduct };
};
