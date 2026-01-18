import { lazy, Suspense } from 'react';
import { StoreMapSkeleton } from '@/components/stores/StoreMapSkeleton';
import type { StoreMapProps } from '@/components/stores/StoreMap';

const StoreMap = lazy(() =>
  import('@/components/stores/StoreMap').then((module) => ({ default: module.StoreMap }))
);

interface LazyStoreMapProps extends StoreMapProps {
  fallbackClassName?: string;
}

export const LazyStoreMap = ({ fallbackClassName, ...props }: LazyStoreMapProps) => {
  return (
    <Suspense fallback={<StoreMapSkeleton className={fallbackClassName} />}>
      <StoreMap {...props} />
    </Suspense>
  );
};
