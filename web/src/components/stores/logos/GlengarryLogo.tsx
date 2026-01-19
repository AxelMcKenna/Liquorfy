import React from 'react';
import glengarryLogo from '@/assets/logos/glengarry.png';

interface LogoProps {
  className?: string;
  color?: string;
}

export const GlengarryLogo: React.FC<LogoProps> = ({ className = "h-4 w-4" }) => {
  return (
    <img
      src={glengarryLogo}
      alt="Glengarry logo"
      className={className}
      style={{ objectFit: 'contain' }}
    />
  );
};

export default React.memo(GlengarryLogo);
