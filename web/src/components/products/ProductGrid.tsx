import { memo } from "react";
import { motion, AnimatePresence } from "framer-motion";
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
    <motion.div
      layout
      className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4"
    >
      <AnimatePresence mode="popLayout">
        {products.map((product, index) => (
          <motion.div
            key={product.id}
            layout
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{
              delay: index * 0.02,
              duration: 0.4,
              layout: { duration: 0.3 }
            }}
          >
            <ProductCard
              product={product}
              isComparing={compareIds.includes(product.id)}
              onToggleCompare={() => onToggleCompare(product)}
              index={index}
              isCompareAtLimit={isCompareAtLimit}
            />
          </motion.div>
        ))}
      </AnimatePresence>
    </motion.div>
  );
};

// Memoize the component to prevent unnecessary re-renders
export const ProductGrid = memo(ProductGridComponent);
