import { Product } from '@/types';
import { ProductGrid } from './ProductGrid';
import { Clock } from 'lucide-react';

interface RecentlyViewedProps {
  products: Product[];
  /** Full-bleed section whose border-t spans the viewport; inner content stays in a max-w-7xl column. */
  fullWidth?: boolean;
}

export const RecentlyViewed = ({ products, fullWidth = false }: RecentlyViewedProps) => {
  if (products.length === 0) return null;

  const content = (
    <>
      <div className="flex items-center gap-2 mb-6">
        <Clock className="h-5 w-5 text-muted-foreground" />
        <h2 className="text-xl font-semibold text-foreground">Recently Viewed</h2>
      </div>
      <ProductGrid products={products.slice(0, 5)} loading={false} />
    </>
  );

  return (
    <section className="py-12 border-t">
      {fullWidth ? (
        <div className="max-w-7xl mx-auto px-4">{content}</div>
      ) : (
        content
      )}
    </section>
  );
};
