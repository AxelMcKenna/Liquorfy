import { SortOption } from '@/types';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface SortDropdownProps {
  value: SortOption;
  onChange: (value: SortOption) => void;
}

const sortOptions = [
  { value: SortOption.DISCOUNT, label: 'Largest Discount' },
  { value: SortOption.BEST_VALUE, label: 'Best Value (per 100ml)' },
  { value: SortOption.CHEAPEST, label: 'Cheapest' },
  { value: SortOption.BEST_PER_DRINK, label: 'Best per Drink' },
  { value: SortOption.DISTANCE, label: 'Nearest Store' },
  { value: SortOption.NEWEST, label: 'Newest' },
];

export const SortDropdown = ({ value, onChange }: SortDropdownProps) => {
  return (
    <div className="flex items-center gap-2">
      <label htmlFor="sort" className="text-sm font-medium text-foreground whitespace-nowrap">
        Sort by:
      </label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id="sort" className="w-[200px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {sortOptions.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};
