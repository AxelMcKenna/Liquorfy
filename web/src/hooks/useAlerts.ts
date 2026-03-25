import { useState, useCallback } from 'react';
import api from '@/lib/api';

export interface Alert {
  id: string;
  product_id: string;
  product_name: string | null;
  threshold_price: number | null;
  alert_on_promo: boolean;
  last_triggered_at: string | null;
  active: boolean;
  created_at: string;
}

interface AlertListResponse {
  items: Alert[];
}

export const useAlerts = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.get<AlertListResponse>('/alerts');
      setAlerts(data.items);
    } catch {
      setError('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  }, []);

  const createAlert = useCallback(async (params: {
    product_id: string;
    threshold_price?: number;
    alert_on_promo?: boolean;
  }) => {
    const { data } = await api.post<Alert>('/alerts', params);
    setAlerts((prev) => [data, ...prev]);
    return data;
  }, []);

  const updateAlert = useCallback(async (alertId: string, params: {
    threshold_price?: number;
    alert_on_promo?: boolean;
    active?: boolean;
  }) => {
    const { data } = await api.patch<Alert>(`/alerts/${alertId}`, params);
    setAlerts((prev) => prev.map((a) => (a.id === alertId ? data : a)));
    return data;
  }, []);

  const deleteAlert = useCallback(async (alertId: string) => {
    await api.delete(`/alerts/${alertId}`);
    setAlerts((prev) => prev.filter((a) => a.id !== alertId));
  }, []);

  return { alerts, loading, error, fetchAlerts, createAlert, updateAlert, deleteAlert };
};
