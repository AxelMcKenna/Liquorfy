import React from 'react';
import { Store as StoreIcon } from 'lucide-react';
import type { ChainType } from '@/types';
import { SuperLiquorLogo } from './SuperLiquorLogo';
import { LiquorlandLogo } from './LiquorlandLogo';
import { CountdownLogo } from './CountdownLogo';
import { NewWorldLogo } from './NewWorldLogo';
import { PaknSaveLogo } from './PaknSaveLogo';
import { BottleOLogo } from './BottleOLogo';
import { LiquorCentreLogo } from './LiquorCentreLogo';
import { GlengarryLogo } from './GlengarryLogo';
import { ThirstyLiquorLogo } from './ThirstyLiquorLogo';
import { BlackBullLogo } from './BlackBullLogo';
import { BigBarrelLogo } from './BigBarrelLogo';

interface ChainLogoProps {
  chain: string;
  className?: string;
  color?: string;
}

/**
 * ChainLogo component - Renders the appropriate logo for a given liquor store chain
 *
 * @param chain - The chain identifier (e.g., "super_liquor", "countdown")
 * @param className - Optional className for sizing and styling
 * @param color - Optional color override (defaults to chain's brand color)
 */
export const ChainLogo: React.FC<ChainLogoProps> = ({ chain, className, color }) => {
  // Map chain IDs to their respective logo components
  const logoComponents: Record<ChainType, React.FC<{ className?: string; color?: string }>> = {
    super_liquor: SuperLiquorLogo,
    liquorland: LiquorlandLogo,
    countdown: CountdownLogo,
    new_world: NewWorldLogo,
    paknsave: PaknSaveLogo,
    bottle_o: BottleOLogo,
    liquor_centre: LiquorCentreLogo,
    glengarry: GlengarryLogo,
    thirsty_liquor: ThirstyLiquorLogo,
    black_bull: BlackBullLogo,
    big_barrel: BigBarrelLogo,
  };

  const LogoComponent = logoComponents[chain as ChainType];

  // If we have a logo for this chain, render it
  if (LogoComponent) {
    return <LogoComponent className={className} color={color} />;
  }

  // Fallback to generic store icon for unknown chains
  return <StoreIcon className={className} style={{ color }} />;
};

export default React.memo(ChainLogo);
