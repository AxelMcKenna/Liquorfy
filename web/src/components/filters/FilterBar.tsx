import { useFilters } from '@/hooks/useFilters';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SlidersHorizontal, X, Sparkles, ArrowUpDown } from 'lucide-react';
import { SortDropdown } from './SortDropdown';
import { SortOption } from '@/types';

interface FilterBarProps {
  onOpenFilters: () => void;
}

export const FilterBar = ({ onOpenFilters }: FilterBarProps) => {
  const { filters, updateFilters, clearFilters, activeFilterCount } = useFilters();

  const categoryLabel = filters.category?.replace('_', ' ');
  const chainCount = filters.chains?.length || 0;
  const hasPriceRange = filters.price_min || filters.price_max;

  return (
    <div className="border-b border-border/40">
      <div className="px-4 py-2.5">
        <div className="flex items-center gap-2 overflow-x-auto no-scrollbar">
          {/* Filter button */}
          <Button
            variant="outline"
            size="sm"
            onClick={onOpenFilters}
            className="flex-shrink-0 gap-1.5 lg:hidden"
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            Filters
            {activeFilterCount > 0 && (
              <Badge className="bg-primary text-white h-5 w-5 p-0 flex items-center justify-center text-[10px] rounded-full">
                {activeFilterCount}
              </Badge>
            )}
          </Button>

          {/* Promo quick toggle */}
          <Button
            variant={filters.promo_only ? 'default' : 'outline'}
            size="sm"
            onClick={() => updateFilters({ promo_only: !filters.promo_only })}
            className="flex-shrink-0 gap-1.5"
          >
            <Sparkles className="h-3.5 w-3.5" />
            Deals
          </Button>

          {/* Active filter chips */}
          {categoryLabel && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => updateFilters({ category: undefined })}
              className="flex-shrink-0 gap-1.5 capitalize"
            >
              {categoryLabel}
              <X className="h-3 w-3" />
            </Button>
          )}

          {chainCount > 0 && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => updateFilters({ chains: [] })}
              className="flex-shrink-0 gap-1.5"
            >
              {chainCount} store{chainCount !== 1 ? 's' : ''}
              <X className="h-3 w-3" />
            </Button>
          )}

          {hasPriceRange && (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => updateFilters({ price_min: undefined, price_max: undefined })}
              className="flex-shrink-0 gap-1.5"
            >
              ${filters.price_min || 0}–${filters.price_max || 200}
              <X className="h-3 w-3" />
            </Button>
          )}

          {activeFilterCount > 1 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFilters}
              className="flex-shrink-0 text-muted-foreground hover:text-foreground"
            >
              Clear all
            </Button>
          )}

          {/* Spacer pushes sort to the right */}
          <div className="flex-1" />

          {/* Sort inline */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground" />
            <SortDropdown
              value={filters.sort || SortOption.BEST_VALUE}
              onChange={(sort) => updateFilters({ sort })}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
