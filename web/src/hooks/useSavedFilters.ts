import { useCallback } from 'react';
import { ChainType } from '@/types';

const STORAGE_KEY = 'liquorfy_saved_filters';

interface SavedFilters {
  chains?: ChainType[];
  category?: string;
  promo_only?: boolean;
}

export const useSavedFilters = () => {
  const getSavedFilters = useCallback((): SavedFilters | null => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  }, []);

  const saveFilters = useCallback((filters: SavedFilters) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filters));
  }, []);

  const clearSavedFilters = useCallback(() => {
    localStorage.removeItem(STORAGE_KEY);
  }, []);

  return { getSavedFilters, saveFilters, clearSavedFilters };
};
