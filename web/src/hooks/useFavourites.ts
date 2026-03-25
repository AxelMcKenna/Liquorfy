import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'liquorfy_favourites';

export const useFavourites = () => {
  const [favouriteIds, setFavouriteIds] = useState<Set<string>>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored ? new Set(JSON.parse(stored)) : new Set();
    } catch {
      return new Set();
    }
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...favouriteIds]));
  }, [favouriteIds]);

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
