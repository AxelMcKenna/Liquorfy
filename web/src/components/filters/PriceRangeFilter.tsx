import { useState, useEffect } from 'react';
import { Slider } from '@/components/ui/slider';

interface PriceRangeFilterProps {
  min?: number;
  max?: number;
  onChange: (min?: number, max?: number) => void;
}

const MIN_PRICE = 0;
const MAX_PRICE = 200;
const PRICE_STEP = 1;

export const PriceRangeFilter = ({ min, max, onChange }: PriceRangeFilterProps) => {
  const [range, setRange] = useState<[number, number]>([
    min ?? MIN_PRICE,
    max ?? MAX_PRICE,
  ]);

  useEffect(() => {
    const nextMin = typeof min === 'number' ? min : MIN_PRICE;
    const nextMax = typeof max === 'number' ? max : MAX_PRICE;
    const normalized: [number, number] = nextMin <= nextMax
      ? [nextMin, nextMax]
      : [nextMax, nextMin];

    setRange((prev) => (
      prev[0] === normalized[0] && prev[1] === normalized[1]
        ? prev
        : normalized
    ));
  }, [min, max]);

  useEffect(() => {
    const timer = setTimeout(() => {
      const [localMin, localMax] = range;
      const minValue = localMin !== MIN_PRICE ? localMin : undefined;
      const maxValue = localMax !== MAX_PRICE ? localMax : undefined;
      const minMatch = typeof min === 'number' ? min === minValue : minValue === undefined;
      const maxMatch = typeof max === 'number' ? max === maxValue : maxValue === undefined;

      if (minMatch && maxMatch) {
        return;
      }
      onChange(minValue, maxValue);
    }, 350);

    return () => clearTimeout(timer);
  }, [range, min, max, onChange]);

  return (
    <div className="space-y-4">
      <div className="text-right text-sm text-tertiary-gray">
        ${Math.round(range[0])} - ${Math.round(range[1])}
      </div>
      <Slider
        value={range}
        min={MIN_PRICE}
        max={MAX_PRICE}
        step={PRICE_STEP}
        onValueChange={(value) => {
          if (value.length < 2) return;
          const nextMin = Math.min(value[0], value[1]);
          const nextMax = Math.max(value[0], value[1]);
          setRange([nextMin, nextMax]);
        }}
      />
      <div className="flex items-center justify-between text-xs text-tertiary-gray">
        <span>${MIN_PRICE}</span>
        <span>${MAX_PRICE}+</span>
      </div>
    </div>
  );
};
