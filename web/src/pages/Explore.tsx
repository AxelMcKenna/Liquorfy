import { useState, useEffect, useRef } from 'react';
import { Header } from '@/components/layout/Header';
import { FilterSidebar } from '@/components/filters/FilterSidebar';
import { FilterChips } from '@/components/filters/FilterChips';
import { ProductGrid } from '@/components/products/ProductGrid';
import { usePaginatedProducts } from '@/hooks/usePaginatedProducts';
import { useFilters } from '@/hooks/useFilters';
import { useLocationContext } from '@/contexts/LocationContext';
import { useSearchParams } from 'react-router-dom';
import { MapPin, SlidersHorizontal, Search, X, Bell } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { Link } from 'react-router-dom';
import { useSavedFilters } from '@/hooks/useSavedFilters';
import { Button } from '@/components/ui/button';
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
  const [bannerDismissed, setBannerDismissed] = useState(false);
  const { location, radiusKm, isLocationSet, openLocationModal, requestAutoLocation, loading: locationLoading, error: locationError } = useLocationContext();
  const { user } = useAuth();
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

  // Dismiss the banner once both conditions are resolved
  const needsLocation = !isLocationSet;
  const needsSignIn = !user;
  const showBanner = !bannerDismissed && (needsLocation || needsSignIn);

  useEffect(() => {
    // Auto-dismiss when everything is resolved
    if (!needsLocation && !needsSignIn) setBannerDismissed(true);
  }, [needsLocation, needsSignIn]);

  useEffect(() => {
    const hasLocation = location && isLocationSet;

    // Build fetch filters: include location if available, otherwise fetch locationless
    const fetchFilters = hasLocation
      ? { ...filters, lat: location.lat, lon: location.lon, radius_km: radiusKm, unique_products: true }
      : { ...filters, unique_products: true };

    // Without location, force promo_only if no search query (API requires either promo_only or q)
    if (!hasLocation && !filters.query) {
      fetchFilters.promo_only = true;
    }

    const nonPageKey = JSON.stringify({
      filters: fetchFilters,
      location: hasLocation ? location : null,
      radiusKm: hasLocation ? radiusKm : null,
    });

    const previous = previousFetchInputsRef.current;
    const effectivePage = hasLocation ? page : 1; // locationless queries pinned to page 1
    const pageChangedOnly = Boolean(
      previous &&
      previous.page !== effectivePage &&
      previous.nonPageKey === nonPageKey
    );

    previousFetchInputsRef.current = { page: effectivePage, nonPageKey };

    if (pageChangedOnly) {
      fetchProducts(fetchFilters, effectivePage);
      return;
    }

    clearProducts();

    const timer = window.setTimeout(() => {
      fetchProducts(fetchFilters, effectivePage);
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
            {/* Combined prompt banner — location + sign-in in one block */}
            {showBanner && (
              <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 mb-4 flex items-center justify-between gap-4">
                <div className="flex flex-col gap-1.5 min-w-0">
                  {needsLocation && (
                    <div className="flex items-center gap-2.5">
                      <MapPin className="h-4 w-4 text-primary flex-shrink-0" />
                      <p className="text-sm text-foreground">
                        <button
                          onClick={requestAutoLocation}
                          disabled={locationLoading}
                          className="font-medium text-primary hover:underline"
                        >
                          {locationLoading ? 'Getting location...' : 'Enable location'}
                        </button>
                        {' '}to see nearby store prices.
                        {' '}
                        <button
                          onClick={openLocationModal}
                          className="text-primary/70 hover:underline text-xs"
                        >
                          Set manually
                        </button>
                      </p>
                    </div>
                  )}
                  {needsSignIn && (
                    <div className="flex items-center gap-2.5">
                      <Bell className="h-4 w-4 text-primary flex-shrink-0" />
                      <p className="text-sm text-foreground">
                        <Link to="/register" className="font-medium text-primary hover:underline">
                          Create an account
                        </Link>
                        {' '}to get notified when prices drop.
                      </p>
                    </div>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setBannerDismissed(true)}
                  className="flex-shrink-0 h-8 w-8 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            )}

            {locationError && !isLocationSet && (
              <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                <p className="text-sm text-destructive">{locationError}</p>
              </div>
            )}

            {/* Mobile filter chips */}
            <FilterChips />

            {error && (
              <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 mb-4">
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            {/* Results count */}
            {!loading && products.length > 0 && (
              <div className="mb-4 text-sm text-muted-foreground">
                {!isLocationSet && (
                  <span className="text-primary/70 mr-2">Showing nationwide results ·</span>
                )}
                {total === 0
                  ? 'No products found'
                  : `${(currentPage - 1) * 24 + 1}–${Math.min(currentPage * 24, total)} of ${total} products`}
              </div>
            )}

            <ProductGrid
              products={products}
              loading={loading}
            />

            {/* Pagination — only when location is set (locationless queries are page-1 only) */}
            {isLocationSet && !loading && products.length > 0 && totalPages > 1 && (
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
                <p className="text-sm text-muted-foreground/70 mt-1">
                  {!isLocationSet
                    ? 'Try enabling location for more results, or adjust your search'
                    : 'Try adjusting your filters or search terms'}
                </p>
              </div>
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
  );
};

export default Explore;
