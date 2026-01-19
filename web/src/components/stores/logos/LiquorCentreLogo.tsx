import React from 'react';
import liquorCentreLogo from '@/assets/logos/liquor_centre.png';

interface LogoProps {
  className?: string;
  color?: string;
}

export const LiquorCentreLogo: React.FC<LogoProps> = ({ className = "h-4 w-4" }) => {
  return (
    <img
      src={liquorCentreLogo}
      alt="Liquor Centre"
      className={className}
      style={{ objectFit: 'contain' }}
    />
  );
};

export default React.memo(LiquorCentreLogo);
