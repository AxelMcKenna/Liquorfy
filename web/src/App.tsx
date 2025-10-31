import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";

interface Price {
  store_id: string;
  store_name: string;
  chain: string;
  price_nzd: number;
  promo_price_nzd?: number | null;
  price_per_100ml?: number | null;
  price_per_standard_drink?: number | null;
  standard_drinks?: number | null;
}

interface Product {
  id: string;
  name: string;
  brand?: string | null;
  category?: string | null;
  price: Price;
  image_url?: string | null;
}

interface ProductListResponse {
  items: Product[];
  total: number;
}

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

const categories = ["beer", "wine", "spirits", "rtd", "cider"];

const App: React.FC = () => {
  const [query, setQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("");
  const [products, setProducts] = useState<ProductListResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [compare, setCompare] = useState<Product[]>([]);

  const fetchProducts = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (query) params.append("q", query);
      if (selectedCategory) params.append("category", selectedCategory);
      const { data } = await axios.get<ProductListResponse>(`${API_BASE}/products`, { params });
      setProducts(data);
    } catch (err) {
      setError("Failed to load products");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const toggleCompare = (product: Product) => {
    setCompare((prev) => {
      const exists = prev.find((p) => p.id === product.id);
      if (exists) {
        return prev.filter((p) => p.id !== product.id);
      }
      if (prev.length >= 4) {
        return prev;
      }
      return [...prev, product];
    });
  };

  const sortedCompare = useMemo(
    () =>
      [...compare].sort(
        (a, b) => (a.price.price_per_100ml ?? Infinity) - (b.price.price_per_100ml ?? Infinity)
      ),
    [compare]
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="bg-slate-900 border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-4 py-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold">Liquorfy</h1>
            <p className="text-sm text-slate-400">Cheapest liquor near you in Aotearoa.</p>
          </div>
          <div className="flex flex-col md:flex-row gap-2 w-full md:w-auto">
            <input
              className="px-4 py-2 rounded bg-slate-800 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              placeholder="Search by name or brand"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") fetchProducts();
              }}
            />
            <select
              className="px-4 py-2 rounded bg-slate-800 border border-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500"
              value={selectedCategory}
              onChange={(event) => setSelectedCategory(event.target.value)}
            >
              <option value="">All categories</option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category.toUpperCase()}
                </option>
              ))}
            </select>
            <button
              onClick={fetchProducts}
              className="px-4 py-2 rounded bg-emerald-600 hover:bg-emerald-500 transition"
            >
              Search
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8">
        {loading && <p>Loading...</p>}
        {error && <p className="text-red-400">{error}</p>}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {products?.items.map((product) => (
            <article key={product.id} className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex flex-col">
              <div className="flex-1">
                <h2 className="text-lg font-semibold">{product.name}</h2>
                <p className="text-sm text-slate-400">{product.brand ?? "Unknown brand"}</p>
                <p className="mt-2 text-2xl font-bold">
                  ${product.price.promo_price_nzd?.toFixed(2) ?? product.price.price_nzd.toFixed(2)}
                </p>
                {product.price.price_per_100ml && (
                  <p className="text-sm text-slate-400">
                    ${product.price.price_per_100ml.toFixed(2)} per 100ml
                  </p>
                )}
                {product.price.price_per_standard_drink && (
                  <p className="text-sm text-slate-400">
                    ${product.price.price_per_standard_drink.toFixed(2)} per standard drink
                  </p>
                )}
              </div>
              <button
                onClick={() => toggleCompare(product)}
                className="mt-4 px-3 py-2 rounded border border-emerald-500 text-emerald-400 hover:bg-emerald-600/10"
              >
                {compare.find((item) => item.id === product.id) ? "Remove" : "Compare"}
              </button>
            </article>
          ))}
        </div>
      </main>

      {compare.length > 0 && (
        <aside className="fixed bottom-0 left-0 right-0 bg-slate-900 border-t border-slate-800">
          <div className="max-w-6xl mx-auto px-4 py-4">
            <h3 className="text-lg font-semibold mb-2">Compare ({compare.length}/4)</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {sortedCompare.map((product) => (
                <div key={product.id} className="bg-slate-800 rounded p-3">
                  <h4 className="font-semibold text-sm">{product.name}</h4>
                  <p className="text-sm text-slate-400">${product.price.price_nzd.toFixed(2)}</p>
                  {product.price.price_per_100ml && (
                    <p className="text-xs text-slate-500">
                      ${product.price.price_per_100ml.toFixed(2)} / 100ml
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </aside>
      )}
    </div>
  );
};

export default App;
