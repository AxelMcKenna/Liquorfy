import React from 'react';
import newWorldLogo from '@/assets/logos/new_world.svg';

interface LogoProps {
  className?: string;
  color?: string;
}

export const NewWorldLogo: React.FC<LogoProps> = ({ className = "h-4 w-4" }) => {
  return (
    <img
      src={newWorldLogo}
      alt="New World logo"
      className={className}
      style={{ objectFit: 'contain' }}
    />
  );
};

export default React.memo(NewWorldLogo);
