import { memo } from "react";
import { Product } from "@/types";
import { ProductCard } from "./ProductCard";
import { ProductSkeleton } from "./ProductSkeleton";
import { useFavourites } from "@/hooks/useFavourites";
import { useRecentlyViewed } from "@/hooks/useRecentlyViewed";

interface ProductGridProps {
  products: Product[];
  loading: boolean;
}

const ProductGridComponent = ({
  products,
  loading,
}: ProductGridProps) => {
  const { isFavourite, toggleFavourite } = useFavourites();
  const { addProduct } = useRecentlyViewed();

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {Array.from({ length: 10 }).map((_, i) => (
          <ProductSkeleton key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {products.map((product, index) => (
        <ProductCard
          key={product.id}
          product={product}
          index={index}
          isFavourite={isFavourite(product.id)}
          onToggleFavourite={() => toggleFavourite(product.id)}
          onView={() => addProduct(product)}
        />
      ))}
    </div>
  );
};

export const ProductGrid = memo(ProductGridComponent);
