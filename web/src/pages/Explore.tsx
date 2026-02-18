import { useState, useEffect } from 'react';
import { Header } from '@/components/layout/Header';
import { FilterBar } from '@/components/filters/FilterBar';
import { FilterSidebar } from '@/components/filters/FilterSidebar';
import { ProductGrid } from '@/components/products/ProductGrid';
import { LocationGate } from '@/components/location/LocationGate';
import { usePaginatedProducts } from '@/hooks/usePaginatedProducts';
import { useFilters } from '@/hooks/useFilters';
import { useLocationContext } from '@/contexts/LocationContext';
import { useSearchParams } from 'react-router-dom';
import { MapPin, Navigation } from 'lucide-react';
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
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState('');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { location, radiusKm, isLocationSet, openLocationModal, requestAutoLocation, loading: locationLoading, error: locationError } = useLocationContext();
  const { filters, updateFilters } = useFilters();
  const { products, total, loading, error, currentPage, totalPages, fetchProducts, goToPage } = usePaginatedProducts();
  const page = parseInt(searchParams.get('page') || '1', 10);

  useEffect(() => {
    setSearchQuery(filters.query || '');
  }, [filters.query]);

  useEffect(() => {
    if (!location || !isLocationSet) {
      return;
    }

    const fetchFilters = {
      ...filters,
      lat: location.lat,
      lon: location.lon,
      radius_km: radiusKm,
    };

    fetchProducts(fetchFilters, page);
    // fetchProducts is stable (wrapped in useCallback with empty deps), so omitting from deps
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filters, location, radiusKm, page, isLocationSet]);

  const handlePageChange = (newPage: number) => {
    const newParams = new URLSearchParams(searchParams);
    newParams.set('page', newPage.toString());
    setSearchParams(newParams);
    goToPage(newPage);
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
          <FilterBar onOpenFilters={() => setIsSidebarOpen(true)} />
        </div>

        <div className="flex">
          <FilterSidebar
            isOpen={isSidebarOpen}
            onClose={() => setIsSidebarOpen(false)}
          />

          <main className="flex-1 overflow-y-auto min-h-screen overscroll-none">
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
                  {error && (
                    <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 mb-4">
                      <p className="text-sm text-destructive">{error}</p>
                    </div>
                  )}

                  {/* Results count */}
                  {!loading && products.length > 0 && (
                    <div className="mb-4 flex items-center justify-between text-sm text-muted-foreground">
                      <span>
                        {total === 0
                          ? 'No products found'
                          : `${(currentPage - 1) * 24 + 1}-${Math.min(currentPage * 24, total)} of ${total}`}
                      </span>
                      <span>Page {currentPage} of {totalPages}</span>
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
                    <div className="text-center py-12">
                      <p className="text-muted-foreground">
                        No products found. Try adjusting your filters.
                      </p>
                    </div>
                  )}
                </>
              )}
            </div>
          </main>
        </div>

      </div>
    </LocationGate>
  );
};

export default Explore;
