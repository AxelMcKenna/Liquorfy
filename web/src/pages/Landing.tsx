import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, useInView } from 'framer-motion';
import { ProductGrid } from '@/components/products/ProductGrid';
import { Button } from '@/components/ui/button';
import { SearchAutocomplete } from '@/components/search/SearchAutocomplete';
import { Slider } from '@/components/ui/slider';
import { LazyStoreMap } from '@/components/stores/LazyStoreMap';
import { StoreMapSkeleton } from '@/components/stores/StoreMapSkeleton';
import { Footer } from '@/components/layout/Footer';
import { useProducts } from '@/hooks/useProducts';
import { useLocationContext } from '@/contexts/LocationContext';
import { useStores } from '@/hooks/useStores';
import { useAuth } from '@/contexts/AuthContext';
import { UserMenu } from '@/components/auth/UserMenu';
import { Search, ArrowRight, MapPin, User } from 'lucide-react';
import { Link } from 'react-router-dom';
import { RecentlyViewed } from '@/components/products/RecentlyViewed';
import { useRecentlyViewed } from '@/hooks/useRecentlyViewed';
import { SortOption } from '@/types';
import { useIntersectionObserver } from '@/hooks/useIntersectionObserver';

/* Scroll-triggered reveal animation */
const Reveal = ({
  children,
  className = '',
  delay = 0,
  direction = 'up',
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  direction?: 'up' | 'left' | 'right';
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: '-40px' });
  const originMap = {
    up: { y: 28, x: 0 },
    left: { x: -36, y: 0 },
    right: { x: 36, y: 0 },
  };
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, ...originMap[direction] }}
      animate={isInView ? { opacity: 1, x: 0, y: 0 } : {}}
      transition={{ duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  );
};

export const Landing = () => {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const { products, loading, fetchProducts } = useProducts();
  const { recentlyViewed } = useRecentlyViewed();
  const { location, radiusKm, setRadiusKm, requestAutoLocation: requestLocation, loading: locationLoading, error: locationError } = useLocationContext();
  const { stores, loading: storesLoading, fetchNearbyStores } = useStores();
  const { user } = useAuth();
  const [tempRadius, setTempRadius] = useState(radiusKm);
  const [shouldLoadMap, setShouldLoadMap] = useState(false);
  const mapRef = useIntersectionObserver({
    enabled: Boolean(location),
    onIntersect: () => setShouldLoadMap(true),
  });

  const promoFetchLimit = 10;

  useEffect(() => {
    if (location && !storesLoading) {
      fetchNearbyStores(location, radiusKm);
    }
  }, [location, radiusKm, fetchNearbyStores]);

  useEffect(() => {
    if (location) {
      fetchProducts({
        promo_only: true,
        limit: promoFetchLimit,
        sort: SortOption.DISCOUNT,
        unique_products: true,
        lat: location.lat,
        lon: location.lon,
        radius_km: radiusKm,
      });
    } else {
      fetchProducts({
        promo_only: true,
        limit: promoFetchLimit,
        sort: SortOption.DISCOUNT,
        unique_products: true,
      });
    }
  }, [location, radiusKm, fetchProducts]);

  useEffect(() => {
    setTempRadius(radiusKm);
  }, [radiusKm]);

  useEffect(() => {
    const debounceId = window.setTimeout(() => {
      if (tempRadius !== radiusKm) {
        setRadiusKm(tempRadius);
      }
    }, 500);

    return () => window.clearTimeout(debounceId);
  }, [tempRadius, radiusKm, setRadiusKm]);

  const getTopDiscountedProducts = () => {
    if (!products?.items) return [];

    return products.items
      .filter((item) => {
        const promoPrice = item.price.promo_price_nzd;
        return promoPrice !== null && promoPrice !== undefined && promoPrice < item.price.price_nzd;
      })
      .map((item) => ({
        ...item,
        discountPercent: ((item.price.price_nzd - (item.price.promo_price_nzd || 0)) / item.price.price_nzd) * 100,
      }))
      .sort((a, b) => b.discountPercent - a.discountPercent)
      .slice(0, 10);
  };

  const topDiscountedProducts = getTopDiscountedProducts();

  const handleSearch = () => {
    const trimmedQuery = query.trim();
    navigate(trimmedQuery ? `/explore?q=${encodeURIComponent(trimmedQuery)}` : '/explore');
  };

  const handleViewAllDeals = () => {
    navigate('/explore?promo_only=true');
  };

  return (
    <div className="min-h-screen bg-background overflow-x-hidden flex flex-col">

      {/* ===== HERO — Split tension: left text, right search ===== */}
      <section className="bg-primary hero-clip relative">
        {/* Layered gradients for depth */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_15%_25%,rgba(255,255,255,0.08),transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_85%_75%,rgba(0,0,0,0.15),transparent_50%)]" />

        <div className="relative z-10 max-w-7xl mx-auto px-4 pt-6 pb-28 md:pb-44">
          {/* Top nav — logo left, account right */}
          <div className="flex items-center justify-between mb-10 md:mb-20 animate-fade-up">
            <Link to="/" className="text-xl font-semibold text-white tracking-[0.15em] font-sans">
              LIQUORFY
            </Link>
            {user ? (
              <UserMenu />
            ) : (
              <Link to="/login">
                <Button variant="ghost" size="sm" className="text-white hover:bg-white/10 font-semibold gap-2 border-0">
                  <User className="h-4 w-4" />
                  Account
                </Button>
              </Link>
            )}
          </div>

          {/* Hero content — asymmetric grid: 7/5 split on desktop */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 md:gap-12 items-end">
            {/* Left: headline — heavy weight, left-aligned */}
            <div className="md:col-span-7 animate-slide-left text-center md:text-left">
              <p className="text-xs sm:text-sm text-white/60 font-medium uppercase tracking-widest mb-2 sm:mb-3">
                NZ Liquor Price Comparison
              </p>
              <h1 className="text-[2rem] leading-[1.15] sm:text-4xl md:text-5xl lg:text-6xl font-semibold text-white tracking-tight md:leading-[1.1]">
                Find the best<br />
                deals <em className="font-display italic font-normal text-white/80">near you</em>
              </h1>
              <hr className="accent-rule mt-3 mx-auto md:mx-0" />
              <p className="text-sm md:text-lg text-white/70 max-w-md mt-3 md:mt-4 mx-auto md:mx-0">
                Compare prices from 10+ major retailers, updated daily.
              </p>
            </div>

            {/* Right: search */}
            <div className="md:col-span-5 animate-slide-right" style={{ animationDelay: '150ms' }}>
              <div className="flex items-center justify-center gap-4 text-xs text-white/50 mb-3 md:mb-3">
                <span className="flex items-center gap-1.5">
                  <span className="w-1 h-1 rounded-full bg-white/40" />
                  10+ retailers
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1 h-1 rounded-full bg-white/40" />
                  Daily updates
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-1 h-1 rounded-full bg-white/40" />
                  Free
                </span>
              </div>
              <div className="relative">
                <SearchAutocomplete
                  query={query}
                  setQuery={setQuery}
                  onSearch={handleSearch}
                  placeholder="Search for beer, wine, spirits..."
                  inputClassName="pl-12 pr-24 h-14 text-base rounded-lg border-0 bg-white text-foreground shadow-lg"
                />
                <Button
                  onClick={handleSearch}
                  size="sm"
                  className="absolute right-1.5 top-1/2 -translate-y-1/2 h-11 z-10"
                >
                  Search
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== DEALS — Left-aligned heading, full grid ===== */}
      <section className="py-14 md:py-20">
        <div className="max-w-7xl mx-auto px-4">
          {/* Offset heading: left-aligned with right action — creates horizontal tension */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 mb-10">
            <Reveal className="md:col-span-8">
              <hr className="accent-rule mb-4" />
              <h2 className="text-2xl md:text-3xl font-semibold text-foreground tracking-tight">
                {location ? 'Deals Near You' : 'Top Deals'}
              </h2>
              {!location && (
                <p className="text-sm text-muted-foreground mt-2">
                  Enable location for personalized results
                </p>
              )}
            </Reveal>
            <Reveal className="md:col-span-4 flex md:justify-end items-end" delay={0.08}>
              <Button
                onClick={handleViewAllDeals}
                variant="ghost"
                size="sm"
                className="text-primary -ml-3 md:ml-0"
              >
                View all deals
                <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Reveal>
          </div>

          <ProductGrid
            products={topDiscountedProducts}
            loading={loading}
          />

          {!loading && topDiscountedProducts.length === 0 && (
            <div className="text-center py-16">
              <Search className="h-10 w-10 text-muted-foreground/30 mx-auto mb-3" />
              <p className="text-muted-foreground">No deals available right now</p>
              <p className="text-sm text-muted-foreground/70 mt-1">Check back soon for new promotions</p>
            </div>
          )}
        </div>
      </section>

      {/* Recently Viewed */}
      <div className="max-w-7xl mx-auto px-4">
        <RecentlyViewed products={recentlyViewed} />
      </div>

      {/* ===== MAP ===== */}
      <section className="py-14 md:py-20 border-t">
        <div className="max-w-7xl mx-auto px-4">
          {!location && (
            <div className="max-w-md mx-auto text-center py-8">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-secondary mb-4">
                <MapPin className="h-6 w-6 text-primary" />
              </div>
              <h3 className="text-lg font-medium mb-2">Enable Location</h3>
              <p className="text-sm text-muted-foreground mb-6">
                See deals from stores in your area
              </p>
              <Button
                onClick={requestLocation}
                disabled={locationLoading}
              >
                {locationLoading ? 'Getting location...' : 'Enable Location'}
              </Button>
              {locationError && (
                <p className="text-destructive text-sm mt-4">{locationError}</p>
              )}
            </div>
          )}

          {location && (
            <div className="space-y-4">
              <div className="bg-secondary rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm font-medium">Search radius</span>
                  <span className="text-sm font-semibold text-primary">
                    {tempRadius} km
                  </span>
                </div>
                <Slider
                  value={[tempRadius]}
                  onValueChange={(value) => setTempRadius(value[0])}
                  min={1}
                  max={10}
                  step={1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground mt-2">
                  <span>1 km</span>
                  <span>{stores.length} stores</span>
                  <span>10 km</span>
                </div>
              </div>

              <div ref={mapRef} className="rounded-lg overflow-hidden border">
                {shouldLoadMap ? (
                  <LazyStoreMap
                    userLocation={location}
                    stores={stores}
                    selectedStore={null}
                    onStoreClick={() => {}}
                    radiusKm={radiusKm}
                  />
                ) : (
                  <StoreMapSkeleton className="h-[400px] border-none" />
                )}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* ===== CTA — Left-heavy with right button, diagonal accent ===== */}
      <section className="py-14 md:py-20 border-t">
        <div className="max-w-7xl mx-auto px-4">
          <Reveal>
            <div className="bg-primary rounded-2xl overflow-hidden relative card-lift">
              {/* Layered gradients */}
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_20%_50%,rgba(255,255,255,0.06),transparent_50%)]" />
              {/* Diagonal accent slab */}
              <div className="absolute top-0 right-0 w-1/3 h-full bg-white/[0.03] skew-x-[-12deg] translate-x-16" />
              <div className="relative z-10 px-8 py-10 md:px-12 md:py-14 grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
                <div className="md:col-span-8">
                  <hr className="accent-rule mb-5" />
                  <h2 className="text-2xl md:text-3xl font-semibold text-white tracking-tight mb-3">
                    Ready to compare?
                  </h2>
                  <p className="text-white/55 max-w-lg text-[15px] leading-relaxed">
                    Browse thousands of products from every major NZ retailer. Find the lowest price near you.
                  </p>
                </div>
                <div className="md:col-span-4 md:text-right">
                  <Button
                    onClick={() => navigate('/explore')}
                    size="lg"
                    className="bg-white text-primary hover:bg-white/90 font-semibold shadow-lg"
                  >
                    <Search className="h-5 w-5 mr-2" />
                    Explore All Products
                  </Button>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* ===== RESPONSIBLE DRINKING ===== */}
      <section className="py-8 border-t">
        <div className="max-w-7xl mx-auto px-4">
          <div className="bg-secondary rounded-lg p-6 max-w-lg mx-auto text-center">
            <p className="text-sm font-medium mb-1">Drink Responsibly</p>
            <p className="text-xs text-muted-foreground">
              You must be 18+ to purchase alcohol. If you need support, visit{' '}
              <a
                href="https://www.alcohol.org.nz"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                Alcohol.org.nz
              </a>
            </p>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Landing;
