/**
 * Shared formatting utilities for consistent display across components
 */

/**
 * Distance thresholds for color coding (in km)
 */
export const DISTANCE_THRESHOLDS = {
  CLOSE: 2,    // Green - walking distance
  MEDIUM: 5,   // Yellow - short drive
} as const;

/**
 * Format distance for display
 * Returns a string like "800m" or "2.5km"
 */
export const formatDistance = (distanceKm: number | null | undefined): string | null => {
  if (distanceKm === null || distanceKm === undefined) return null;

  if (distanceKm < 1) {
    return `${Math.round(distanceKm * 1000)}m`;
  }
  return `${distanceKm.toFixed(1)}km`;
};

/**
 * Format distance with "away" suffix for fuller context
 */
export const formatDistanceAway = (distanceKm: number | null | undefined): string | null => {
  const formatted = formatDistance(distanceKm);
  if (!formatted) return null;
  return `${formatted} away`;
};

/**
 * Get distance color class based on thresholds
 * Returns semantic CSS class names
 */
export const getDistanceColorClass = (distanceKm: number | null | undefined): string => {
  if (distanceKm === null || distanceKm === undefined) return 'text-muted-foreground';

  if (distanceKm < DISTANCE_THRESHOLDS.CLOSE) {
    return 'text-distance-close';
  }
  if (distanceKm < DISTANCE_THRESHOLDS.MEDIUM) {
    return 'text-distance-medium';
  }
  return 'text-distance-far';
};

/**
 * Format promo end date for display
 * Shows relative time for nearby dates, absolute for further dates
 */
export const formatPromoEndDate = (endDate: string | null | undefined): string | null => {
  if (!endDate) return null;

  const end = new Date(endDate);
  const now = new Date();
  const diffTime = end.getTime() - now.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays < 0) return 'Expired';
  if (diffDays === 0) return 'Ends today';
  if (diffDays === 1) return 'Ends tomorrow';
  if (diffDays <= 7) return `${diffDays}d left`;

  return `Ends ${end.toLocaleDateString('en-NZ', { month: 'short', day: 'numeric' })}`;
};

/**
 * Calculate savings percentage
 */
export const calculateSavingsPercent = (
  originalPrice: number,
  promoPrice: number | null | undefined
): number => {
  if (!promoPrice || promoPrice >= originalPrice) return 0;
  return Math.round(((originalPrice - promoPrice) / originalPrice) * 100);
};

/**
 * Format price for display
 */
export const formatPrice = (price: number): string => {
  return `$${price.toFixed(2)}`;
};

/**
 * Format price per unit
 */
export const formatPricePerUnit = (price: number, unit: string): string => {
  return `${formatPrice(price)} per ${unit}`;
};
