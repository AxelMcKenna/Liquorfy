import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'liquorfy_favourites';

function readFavourites(): Set<string> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? new Set(JSON.parse(stored)) : new Set();
  } catch {
    return new Set();
  }
}

export const useFavourites = () => {
  const [favouriteIds, setFavouriteIds] = useState<Set<string>>(readFavourites);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...favouriteIds]));
  }, [favouriteIds]);

  // Sync across tabs
  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key === STORAGE_KEY) {
        setFavouriteIds(readFavourites());
      }
    };
    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  const toggleFavourite = useCallback((productId: string) => {
    setFavouriteIds((prev) => {
      const next = new Set(prev);
      if (next.has(productId)) {
        next.delete(productId);
      } else {
        next.add(productId);
      }
      return next;
    });
  }, []);

  const isFavourite = useCallback(
    (productId: string) => favouriteIds.has(productId),
    [favouriteIds]
  );

  const favouriteCount = favouriteIds.size;

  return { favouriteIds, toggleFavourite, isFavourite, favouriteCount };
};
