import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell } from 'lucide-react';
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
      toast.success(`Alert set for ${productName}`);
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
            <DialogTitle>Set Price Alert</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">{productName}</p>
          <p className="text-sm">
            Current price: <strong>${currentPrice.toFixed(2)}</strong>
          </p>
          <div className="space-y-4 pt-2">
            <div>
              <Label htmlFor="threshold">Alert when price drops below ($)</Label>
              <Input
                id="threshold"
                type="number"
                step="0.01"
                min="0"
                value={thresholdPrice}
                onChange={(e) => setThresholdPrice(e.target.value)}
                placeholder="e.g. 25.00"
                className="mt-1"
              />
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="promo"
                checked={alertOnPromo}
                onCheckedChange={(v) => setAlertOnPromo(!!v)}
              />
              <Label htmlFor="promo" className="text-sm font-normal">
                Also alert me when this goes on promo
              </Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSave} disabled={saving || (!thresholdPrice && !alertOnPromo)}>
              {saving ? 'Saving...' : 'Set Alert'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
