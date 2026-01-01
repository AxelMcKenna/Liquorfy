import { useFilters } from '@/hooks/useFilters';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SlidersHorizontal } from 'lucide-react';

interface FilterBarProps {
  onOpenFilters: () => void;
}

export const FilterBar = ({ onOpenFilters }: FilterBarProps) => {
  const { activeFilterCount } = useFilters();

  return (
    <div className="bg-white border-b border-subtle lg:hidden">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
        <Button
          variant="outline"
          onClick={onOpenFilters}
          className="flex items-center gap-2 border-subtle py-4 px-4"
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filters
          {activeFilterCount > 0 && (
            <Badge className="bg-primary text-white ml-1">
              {activeFilterCount}
            </Badge>
          )}
        </Button>
      </div>
    </div>
  );
};
