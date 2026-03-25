import { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Bell, Heart, TrendingDown } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useFavourites } from '@/hooks/useFavourites';
import { useAlerts, Alert } from '@/hooks/useAlerts';

export const PersonalisedBanner = () => {
  const { user } = useAuth();
  const { favouriteCount } = useFavourites();
  const { alerts, fetchAlerts } = useAlerts();
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (user && !loaded) {
      fetchAlerts().then(() => setLoaded(true));
    }
  }, [user, loaded, fetchAlerts]);

  if (!user) return null;

  const alertCount = alerts.length;

  return (
    <section className="bg-primary/5 border-b">
      <div className="max-w-6xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <p className="text-sm text-foreground">
            Welcome back, <strong>{user.user_metadata?.full_name || user.user_metadata?.name || user.email?.split('@')[0]?.split('.')[0] || 'there'}</strong>
          </p>
          <div className="flex items-center gap-4 text-sm">
            {alertCount > 0 && (
              <Link to="/settings" className="flex items-center gap-1.5 text-primary hover:underline">
                <Bell className="h-4 w-4" />
                {alertCount} alert{alertCount !== 1 ? 's' : ''}
              </Link>
            )}
            {favouriteCount > 0 && (
              <Link to="/settings" className="flex items-center gap-1.5 text-red-500 hover:underline">
                <Heart className="h-4 w-4" />
                {favouriteCount} saved
              </Link>
            )}
            {alertCount === 0 && favouriteCount === 0 && (
              <Link to="/explore" className="flex items-center gap-1.5 text-primary hover:underline">
                <TrendingDown className="h-4 w-4" />
                Find deals
              </Link>
            )}
          </div>
        </div>
      </div>
    </section>
  );
};
