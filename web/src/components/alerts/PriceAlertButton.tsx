import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, TrendingDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { useAuth } from '@/contexts/AuthContext';
import { useAlerts } from '@/hooks/useAlerts';
import { toast } from 'sonner';

interface PriceAlertButtonProps {
  productId: string;
  productName: string;
  currentPrice: number;
}

export const PriceAlertButton = ({
  productId,
  productName,
  currentPrice,
}: PriceAlertButtonProps) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { createAlert } = useAlerts();
  const [open, setOpen] = useState(false);
  const [thresholdPrice, setThresholdPrice] = useState('');
  const [alertOnPromo, setAlertOnPromo] = useState(false);
  const [saving, setSaving] = useState(false);

  const handleClick = () => {
    if (!user) {
      navigate('/login');
      return;
    }
    setThresholdPrice((currentPrice * 0.9).toFixed(2));
    setAlertOnPromo(false);
    setOpen(true);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await createAlert({
        product_id: productId,
        threshold_price: thresholdPrice ? parseFloat(thresholdPrice) : undefined,
        alert_on_promo: alertOnPromo,
      });
      toast.success(`Alert set for ${productName}`, {
        description: 'Manage alerts in your Watchlist',
        action: {
          label: 'View',
          onClick: () => navigate('/watchlist'),
        },
      });
      setOpen(false);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      toast.error(detail || 'Failed to create alert');
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleClick}
        className="gap-1.5 text-muted-foreground hover:text-primary"
        title="Set price alert"
      >
        <Bell className="h-4 w-4" />
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <Bell className="h-4 w-4 text-primary" />
              </div>
              Set Price Alert
            </DialogTitle>
          </DialogHeader>

          {/* Product info card */}
          <div className="bg-secondary rounded-lg p-3 flex items-center gap-3">
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium text-foreground truncate">{productName}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                Current price: <span className="font-semibold text-primary">${currentPrice.toFixed(2)}</span>
              </p>
            </div>
          </div>

          <div className="space-y-5 pt-1">
            {/* Threshold input */}
            <div>
              <Label htmlFor="threshold" className="flex items-center gap-1.5 text-sm font-medium mb-2">
                <TrendingDown className="h-3.5 w-3.5 text-primary" />
                Alert when price drops below
              </Label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">$</span>
                <Input
                  id="threshold"
                  type="number"
                  step="0.01"
                  min="0"
                  value={thresholdPrice}
                  onChange={(e) => setThresholdPrice(e.target.value)}
                  placeholder="0.00"
                  className="pl-7"
                />
              </div>
            </div>

            {/* Promo checkbox */}
            <div className="flex items-start gap-3 p-3 rounded-lg border hover:border-primary/30 transition-colors">
              <Checkbox
                id="promo"
                checked={alertOnPromo}
                onCheckedChange={(v) => setAlertOnPromo(!!v)}
                className="mt-0.5"
              />
              <div>
                <Label htmlFor="promo" className="text-sm font-medium cursor-pointer">
                  Alert on promotions
                </Label>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Get notified when this product goes on sale
                </p>
              </div>
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              disabled={saving || (!thresholdPrice && !alertOnPromo)}
              className="gap-1.5"
            >
              <Bell className="h-4 w-4" />
              {saving ? 'Saving...' : 'Set Alert'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
