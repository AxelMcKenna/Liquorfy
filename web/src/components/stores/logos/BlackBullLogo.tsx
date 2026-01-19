import React from 'react';
import blackBullLogo from '@/assets/logos/black_bull.png';

interface LogoProps {
  className?: string;
  color?: string;
}

export const BlackBullLogo: React.FC<LogoProps> = ({ className = "h-4 w-4" }) => {
  return (
    <img
      src={blackBullLogo}
      alt="Black Bull logo"
      className={className}
      style={{ objectFit: 'contain' }}
    />
  );
};

export default React.memo(BlackBullLogo);
