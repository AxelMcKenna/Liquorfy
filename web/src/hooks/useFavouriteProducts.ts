import { useState, useEffect, useCallback, useRef } from 'react';
import api from '@/lib/api';
import { Product } from '@/types';
import { useLocationContext } from '@/contexts/LocationContext';

export const useFavouriteProducts = (favouriteIds: Set<string>) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { location, radiusKm, isLocationSet } = useLocationContext();
  const activeRequest = useRef<AbortController | null>(null);

  const fetchFavourites = useCallback(async (ids: Set<string>) => {
    if (ids.size === 0) {
      setProducts([]);
      return;
    }

    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;

    setLoading(true);
    setError(null);

    try {
      const body: Record<string, unknown> = {
        ids: [...ids],
      };
      if (isLocationSet && location) {
        body.lat = location.lat;
        body.lon = location.lon;
        body.radius_km = radiusKm;
      }

      const { data } = await api.post<Product[]>('/products/batch', body, {
        signal: controller.signal,
      });
      setProducts(data);
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      setError('Failed to load favourites');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, [location, radiusKm, isLocationSet]);

  useEffect(() => {
    fetchFavourites(favouriteIds);
    return () => { activeRequest.current?.abort(); };
  }, [favouriteIds, fetchFavourites]);

  return { products, loading, error, refetch: () => fetchFavourites(favouriteIds) };
};
