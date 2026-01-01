import { Category } from '@/types';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface CategoryFilterProps {
  value?: string;
  onChange: (category?: string) => void;
}

const categories: { value: Category; label: string; group: string }[] = [
  // Beer
  { value: 'beer', label: 'All Beer', group: 'Beer' },
  { value: 'lager', label: 'Lager', group: 'Beer' },
  { value: 'ale', label: 'Ale', group: 'Beer' },
  { value: 'ipa', label: 'IPA', group: 'Beer' },
  { value: 'stout', label: 'Stout', group: 'Beer' },
  { value: 'craft_beer', label: 'Craft Beer', group: 'Beer' },

  // Wine
  { value: 'wine', label: 'All Wine', group: 'Wine' },
  { value: 'red_wine', label: 'Red Wine', group: 'Wine' },
  { value: 'white_wine', label: 'White Wine', group: 'Wine' },
  { value: 'rose', label: 'Rosé', group: 'Wine' },
  { value: 'sparkling', label: 'Sparkling Wine', group: 'Wine' },
  { value: 'champagne', label: 'Champagne', group: 'Wine' },

  // Spirits
  { value: 'spirits', label: 'All Spirits', group: 'Spirits' },
  { value: 'vodka', label: 'Vodka', group: 'Spirits' },
  { value: 'gin', label: 'Gin', group: 'Spirits' },
  { value: 'rum', label: 'Rum', group: 'Spirits' },
  { value: 'whisky', label: 'Whisky', group: 'Spirits' },
  { value: 'bourbon', label: 'Bourbon', group: 'Spirits' },
  { value: 'scotch', label: 'Scotch', group: 'Spirits' },
  { value: 'tequila', label: 'Tequila', group: 'Spirits' },
  { value: 'brandy', label: 'Brandy', group: 'Spirits' },
  { value: 'liqueur', label: 'Liqueur', group: 'Spirits' },

  // Other
  { value: 'rtd', label: 'RTD (Ready to Drink)', group: 'Other' },
  { value: 'cider', label: 'Cider', group: 'Other' },
  { value: 'mixer', label: 'Mixers', group: 'Other' },
  { value: 'non_alcoholic', label: 'Non-Alcoholic', group: 'Other' },
];

const groupedCategories = categories.reduce((acc, cat) => {
  if (!acc[cat.group]) {
    acc[cat.group] = [];
  }
  acc[cat.group].push(cat);
  return acc;
}, {} as Record<string, typeof categories>);

export const CategoryFilter = ({ value, onChange }: CategoryFilterProps) => {
  return (
    <div className="flex items-center gap-2">
      <label htmlFor="category" className="text-sm font-medium text-foreground whitespace-nowrap">
        Category:
      </label>
      <Select
        value={value || 'all'}
        onValueChange={(val) => onChange(val === 'all' ? undefined : val)}
      >
        <SelectTrigger id="category" className="w-[180px]">
          <SelectValue placeholder="All Categories" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Categories</SelectItem>
          {Object.entries(groupedCategories).map(([group, items]) => (
            <div key={group}>
              <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
                {group}
              </div>
              {items.map((cat) => (
                <SelectItem key={cat.value} value={cat.value}>
                  {cat.label}
                </SelectItem>
              ))}
            </div>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
};
