import React from 'react';
import bottleOLogo from '@/assets/logos/bottle_o.png';

interface LogoProps {
  className?: string;
  color?: string;
}

export const BottleOLogo: React.FC<LogoProps> = ({ className = "h-4 w-4" }) => {
  return (
    <img
      src={bottleOLogo}
      alt="Bottle-O logo"
      className={className}
      style={{ objectFit: 'contain' }}
    />
  );
};

export default React.memo(BottleOLogo);
