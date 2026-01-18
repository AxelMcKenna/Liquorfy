import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

interface StoreMapSkeletonProps {
  className?: string;
}

export const StoreMapSkeleton = ({ className }: StoreMapSkeletonProps) => {
  return (
    <div className={cn("w-full h-[500px] rounded-lg overflow-hidden border-2 border-gray-200", className)}>
      <Skeleton className="h-full w-full" />
    </div>
  );
};
