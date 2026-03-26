import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { useAlerts } from '@/hooks/useAlerts';
import { toast } from 'sonner';

export const AlertsList = () => {
  const navigate = useNavigate();
  const { alerts, loading, error, fetchAlerts, deleteAlert } = useAlerts();

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const handleDelete = async (alertId: string) => {
    try {
      await deleteAlert(alertId);
      toast.success('Alert deleted');
    } catch {
      toast.error('Failed to delete alert');
    }
  };

  if (loading) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex items-center justify-between gap-4 p-4 bg-white rounded-lg border">
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className="h-5 w-3/4" />
              <Skeleton className="h-4 w-1/3" />
            </div>
            <Skeleton className="h-8 w-8 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8 text-center text-destructive">
        {error}
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="py-8 text-center text-muted-foreground">
        <Bell className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No price alerts set.</p>
        <p className="text-sm mt-1">
          Tap the bell icon on any product to get notified when prices drop.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          role="button"
          tabIndex={0}
          onClick={() => navigate(`/product/${alert.product_id}`)}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate(`/product/${alert.product_id}`); }}
          className="flex items-center justify-between gap-4 p-4 bg-white rounded-lg border cursor-pointer hover:border-primary/30 hover:bg-primary/5 transition-colors"
        >
          <div className="min-w-0">
            <p className="font-medium truncate">
              {alert.product_name || 'Unknown product'}
            </p>
            <div className="flex gap-3 text-sm text-muted-foreground mt-1">
              {alert.threshold_price && (
                <span>Below ${alert.threshold_price.toFixed(2)}</span>
              )}
              {alert.alert_on_promo && (
                <span>On promo</span>
              )}
              {!alert.active && (
                <span className="text-amber-600">Paused</span>
              )}
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => { e.stopPropagation(); handleDelete(alert.id); }}
            className="text-muted-foreground hover:text-destructive flex-shrink-0"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ))}
    </div>
  );
};
