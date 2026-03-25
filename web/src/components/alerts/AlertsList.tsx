import { useEffect } from 'react';
import { Bell, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAlerts } from '@/hooks/useAlerts';
import { toast } from 'sonner';

export const AlertsList = () => {
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
      <div className="py-8 text-center text-muted-foreground">
        Loading alerts...
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
          className="flex items-center justify-between gap-4 p-4 bg-white rounded-lg border"
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
            onClick={() => handleDelete(alert.id)}
            className="text-muted-foreground hover:text-destructive flex-shrink-0"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      ))}
    </div>
  );
};
