import { memo } from "react";
import { Product } from "@/types";
import { ProductCard } from "./ProductCard";
import { ProductSkeleton } from "./ProductSkeleton";

interface ProductGridProps {
  products: Product[];
  loading: boolean;
  compareIds: string[];
  onToggleCompare: (product: Product) => void;
  isCompareAtLimit?: boolean;
}

const ProductGridComponent = ({
  products,
  loading,
  compareIds,
  onToggleCompare,
  isCompareAtLimit = false,
}: ProductGridProps) => {
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
          isComparing={compareIds.includes(product.id)}
          onToggleCompare={() => onToggleCompare(product)}
          index={index}
          isCompareAtLimit={isCompareAtLimit}
        />
      ))}
    </div>
  );
};

export const ProductGrid = memo(ProductGridComponent);
