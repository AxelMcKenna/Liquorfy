import { useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, useInView } from 'framer-motion';
import { Heart, Eye, Settings, Bell, Search, ArrowRight } from 'lucide-react';
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

        {/* ── Hero summary strip ── */}
        <div className="bg-primary relative">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_30%_50%,rgba(255,255,255,0.06),transparent_50%)]" />
          <div className="relative z-10 max-w-6xl mx-auto px-4 py-10 md:py-14">
            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            >
              <p className="text-[11px] text-white/50 font-medium uppercase tracking-[0.2em] mb-3">
                Your Watchlist
              </p>
              <h1 className="text-3xl md:text-4xl font-semibold text-white tracking-tight leading-tight">
                Prices you're <em className="font-display italic font-normal text-white/80">watching</em>
              </h1>
              <hr className="accent-rule mt-5" />
            </motion.div>

            {/* Stat counters */}
            <motion.div
              className="flex gap-8 mt-6"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
            >
              <div>
                <p className="text-2xl font-semibold text-white">{favouriteIds.size}</p>
                <p className="text-xs text-white/50 mt-0.5">Favourites</p>
              </div>
              <div>
                <p className="text-2xl font-semibold text-white">{recentlyViewed.length}</p>
                <p className="text-xs text-white/50 mt-0.5">Recently Viewed</p>
              </div>
            </motion.div>
          </div>
        </div>

        <main className="max-w-6xl mx-auto px-4 py-10 md:py-14 space-y-14 flex-1 w-full">

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
                <div className="flex items-center gap-3">
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
                    <Heart className="h-5 w-5 text-red-400" />
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
        </main>

        <Footer />
      </div>
    </ProtectedRoute>
  );
};

export default WatchlistPage;
