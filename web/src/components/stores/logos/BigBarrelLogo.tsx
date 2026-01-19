import React from 'react';
import bigBarrelLogo from '@/assets/logos/big_barrel.jpeg';

interface LogoProps {
  className?: string;
  color?: string;
}

export const BigBarrelLogo: React.FC<LogoProps> = ({ className = "h-4 w-4" }) => {
  return (
    <img
      src={bigBarrelLogo}
      alt="Big Barrel logo"
      className={className}
      style={{ objectFit: 'contain' }}
    />
  );
};

export default React.memo(BigBarrelLogo);
