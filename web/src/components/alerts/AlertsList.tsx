import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Trash2, TrendingDown, Tag, ChevronRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
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
          <div key={i} className="flex items-center gap-4 p-4 bg-white rounded-lg border">
            <Skeleton className="h-10 w-10 rounded-full flex-shrink-0" />
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
            <Skeleton className="h-8 w-8 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8 text-center">
        <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center mx-auto mb-3">
          <Bell className="h-6 w-6 text-red-400" />
        </div>
        <p className="text-sm text-destructive">{error}</p>
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="border border-dashed rounded-xl p-8 sm:p-10 text-center">
        <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
          <Bell className="h-6 w-6 text-primary" />
        </div>
        <p className="text-foreground font-medium mb-1">No price alerts set</p>
        <p className="text-sm text-muted-foreground max-w-xs mx-auto">
          Tap the bell icon on any product to get notified when prices drop.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert) => (
        <div
          key={alert.id}
          role="button"
          tabIndex={0}
          onClick={() => navigate(`/product/${alert.product_id}`)}
          onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') navigate(`/product/${alert.product_id}`); }}
          className="flex items-center gap-3 sm:gap-4 p-3 sm:p-4 bg-white rounded-lg border hover:border-primary/30 hover:bg-primary/5 transition-colors cursor-pointer group"
        >
          {/* Icon */}
          <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
            <Bell className="h-4 w-4 text-primary" />
          </div>

          {/* Content */}
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-foreground truncate group-hover:text-primary transition-colors">
              {alert.product_name || 'Unknown product'}
            </p>
            <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
              {alert.threshold_price && (
                <Badge variant="outline" className="text-[11px] gap-1 px-2 py-0 h-5 font-normal">
                  <TrendingDown className="h-3 w-3" />
                  Below ${alert.threshold_price.toFixed(2)}
                </Badge>
              )}
              {alert.alert_on_promo && (
                <Badge variant="outline" className="text-[11px] gap-1 px-2 py-0 h-5 font-normal">
                  <Tag className="h-3 w-3" />
                  On promo
                </Badge>
              )}
              {!alert.active && (
                <Badge className="bg-amber-100 text-amber-700 border-amber-200 text-[11px] px-2 py-0 h-5 font-normal">
                  Paused
                </Badge>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-1 flex-shrink-0">
            <Button
              variant="ghost"
              size="icon"
              onClick={(e) => { e.stopPropagation(); handleDelete(alert.id); }}
              className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
            <ChevronRight className="h-4 w-4 text-muted-foreground/50" />
          </div>
        </div>
      ))}
    </div>
  );
};
