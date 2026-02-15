import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Header } from "@/components/layout/Header";
import { ProductGrid } from "@/components/products/ProductGrid";
import { useProducts } from "@/hooks/useProducts";

const App = () => {
  const [query, setQuery] = useState("");

  const { products, loading, error, fetchProducts } = useProducts();

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
    </div>
  );
};

export default App;
