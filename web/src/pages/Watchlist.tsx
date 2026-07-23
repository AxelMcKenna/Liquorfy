import { Link, useNavigate } from 'react-router-dom';
import { Heart, Settings, Bell, Search, ArrowRight, Eye } from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AlertsList } from '@/components/alerts/AlertsList';
import { Footer } from '@/components/layout/Footer';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { SectionHeader } from '@/components/ui/section-header';
import { useFavourites } from '@/hooks/useFavourites';
import { useFavouriteProducts } from '@/hooks/useFavouriteProducts';
import { useRecentlyViewed } from '@/hooks/useRecentlyViewed';
import { ProductGrid } from '@/components/products/ProductGrid';
import { ProductSkeleton } from '@/components/products/ProductSkeleton';

const Reveal = ({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) => {
  return <div className={className}>{children}</div>;
};

const StatPill = ({ icon: Icon, value, label }: { icon: React.ElementType; value: number; label: string }) => (
  <Card variant="flat" className="flex items-center gap-2.5 px-4 py-2">
    <Icon className="h-4 w-4 text-muted-foreground" />
    <span className="text-sm font-semibold text-foreground">{value}</span>
    <span className="text-sm text-muted-foreground">{label}</span>
  </Card>
);

const WatchlistPage = () => {
  const navigate = useNavigate();
  const { favouriteIds } = useFavourites();
  const { products: favouriteProducts, loading: favouritesLoading } = useFavouriteProducts(favouriteIds);
  const { recentlyViewed } = useRecentlyViewed();

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background flex flex-col">
        <PageHeader
          rightContent={
            <Link
              to="/settings"
              aria-label="Settings"
              className="flex items-center justify-center h-11 w-11 rounded-lg text-white/80 hover:text-white hover:bg-white/10 transition-colors"
            >
              <Settings className="h-4 w-4" />
            </Link>
          }
        />

        <main className="max-w-6xl mx-auto px-4 w-full flex-1">

          {/* ── Page intro ── */}
          <div className="pt-10 md:pt-14 pb-8">
            <h1 className="font-display text-3xl md:text-4xl font-semibold text-foreground tracking-tight leading-tight">
              Your Watchlist
            </h1>
            <p className="text-muted-foreground mt-2 text-[15px]">
              Favourites, alerts, and recently viewed - all in one place.
            </p>

            <div className="flex flex-wrap gap-3 mt-5">
              <StatPill icon={Heart} value={favouriteIds.size} label="favourites" />
              <StatPill icon={Eye} value={recentlyViewed.length} label="viewed" />
            </div>
          </div>

          <div className="space-y-14 pb-14">

            {/* ── Price Alerts ── */}
            <Reveal>
              <section>
                <div className="flex items-center justify-between mb-5">
                  <SectionHeader
                    className="w-full"
                    title="Price Alerts"
                    description="Get notified when prices drop"
                    action={
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-primary"
                        onClick={() => navigate('/explore')}
                      >
                        Browse products
                        <ArrowRight className="ml-1 h-4 w-4" />
                      </Button>
                    }
                  />
                </div>
                <AlertsList />
              </section>
            </Reveal>

            {/* ── Favourites ── */}
            <Reveal>
              <section>
                <SectionHeader
                  className="mb-5"
                  title={
                    <span className="flex items-center gap-2">
                      Favourites
                      {favouriteIds.size > 0 && (
                        <span className="text-sm text-muted-foreground font-normal">({favouriteIds.size})</span>
                      )}
                    </span>
                  }
                  description="Products you've saved"
                />

                {favouritesLoading ? (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                    {Array.from({ length: Math.min(favouriteIds.size, 10) || 4 }).map((_, i) => (
                      <ProductSkeleton key={i} />
                    ))}
                  </div>
                ) : favouriteProducts.length > 0 ? (
                  <ProductGrid products={favouriteProducts} loading={false} />
                ) : (
                  <EmptyState
                    icon={Heart}
                    className="border border-dashed rounded-xl px-6 py-10 md:py-14"
                    title={
                      favouriteIds.size > 0
                        ? 'Some favourited products may no longer be available'
                        : 'No favourites yet'
                    }
                    description={
                      favouriteIds.size > 0
                        ? 'Try browsing for similar products'
                        : 'Tap the heart icon on any product to save it here'
                    }
                    action={
                      <Button variant="outline" size="sm" onClick={() => navigate('/explore')}>
                        <Search className="h-4 w-4 mr-2" />
                        Browse products
                      </Button>
                    }
                  />
                )}
              </section>
            </Reveal>

            {/* ── Recently Viewed ── */}
            {recentlyViewed.length > 0 && (
              <Reveal>
                <section>
                  <SectionHeader
                    className="mb-5"
                    title="Recently Viewed"
                    description="Pick up where you left off"
                    action={
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-primary"
                        onClick={() => navigate('/explore')}
                      >
                        Explore more
                        <ArrowRight className="ml-1 h-4 w-4" />
                      </Button>
                    }
                  />
                  <ProductGrid products={recentlyViewed.slice(0, 10)} loading={false} />
                </section>
              </Reveal>
            )}
          </div>
        </main>

        <Footer />
      </div>
    </ProtectedRoute>
  );
};

export default WatchlistPage;
