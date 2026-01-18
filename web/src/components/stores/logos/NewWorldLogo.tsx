import React from 'react';

interface LogoProps {
  className?: string;
  color?: string;
}

export const NewWorldLogo: React.FC<LogoProps> = ({ className = "h-4 w-4", color = "#a855f7" }) => {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Stylized "NW" monogram */}
      <path
        d="M3 4H5L10 14V4H12V20H10L5 10V20H3V4Z"
        fill={color}
      />
      <path
        d="M14 4H16L18 10L20 4H22L19 14L22 20H20L18 14L16 20H14L17 14L14 4Z"
        fill={color}
      />
    </svg>
  );
};

export default React.memo(NewWorldLogo);
