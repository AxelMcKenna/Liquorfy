import { useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useFavourites } from '@/hooks/useFavourites';
import { useAlerts } from '@/hooks/useAlerts';
import { toast } from 'sonner';

export const PersonalisedBanner = () => {
  const { user } = useAuth();
  const { favouriteCount } = useFavourites();
  const { alerts, fetchAlerts } = useAlerts();
  const shown = useRef(false);

  useEffect(() => {
    if (user && !shown.current) {
      fetchAlerts();
      shown.current = true;
    }
  }, [user, fetchAlerts]);

  useEffect(() => {
    if (!user || !shown.current) return;
    // Show toast once alerts have loaded
    if (alerts === undefined) return;

    const rawName = user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split('@')[0]?.split('.')[0] || 'there';
    const name = rawName.split(' ').map((w: string) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
    const alertCount = alerts.length;
    const parts: string[] = [];
    if (alertCount > 0) parts.push(`${alertCount} alert${alertCount !== 1 ? 's' : ''}`);
    if (favouriteCount > 0) parts.push(`${favouriteCount} saved`);

    const description = parts.length > 0 ? parts.join(' · ') : undefined;

    toast(`Welcome back, ${name}`, {
      description,
      duration: 4000,
    });
  }, [user, alerts, favouriteCount]);

  return null;
};
