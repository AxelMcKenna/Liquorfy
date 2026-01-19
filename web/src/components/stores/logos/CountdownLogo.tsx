import React from 'react';
import countdownLogo from '@/assets/logos/countdown.svg';

interface LogoProps {
  className?: string;
  color?: string;
}

export const CountdownLogo: React.FC<LogoProps> = ({ className = "h-4 w-4" }) => {
  return (
    <img
      src={countdownLogo}
      alt="Countdown logo"
      className={className}
      style={{ objectFit: 'contain' }}
    />
  );
};

export default React.memo(CountdownLogo);
