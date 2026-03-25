import { Product } from '@/types';
import { ProductGrid } from './ProductGrid';
import { Clock } from 'lucide-react';

interface RecentlyViewedProps {
  products: Product[];
}

export const RecentlyViewed = ({ products }: RecentlyViewedProps) => {
  if (products.length === 0) return null;

  return (
    <section className="py-12 border-t">
      <div className="flex items-center gap-2 mb-6">
        <Clock className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-xl font-semibold text-foreground">Recently Viewed</h2>
      </div>
      <ProductGrid products={products.slice(0, 5)} loading={false} />
    </section>
  );
};
