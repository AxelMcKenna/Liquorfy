import { useFilters } from '@/hooks/useFilters';
import { SortDropdown } from './SortDropdown';
import { SortOption } from '@/types';

export const ResultsBar = () => {
  const { filters, updateFilters } = useFilters();
  const currentSort = filters.sort ?? SortOption.BEST_VALUE;

  return (
    <div className="mb-4 flex justify-end">
      <div className="flex w-full flex-col gap-1.5 sm:w-56">
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
