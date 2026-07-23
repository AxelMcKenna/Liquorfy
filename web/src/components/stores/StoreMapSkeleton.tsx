import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { MapSurface } from './MapSurface';

interface StoreMapSkeletonProps {
  className?: string;
}

export const StoreMapSkeleton = ({ className }: StoreMapSkeletonProps) => {
  return (
    <MapSurface className={cn("border-2 border-gray-200", className)}>
      <Skeleton className="h-full w-full" />
    </MapSurface>
  );
};
