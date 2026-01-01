import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';

interface PriceRangeFilterProps {
  min?: number;
  max?: number;
  onChange: (min?: number, max?: number) => void;
}

export const PriceRangeFilter = ({ min, max, onChange }: PriceRangeFilterProps) => {
  const [localMin, setLocalMin] = useState(min?.toString() ?? '');
  const [localMax, setLocalMax] = useState(max?.toString() ?? '');

  useEffect(() => {
    setLocalMin(min?.toString() ?? '');
  }, [min]);

  useEffect(() => {
    setLocalMax(max?.toString() ?? '');
  }, [max]);

  useEffect(() => {
    const timer = setTimeout(() => {
      const minValue = localMin ? parseFloat(localMin) : undefined;
      const maxValue = localMax ? parseFloat(localMax) : undefined;

      if (minValue !== min || maxValue !== max) {
        onChange(minValue, maxValue);
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [localMin, localMax]);

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-foreground">Price Range</h3>
      <div className="flex items-center gap-2">
        <Input
          type="number"
          placeholder="Min"
          value={localMin}
          onChange={(e) => setLocalMin(e.target.value)}
          className="w-24"
          min="0"
          step="0.01"
        />
        <span className="text-muted-foreground">-</span>
        <Input
          type="number"
          placeholder="Max"
          value={localMax}
          onChange={(e) => setLocalMax(e.target.value)}
          className="w-24"
          min="0"
          step="0.01"
        />
      </div>
    </div>
  );
};
