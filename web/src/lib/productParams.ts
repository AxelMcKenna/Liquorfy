import { ProductFilters } from '@/types';

/**
 * Build URLSearchParams from ProductFilters.
 * Shared utility to avoid duplication across hooks.
 */
export function buildProductQueryParams(filters: ProductFilters): URLSearchParams {
  const params = new URLSearchParams();

  if (filters.query) params.append("q", filters.query);
  if (filters.category) params.append("category", filters.category);
  if (filters.chains && filters.chains.length > 0) {
    params.append("chain", filters.chains.join(","));
  }
  if (filters.store_ids && filters.store_ids.length > 0) {
    params.append("store", filters.store_ids.join(","));
  }
  if (filters.promo_only) params.append("promo_only", "true");
  if (filters.unique_products) params.append("unique_products", "true");
  if (filters.price_min !== undefined) params.append("price_min", filters.price_min.toString());
  if (filters.price_max !== undefined) params.append("price_max", filters.price_max.toString());
  if (filters.sort) params.append("sort", filters.sort);
  if (filters.lat !== undefined) params.append("lat", filters.lat.toString());
  if (filters.lon !== undefined) params.append("lon", filters.lon.toString());
  if (filters.radius_km !== undefined) params.append("radius_km", filters.radius_km.toString());

  return params;
}
