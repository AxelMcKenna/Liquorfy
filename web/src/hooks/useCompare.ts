import { useState, useMemo } from 'react';
import { Product } from '@/types';

const MAX_COMPARE = 4;

export const useCompare = () => {
  const [compare, setCompare] = useState<Product[]>([]);

  const toggleCompare = (product: Product) => {
    setCompare((prev) => {
      const exists = prev.find((p) => p.id === product.id);
      if (exists) {
        return prev.filter((p) => p.id !== product.id);
      }
      if (prev.length >= MAX_COMPARE) {
        return prev;
      }
      return [...prev, product];
    });
  };

  const sortedCompare = useMemo(
    () =>
      [...compare].sort(
        (a, b) => (a.price.price_per_100ml ?? Infinity) - (b.price.price_per_100ml ?? Infinity)
      ),
    [compare]
  );

  const clearCompare = () => setCompare([]);

  const isAtLimit = compare.length >= MAX_COMPARE;
  const canAddMore = compare.length < MAX_COMPARE;

  return {
    compare,
    sortedCompare,
    toggleCompare,
    clearCompare,
    isAtLimit,
    canAddMore,
    compareCount: compare.length,
    maxCompare: MAX_COMPARE,
  };
};
