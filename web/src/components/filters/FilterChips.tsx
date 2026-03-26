import { useFilters } from '@/hooks/useFilters';
import { cn } from '@/lib/utils';
import { Tag, Wine, Beer, Martini, CupSoda, X } from 'lucide-react';

const CATEGORY_GROUPS = [
  { value: 'beer', label: 'Beer', icon: Beer },
  { value: 'wine', label: 'Wine', icon: Wine },
  { value: 'spirits', label: 'Spirits', icon: Martini },
  { value: 'rtd', label: 'RTDs', icon: CupSoda },
] as const;

export const FilterChips = () => {
  const { filters, updateFilters } = useFilters();

  const toggleCategory = (category: string) => {
    updateFilters({ category: filters.category === category ? undefined : category });
  };

  const togglePromo = () => {
    updateFilters({ promo_only: !filters.promo_only });
  };

  return (
    <div className="flex gap-2 overflow-x-auto pb-1 no-scrollbar lg:hidden mb-3">
      {/* Deals chip */}
      <button
        onClick={togglePromo}
        className={cn(
          "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap border transition-colors flex-shrink-0",
          filters.promo_only
            ? "bg-primary text-white border-primary"
            : "bg-white text-[hsl(var(--foreground-secondary))] border-[hsl(var(--border))] hover:border-primary/40"
        )}
      >
        <Tag className="h-3 w-3" />
        Deals
        {filters.promo_only && <X className="h-3 w-3 ml-0.5" />}
      </button>

      {/* Category chips */}
      {CATEGORY_GROUPS.map(({ value, label, icon: Icon }) => {
        const isActive = filters.category === value;
        return (
          <button
            key={value}
            onClick={() => toggleCategory(value)}
            className={cn(
              "flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap border transition-colors flex-shrink-0",
              isActive
                ? "bg-primary text-white border-primary"
                : "bg-white text-[hsl(var(--foreground-secondary))] border-[hsl(var(--border))] hover:border-primary/40"
            )}
          >
            <Icon className="h-3 w-3" />
            {label}
            {isActive && <X className="h-3 w-3 ml-0.5" />}
          </button>
        );
      })}

      {/* Active category label if subcategory selected */}
      {filters.category && !CATEGORY_GROUPS.some(g => g.value === filters.category) && (
        <button
          onClick={() => updateFilters({ category: undefined })}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap border transition-colors flex-shrink-0 bg-primary text-white border-primary"
        >
          {filters.category.replace('_', ' ')}
          <X className="h-3 w-3 ml-0.5" />
        </button>
      )}
    </div>
  );
};
