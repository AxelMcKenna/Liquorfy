import React from 'react';
import superLiquorLogo from '@/assets/logos/super_liquor.png';

interface LogoProps {
  className?: string;
  color?: string;
}

export const SuperLiquorLogo: React.FC<LogoProps> = ({ className = "h-4 w-4" }) => {
  return (
    <img
      src={superLiquorLogo}
      alt="Super Liquor logo"
      className={className}
      style={{ objectFit: 'contain' }}
    />
  );
};

export default React.memo(SuperLiquorLogo);
