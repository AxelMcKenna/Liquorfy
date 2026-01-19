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
  super_liquor: '#0066cc',    // Blue
  liquorland: '#50b848',      // Brand green
  countdown: '#00984f',       // Brand green
  new_world: '#e11a2c',       // Brand red
  paknsave: '#ffd600',        // Brand yellow
  bottle_o: '#00984f',        // Brand green
  liquor_centre: '#84cfca',   // Light blue/teal
  glengarry: '#111111',       // Brand black
  thirsty_liquor: '#f6861e',  // Brand orange
  black_bull: '#111827',      // Brand black
  big_barrel: '#431717',      // Brand maroon
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
  big_barrel: 'Big Barrel',
};

/**
 * Tailwind CSS background color classes for each chain
 * Used in components that need Tailwind class names (e.g., badges)
 */
export const chainColorClasses: Record<ChainType, string> = {
  super_liquor: 'bg-[#0066cc]',
  liquorland: 'bg-[#50b848]',
  countdown: 'bg-[#00984f]',
  new_world: 'bg-[#e11a2c]',
  paknsave: 'bg-[#ffd600]',
  bottle_o: 'bg-[#00984f]',
  liquor_centre: 'bg-[#84cfca]',
  glengarry: 'bg-[#111111]',
  thirsty_liquor: 'bg-[#f6861e]',
  black_bull: 'bg-[#111827]',
  big_barrel: 'bg-[#431717]',
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
