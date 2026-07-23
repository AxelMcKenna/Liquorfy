import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Bell, Trash2, TrendingDown, Tag, ChevronRight } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { InlineAlert } from '@/components/ui/inline-alert';
import { Skeleton } from '@/components/ui/skeleton';
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
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <Card key={i} variant="flat" className="flex items-center gap-4 p-4">
            <Skeleton className="h-10 w-10 rounded-full flex-shrink-0" />
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-1/2" />
            </div>
            <Skeleton className="h-8 w-8 rounded" />
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <InlineAlert variant="error" className="text-center">
        {error}
      </InlineAlert>
    );
  }

  if (alerts.length === 0) {
    return (
      <EmptyState
        icon={Bell}
        title="No price alerts set"
        description="Tap the bell icon on any product to get notified when prices drop."
        className="rounded-xl border border-dashed px-6 py-10"
      />
    );
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert) => (
        <Card
          key={alert.id}
          variant="interactive"
          className="group flex items-center rounded-lg hover:bg-primary/5"
        >
          <Link
            to={`/product/${alert.product_id}`}
            className="flex min-w-0 flex-1 items-center gap-3 rounded-l-[inherit] p-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-inset sm:gap-4 sm:p-4"
            aria-label={`View alert for ${alert.product_name || 'unknown product'}`}
          >
            <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
              <Bell className="h-4 w-4 text-primary" />
            </div>

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

            <ChevronRight className="h-4 w-4 flex-shrink-0 text-muted-foreground/50" />
          </Link>

          <div className="flex-shrink-0 pr-2 sm:pr-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => handleDelete(alert.id)}
              aria-label={`Delete alert for ${alert.product_name || 'unknown product'}`}
              className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );
};
