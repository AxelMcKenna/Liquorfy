import { useEffect, useState } from 'react';
import { useFilters } from '@/hooks/useFilters';
import { SortDropdown } from './SortDropdown';
import { SortOption } from '@/types';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Wine, X } from 'lucide-react';

const parseOptionalFloat = (raw: string): number | undefined => {
  const trimmed = raw.trim();
  if (trimmed === '') return undefined;
  const parsed = parseFloat(trimmed);
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined;
};

export const ResultsBar = () => {
  const { filters, updateFilters } = useFilters();

  const [minDraft, setMinDraft] = useState<string>(
    filters.std_drinks_min !== undefined ? String(filters.std_drinks_min) : ''
  );
  const [maxDraft, setMaxDraft] = useState<string>(
    filters.std_drinks_max !== undefined ? String(filters.std_drinks_max) : ''
  );

  useEffect(() => {
    setMinDraft(filters.std_drinks_min !== undefined ? String(filters.std_drinks_min) : '');
  }, [filters.std_drinks_min]);

  useEffect(() => {
    setMaxDraft(filters.std_drinks_max !== undefined ? String(filters.std_drinks_max) : '');
  }, [filters.std_drinks_max]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const nextMin = parseOptionalFloat(minDraft);
      const nextMax = parseOptionalFloat(maxDraft);
      if (nextMin === filters.std_drinks_min && nextMax === filters.std_drinks_max) return;
      updateFilters({ std_drinks_min: nextMin, std_drinks_max: nextMax });
    }, 400);
    return () => window.clearTimeout(timer);
  }, [minDraft, maxDraft, filters.std_drinks_min, filters.std_drinks_max, updateFilters]);

  const hasStdDrinksFilter =
    filters.std_drinks_min !== undefined || filters.std_drinks_max !== undefined;

  const clearStdDrinks = () => {
    setMinDraft('');
    setMaxDraft('');
    updateFilters({ std_drinks_min: undefined, std_drinks_max: undefined });
  };

  const currentSort = filters.sort ?? SortOption.BEST_VALUE;

  return (
    <div className="mb-4 flex flex-col gap-3 rounded-lg border border-border/40 bg-white p-3 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex flex-col gap-1.5">
        <label className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-secondary-gray">
          <Wine className="h-3.5 w-3.5 text-primary" />
          Standard drinks
        </label>
        <div className="flex items-center gap-2">
          <Input
            type="number"
            inputMode="decimal"
            min={0}
            step={0.5}
            placeholder="Min"
            value={minDraft}
            onChange={(e) => setMinDraft(e.target.value)}
            className="h-9 w-24 text-sm"
            aria-label="Minimum standard drinks"
          />
          <span className="text-tertiary-gray text-sm">–</span>
          <Input
            type="number"
            inputMode="decimal"
            min={0}
            step={0.5}
            placeholder="Max"
            value={maxDraft}
            onChange={(e) => setMaxDraft(e.target.value)}
            className="h-9 w-24 text-sm"
            aria-label="Maximum standard drinks"
          />
          {hasStdDrinksFilter && (
            <Button
              variant="ghost"
              size="icon"
              onClick={clearStdDrinks}
              className="h-8 w-8 text-secondary-gray hover:text-primary-gray"
              aria-label="Clear standard drinks filter"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      <div className="flex flex-col gap-1.5 sm:w-56">
        <label htmlFor="sort" className="text-xs font-semibold uppercase tracking-wide text-secondary-gray">
          Sort by
        </label>
        <SortDropdown
          value={currentSort}
          onChange={(sort) => updateFilters({ sort })}
        />
      </div>
    </div>
  );
};
