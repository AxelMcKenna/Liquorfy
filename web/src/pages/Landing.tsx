import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ProductGrid } from '@/components/products/ProductGrid';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { LazyStoreMap } from '@/components/stores/LazyStoreMap';
import { StoreMapSkeleton } from '@/components/stores/StoreMapSkeleton';
import { useProducts } from '@/hooks/useProducts';
import { useLocationContext } from '@/contexts/LocationContext';
import { useStores } from '@/hooks/useStores';
import { Search, ArrowRight, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';
import { SortOption } from '@/types';
import { useIntersectionObserver } from '@/hooks/useIntersectionObserver';

export const Landing = () => {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const { products, loading, fetchProducts } = useProducts();
  const { location, radiusKm, setRadiusKm, requestAutoLocation: requestLocation, loading: locationLoading, error: locationError } = useLocationContext();
  const { stores, loading: storesLoading, fetchNearbyStores } = useStores();
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
    <div className="min-h-screen bg-background">
      {/* Hero */}
      <section className="bg-primary">
        <div className="max-w-3xl mx-auto px-4 py-16 md:py-20 text-center">
          <h1 className="text-4xl md:text-5xl font-semibold text-white mb-3 tracking-tight">
            Compare liquor prices across NZ
          </h1>
          <p className="text-base text-white/80 mb-8 max-w-lg mx-auto">
            Find the best deals from major retailers near you
          </p>

          <div className="relative max-w-xl mx-auto">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search for beer, wine, or spirits"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="pl-12 pr-24 h-12 text-base rounded-lg border-0 bg-white text-foreground shadow-sm"
            />
            <Button
              onClick={handleSearch}
              size="sm"
              className="absolute right-1.5 top-1/2 -translate-y-1/2 h-9"
            >
              Search
            </Button>
          </div>
        </div>
      </section>

      <main className="max-w-6xl mx-auto px-4">
        {/* Featured Products */}
        <section className="py-12">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-semibold text-foreground">
                {location ? 'Deals Near You' : 'Top Deals'}
              </h2>
              {!location && (
                <p className="text-sm text-muted-foreground mt-1">
                  Enable location for personalized results
                </p>
              )}
            </div>
            <Button
              onClick={handleViewAllDeals}
              variant="ghost"
              size="sm"
              className="text-primary"
            >
              View all
              <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </div>

          <ProductGrid
            products={topDiscountedProducts}
            loading={loading}
          />

          {!loading && topDiscountedProducts.length === 0 && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No deals available</p>
            </div>
          )}
        </section>

        {/* Store Map */}
        <section className="py-12 border-t">
          {!location && (
            <div className="max-w-md mx-auto text-center py-12">
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
        </section>

        {/* Stats */}
        <section className="py-12 border-t">
          <div className="text-center mb-8">
            <h2 className="text-xl font-semibold text-foreground mb-2">
              Transparent Pricing
            </h2>
            <p className="text-sm text-muted-foreground max-w-md mx-auto">
              Compare prices across major retailers in real-time
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4 sm:gap-8 max-w-lg mx-auto mb-8">
            <div className="text-center">
              <div className="text-2xl font-semibold text-primary">10+</div>
              <div className="text-xs text-muted-foreground">Retailers</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-semibold text-primary">Daily</div>
              <div className="text-xs text-muted-foreground">Updates</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-semibold text-primary">Free</div>
              <div className="text-xs text-muted-foreground">Always</div>
            </div>
          </div>

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
          <p className="text-xs text-muted-foreground mt-6 text-right">
            <Link to="/privacy" className="hover:underline">Privacy</Link>
            {' · '}
            <Link to="/support" className="hover:underline">Support</Link>
          </p>
        </section>
      </main>

    </div>
  );
};

export default Landing;
