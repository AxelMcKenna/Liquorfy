import { useState, useCallback } from 'react';
import axios from 'axios';
import { Store, StoreListResponse, Location } from '@/types';

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface UseStoresReturn {
  stores: Store[];
  loading: boolean;
  error: string | null;
  fetchNearbyStores: (location: Location, radiusKm?: number) => Promise<void>;
}

export const useStores = (): UseStoresReturn => {
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchNearbyStores = useCallback(async (location: Location, radiusKm: number = 20) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        lat: location.lat.toString(),
        lon: location.lon.toString(),
        radius_km: radiusKm.toString(),
      });

      const { data } = await axios.get<StoreListResponse>(
        `${API_BASE}/stores?${params.toString()}`
      );

      setStores(data.items);
    } catch (err) {
      setError('Failed to load nearby stores');
      console.error('Error fetching stores:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  return { stores, loading, error, fetchNearbyStores };
};
