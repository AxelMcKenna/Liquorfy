import { Link } from 'react-router-dom';
import { Heart, Eye, Loader2, Settings } from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AlertsList } from '@/components/alerts/AlertsList';
import { Footer } from '@/components/layout/Footer';
import { PageHeader } from '@/components/layout/PageHeader';
import { useFavourites } from '@/hooks/useFavourites';
import { useFavouriteProducts } from '@/hooks/useFavouriteProducts';
import { useRecentlyViewed } from '@/hooks/useRecentlyViewed';
import { ProductGrid } from '@/components/products/ProductGrid';

const WatchlistPage = () => {
  const { favouriteIds } = useFavourites();
  const { products: favouriteProducts, loading: favouritesLoading } = useFavouriteProducts(favouriteIds);
  const { recentlyViewed } = useRecentlyViewed();

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background flex flex-col">
        <PageHeader
          rightContent={
            <Link to="/settings" className="flex items-center justify-center h-8 w-8 rounded-md text-white/70 hover:text-white hover:bg-white/10 transition-colors">
              <Settings className="h-4 w-4" />
            </Link>
          }
        />

        <main className="max-w-3xl mx-auto px-4 py-8 space-y-8 flex-1">
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
            {favouritesLoading ? (
              <div className="bg-white rounded-lg border p-6 flex items-center justify-center gap-2 text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span className="text-sm">Loading favourites...</span>
              </div>
            ) : favouriteProducts.length > 0 ? (
              <ProductGrid products={favouriteProducts} loading={false} />
            ) : favouriteIds.size > 0 ? (
              <div className="bg-white rounded-lg border p-6 text-center text-muted-foreground">
                <Heart className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">
                  Some favourited products may no longer be available.
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
