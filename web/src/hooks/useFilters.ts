import { useSearchParams } from 'react-router-dom';
import { useMemo, useCallback } from 'react';
import { ProductFilters, SortOption, ChainType } from '@/types';

export const useFilters = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters: ProductFilters = useMemo(() => {
    const query = searchParams.get('q') || undefined;
    const category = searchParams.get('category') || undefined;
    const chainParam = searchParams.get('chain');
    const chains = chainParam ? (chainParam.split(',') as ChainType[]) : undefined;
    const promo_only = searchParams.get('promo_only') === 'true' ? true : undefined;
    const price_min = searchParams.get('price_min') ? parseFloat(searchParams.get('price_min')!) : undefined;
    const price_max = searchParams.get('price_max') ? parseFloat(searchParams.get('price_max')!) : undefined;
    const sortParam = searchParams.get('sort') as SortOption | null;
    const sort = sortParam || (promo_only ? SortOption.DISCOUNT : SortOption.BEST_VALUE);
    const storeIdsParam = searchParams.get('store_ids');
    const store_ids = storeIdsParam ? storeIdsParam.split(',') : undefined;

    return {
      query,
      category,
      chains,
      promo_only,
      price_min,
      price_max,
      sort,
      store_ids,
    };
  }, [searchParams]);

  const updateFilters = useCallback((updates: Partial<ProductFilters>) => {
    const newParams = new URLSearchParams(searchParams);
    if (Object.keys(updates).length > 0) {
      newParams.delete('page');
    }

    Object.entries(updates).forEach(([key, value]) => {
      if (value === undefined || value === null || value === '') {
        newParams.delete(key);
      } else if (key === 'chains' && Array.isArray(value)) {
        if (value.length === 0) {
          newParams.delete('chain');
        } else {
          newParams.set('chain', value.join(','));
        }
      } else if (key === 'store_ids' && Array.isArray(value)) {
        if (value.length === 0) {
          newParams.delete('store_ids');
        } else {
          newParams.set('store_ids', value.join(','));
        }
      } else if (key === 'promo_only') {
        if (value) {
          newParams.set('promo_only', 'true');
        } else {
          newParams.delete('promo_only');
        }
      } else {
        newParams.set(key, String(value));
      }
    });

    setSearchParams(newParams);
  }, [searchParams, setSearchParams]);

  const clearFilters = useCallback(() => {
    setSearchParams({});
  }, [setSearchParams]);

  const hasActiveFilters = useMemo(() => {
    return !!(
      filters.query ||
      filters.category ||
      filters.chains?.length ||
      filters.promo_only ||
      filters.price_min ||
      filters.price_max ||
      (filters.sort && filters.sort !== SortOption.BEST_VALUE)
    );
  }, [filters]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.category) count++;
    if (filters.chains?.length) count += filters.chains.length;
    if (filters.promo_only) count++;
    if (filters.price_min || filters.price_max) count++;
    if (filters.sort && filters.sort !== SortOption.BEST_VALUE) count++;
    return count;
  }, [filters]);

  return {
    filters,
    updateFilters,
    clearFilters,
    hasActiveFilters,
    activeFilterCount,
  };
};
