/**
 * Centralized constants for liquor store chains
 *
 * This file provides a single source of truth for chain-related data including
 * brand colors and display names used throughout the application.
 */

import type { ChainType } from '@/types';

/**
 * Brand colors for each liquor store chain (hex format)
 * Used for map markers, badges, and other brand-specific UI elements
 */
export const chainColors: Record<ChainType, string> = {
  super_liquor: '#ef4444',    // Red
  liquorland: '#3b82f6',      // Blue
  countdown: '#22c55e',       // Green
  new_world: '#a855f7',       // Purple
  paknsave: '#eab308',        // Yellow
  bottle_o: '#f97316',        // Orange
  liquor_centre: '#6366f1',   // Indigo
  glengarry: '#ec4899',       // Pink
  thirsty_liquor: '#14b8a6',  // Teal
  black_bull: '#1f2937',      // Dark Gray/Charcoal
};

/**
 * Display names for each liquor store chain
 * Used in UI labels, popups, and filters
 */
export const chainNames: Record<ChainType, string> = {
  super_liquor: 'Super Liquor',
  liquorland: 'Liquorland',
  countdown: 'Countdown',
  new_world: 'New World',
  paknsave: "PAK'nSAVE",
  bottle_o: 'Bottle-O',
  liquor_centre: 'Liquor Centre',
  glengarry: 'Glengarry',
  thirsty_liquor: 'Thirsty Liquor',
  black_bull: 'Black Bull',
};

/**
 * Tailwind CSS background color classes for each chain
 * Used in components that need Tailwind class names (e.g., badges)
 */
export const chainColorClasses: Record<ChainType, string> = {
  super_liquor: 'bg-red-500',
  liquorland: 'bg-blue-500',
  countdown: 'bg-green-500',
  new_world: 'bg-purple-500',
  paknsave: 'bg-yellow-500',
  bottle_o: 'bg-orange-500',
  liquor_centre: 'bg-indigo-500',
  glengarry: 'bg-pink-500',
  thirsty_liquor: 'bg-teal-500',
  black_bull: 'bg-gray-800',
};

/**
 * Get the color for a given chain, with fallback
 */
export const getChainColor = (chain: string): string => {
  return chainColors[chain as ChainType] || '#6b7280'; // Gray fallback
};

/**
 * Get the display name for a given chain, with fallback
 */
export const getChainName = (chain: string): string => {
  return chainNames[chain as ChainType] || chain;
};

/**
 * Get the Tailwind class for a given chain, with fallback
 */
export const getChainColorClass = (chain: string): string => {
  return chainColorClasses[chain as ChainType] || 'bg-gray-500';
};
