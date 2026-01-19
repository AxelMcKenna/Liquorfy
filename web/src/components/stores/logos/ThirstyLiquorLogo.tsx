import React from 'react';
import thirstyLiquorLogo from '@/assets/logos/thirsty_liquor.png';

interface LogoProps {
  className?: string;
  color?: string;
}

export const ThirstyLiquorLogo: React.FC<LogoProps> = ({ className = "h-4 w-4" }) => {
  return (
    <img
      src={thirstyLiquorLogo}
      alt="Thirsty Liquor logo"
      className={className}
      style={{ objectFit: 'contain' }}
    />
  );
};

export default React.memo(ThirstyLiquorLogo);
