import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Header } from '@/components/layout/Header';
import { FilterBar } from '@/components/filters/FilterBar';
import { FilterSidebar } from '@/components/filters/FilterSidebar';
import { ProductGrid } from '@/components/products/ProductGrid';
import { ComparisonTray } from '@/components/layout/ComparisonTray';
import { LocationGate } from '@/components/location/LocationGate';
import { usePaginatedProducts } from '@/hooks/usePaginatedProducts';
import { useFilters } from '@/hooks/useFilters';
import { useLocationContext } from '@/contexts/LocationContext';
import { useCompareContext } from '@/contexts/CompareContext';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { MapPin, X, Navigation } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from '@/components/ui/pagination';

export const Explore = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { location, radiusKm, isLocationSet, openLocationModal, requestAutoLocation, loading: locationLoading, error: locationError } = useLocationContext();
  const { filters, updateFilters } = useFilters();
  const { products, total, loading, error, currentPage, totalPages, fetchProducts, goToPage } = usePaginatedProducts();
  const { compare, sortedCompare, toggleCompare, clearCompare, isAtLimit, maxCompare } = useCompareContext();

  // Get page from URL or default to 1
  const page = parseInt(searchParams.get('page') || '1', 10);

  useEffect(() => {
    setSearchQuery(filters.query || '');
  }, [filters.query]);

  // Fetch products ONLY with location
  useEffect(() => {
    if (!location || !isLocationSet) {
      return; // Don't fetch without location
    }

    const fetchFilters = {
      ...filters,
      lat: location.lat,
      lon: location.lon,
      radius_km: radiusKm,
    };

    fetchProducts(fetchFilters, page);
  }, [filters, location, radiusKm, page, isLocationSet, fetchProducts]);

  const handlePageChange = (newPage: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', newPage.toString());
    setSearchParams(newParams);
    goToPage(newPage);
  };

  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages: (number | 'ellipsis')[] = [];
    const maxVisible = 7;

    if (totalPages <= maxVisible) {
      // Show all pages
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Always show first page
      pages.push(1);

      if (currentPage > 3) {
        pages.push('ellipsis');
      }

      // Show pages around current
      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (currentPage < totalPages - 2) {
        pages.push('ellipsis');
      }

      // Always show last page
      pages.push(totalPages);
    }

    return pages;
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      navigate(`/explore?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <LocationGate>
      <div className="min-h-screen bg-secondary">
        <div className="sticky top-0 z-50 bg-secondary">
          <Header
            query={searchQuery}
            setQuery={setSearchQuery}
            onSearch={handleSearch}
            variant="compact"
          />
          <FilterBar onOpenFilters={() => setIsSidebarOpen(true)} />
        </div>

        <div className="flex">
          <FilterSidebar
            isOpen={isSidebarOpen}
            onClose={() => setIsSidebarOpen(false)}
          />

          <main className="flex-1 overflow-y-auto min-h-screen overscroll-none">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-36">
              {/* Location requirement gate */}
              {!isLocationSet && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center justify-center min-h-[60vh]"
                >
                  <Card className="glass-card p-12 text-center max-w-lg">
                    <div className="inline-block p-6 bg-primary/10 rounded-full mb-6">
                      <Navigation className="h-16 w-16 text-primary" />
                    </div>
                    <h2 className="text-3xl font-semibold mb-4 text-primary-gray">
                      Location Required
                    </h2>
                    <p className="text-lg mb-2 text-secondary-gray">
                      To provide you with accurate pricing and availability, we need to know your location.
                    </p>
                    <p className="text-base mb-8 text-tertiary-gray">
                      This helps us show you products from stores in your area and prevents excessive database queries.
                    </p>
                    {locationError && (
                      <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                        <p className="text-sm text-red-800">{locationError}</p>
                      </div>
                    )}
                    <div className="space-y-3">
                      <Button
                        onClick={requestAutoLocation}
                        disabled={locationLoading}
                        size="lg"
                        className="w-full bg-primary hover:bg-accent text-white px-10 py-6 text-base font-medium rounded-card-xl"
                      >
                        {locationLoading ? (
                          <>
                            <span className="animate-spin mr-2">⏳</span>
                            Getting Location...
                          </>
                        ) : (
                          <>
                            <Navigation className="h-5 w-5 mr-2" />
                            Use My Location
                          </>
                        )}
                      </Button>
                      <Button
                        onClick={openLocationModal}
                        variant="outline"
                        size="lg"
                        className="w-full rounded-card-xl font-medium border-subtle text-primary-gray py-6"
                      >
                        <MapPin className="h-5 w-5 mr-2" />
                        Set Location Manually
                      </Button>
                    </div>
                  </Card>
                </motion.div>
              )}

              {/* Only show content if location is set */}
              {isLocationSet && (
                <>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="glass border-destructive/30 rounded-xl p-6 mb-6"
                    >
                      <p className="text-destructive font-medium">{error}</p>
                    </motion.div>
                  )}

                  {/* Results count */}
                  {!loading && products.length > 0 && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="mb-4 flex items-center justify-between"
                    >
                      <p className="text-tertiary-gray text-sm font-normal">
                        {total === 0
                          ? 'No products found'
                          : `Showing ${(currentPage - 1) * 24 + 1}-${Math.min(currentPage * 24, total)} of ${total} product${total === 1 ? '' : 's'}`}
                      </p>
                      <p className="text-tertiary-gray text-sm font-normal">
                        Page {currentPage} of {totalPages}
                      </p>
                    </motion.div>
                  )}

                  <ProductGrid
                    products={products}
                    loading={loading}
                    compareIds={compare.map((p) => p.id)}
                    onToggleCompare={toggleCompare}
                    isCompareAtLimit={isAtLimit}
                  />

                  {/* Pagination */}
                  {!loading && products.length > 0 && totalPages > 1 && (
              <div className="mt-8 mb-4">
                <Pagination>
                  <PaginationContent>
                    <PaginationItem>
                      <PaginationPrevious
                        onClick={() => currentPage > 1 && handlePageChange(currentPage - 1)}
                        className={currentPage === 1 ? 'pointer-events-none opacity-50' : ''}
                      />
                    </PaginationItem>

                    {getPageNumbers().map((pageNum, idx) =>
                      pageNum === 'ellipsis' ? (
                        <PaginationItem key={`ellipsis-${idx}`}>
                          <PaginationEllipsis />
                        </PaginationItem>
                      ) : (
                        <PaginationItem key={pageNum}>
                          <PaginationLink
                            onClick={() => handlePageChange(pageNum)}
                            isActive={currentPage === pageNum}
                          >
                            {pageNum}
                          </PaginationLink>
                        </PaginationItem>
                      )
                    )}

                    <PaginationItem>
                      <PaginationNext
                        onClick={() => currentPage < totalPages && handlePageChange(currentPage + 1)}
                        className={currentPage === totalPages ? 'pointer-events-none opacity-50' : ''}
                      />
                    </PaginationItem>
                  </PaginationContent>
                </Pagination>
                    </div>
                  )}

                  {!loading && products.length === 0 && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-center py-12"
                    >
                      <p className="text-muted-foreground text-lg">
                        No products found. Try adjusting your search or filters.
                      </p>
                    </motion.div>
                  )}
                </>
              )}
            </div>
          </main>
        </div>

        <ComparisonTray
          products={sortedCompare}
          onClear={clearCompare}
          onRemoveProduct={toggleCompare}
          maxCompare={maxCompare}
        />
      </div>
    </LocationGate>
  );
};

export default Explore;
