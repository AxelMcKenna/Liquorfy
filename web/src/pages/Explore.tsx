import { useState, useEffect, useRef } from 'react';
import { Header } from '@/components/layout/Header';
import { FilterSidebar } from '@/components/filters/FilterSidebar';
import { ProductGrid } from '@/components/products/ProductGrid';
import { LocationGate } from '@/components/location/LocationGate';
import { usePaginatedProducts } from '@/hooks/usePaginatedProducts';
import { useFilters } from '@/hooks/useFilters';
import { useLocationContext } from '@/contexts/LocationContext';
import { useSearchParams } from 'react-router-dom';
import { MapPin, Navigation, SlidersHorizontal, Search } from 'lucide-react';
import { SignInNudge } from '@/components/auth/SignInNudge';
import { SortOption } from '@/types';
import { useSavedFilters } from '@/hooks/useSavedFilters';
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
  const FETCH_DEBOUNCE_MS = 220;
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(() => window.innerWidth >= 1024);
  const { location, radiusKm, isLocationSet, openLocationModal, requestAutoLocation, loading: locationLoading, error: locationError } = useLocationContext();
  const { filters, updateFilters } = useFilters();
  const { products, total, loading, error, currentPage, totalPages, fetchProducts, goToPage, clearProducts } = usePaginatedProducts();
  const { getSavedFilters } = useSavedFilters();
  const page = parseInt(searchParams.get('page') || '1', 10);
  const previousFetchInputsRef = useRef<{ page: number; nonPageKey: string } | null>(null);
  const appliedSavedFiltersRef = useRef(false);

  // Auto-apply saved filter defaults when landing on /explore with no params
  useEffect(() => {
    if (appliedSavedFiltersRef.current) return;
    appliedSavedFiltersRef.current = true;

    if (searchParams.toString() === '') {
      const saved = getSavedFilters();
      if (saved) {
        updateFilters(saved);
      }
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    setSearchQuery(filters.query || '');
  }, [filters.query]);

  useEffect(() => {
    if (!location || !isLocationSet) {
      return;
    }

    const nonPageKey = JSON.stringify({
      filters,
      location,
      radiusKm,
      isLocationSet,
    });

    const previous = previousFetchInputsRef.current;
    const pageChangedOnly = Boolean(
      previous &&
      previous.page !== page &&
      previous.nonPageKey === nonPageKey
    );

    previousFetchInputsRef.current = { page, nonPageKey };

    const fetchFilters = {
      ...filters,
      lat: location.lat,
      lon: location.lon,
      radius_km: radiusKm,
    };

    if (pageChangedOnly) {
      fetchProducts(fetchFilters, page);
      return;
    }

    clearProducts();

    const timer = window.setTimeout(() => {
      fetchProducts(fetchFilters, page);
    }, FETCH_DEBOUNCE_MS);

    return () => window.clearTimeout(timer);
    // fetchProducts is stable (wrapped in useCallback with empty deps), so omitting from deps
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, location, radiusKm, page, isLocationSet, clearProducts]);

  const handlePageChange = (newPage: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', newPage.toString());
    setSearchParams(newParams);
    goToPage(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const getPageNumbers = () => {
    const pages: (number | 'ellipsis')[] = [];
    const maxVisible = 7;

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      pages.push(1);

      if (currentPage > 3) {
        pages.push('ellipsis');
      }

      const start = Math.max(2, currentPage - 1);
      const end = Math.min(totalPages - 1, currentPage + 1);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }

      if (currentPage < totalPages - 2) {
        pages.push('ellipsis');
      }

      pages.push(totalPages);
    }

    return pages;
  };

  const handleSearch = () => {
    const trimmedQuery = searchQuery.trim();
    const nextParams = new URLSearchParams(searchParams);

    if (trimmedQuery) {
      nextParams.set('q', trimmedQuery);
    } else {
      nextParams.delete('q');
    }

    nextParams.delete('page');
    setSearchParams(nextParams);
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
        </div>

        <div className="flex">
          <FilterSidebar
            isOpen={isSidebarOpen}
            onClose={() => setIsSidebarOpen(false)}
          />

          <main className="flex-1 min-h-screen">
            <div className="max-w-6xl mx-auto px-4 py-6 pb-32">
              {/* Location requirement gate */}
              {!isLocationSet && (
                <div className="flex items-center justify-center min-h-[50vh]">
                  <Card className="p-8 text-center max-w-md border bg-card">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-secondary mb-4">
                      <Navigation className="h-6 w-6 text-primary" />
                    </div>
                    <h2 className="text-xl font-semibold mb-2">
                      Location Required
                    </h2>
                    <p className="text-sm text-muted-foreground mb-6">
                      Enable location to see products from stores in your area.
                    </p>
                    {locationError && (
                      <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                        <p className="text-sm text-destructive">{locationError}</p>
                      </div>
                    )}
                    <div className="space-y-2">
                      <Button
                        onClick={requestAutoLocation}
                        disabled={locationLoading}
                        className="w-full"
                      >
                        {locationLoading ? (
                          'Getting location...'
                        ) : (
                          <>
                            <Navigation className="h-4 w-4 mr-2" />
                            Use My Location
                          </>
                        )}
                      </Button>
                      <Button
                        onClick={openLocationModal}
                        variant="outline"
                        className="w-full"
                      >
                        <MapPin className="h-4 w-4 mr-2" />
                        Set Manually
                      </Button>
                    </div>
                  </Card>
                </div>
              )}

              {/* Content when location is set */}
              {isLocationSet && (
                <>
                  <SignInNudge />

                  {error && (
                    <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 mb-4">
                      <p className="text-sm text-destructive">{error}</p>
                    </div>
                  )}

                  {/* Results count */}
                  {!loading && products.length > 0 && (
                    <div className="mb-4 text-sm text-muted-foreground">
                      {total === 0
                        ? 'No products found'
                        : `${(currentPage - 1) * 24 + 1}–${Math.min(currentPage * 24, total)} of ${total} products`}
                    </div>
                  )}

                  <ProductGrid
                    products={products}
                    loading={loading}
                  />

                  {/* Pagination */}
                  {!loading && products.length > 0 && totalPages > 1 && (
                    <div className="mt-6">
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
                    <div className="text-center py-16">
                      <Search className="h-10 w-10 text-muted-foreground/30 mx-auto mb-3" />
                      <p className="text-muted-foreground font-medium">No products found</p>
                      <p className="text-sm text-muted-foreground/70 mt-1">Try adjusting your filters or search terms</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </main>
        </div>

        {/* Mobile filter FAB */}
        <button
          onClick={() => setIsSidebarOpen(true)}
          className="fixed bottom-6 right-6 z-30 lg:hidden bg-primary text-white rounded-full w-14 h-14 flex items-center justify-center shadow-lg hover:bg-primary/90 transition-colors"
        >
          <SlidersHorizontal className="h-5 w-5" />
        </button>
      </div>
    </LocationGate>
  );
};

export default Explore;
