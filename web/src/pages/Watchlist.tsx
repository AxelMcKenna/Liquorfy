import { Link } from 'react-router-dom';
import { ArrowLeft, Heart, Eye } from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AlertsList } from '@/components/alerts/AlertsList';
import { Footer } from '@/components/layout/Footer';
import { useFavourites } from '@/hooks/useFavourites';
import { useRecentlyViewed } from '@/hooks/useRecentlyViewed';
import { ProductGrid } from '@/components/products/ProductGrid';

const WatchlistPage = () => {
  const { favouriteIds } = useFavourites();
  const { recentlyViewed } = useRecentlyViewed();

  const favouriteProducts = recentlyViewed.filter((p) => favouriteIds.has(p.id));

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background">
        <header className="border-b">
          <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-4">
            <Link to="/" className="text-muted-foreground hover:text-foreground">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <h1 className="text-lg font-semibold">Watchlist</h1>
          </div>
        </header>

        <main className="max-w-3xl mx-auto px-4 py-8 space-y-8">
          {/* Price Alerts */}
          <section>
            <h2 className="text-lg font-serif font-semibold mb-3">Price Alerts</h2>
            <AlertsList />
          </section>

          {/* Favourites */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <Heart className="h-5 w-5 text-red-500" />
              <h2 className="text-lg font-serif font-semibold">Favourites</h2>
              {favouriteIds.size > 0 && (
                <span className="text-sm text-muted-foreground">({favouriteIds.size})</span>
              )}
            </div>
            {favouriteProducts.length > 0 ? (
              <ProductGrid products={favouriteProducts} loading={false} />
            ) : favouriteIds.size > 0 ? (
              <div className="bg-white rounded-lg border p-6 text-center text-muted-foreground">
                <Heart className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  You have {favouriteIds.size} favourited product{favouriteIds.size !== 1 ? 's' : ''}.
                  Browse products to see them here.
                </p>
              </div>
            ) : (
              <div className="bg-white rounded-lg border p-6 text-center text-muted-foreground">
                <Heart className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No favourites yet. Tap the heart icon on any product to save it.</p>
              </div>
            )}
          </section>

          {/* Recently Viewed */}
          {recentlyViewed.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-3">
                <Eye className="h-5 w-5 text-muted-foreground" />
                <h2 className="text-lg font-serif font-semibold">Recently Viewed</h2>
              </div>
              <ProductGrid products={recentlyViewed.slice(0, 10)} loading={false} />
            </section>
          )}
        </main>

        <Footer />
      </div>
    </ProtectedRoute>
  );
};

export default WatchlistPage;
