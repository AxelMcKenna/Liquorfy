import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Header } from "@/components/layout/Header";
import { ProductGrid } from "@/components/products/ProductGrid";
import { ComparisonTray } from "@/components/layout/ComparisonTray";
import { useProducts } from "@/hooks/useProducts";
import { useCompare } from "@/hooks/useCompare";

const App = () => {
  const [query, setQuery] = useState("");

  const { products, loading, error, fetchProducts } = useProducts();
  const { compare, sortedCompare, toggleCompare, clearCompare } = useCompare();

  useEffect(() => {
    fetchProducts("", "");
  }, [fetchProducts]);

  const handleSearch = () => {
    fetchProducts(query, "");
  };

  return (
    <div className="min-h-screen bg-background">
      <Header
        query={query}
        setQuery={setQuery}
        onSearch={handleSearch}
      />

      <main className="max-w-7xl mx-auto px-4 py-8 pb-32">
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-destructive/10 border-2 border-destructive rounded-lg p-4 mb-6"
          >
            <p className="text-destructive font-medium">{error}</p>
          </motion.div>
        )}

        <ProductGrid
          products={products?.items ?? []}
          loading={loading}
          compareIds={compare.map((p) => p.id)}
          onToggleCompare={toggleCompare}
        />

        {!loading && products?.items.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-12"
          >
            <p className="text-muted-foreground text-lg">
              No products found. Try adjusting your search.
            </p>
          </motion.div>
        )}
      </main>

      <ComparisonTray products={sortedCompare} onClear={clearCompare} />
    </div>
  );
};

export default App;
