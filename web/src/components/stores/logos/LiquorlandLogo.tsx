import React from 'react';
import liquorlandLogo from '@/assets/logos/liquorland.svg';

interface LogoProps {
  className?: string;
  color?: string;
}

export const LiquorlandLogo: React.FC<LogoProps> = ({ className = "h-4 w-4" }) => {
  return (
    <img
      src={liquorlandLogo}
      alt="Liquorland logo"
      className={className}
      style={{ objectFit: 'contain' }}
    />
  );
};

export default React.memo(LiquorlandLogo);
