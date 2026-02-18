import { ChainType } from '@/types';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';

interface ChainFilterProps {
  selected: ChainType[];
  onChange: (chains: ChainType[]) => void;
}

const chains: { value: ChainType; label: string }[] = [
  { value: 'countdown', label: 'Countdown' },
  { value: 'liquorland', label: 'Liquorland' },
  { value: 'liquor_centre', label: 'Liquor Centre' },
  { value: 'super_liquor', label: 'Super Liquor' },
  { value: 'bottle_o', label: 'The Bottle-O' },
  { value: 'new_world', label: 'New World' },
  { value: 'paknsave', label: 'Pak\'nSave' },
  { value: 'glengarry', label: 'Glengarry' },
  { value: 'thirsty_liquor', label: 'Thirsty Liquor' },
  { value: 'black_bull', label: 'Black Bull' },
  { value: 'big_barrel', label: 'Big Barrel' },
];

export const ChainFilter = ({ selected, onChange }: ChainFilterProps) => {
  const handleToggle = (chain: ChainType) => {
    const newSelected = selected.includes(chain)
      ? selected.filter((c) => c !== chain)
      : [...selected, chain];
    onChange(newSelected);
  };

  const handleSelectAll = () => {
    onChange(chains.map(c => c.value));
  };

  const handleClearAll = () => {
    onChange([]);
  };

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <div className="flex gap-2 text-xs">
          <button
            onClick={handleSelectAll}
            className="text-primary hover:text-accent transition-colors"
          >
            Select All
          </button>
          {selected.length > 0 && (
            <>
              <span className="text-muted-foreground">|</span>
              <button
                onClick={handleClearAll}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                Clear
              </button>
            </>
          )}
        </div>
      </div>
      <div className="max-h-64 overflow-y-auto space-y-2 pr-2">
        {chains.map((chain) => (
          <div key={chain.value} className="flex items-center space-x-2">
            <Checkbox
              id={chain.value}
              checked={selected.includes(chain.value)}
              onCheckedChange={() => handleToggle(chain.value)}
            />
            <Label
              htmlFor={chain.value}
              className="text-sm font-normal cursor-pointer"
            >
              {chain.label}
            </Label>
          </div>
        ))}
      </div>
    </div>
  );
};
