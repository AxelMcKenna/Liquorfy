import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';

interface PromoToggleProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
}

export const PromoToggle = ({ checked, onChange }: PromoToggleProps) => {
  return (
    <div className="flex items-center space-x-2">
      <Checkbox
        id="promo-only"
        checked={checked}
        onCheckedChange={(checkedState) => onChange(checkedState === true)}
      />
      <Label
        htmlFor="promo-only"
        className="text-sm font-medium cursor-pointer"
      >
        Promo items only
      </Label>
    </div>
  );
};
