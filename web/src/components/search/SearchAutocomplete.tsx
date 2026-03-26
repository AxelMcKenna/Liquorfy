import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Clock, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import api from '@/lib/api';
import { ProductListResponse } from '@/types';
import { useLocationContext } from '@/contexts/LocationContext';
import { cn } from '@/lib/utils';

const RECENT_SEARCHES_KEY = 'liquorfy_recent_searches';
const MAX_RECENT = 5;
const DEBOUNCE_MS = 250;

function getRecentSearches(): string[] {
  try {
    return JSON.parse(localStorage.getItem(RECENT_SEARCHES_KEY) || '[]');
  } catch {
    return [];
  }
}

function addRecentSearch(query: string) {
  const trimmed = query.trim();
  if (!trimmed) return;
  const recent = getRecentSearches().filter(s => s !== trimmed);
  recent.unshift(trimmed);
  localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(recent.slice(0, MAX_RECENT)));
}

function removeRecentSearch(query: string) {
  const recent = getRecentSearches().filter(s => s !== query);
  localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(recent));
}

interface Suggestion {
  id: string;
  name: string;
  brand?: string | null;
  price: number;
  image_url?: string | null;
}

interface SearchAutocompleteProps {
  query: string;
  setQuery: (query: string) => void;
  onSearch: () => void;
  placeholder?: string;
  className?: string;
  inputClassName?: string;
}

export const SearchAutocomplete = ({
  query,
  setQuery,
  onSearch,
  placeholder = 'Search products...',
  className,
  inputClassName,
}: SearchAutocompleteProps) => {
  const navigate = useNavigate();
  const { location, radiusKm, isLocationSet } = useLocationContext();
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [recentSearches, setRecentSearches] = useState<string[]>(getRecentSearches);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<number | null>(null);

  const showRecent = isOpen && !query.trim() && recentSearches.length > 0;
  const showSuggestions = isOpen && query.trim().length >= 2 && suggestions.length > 0;
  const showDropdown = showRecent || showSuggestions;

  // Fetch suggestions
  const fetchSuggestions = useCallback(async (q: string) => {
    abortRef.current?.abort();
    const trimmed = q.trim();
    if (trimmed.length < 2) {
      setSuggestions([]);
      return;
    }

    const controller = new AbortController();
    abortRef.current = controller;
    setLoadingSuggestions(true);

    try {
      const params = new URLSearchParams({ q: trimmed, page_size: '6', page: '1', unique_products: 'true' });
      if (isLocationSet && location) {
        params.append('lat', location.lat.toString());
        params.append('lon', location.lon.toString());
        params.append('radius_km', radiusKm.toString());
      }
      const { data } = await api.get<ProductListResponse>('/products', {
        params,
        signal: controller.signal,
      });
      setSuggestions(data.items.map(p => ({
        id: p.id,
        name: p.name,
        brand: p.brand,
        price: p.price.promo_price_nzd ?? p.price.price_nzd,
        image_url: p.image_url,
      })));
    } catch {
      // cancelled or failed — ignore
    } finally {
      setLoadingSuggestions(false);
    }
  }, [isLocationSet, location, radiusKm]);

  // Debounced fetch
  useEffect(() => {
    if (debounceRef.current) window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => {
      fetchSuggestions(query);
    }, DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current);
    };
  }, [query, fetchSuggestions]);

  // Close on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  // Reset active index when dropdown content changes
  useEffect(() => {
    setActiveIndex(-1);
  }, [suggestions, recentSearches, query]);

  const executeSearch = (searchQuery: string) => {
    const trimmed = searchQuery.trim();
    if (trimmed) addRecentSearch(trimmed);
    setRecentSearches(getRecentSearches());
    setQuery(trimmed);
    setIsOpen(false);
    onSearch();
  };

  const navigateToProduct = (id: string) => {
    setIsOpen(false);
    navigate(`/product/${id}`);
  };

  const handleRemoveRecent = (e: React.MouseEvent, search: string) => {
    e.stopPropagation();
    removeRecentSearch(search);
    setRecentSearches(getRecentSearches());
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!showDropdown) {
      if (e.key === 'Enter') {
        executeSearch(query);
      }
      return;
    }

    const items = showRecent ? recentSearches : suggestions;
    const count = items.length;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setActiveIndex(prev => (prev + 1) % count);
        break;
      case 'ArrowUp':
        e.preventDefault();
        setActiveIndex(prev => (prev - 1 + count) % count);
        break;
      case 'Enter':
        e.preventDefault();
        if (activeIndex >= 0 && activeIndex < count) {
          if (showRecent) {
            executeSearch(recentSearches[activeIndex]);
          } else {
            navigateToProduct(suggestions[activeIndex].id);
          }
        } else {
          executeSearch(query);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        break;
    }
  };

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground z-10" />
      <Input
        placeholder={placeholder}
        value={query}
        onChange={(e) => { setQuery(e.target.value); setIsOpen(true); }}
        onFocus={() => setIsOpen(true)}
        onKeyDown={handleKeyDown}
        className={cn("pl-10", inputClassName)}
        autoComplete="off"
      />

      {/* Dropdown */}
      {showDropdown && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg border border-[hsl(var(--border))] shadow-lg z-50 overflow-hidden">
          {/* Recent searches */}
          {showRecent && (
            <div className="py-1.5">
              <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-[hsl(var(--foreground-tertiary))]">
                Recent
              </p>
              {recentSearches.map((search, idx) => (
                <button
                  key={search}
                  onClick={() => executeSearch(search)}
                  className={cn(
                    "w-full flex items-center justify-between gap-2 px-3 py-2 text-sm text-left hover:bg-secondary transition-colors",
                    activeIndex === idx && "bg-secondary"
                  )}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <Clock className="h-3.5 w-3.5 text-[hsl(var(--foreground-tertiary))] flex-shrink-0" />
                    <span className="truncate text-[hsl(var(--foreground))]">{search}</span>
                  </div>
                  <button
                    onClick={(e) => handleRemoveRecent(e, search)}
                    className="text-[hsl(var(--foreground-tertiary))] hover:text-[hsl(var(--foreground))] p-0.5 flex-shrink-0"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </button>
              ))}
            </div>
          )}

          {/* Product suggestions */}
          {showSuggestions && (
            <div className="py-1.5">
              {suggestions.map((item, idx) => (
                <button
                  key={item.id}
                  onClick={() => navigateToProduct(item.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-secondary transition-colors",
                    activeIndex === idx && "bg-secondary"
                  )}
                >
                  {item.image_url ? (
                    <img src={item.image_url} alt="" className="h-8 w-8 object-contain flex-shrink-0 rounded" />
                  ) : (
                    <div className="h-8 w-8 rounded bg-secondary flex items-center justify-center flex-shrink-0">
                      <Search className="h-3 w-3 text-muted-foreground" />
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-[hsl(var(--foreground))] truncate">{item.name}</p>
                    {item.brand && (
                      <p className="text-xs text-[hsl(var(--foreground-tertiary))] truncate">{item.brand}</p>
                    )}
                  </div>
                  <span className="text-sm font-semibold text-primary flex-shrink-0">
                    ${item.price.toFixed(2)}
                  </span>
                </button>
              ))}
              {/* Search all link */}
              <button
                onClick={() => executeSearch(query)}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-primary font-medium hover:bg-secondary transition-colors border-t border-[hsl(var(--border))]"
              >
                <Search className="h-3.5 w-3.5" />
                Search all for "{query.trim()}"
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
