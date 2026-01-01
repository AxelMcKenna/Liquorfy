import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ProductGrid } from '@/components/products/ProductGrid';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import { StoreMap } from '@/components/stores/StoreMap';
import { useProducts } from '@/hooks/useProducts';
import { useLocationContext } from '@/contexts/LocationContext';
import { useStores } from '@/hooks/useStores';
import { useCompareContext } from '@/contexts/CompareContext';
import { ComparisonTray } from '@/components/layout/ComparisonTray';
import { Search, ArrowRight, MapPin } from 'lucide-react';

export const Landing = () => {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();
  const { products, loading, fetchProducts } = useProducts();
  const { location, radiusKm, setRadiusKm, requestAutoLocation: requestLocation, loading: locationLoading, error: locationError } = useLocationContext();
  const { stores, loading: storesLoading, fetchNearbyStores } = useStores();
  const { compare, toggleCompare, clearCompare, isAtLimit, maxCompare } = useCompareContext();
  const [tempRadius, setTempRadius] = useState(radiusKm);

  // Fetch nearby stores when location or radius changes
  useEffect(() => {
    if (location && !storesLoading) {
      fetchNearbyStores(location, radiusKm);
    }
  }, [location, radiusKm, fetchNearbyStores]);

  useEffect(() => {
    // Fetch top deals - with location if available, nationwide if not
    // This provides immediate value and is a lighter, cacheable query
    if (location) {
      // Show best deals in user's area
      fetchProducts({
        promo_only: true,
        limit: 10,
        lat: location.lat,
        lon: location.lon,
        radius_km: radiusKm,
      });
    } else {
      // Show best deals nationwide (faster, cached query)
      fetchProducts({
        promo_only: true,
        limit: 10,
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

  // Get top 10 products sorted by discount percentage
  const getTopDiscountedProducts = () => {
    if (!products?.items) return [];

    return products.items
      .filter(p => p.price.promo_price_nzd && p.price.promo_price_nzd < p.price.price_nzd)
      .map(p => ({
        ...p,
        discountPercent: ((p.price.price_nzd - (p.price.promo_price_nzd || 0)) / p.price.price_nzd) * 100
      }))
      .sort((a, b) => b.discountPercent - a.discountPercent)
      .slice(0, 10);
  };

  const topDiscountedProducts = getTopDiscountedProducts();

  const handleSearch = () => {
    if (query.trim()) {
      navigate(`/explore?q=${encodeURIComponent(query)}`);
    }
  };

  const handleViewAllDeals = () => {
    navigate('/explore?promo_only=true');
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Minimal Hero Banner */}
      <section className="bg-white">
        <div className="max-w-5xl mx-auto px-6 py-32 text-center">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-6xl md:text-7xl font-semibold mb-6 text-primary-gray tracking-tight leading-[1.1]"
          >
            Find Better Prices
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-2xl mb-16 max-w-xl mx-auto text-secondary-gray font-normal"
          >
            Compare liquor prices across New Zealand's top retailers
          </motion.p>

          {/* Search bar */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="max-w-2xl mx-auto"
          >
            <div className="relative group">
              <Search className="absolute left-6 top-1/2 transform -translate-y-1/2 h-5 w-5 text-tertiary-gray group-focus-within:text-primary transition-colors" />
              <Input
                placeholder="Search for beer, wine, or spirits"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="pl-16 pr-32 py-8 text-lg rounded-2xl border-2 border-border bg-white focus:border-primary focus:ring-0 transition-all"
              />
              <Button
                onClick={handleSearch}
                className="absolute right-2 top-1/2 -translate-y-1/2 bg-primary hover:bg-accent text-white px-8 py-5 text-base font-medium rounded-xl shadow-none"
              >
                Search
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      <main className="max-w-7xl mx-auto px-6">
        {/* Featured Products Section */}
        <section className="py-24">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-end justify-between mb-12">
              <div>
                <h2 className="text-5xl font-semibold text-primary-gray mb-3">
                  {location ? 'Deals Near You' : 'Top Deals'}
                </h2>
                {!location && (
                  <p className="text-lg text-tertiary-gray">
                    Enable location for personalized deals
                  </p>
                )}
              </div>
              <Button
                onClick={handleViewAllDeals}
                variant="ghost"
                className="text-primary hover:text-accent hover:bg-transparent font-medium text-lg"
              >
                View All
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </div>

            <ProductGrid
              products={topDiscountedProducts}
              loading={loading}
              compareIds={compare.map((p) => p.id)}
              onToggleCompare={toggleCompare}
              isCompareAtLimit={isAtLimit}
            />

            {!loading && topDiscountedProducts.length === 0 && (
              <div className="text-center py-20">
                <p className="text-xl text-tertiary-gray">No deals available at the moment</p>
              </div>
            )}
          </div>
        </section>

        {/* Store Map Section */}
        <section className="py-24">
          <div className="max-w-7xl mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-5xl font-semibold mb-4 text-primary-gray">
                Stores Near You
              </h2>
              <p className="text-xl max-w-2xl mx-auto text-secondary-gray">
                Find local deals from nearby retailers
              </p>
            </div>

            {!location && (
              <div className="max-w-2xl mx-auto text-center py-20">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-secondary mb-8">
                  <MapPin className="h-10 w-10 text-primary" />
                </div>
                <h3 className="text-3xl font-semibold mb-4 text-primary-gray">Enable Location</h3>
                <p className="text-xl mb-10 max-w-md mx-auto text-secondary-gray">
                  See deals from stores in your area
                </p>
                <Button
                  onClick={requestLocation}
                  disabled={locationLoading}
                  size="lg"
                  className="bg-primary hover:bg-accent text-white px-10 py-6 text-lg font-medium rounded-xl"
                >
                  {locationLoading ? 'Getting Location...' : 'Enable Location'}
                </Button>
                {locationError && (
                  <p className="text-destructive mt-6 text-base">{locationError}</p>
                )}
              </div>
            )}

            {location && (
              <div className="space-y-8">
                <div className="bg-secondary rounded-2xl p-8">
                  <div className="space-y-6">
                    <div className="flex items-center justify-between">
                      <label className="text-xl font-medium text-primary-gray">
                        Search Radius
                      </label>
                      <span className="text-3xl font-semibold text-primary">
                        {tempRadius} km
                      </span>
                    </div>
                    <Slider
                      value={[tempRadius]}
                      onValueChange={(value) => setTempRadius(value[0])}
                      min={5}
                      max={50}
                      step={1}
                      className="w-full"
                    />
                    <div className="flex justify-between text-base text-tertiary-gray">
                      <span>5km</span>
                      <span>{stores.length} stores</span>
                      <span>50km</span>
                    </div>
                  </div>
                </div>

                <div className="rounded-2xl overflow-hidden border border-border">
                  <StoreMap
                    userLocation={location}
                    stores={stores}
                    selectedStore={null}
                    onStoreClick={() => {}}
                    radiusKm={radiusKm}
                  />
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-32">
          <div className="max-w-5xl mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center"
            >
              <h2 className="text-5xl md:text-6xl font-semibold mb-6 text-primary-gray tracking-tight">
                Transparent Pricing
              </h2>
              <p className="text-2xl leading-relaxed text-secondary-gray max-w-2xl mx-auto mb-20">
                Compare prices across major retailers in real-time
              </p>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-12 max-w-4xl mx-auto mb-20">
                <div className="text-center">
                  <div className="text-6xl font-semibold text-primary mb-3">10+</div>
                  <div className="text-lg text-secondary-gray">Retailers</div>
                </div>
                <div className="text-center">
                  <div className="text-6xl font-semibold text-primary mb-3">Live</div>
                  <div className="text-lg text-secondary-gray">Prices</div>
                </div>
                <div className="text-center">
                  <div className="text-6xl font-semibold text-primary mb-3">Free</div>
                  <div className="text-lg text-secondary-gray">Always</div>
                </div>
              </div>

              <div className="bg-secondary/50 rounded-2xl p-10 max-w-3xl mx-auto border border-border/50">
                <p className="text-base text-primary-gray font-medium mb-3">
                  Drink Responsibly
                </p>
                <p className="text-sm text-secondary-gray leading-relaxed">
                  This platform is an informational tool only. You must be 18+ to purchase alcohol.
                  If you need support, visit <a href="https://www.alcohol.org.nz" target="_blank" rel="noopener noreferrer" className="text-primary hover:text-accent transition-colors">Alcohol.org.nz</a> or call 0800 787 797.
                </p>
              </div>
            </motion.div>
          </div>
        </section>
      </main>

      <ComparisonTray
        products={compare}
        onClear={clearCompare}
        onRemoveProduct={toggleCompare}
        maxCompare={maxCompare}
      />
    </div>
  );
};

export default Landing;
