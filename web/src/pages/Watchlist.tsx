import { useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, useInView } from 'framer-motion';
import { Heart, Settings, Bell, Search, ArrowRight, Eye } from 'lucide-react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AlertsList } from '@/components/alerts/AlertsList';
import { Footer } from '@/components/layout/Footer';
import { PageHeader } from '@/components/layout/PageHeader';
import { Button } from '@/components/ui/button';
import { useFavourites } from '@/hooks/useFavourites';
import { useFavouriteProducts } from '@/hooks/useFavouriteProducts';
import { useRecentlyViewed } from '@/hooks/useRecentlyViewed';
import { ProductGrid } from '@/components/products/ProductGrid';
import { ProductSkeleton } from '@/components/products/ProductSkeleton';

/* Scroll-triggered reveal */
const Reveal = ({
  children,
  className = '',
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-40px' });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 24 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.55, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

const StatPill = ({ icon: Icon, value, label }: { icon: React.ElementType; value: number; label: string }) => (
  <div className="flex items-center gap-2.5 px-4 py-2 bg-white rounded-lg border">
    <Icon className="h-4 w-4 text-muted-foreground" />
    <span className="text-sm font-semibold text-foreground">{value}</span>
    <span className="text-sm text-muted-foreground">{label}</span>
  </div>
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
            <Link to="/settings" className="flex items-center justify-center h-8 w-8 rounded-md text-white/70 hover:text-white hover:bg-white/10 transition-colors">
              <Settings className="h-4 w-4" />
            </Link>
          }
        />

        <main className="max-w-6xl mx-auto px-4 w-full flex-1">

          {/* ── Page intro ── */}
          <motion.div
            className="pt-10 md:pt-14 pb-8"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          >
            <h1 className="font-display text-3xl md:text-4xl font-semibold text-foreground tracking-tight leading-tight">
              Your Watchlist
            </h1>
            <p className="text-muted-foreground mt-2 text-[15px]">
              Favourites, alerts, and recently viewed — all in one place.
            </p>

            <div className="flex flex-wrap gap-3 mt-5">
              <StatPill icon={Heart} value={favouriteIds.size} label="favourites" />
              <StatPill icon={Eye} value={recentlyViewed.length} label="viewed" />
            </div>
          </motion.div>

          <div className="space-y-14 pb-14">

            {/* ── Price Alerts ── */}
            <Reveal>
              <section>
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <hr className="accent-rule mb-3" />
                    <h2 className="text-xl md:text-2xl font-semibold text-foreground tracking-tight">
                      Price Alerts
                    </h2>
                    <p className="text-sm text-muted-foreground mt-1">
                      Get notified when prices drop
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-primary"
                    onClick={() => navigate('/explore')}
                  >
                    Browse products
                    <ArrowRight className="ml-1 h-4 w-4" />
                  </Button>
                </div>
                <AlertsList />
              </section>
            </Reveal>

            {/* ── Favourites ── */}
            <Reveal>
              <section>
                <div className="flex items-center justify-between mb-5">
                  <div>
                    <hr className="accent-rule mb-3" />
                    <div className="flex items-center gap-2">
                      <h2 className="text-xl md:text-2xl font-semibold text-foreground tracking-tight">
                        Favourites
                      </h2>
                      {favouriteIds.size > 0 && (
                        <span className="text-sm text-muted-foreground font-normal">({favouriteIds.size})</span>
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      Products you've saved
                    </p>
                  </div>
                </div>

                {favouritesLoading ? (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                    {Array.from({ length: Math.min(favouriteIds.size, 10) || 4 }).map((_, i) => (
                      <ProductSkeleton key={i} />
                    ))}
                  </div>
                ) : favouriteProducts.length > 0 ? (
                  <ProductGrid products={favouriteProducts} loading={false} />
                ) : (
                  <div className="border border-dashed rounded-xl p-10 md:p-14 text-center">
                    <div className="w-12 h-12 rounded-xl bg-red-50 flex items-center justify-center mx-auto mb-4">
                      <Heart className="h-6 w-6 text-red-400" />
                    </div>
                    <p className="text-foreground font-medium mb-1">
                      {favouriteIds.size > 0
                        ? 'Some favourited products may no longer be available'
                        : 'No favourites yet'}
                    </p>
                    <p className="text-sm text-muted-foreground mb-6 max-w-xs mx-auto">
                      {favouriteIds.size > 0
                        ? 'Try browsing for similar products'
                        : 'Tap the heart icon on any product to save it here'}
                    </p>
                    <Button variant="outline" size="sm" onClick={() => navigate('/explore')}>
                      <Search className="h-4 w-4 mr-2" />
                      Browse products
                    </Button>
                  </div>
                )}
              </section>
            </Reveal>

            {/* ── Recently Viewed ── */}
            {recentlyViewed.length > 0 && (
              <Reveal>
                <section>
                  <div className="flex items-center justify-between mb-5">
                    <div>
                      <hr className="accent-rule mb-3" />
                      <h2 className="text-xl md:text-2xl font-semibold text-foreground tracking-tight">
                        Recently Viewed
                      </h2>
                      <p className="text-sm text-muted-foreground mt-1">
                        Pick up where you left off
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-primary"
                      onClick={() => navigate('/explore')}
                    >
                      Explore more
                      <ArrowRight className="ml-1 h-4 w-4" />
                    </Button>
                  </div>
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
